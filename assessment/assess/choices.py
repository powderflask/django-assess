""" Model choices and other business-logic constant values  - most can be overridden in settings """
from django.conf import settings
import assessment.builder.choices

# ----- STATUS_CHOICES ----- #

COMPLETE_STATUS = 'complete'
DRAFT_STATUS = 'draft'

STATUS_CHOICES = (
    (DRAFT_STATUS, DRAFT_STATUS.capitalize()),
    (COMPLETE_STATUS, COMPLETE_STATUS.capitalize()),
)


# ----- ASSESSMENT_TYPE_CHOICES ----- #
QA_ASSESSMENT_TYPE = 'qa'
QC_ASSESSMENT_TYPE = 'qc'

DEFAULT_ASSESSMENT_TYPE_CHOICES = (
    (QA_ASSESSMENT_TYPE, 'Quality Assurance'),
    (QC_ASSESSMENT_TYPE, 'Quality Control'),
)

ASSESSMENT_TYPE_CHOICES = getattr(settings, 'ASSESSMENT_TYPE_CHOICES', DEFAULT_ASSESSMENT_TYPE_CHOICES)

SCORE_CHOICES = assessment.builder.choices.SCORE_CHOICES


# ----- DOCUMENT_TYPE_CHOICES ----- #

DOCUMENT_TYPE_NONE = getattr(settings, 'ASSESSMENT_DOCUMENT_TYPE_NONE ', 'none')

DEFAULT_DOCUMENT_TYPE_CHOICES = (
    (DOCUMENT_TYPE_NONE, 'None / Missing'),
    ('spreadsheet', 'Spreadsheet'),
    ('notes', 'Notes'),
)

DOCUMENT_TYPE_CHOICES = getattr(settings, 'ASSESSMENT_DOCUMENT_TYPE_CHOICES', DEFAULT_DOCUMENT_TYPE_CHOICES)

# Choices must at least include the Default Type value
assert DOCUMENT_TYPE_NONE in (v for v, _ in DOCUMENT_TYPE_CHOICES)


# ----- DOCUMENT_LOCATION_CHOICES ------ #

DOCUMENT_LOCATION_ATTACHED = getattr(settings, 'ASSESSMENT_DOCUMENT_LOCATION_ATTACHED', 'attached')

DOCUMENT_LOCATION_LINK = 'url'

DEFAULT_DOCUMENT_LOCATION_CHOICES = (
    (DOCUMENT_LOCATION_ATTACHED, DOCUMENT_LOCATION_ATTACHED.capitalize()),
    (DOCUMENT_LOCATION_LINK, 'Link'),
)

DOCUMENT_LOCATION_CHOICES = getattr(settings, 'ASSESSMENT_DOCUMENT_LOCATION_CHOICES', DEFAULT_DOCUMENT_LOCATION_CHOICES)

# Choices must at least include the Attached Location value
assert DOCUMENT_LOCATION_ATTACHED in (v for v, _ in DOCUMENT_LOCATION_CHOICES)
