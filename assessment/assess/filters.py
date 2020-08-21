from django import forms
import django_filters as filters
from assessment.assess import models, choices


class BaseAssessmentFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=choices.STATUS_CHOICES,
                                  widget=forms.Select(attrs={'class':'form-control'}))
    assessment_type = filters.ChoiceFilter(choices=choices.ASSESSMENT_TYPE_SHORT_CHOICES,
                                           widget=forms.Select(attrs={'class':'form-control'}))
    class Meta:
        model = models.AssessmentRecord
        fields = [
            'status',
            'assessment_type',
        ]

    def __init__(self, *args, filter_specs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_specs = filter_specs or {}

    @property
    def qs(self):
        qs = super().qs
        return qs.filter(**self.filter_specs) if self.filter_specs else qs


SubjectModel = models.get_assessment_subject_model()
subject_accessor = models.get_assessment_subject_related_name()
assessment_subject_filterset = SubjectModel.get_related_subject_filterset(subject_accessor)


class CategoryAssessmentsFilter(BaseAssessmentFilter, assessment_subject_filterset):
    class Meta:
        model = models.AssessmentRecord
        fields = BaseAssessmentFilter.Meta.fields + assessment_subject_filterset.Meta.fields


group_subject_accessor = 'assessment_set__{subject}'.format(subject=subject_accessor)
group_subject_filterset = SubjectModel.get_related_subject_filterset(group_subject_accessor)


class GroupAssessmentsFilter(BaseAssessmentFilter, group_subject_filterset):

    class Meta:
        model = models.AssessmentGroup
        fields = BaseAssessmentFilter.Meta.fields + group_subject_filterset.Meta.fields
