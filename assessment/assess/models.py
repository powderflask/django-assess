import datetime, statistics, bisect, os
from django.utils.functional import cached_property
from django.urls import reverse
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from assessment import settings
from assessment.builder.models import (  # import all builder models so they are available on import assess.models
    Activity, Topic, AssessmentCategory,
    AssessmentQuestion, AssessmentMetric, ReferenceDocument
)
from assessment.assess import choices

from django.apps import apps
appConfig = apps.get_app_config('assess')


def get_assessment_subject_model():
    """ Return swappable concrete Assessment Subject model """
    return appConfig.get_assessment_subject_model()


class DraftsQueryset(models.QuerySet):
    """ Custom query set for models with drafts / complete """
    def drafts(self):
        return self.filter(status=choices.DRAFT_STATUS)

    def complete(self):
        return self.filter(status=choices.COMPLETE_STATUS)


class AssessmentQueryset(DraftsQueryset):
    def annotate_avg_score(self, field_name='score_set', annotation_name='avg_score'):
        """
            Add an annotation equivalent to: .annotate(annotation_name=Avg(field_name))
            field_name is accessor to a related field
            Note: annotation should yield same result as base model's assessment_score() method
        """
        field = '{field_name}__score'.format(field_name=field_name)
        applicable = '{field_name}__applicable'.format(field_name=field_name)
        annotation = {annotation_name : models.Avg(field, filter=models.Q(**{applicable: True}))}
        return self.annotate(**annotation)


class AssessmentManager(models.Manager):
    def get_queryset(self):
        subject = appConfig.get_assessment_subject_related_name()
        select = (subject, 'group', 'category', 'category__topic', 'category__activity')
        prefetch = ('score_set', 'score_set__doc_set', 'score_set__metric')
        return super().get_queryset().select_related(*select)\
                                     .prefetch_related(*prefetch)\
                                     .annotate_avg_score()

class AssessmentSetManager(models.Manager):
    def get_queryset(self):
        assessment_set_subject = 'assessment_set__{}'.format(appConfig.get_assessment_subject_related_name())
        prefetch = ('assessment_set', assessment_set_subject, 'assessment_set__score_set',
                    'assessment_set__score_set__doc_set', 'assessment_set__score_set__metric')

        return super().get_queryset().select_related('activity', 'topic')\
                                     .prefetch_related(*prefetch)\
                                     .annotate_avg_score(field_name='assessment_set__score_set')


class AbstractAssessmentRecord(models.Model):
    """ Fields and methods common to models that represent a set of assessment questions / metric records """
    created = models.DateField(auto_now_add=True)
    assessor = models.ForeignKey(get_user_model(), verbose_name='Assessed by',
                                 on_delete=models.DO_NOTHING, related_name='assessment_set')
    assessment_type = models.CharField(max_length=16, choices=choices.ASSESSMENT_TYPE_CHOICES, verbose_name='Type')
    status = models.CharField(max_length=16, choices=choices.STATUS_CHOICES, default=choices.DRAFT_STATUS)

    class Meta:
        abstract = True

    @property
    def applicable_scores(self):
        """ Return iterable of applicable metric scores for this Assessment Record """
        raise NotImplementedError

    def assessment_score(self):
        """ Average metric scores on this assessment """
        try:  # try getting query annotation first, calculate mean as a backup (force lazy eval to avoid extra queries)
            return self.avg_score
        except AttributeError:
            try:
                return statistics.mean(metric.score for metric in self.applicable_scores)
            except statistics.StatisticsError:  # e.g., all scores were None.
                return 0

    @property
    def score_class(self):
        # bisect will crash on None - treat as a zero.
        index = bisect.bisect(appConfig.settings.SCORE_CLASSES, (self.assessment_score() or 0, ))
        return appConfig.settings.SCORE_CLASSES[index][1]


class AssessmentGroup(AbstractAssessmentRecord):
    """
        Group of Assessment Records for a single Activity OR Topic
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                 null=True, blank=True, related_name='assessment_group_set')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE,
                              null=True, blank=True, related_name='assessment_group_set')
    assessor = models.ForeignKey(get_user_model(), verbose_name='Assessed by',
                                 on_delete=models.DO_NOTHING, related_name='assessment_group_set')

    objects = AssessmentSetManager.from_queryset(AssessmentQueryset)()

    class Meta:
        constraints = [
            models.CheckConstraint(check=(models.Q(topic=None) | models.Q(activity=None)) &
                                         (~models.Q(topic=None) | ~models.Q(activity=None)),
                                   name='group_exclusive_activity_or_topic'),
        ]
        verbose_name = 'Assessment Set'

    def __str__(self):
        return self.root.label

    def get_absolute_url(self):
        return reverse('assessment.assess:group-detail', args=(self.pk, ))

    def get_update_url(self):
        return reverse('assessment.assess:group-update', args=(self.pk, ))

    def get_delete_url(self):
        return reverse('assessment.assess:group-delete', args=(self.pk, ))

    def clean(self):
        # A group must define exactly one of activity or topic
        def xor(a, b): return (a or b) and not (a and b)
        if not xor(self.topic, self.activity):
            raise ValidationError({'activity': 'Assessment group must define either Activity or Topic, not both.'})

    def save(self, *args, **kwargs):
        """ Set the status for all Assessments in this Group """
        super().save(*args, **kwargs)
        self.assessment_set.all().update(status=self.status)

    @property
    def is_activity_group(self):
        return bool(self.activity_id)

    @property
    def is_topic_group(self):
        return bool(self.topic_id)

    @property
    def root(self):
        """ the 'root node' object for this group (an Activity or Topic object """
        return self.activity if self.is_activity_group else self.topic

    @property
    def category_set(self):
        """ Return queryset for complete set of active categories covered by this Group """
        return AssessmentCategory.active.filter(topic=self.topic) if self.is_topic_group else \
            AssessmentCategory.active.filter(activity=self.activity)

    @property
    def reference_docs(self):
        """ Return queryset for complete set of reference docs for all categories in this Group """
        return self.root.reference_docs

    @property
    def metric_set(self):
        """ Return queryset for complete set of metrics for all Assessments in this Group """
        return AssessmentMetric.objects.filter(question__category__in=self.category_set)

    @property
    def score_set(self):
        """ Return queryset for complete set of metric scores for all Assessments in this Group """
        return MetricScore.objects.filter(assessment__group=self)

    @property
    def applicable_scores(self):
        """ Return queryset for set of applicable metric scores for all Assessments in this Group """
        return MetricScore.applies.filter(assessment__group=self)

    @property
    def subject(self):
        """ Return the AssessmentSubject object from one of the Assessments in this group """
        return getattr(self.assessment_set.first(), 'subject', None)

    @cached_property
    def last_edited_assessment(self):
        """ Return the most recently edited Assessment in this group """
        return self.assessment_set.order_by('-last_edited').first()

    @property
    def last_edited(self):
        """ Return the edit date of most recently edited Assessment in this group """
        return self.last_edited_assessment.last_edited

    @property
    def last_edited_by(self):
        """ Return the user who most recently edited an Assessment in this group """
        return self.last_edited_assessment.last_edited_by

    def scores_by_question(self):
        return self.score_set.all().order_by('metric__question')

    def create_assessment_set_from_template(self, assessment):
        """ Create a complete set of Assessments for this Group, using given assessment as template """
        # Exclude categories for which there is already an assessment in this group
        assert self.pk is not None, 'AssessmentSet must be saved before attempting to load with assessments'
        categories = self.category_set.exclude(pk__in=self.assessment_set.all().values_list('category__pk', flat=True))
        assessment.group = self
        assessment.status = self.status
        subject = assessment.subject
        for cat in categories:
            assessment.pk = None
            assessment.category = cat
            assessment.save()
            subject.pk = None
            subject.record = assessment
            subject.save()


class AssessmentRecord(AbstractAssessmentRecord):
    """
        A record of a single assessment performed for a single AssessmentCategory
        Assessments may be completed as a Group (e.g., across all Topics or across all Activities)
            Grouped AssessmentRecords share the same "group" value, which is a unique identifier for such groups
    """
    category = models.ForeignKey(AssessmentCategory,
                                 on_delete=models.CASCADE, related_name='assessment_set')
    group = models.ForeignKey(AssessmentGroup, null=True, blank=True,
                              on_delete=models.CASCADE, related_name='assessment_set')
    last_edited = models.DateTimeField(auto_now=True)
    last_edited_by = models.ForeignKey(get_user_model(),
                                       on_delete=models.DO_NOTHING, related_name='+')

    objects = AssessmentManager.from_queryset(AssessmentQueryset)()

    class Meta:
        ordering = ('category__topic__order', 'category__activity__order', '-created', )
        verbose_name = 'Assessment Record'

    def __str__(self):
        cat = str(self.group) if self.is_in_assessment_group() else str(self.category)
        return '{subject} ({cat}): {created:%b-%Y}'.format(subject=self.subject if self.has_subject else '',
                                                           cat=self.category, created=self.created)

    def get_absolute_url(self):
        return reverse('assessment.assess:detail', args=(self.pk, ))

    def get_update_url(self):
        return reverse('assessment.assess:update', args=(self.pk, ))

    def get_delete_url(self):
        return reverse('assessment.assess:delete', args=(self.pk, ))

    def get_subject(self):
        """ Return the subject for this assessment record """
        subject_field = appConfig.get_assessment_subject_related_name()
        return getattr(self, subject_field, None)

    def set_subject(self, subject):
        """ Set the subject for this assessment record """
        subject_field = appConfig.get_assessment_subject_related_name()
        setattr(self, subject_field, subject)

    subject = property(get_subject, set_subject)

    @property
    def has_subject(self):
        """  No assessment assess should exist without a subject, but hard to force this at ref. integrity layer """
        try:
            return self.subject is not None
        except get_assessment_subject_model().DoesNotExist:
            return False

    def _create_score_set(self):
        """ Creates a complete set of related metric scores for this EMPTY assessment """
        assert self.score_set.count() == 0  # ONLY allowed on new records with no assessments
        scores = [
            MetricScore(assessment=self, metric=metric) for question in self.category.question_set.all()
            for metric in question.metric_set.all()
        ]
        MetricScore.objects.bulk_create(scores)

    def save(self, *args, **kwargs):
        """ On create, configure a set of 'empty' MetricScores for this Assessment """
        adding = not self.pk
        super().save(*args, **kwargs)
        if adding:
            self._create_score_set()

    @property
    def metric_set(self):
        """ Return queryset for complete set of metrics for this Assessment"""
        return AssessmentMetric.objects.filter(question__category=self.category)

    @property
    def applicable_scores(self):
        """ Return queryset for set of applicable metric scores for all Assessments in this Group """
        return MetricScore.applies.filter(assessment=self)

    def scores_by_question(self):
        return self.score_set.all().order_by('metric__question')

    def is_in_assessment_group(self):
        """ Return True iff this assessment is part of a larger group """
        return self.group is not None
    is_in_assessment_group.short_description = 'In assessment group?'

    def group_assessments(self):
        """ Return a queryset with all assessments in same group as this one """
        return self.group.assessment_set.all() if self.is_in_assessment_group() else \
            AssessmentRecord.objects.filter(pk=self.pk)


class AbstractAssessmentSubject(models.Model):
    """
        The subject of an Assessment (i.e, what is the person, project, thing being assessed)
        Every AssessmentRecord MUST have exactly one AssessmentSubject.
        This is a "swappable" model -- clients define their own by supplying a model (usually a sub-class)
             that implements this interface.
    """
    # Re: blank=True - no other reasonable way to validate modelforms that don't include required field ** sigh **
    # Re: related_name - see https://docs.djangoproject.com/en/2.2/topics/db/models/#be-careful-with-related-name-and-related-query-name
    record = models.OneToOneField(AssessmentRecord, blank=True, on_delete=models.CASCADE,
                                  related_name='%(app_label)s_%(class)s')

    class Meta:
        abstract = True
        verbose_name = 'Assessment Subject'

    def __str__(self):
        """ Concrete implementations should override this to provide a user-friendly label for subject """
        return "Subject-{}".format(self.pk)

    @classmethod
    def get_modelform(cls):
        """ Concrete implementations MUST supply method that returns a modelform for this model """
        raise NotImplemented


class AssessmentSubject(AbstractAssessmentSubject):
    """
        Default Concrete Assessment Subject, can be overridden with ASSESSMENT_SUBJECT_MODEL setting.
    """
    label = models.CharField(max_length=128,  verbose_name='Subject',
                             help_text='Short label for the subject of this assessment')
    description = models.TextField(blank=True,
                                   help_text='Optional longer description of the assessment subject.')

    def __str__(self):
        return self.label

    @classmethod
    def get_modelform(cls, **kwargs):
        """ return a modelform used to create / edit this model """
        from django import forms
        if not 'exclude' in kwargs:
            kwargs['fields'] = kwargs.get('fields', ('label', 'description', 'record'))
        kwargs['widgets'] = kwargs.get('widgets',
                                       {
                                          'description': forms.Textarea(attrs={'rows': 2, 'cols': 80}),
                                          'record'     : forms.HiddenInput()
                                       })
        return forms.modelform_factory(cls, **kwargs)


class ScoreManager(models.Manager):
    def get_queryset(self):
        related = ('metric', 'metric__question', 'assessment', 'assessment__category', )
        return super().get_queryset().select_related(*related)


class ApplicableScoreManager(ScoreManager):
    def get_queryset(self):
        return super().get_queryset().filter(applicable=True)


class MetricScore(models.Model):
    """
        Records the score for a single AssessmentMetric within an AssessmentRecord
    """
    assessment = models.ForeignKey(AssessmentRecord, on_delete=models.CASCADE, related_name='score_set')
    metric = models.ForeignKey(AssessmentMetric, on_delete=models.CASCADE, related_name='score_set')
    applicable = models.BooleanField(default=True)
    score = models.PositiveSmallIntegerField(choices=choices.SCORE_CHOICES, default=choices.SCORE_CHOICES[0][0])
    comments = models.TextField(blank=True)

    objects = ScoreManager()
    applies = ApplicableScoreManager()

    class Meta:
        ordering = ('assessment', 'metric__question', )

    def __str__(self):
        return '{metric}: {score}'.format(metric=self.metric, score=self.get_score())

    def get_score(self):
        return self.score if self.applicable else "N/A"

    def get_score_display(self):
        return self.metric.get_choice_display(self.score)

    @property
    def score_class(self):
        return 'not-applicable' if not self.applicable else \
                'score-{}'.format(self.score)

    def clean(self):
        # Don't allow metrics from a different category than the assessment.
        # Careful - some forms need to validate before assessment is set.
        if self.assessment_id and self.metric.question.category_id != self.assessment.category_id:
            raise ValidationError(
                {'metric': 'Invalid metric for assessment in category {}.'.format(self.assessment.category)}
            )
        # Check score is permitted for metric.
        if not self.metric.validate(self.score):
            raise ValidationError(
                {'score': 'Invalid score for this metric ({choices})'.format(choices=self.metric.choices)}
            )


def supporting_doc_directory_path(instance, filename):
    """ Return directory path under MEDIA_ROOT (or PRIVATE_STORAGE_ROOT) where SupportingDoc file attachments live """
    # .../support_docs/<assessment slug>/<metric slug>/year/<filename>
    metric = instance.score.metric
    path = {
        'assessment': metric.question.category.slug,
        'metric':     metric.slug,
        'year':       datetime.date.today().year,
        'filename':   filename
    }
    return 'support_docs/{assessment}/{metric}/{year}/{filename}'.format(**path)


class SupportingDoc(models.Model):
    """
        Documentation attached to a particular metric score - paper trail for how the score was derived
    """
    score = models.ForeignKey(MetricScore, on_delete=models.CASCADE, related_name='doc_set')
    document_type = models.CharField(max_length=64, choices=choices.DOCUMENT_TYPE_CHOICES,
                                     default=choices.DOCUMENT_TYPE_NONE)
    document_location = models.CharField(max_length=64, choices=choices.DOCUMENT_LOCATION_CHOICES,
                                         default=choices.DOCUMENT_LOCATION_ATTACHED)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    if appConfig.settings.USE_PRIVATE_FILES:
        from private_storage.fields import PrivateFileField
        file = PrivateFileField(null=True, blank=True, upload_to=supporting_doc_directory_path)
    else:
        file = models.FileField(null=True, blank=True, upload_to=supporting_doc_directory_path)

    def __str__(self):
        doc = self.url if self.url else os.path.basename(self.file.path) if self.file else self.description
        return '{doc}'.format(doc=doc)

    @property
    def href(self):
        return self.file.url if self.file else self.url if self.url else None
