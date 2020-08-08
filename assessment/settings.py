""" Overridable settings used by django-assess See also: assess.apps, builder.choices and assess.choices """
import math
from django.conf import settings

# AssessmentSubject model is swappable.
# Default model provides a text label and description - swap it out here for a richer subject model
# Base code does not inspect this model, it assumes only (i) each AssessmentRecord has a subject; and (ii) there is a meaninful __str__ method to display the Subject
# It is possible to maintain any number of Subject models, but this requires overriding views/forms that create Subjects
# E.g., subclass AssessmentRecordCreateView and set the subject_form_class class attribute to create assessments with a different type of Subject
ASSESSMENT_SUBJECT_MODEL = getattr(settings, 'ASSESSMENT_SUBJECT_MODEL', 'assess.AssessmentSubject')


# Assessment Subject ordering fields for tables where subject is listed.
# Tuple of AssessmentSubject fields passed to Tables.Column.order_by:  https://django-tables2.readthedocs.io/en/latest/pages/ordering.html#ordering-by-accessors
ASSESSMENT_SUBJECT_ORDER_BY = getattr(settings, 'ASSESSMENT_SUBJECT_ORDER_BY', ('label', ))

# assess.models.MetricScore provides a "score_class" property that returns either "not-applicable" or "score-X" where x is the integer score
# assess.models.AssessmentRecord also provides a "score_class" property that returns a a string representing a classification
#   of the average score across all metrics in the record.
# This setting provides a means of customizing the AssessmentRecord "score_class"
DEFAULT_SCORE_CLASSES = (
    (0.5, 'fail'),
    (1.0, 'poor'),
    (1.5, 'satisfactory'),
    (math.inf, 'good'),
)
ASSESSMENT_SCORE_CLASSES = list(
    getattr(settings, 'ASSESSMENT_SCORE_CLASSES', DEFAULT_SCORE_CLASSES)
)
ASSESSMENT_SCORE_CLASSES.sort()

# Configurable permisssions module
# provide dotted-path to python module with permissions functions -- see permissions.py
ASSESSMENT_PERMISSIONS = getattr(settings, 'ASSESSMENT_PERMISSIONS', 'assessment.permissions')
