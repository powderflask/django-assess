import json

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.db import models
from ordered_model.models import OrderedModelManager, OrderedModel
from . import choices, validators


class ActiveManager(models.Manager):
    """ Custom query manager for models with publication status """
    def get_queryset(self):
        return super().get_queryset().filter(status=choices.ACTIVE_STATUS)


class StatusMix(models.Model):
    status = models.CharField(max_length=8, choices=choices.STATUS_CHOICES, default=choices.ACTIVE_STATUS)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        abstract = True

    @property
    def is_active(self):
        """ Is this category active (visible to users) """
        return self.status == choices.ACTIVE_STATUS


# TODO: more base classes and managers here to mix status and ordered models / querysets
#       currently ordered querysets include inactive records and active querysets are not ordered.

class AbstractClassification(StatusMix, OrderedModel):
    """
        Base class for defining assessment categories
    """
    label = models.CharField(max_length=64,
                            help_text='Unique label for this classification. e.g., Education & Research')
    slug = models.SlugField(unique=True, max_length=64,
                            help_text='Unique, short abbreviation e.g., edu-research for Education & Research')
    description = models.TextField(blank=True,
                                   help_text='Optional description of the classification.')

    objects = OrderedModelManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.label

    @property
    def reference_docs(self):
        """ Return queryset for complete set of reference docs for all categories in this Group """
        return ReferenceDocument.objects.filter(category__in=self.category_set.all())


class Activity(AbstractClassification):
    """
        Type of activity being assessed - categories of things to assess
        Typically these are the "big picture" activities an organization conducts in pursuit of its mission
        E.g.  Teaching & Learning
    """
    class Meta(AbstractClassification.Meta):
        ordering = ('order',)
        verbose_name = "Activity"
        verbose_name_plural = "1. Activities"
        constraints = [
            models.UniqueConstraint(fields=['label'], condition=models.Q(status='active'), name='activity_unique_active_label'),
        ]

    def get_absolute_url(self):
        return reverse('assessment.assess:activity', args=(self.slug, ))


class Topic(AbstractClassification):
    """
        Type of concerns being assessed - categories on which an activity might be assessed
        Typically, these are the "big picture" values represented in an organization's mission
        E.g., Quality, Cost, Experience, etc.
    """
    class Meta(AbstractClassification.Meta):
        ordering = ('order',)
        verbose_name = "Topic"
        verbose_name_plural = "2. Topics"
        constraints = [
            models.UniqueConstraint(fields=['label'], condition=models.Q(status='active'), name='topic_unique_active_label'),
        ]

    def get_absolute_url(self):
        return reverse('assessment.assess:topic', args=(self.slug, ))


class ActiveCategoryManager(models.Manager):
    """ Custom query manager for active AssessmentCategory - their topic and activity must be active also """
    def get_queryset(self):
        return super().get_queryset().filter(status=choices.ACTIVE_STATUS)\
                                     .filter(activity__status=choices.ACTIVE_STATUS) \
                                     .filter(topic__status=choices.ACTIVE_STATUS)


class AssessmentCategory(StatusMix, models.Model):
    """
        Category for Assessment Questions - defined by one unique Activity / Topic pair
    """
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='category_set')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='category_set')
    label = models.CharField(max_length=64, blank=True, # builder sets default if left blank
                             help_text='Unique label for this assessment. e.g., Student Learning Experience')
    slug = models.SlugField(unique=True, max_length=64, blank=True,  # builder sets default if left blank.
                            help_text='Unique, short abbreviation for category. e.g. student-experience')
    description = models.TextField(blank=True,
                                   help_text='Optional description of this Assessment Category.')

    active = ActiveCategoryManager()

    class Meta:
        verbose_name = 'Assessment Category'
        verbose_name_plural = "3. Assessment Categories"
        constraints = [
            models.UniqueConstraint(fields=['activity', 'topic'], name='unique_activity_topic'),
        ]

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse('assessment.assess:category', args=(self.slug, ))

    @classmethod
    def get_default_label(cls, activity, topic):
        """ Return a slug appropriate for category defined for the given activity / topic pair """
        return '{activity} - {topic}'.format(activity=activity, topic=topic)

    def question_count(self) :
        """ Return the total number of questions defined for this category """
        return self.question_set.count()


class ReferenceDocument(OrderedModel):
    """
        A link to documentation useful for completing a particular type of Assessment
    """
    category = models.ForeignKey(AssessmentCategory, on_delete=models.CASCADE, related_name='reference_docs')
    label = models.CharField(max_length=128,
                             help_text='Short label for this document. e.g., SOP Classroom Safety')
    description = models.TextField(blank=True,
                                   help_text='Optional description of document and/or how it is used in the Assessment.')
    url = models.URLField(max_length=256,
                          help_text="URL for this document. e.g., https://docs.example.com/sop/classroom-safety.pdf ")

    order_with_respect_to = 'category'

    def __str__(self):
        return self.label


class AssessmentQuestion(StatusMix, OrderedModel):
    """
        A set of metrics used to assess a specific concern or question within a given Category
    """
    category = models.ForeignKey(AssessmentCategory, on_delete=models.CASCADE, related_name='question_set')
    label = models.CharField(max_length=64,
                             help_text='Short label for this question. e.g., Use of Visual Aids')
    description = models.TextField(blank=True,
                                   help_text='Complete question text or detailed description of concern to be assessed.')

    order_with_respect_to = 'category'

    objects = OrderedModelManager()

    class Meta:
        ordering = ('order',)
        verbose_name = 'Question'
        verbose_name_plural = "4. Questions"

    def __str__(self):
        return '{label}: {desc}'.format(label=self.label, desc=self.description)

    def metric_count(self) :
        """ Return the total number of metrics defined for this question """
        return self.metric_set.count()


class MetricChoicesType(models.Model):
    """ metric choice types """
    label = models.CharField(max_length=64,
                            help_text='Short label for these choices. e.g., Percentage Range')
    choice_map = models.TextField(verbose_name="Choices",
                                  validators=[validators.validate_JSON_scoring_choices, ],
                                  help_text="""JSON enoded dictionary mapping choices to integer values. 
                                               E.g., { "< 80%" : 0, "80 - 90%" : 1, ">90%" : 2 }""")

    class Meta:
        verbose_name = 'Metric Choices Type'
        verbose_name_plural = 'Metric Choices Types'

    def __str__(self):
        return '{label}: ({choices})'.format(label=self.label, choices=', '.join(self.choice_dict.values()))

    @cached_property
    def choice_dict(self):
        """ choice dictionary mapping choice DB value to choice label """
        return {value: key for key, value in json.loads(self.choice_map).items()}  # flip JSON mapping

    @cached_property
    def choices(self):
        """ Return standard Django choices tuple """
        return tuple(self.choice_dict.items())

    def get_choice_display(self, value):
        return self.choice_dict[value]

    def validate(self, value):
        """ Return True iff the value is a valid choice DB value """
        return type(value) is int and value in self.choice_dict.keys()



class MetricManager(OrderedModelManager):
    """ Custom ordered manager for AssessmentMetric  """
    def for_category(self, category_id):
        return self.get_queryset().filter(question__category_id=category_id)



class AssessmentMetric(StatusMix, OrderedModel):
    """
        A single metric used to assess a specific detail
    """
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE, related_name='metric_set')
    label = models.CharField(max_length=64,
                             help_text='Label for this metric. e.g., Uses appropriate font size')
    description = models.TextField(blank=True,
                                   help_text='Optional description of how to assess this metric.')
    choices = models.ForeignKey(MetricChoicesType, on_delete=models.CASCADE,
                                help_text='Define choices used to score this metric.')

    order_with_respect_to = 'question'

    objects = MetricManager()

    class Meta:
        ordering = ('order',)
        verbose_name = 'Metric'
        verbose_name_plural = "5. Metrics"

    def __str__(self):
        return self.label

    @property
    def slug(self):
        return slugify(self.label)

    def validate(self, value):
        """ Return True iff the value is valid for this metric """
        return self.choices.validate(value)

    def get_choice_display(self, value):
        return self.choices.get_choice_display(value)
