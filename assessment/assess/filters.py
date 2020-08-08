from django.contrib.auth import get_user_model
import django_filters as filters
from assessment.assess import models, choices

class BaseAssessmentFilter(filters.FilterSet):
    def __init__(self, *args, filter_specs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_specs = filter_specs or {}

    @property
    def qs(self):
        qs = super().qs
        return qs.filter(**self.filter_specs) if self.filter_specs else qs


class CategoryAssessmentsFilter(BaseAssessmentFilter):
    created = filters.DateRangeFilter(field_name='created')

    # assessor = filters.ModelMultipleChoiceFilter(field_name='assessor',
    #                                                queryset=get_user_model().objects.all(),  # could be a callable that takes request
    #                                             )

    class Meta:
        model = models.AssessmentRecord
        fields = [
            'status',
            'assessment_type',
            'created',
            'assessor',
        ]

    @property
    def qs(self):
        qs = super().qs
        return qs.select_related('category', 'category__topic', 'category__activity')


class GroupAssessmentsFilter(BaseAssessmentFilter):
    created = filters.DateRangeFilter(field_name='created')

    class Meta:
        model = models.AssessmentGroup
        fields = [
            'status',
            'assessment_type',
            'created',
            'assessor',
        ]

    @property
    def qs(self):
        qs = super().qs
        return qs.select_related('activity', 'topic')

