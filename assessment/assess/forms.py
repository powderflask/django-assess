from django import forms
from . import models


class AssessmentSubjectForm(forms.ModelForm):
    """ Model form for default Subject model - replace using ASSESSMENT_SUBJECT_FORM setting """
    class Meta:
        model = models.get_assessment_subject_model()
        fields = (
            'label',
            'description',
            'record',
        )

        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 80}),
            'record'     : forms.HiddenInput()
        }
