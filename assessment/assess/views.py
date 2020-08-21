from itertools import groupby
from django.utils.functional import cached_property
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import Http404
from django.views import generic
from django import http, urls
import django.forms
from assessment.helpers.algorithms import sparse_to_full_matrix, index_vector
from assessment.assess import models, tables, filters
from .permissions import permissions, permission_required, get_permissions_context


# --------------------------------------------
#  Category / Navigation views
# --------------------------------------------
# No permission to view top-level matrix categories
class AssessmentMatrixView(generic.ListView):
    model = models.AssessmentCategory
    queryset = models.AssessmentCategory.active.all().order_by('topic', 'activity')
    context_object_name = 'categories'
    template_name = 'assessment/matrix.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        categories = context[self.context_object_name]
        activities = models.Activity.active.all()
        topics = models.Topic.active.all()

        context['activities'] = activities
        context['topics'] = topics
        matrix = sparse_to_full_matrix(categories,
                                       index_vector(topics), lambda cat: cat.topic,
                                       index_vector(activities), lambda cat: cat.activity,
                                       empty_value=''
                                       )
        context['matrix'] = zip(topics, matrix)  # because its a pain otherwise in template logic.
        return context


@permission_required(permissions.user_can_view_assessments)
class AbstractGroupView(tables.BaseFilteredTableView):
    group_model = None  # Sub-classes MUST define the concrete group-type model
    slug_filter = ''    # Sub-classes MUST define a queryset filter key suitable for filtering Groups by slug
    table_class = tables.AssessmentSetTable
    filterset_class = filters.GroupAssessmentsFilter
    template_name = 'assessment/groups.html'

    @cached_property
    def group(self):
        return get_object_or_404(self.group_model.objects, slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        kwargs['group'] = self.group
        return super().get_context_data(**get_permissions_context(self), **kwargs)

    @property
    def assessment_filter_specs(self):
        """ Return AssessmentFilter filter specs for current Group """
        return {
            # 'user': self.request.user,
            self.slug_filter: self.kwargs.get('slug', None),
        }


class ActivityView(AbstractGroupView):
    group_model = models.Activity  # Assessments grouped by Activity
    slug_filter = 'activity__slug'


class TopicView(AbstractGroupView):
    group_model = models.Topic  # Assessments grouped by Topic
    slug_filter = 'topic__slug'


@permission_required(permissions.user_can_view_assessments)
class AssessmentCategoryView(tables.BaseFilteredTableView):
    table_class = tables.CategoryAssessmentsTable
    filterset_class = filters.CategoryAssessmentsFilter

    template_name = 'assessment/category.html'

    @cached_property
    def category(self):
        return get_object_or_404(models.AssessmentCategory.objects, slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        kwargs['category'] = self.category
        return super().get_context_data(**get_permissions_context(self), **kwargs)


# --------------------------------------------
#  Assessment Record CRUD views
# --------------------------------------------
@permission_required(permissions.user_can_view_assessments)
class AssessmentRecordDetailView(generic.DetailView):
    model = models.AssessmentRecord
    context_object_name = 'assessment_record'
    template_name = 'assessment/record/detail.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**get_permissions_context(self), **kwargs)


@permission_required(permissions.user_can_create_assessment)
class AssessmentRecordCreateView(generic.CreateView):
    """ Create an 'empty' AssessmentRecord and its related Subject """
    model = models.AssessmentRecord
    context_object_name = 'record'
    hidden_fields = ('category', 'assessor', 'last_edited_by')  # required on model but supplied by view
    form_class = django.forms.modelform_factory(
        model,
        fields=('assessment_type', *hidden_fields),
        widgets={field: django.forms.HiddenInput() for field in hidden_fields},
    )
    # form for swappable Subject model is supplied by model itself (simple if unorthodox)
    subject_form_class = models.get_assessment_subject_model().get_modelform()

    template_name = 'assessment/record/create.html'

    @cached_property
    def category(self):
        return get_object_or_404(models.AssessmentCategory.active, slug=self.kwargs['slug'])

    def get_success_url(self):
        """ On success, we move directly to the update view so user can edit the MetricScores for this assessment """
        return urls.reverse('assessment.assess:update', args=(self.object.pk, ))

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        initial = self.initial.copy()
        initial['category'] = self.category
        # Initial values provided so required hidden form fields validate - actual values are forced during save
        initial['assessor'] = initial['last_edited_by'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        kwargs['category'] = self.category
        if 'subject_form' not in kwargs:
            kwargs['subject_form'] = self.get_subject_form()
        return super().get_context_data(**kwargs)

    def get_subject_form(self):
        kwargs = self.get_form_kwargs()
        kwargs['instance'] = None
        return self.subject_form_class(**kwargs)

    def save_subject_form(self, subject_form):
        subject = subject_form.save(commit=False)
        subject.record = self.object  # the assessment record object MUST be saved first!
        subject.save()
        return subject

    def save_models(self, form, subject_form):
        # MUST save assessment record first so relation to it can be formed to it.
        self.object = form.save(commit=False)
        self.object.assessor = self.object.last_edited_by = self.request.user  # override values provided by client.
        self.object.save()  # Note: this call also creates all the 'empty' MetricScore records for assessment

        # Now that we have an assessment record, we can save the related form...
        self.save_subject_form(subject_form)

    def forms_valid(self, form, subject_form):
        """ If the form is valid, save the associated model. """
        self.save_models(form, subject_form)
        return http.HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, subject_form):
        """ If any of the forms are invalid, render the invalid forms. """
        return self.render_to_response(self.get_context_data(form=form, subject_form=subject_form))

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: save AssessmentRecord form, then use new object to create Subject and MetricScores
        """
        self.object = None
        form = self.get_form()
        subject_form = self.get_subject_form()
        if form.is_valid() and subject_form.is_valid():
            return self.forms_valid(form, subject_form)
        else:
            return self.forms_invalid(form, subject_form)


@permission_required(permissions.user_can_edit_assessment)
class AssessmentRecordUpdateView(generic.UpdateView):
    """ Update the AssessmentRecord's status and metric_set """
    model = models.AssessmentRecord
    context_object_name = 'record'
    queryset = model.objects.all()  # Prefetch related is on objects manager
    form_class = django.forms.modelform_factory(model, fields=('status', ))
    docs_formset_class = django.forms.inlineformset_factory(
        models.MetricScore,
        models.SupportingDoc,
        widgets={'description': django.forms.Textarea(attrs={'rows': 1})},
        exclude=(), extra=1,
    )
    mf_hidden_fields = ('metric', 'assessment',)  # required on model but value is supplied by view
    metric_form_class = django.forms.modelform_factory(
        models.MetricScore,
        fields=('applicable', 'score', 'comments', *mf_hidden_fields),
        widgets={
            "comments": django.forms.Textarea(attrs={'rows': '2', 'cols': 80}),
            **{field: django.forms.HiddenInput() for field in mf_hidden_fields}
        },
    )
    template_name = 'assessment/record/update.html'

    @cached_property
    def assessment(self):
        return self.get_object()  # Caution: sub-class of this view may return duck-typed object instead!

    def get_context_data(self, **kwargs):
        kwargs['assessment_record'] = self.assessment
        if 'metric_forms' not in kwargs:
            kwargs['metric_forms'] = self._metric_forms_by_category_by_question(self.get_metric_forms())
        return super().get_context_data(**kwargs)

    @staticmethod
    def _metric_forms_by_category_by_question(metric_forms):
        """ Return {category: {question: questions_metric_forms}}; each form must have a metric_score instance """
        return {
            category: {
                question: list(q_forms)
                for question, q_forms in groupby(cat_forms, lambda form: form.instance.metric.question)
            } for category, cat_forms in groupby(metric_forms, lambda form: form.instance.assessment.category)
        }

    def get_metric_score_set(self):
        return self.assessment.score_set.all()

    def get_metric_form(self, score, **kwargs):
        """ Return a form for the given score """
        prefix = 'score-{pk}'.format(pk=score.pk)
        metric_form = self.metric_form_class(instance=score, prefix=prefix, **kwargs)
        metric_form.fields['score'].widget = django.forms.Select(choices=score.metric.choices.choices)
        metric_form.docs_formset = self.get_docs_formset(prefix, score)
        return metric_form

    def get_metric_forms(self):
        kwargs = {'data': self.request.POST} if self.request.method in ('POST', 'PUT') else {}
        return [self.get_metric_form(score, **kwargs) for score in self.get_metric_score_set()]

    def get_docs_formset(self, prefix, metric_score):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = prefix+'-docs'
        kwargs['instance'] = metric_score
        return self.docs_formset_class(**kwargs)

    def save_metric_forms(self, metric_forms):
        scores = []
        for form in metric_forms:
            scores.append(form.save())
            form.docs_formset.save()
        return scores

    def forms_valid(self, form, metric_forms):
        """ If the forms are valid, save the associated models. """
        self.object = form.save()
        self.save_metric_forms(metric_forms)
        return http.HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, metric_forms):
        """ If any of the forms are invalid, render the invalid forms. """
        return self.render_to_response(
            self.get_context_data(form=form, metric_forms=self._metric_forms_by_category_by_question(metric_forms))
        )

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: save AssessmentRecord form, update related MetricScores
        """
        self.object = self.assessment
        form = self.get_form()
        metric_forms = self.get_metric_forms()
        if form.is_valid() and all(form.is_valid() and form.docs_formset.is_valid() for form in metric_forms):
            return self.forms_valid(form, metric_forms)
        else:
            return self.forms_invalid(form, metric_forms)


@permission_required(permissions.user_can_delete_assessment)
class AssessmentRecordDeleteView(generic.edit.DeleteView):
    model = models.AssessmentRecord
    template_name = 'assessment/confirm_delete.html'

    @cached_property
    def assessment(self):
        return self.get_object()

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            cancel_url=self.get_success_url(),
            **kwargs
        )

    def get_success_url(self):
        return reverse('assessment.assess:category', args=(self.assessment.category.slug,))


# --------------------------------------------
#  Assessment Group CRUD views
# --------------------------------------------
@permission_required(permissions.user_can_view_assessments)
class AssessmentGroupDetailView(generic.DetailView):
    model = models.AssessmentGroup
    context_object_name = 'assessment_group'
    template_name = 'assessment/group/detail.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**get_permissions_context(self), **kwargs)


@permission_required(permissions.user_can_create_assessment)
class AssessmentGroupCreateView(AssessmentRecordCreateView):
    """ Same as AssessmentRecordCreate, but creates the group and entire set of related assessments """
    template_name = 'assessment/group/create.html'

    def get_activity_and_topic(self):
        """ Returns (Activity, None) or (None, Topic) depending on the view's slug """
        try:
            return models.Activity.objects.get(slug=self.kwargs['slug']), None
        except models.Activity.DoesNotExist:
            return None, models.Topic.objects.get(slug=self.kwargs['slug'])

    @cached_property
    def assessment_group(self):
        """ The new (unsaved) AssessmentGroup this view is creating """
        activity, topic = self.get_activity_and_topic()
        if not (topic or activity):
            raise Http404("No such topic or activity")
        return models.AssessmentGroup(topic=topic, activity=activity)

    @cached_property
    def category(self):
        # This category is a dummy placeholder - just need some category for model form to validate
        return self.assessment_group.category_set.first()

    def get_success_url(self):
        """ On success, we move directly to the update view so user can edit the MetricScores for this assessment """
        return urls.reverse('assessment.assess:group-update', args=(self.assessment_group.pk, ))

    def get_context_data(self, **kwargs):
        kwargs['assessment_group'] = self.assessment_group
        return super().get_context_data(**kwargs)

    def save_models(self, form, subject_form):
        # Create the groups assessment set based on the assessment defined in form.
        assessment = form.save(commit=False)
        assessment.subject = subject_form.save(commit=False)
        # hard-code the assessor
        assessment.assessor = assessment.last_edited_by = self.request.user
        # copy fields onto group required for filtering assessment groups in DB
        self.assessment_group.assessor = assessment.assessor
        self.assessment_group.assessment_type = assessment.assessment_type
        self.assessment_group.save()
        self.assessment_group.create_assessment_set_from_template(assessment)


@permission_required(permissions.user_can_edit_assessment)
class AssessmentGroupUpdateView(AssessmentRecordUpdateView):
    """ Same as updating AssessmentRecord except status and metric_set are housed on Group. """
    model = models.AssessmentGroup
    context_object_name = 'assessment_group'
    queryset = model.objects.all()  # Prefetch related is on objects manager
    form_class = django.forms.modelform_factory(model, fields=('status', ))
    docs_formset_class = django.forms.inlineformset_factory(
        models.MetricScore,
        models.SupportingDoc,
        widgets={'description': django.forms.Textarea(attrs={'rows': 2})},
        exclude=(), extra=1,
    )
    template_name = 'assessment/group/update.html'

    # Sneaky trick -- assessment property of parent class left in-tact, but will also return AssessmentGroup object
    # IMPORTANT: AssessmentGroup must present consistent API in terms of what is used by that view
    def get_context_data(self, **kwargs):
        kwargs['assessment_group'] = self.assessment
        return super().get_context_data(**kwargs)


@permission_required(permissions.user_can_delete_assessment)
class AssessmentGroupDeleteView(generic.edit.DeleteView):
    model = models.AssessmentGroup
    template_name = 'assessment/confirm_delete.html'

    @cached_property
    def assessment_group(self):
        return self.get_object()

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            cancel_url=self.get_success_url(),
            **kwargs
        )

    def get_success_url(self):
        grp = self.assessment_group
        group_type = 'topic' if grp.is_topic_group else 'activity'
        slug = grp.topic.slug if grp.is_topic_group else grp.activity.slug
        return reverse('assessment.assess:{group_type}'.format(group_type=group_type), args=(slug,))
