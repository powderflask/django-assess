from django.template.loader import get_template
import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from django_filters.views import FilterView
from assessment.assess import models
from .permissions import get_permissions_context_from_request

class TemplateRenderedColumn(tables.Column):
    TEMPLATE = None

    def get_template(self):
        return self.TEMPLATE

    def render(self, record, **kwargs):
        kwargs['record'] = record
        return self.get_template().render(context=kwargs)


class RecordStatusColumn(TemplateRenderedColumn):
    TEMPLATE = get_template('assessment/include/assessment_record_status_label.html')


class RecordScoreColumn(TemplateRenderedColumn):
    TEMPLATE = get_template('assessment/include/assessment_record_score_badge.html')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('order_by', 'avg_score')  # annotation added by objects model manager
        super().__init__(*args, **kwargs)


class RecordActionsColumn(TemplateRenderedColumn):
    TEMPLATE = get_template('assessment/include/assessment_record_tools.html')

    def __init__(self, *args, **kwargs):
        kwargs['orderable'] = False
        super().__init__(*args, **kwargs)


class SubjectColumn(tables.Column):

    def __init__(self, *args, subject_field='subject', **kwargs):
        from django.apps import apps
        appConfig = apps.get_app_config('assess')
        subject_ordering = tuple(
            '{subject_field}__{order_by_field}'.format(subject_field=subject_field, order_by_field=field)
            for field in appConfig.settings.SUBJECT_ORDER_BY
        )
        kwargs.setdefault('order_by', subject_ordering)
        kwargs.setdefault('verbose_name', 'Subject')
        super().__init__(*args, **kwargs)


class BaseAssessmentTable(tables.Table):
    status = RecordStatusColumn(accessor='status')
    subject = SubjectColumn(accessor='subject', linkify=True)
    score = RecordScoreColumn(accessor='avg_score', verbose_name='Score')
    actions = RecordActionsColumn(accessor='pk', verbose_name='Actions')

    class Meta:
        model = None   # Sub-classes must override
        fields = [
            'status',
            'subject',
            'assessment_type',
            'score',
            'created',
            'assessor',
            'actions',
        ]
        template_name = 'django_tables2/bootstrap.html'

    def render_created(self, value):
        return '{:%d-%m-%Y}'.format(value)

    def render_assessment_type(self, value):
        return "".join([word[0] for word in value.split()]).upper()

    def render_assessor(self, value):
        try:
            return value.get_full_name()
        except AttributeError:
            return value

    def render_actions(self, record, column):
        # Bit of hackery going on here to pass permissions context to Actions column render function.
        return column.render(record, **get_permissions_context_from_request(self.request))


class CategoryAssessmentsTable(BaseAssessmentTable):

    class Meta(BaseAssessmentTable.Meta):
        model = models.AssessmentRecord


class AssessmentSetTable(BaseAssessmentTable):
    subject = SubjectColumn(accessor='subject', linkify=True,
                            subject_field='assessment_set__first__subject')

    class Meta(BaseAssessmentTable.Meta):
        model = models.AssessmentGroup


# -----------  Base Table Views and Mixins -------------- #


class BaseFilteredTableView(tables.SingleTableMixin, ExportMixin, FilterView):
    template_name = None
    table_class = None
    export_table_class = None
    filterset_class = None
    export_filterset_class = None

    def get_table_class(self):
        if self.is_export and self.export_table_class:
            return self.export_table_class
        return super().get_table_class()

    def get_filterset_class(self):
        if self.is_export and self.export_filterset_class:
            return self.export_filterset_class
        return super().get_filterset_class()

    @property
    def is_export(self):
        return self.request.GET.get(self.export_trigger_param, False)

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs.update({
            'filter_specs': self.assessment_filter_specs
        })
        return kwargs

    @property
    def assessment_filter_specs(self):
        """
            Return dictionary of filter specs, suitable for creating an AssessmentFilter
        """
        return {
            # 'user': self.request.user,
            'category__slug': self.kwargs.get('slug', None),
        }
