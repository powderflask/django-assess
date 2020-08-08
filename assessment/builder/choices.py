""" Model choices and other business-logic constant values  - most can be overridden in settings """
from django.conf import settings

#### STATUS_CHOICES ####

ACTIVE_STATUS = getattr(settings, 'ASSESSMENT_ACTIVE_STATUS', 'active')

DEFAULT_STATUS_CHOICES = (
    ('draft', 'Draft'),
    (ACTIVE_STATUS, ACTIVE_STATUS.capitalize()),
    ('retired', 'Retired'),
)

STATUS_CHOICES = getattr(settings, 'ASSESSMENT_STATUS_CHOICES', DEFAULT_STATUS_CHOICES)

# Choices must at least include the Activ Status value
assert ACTIVE_STATUS in (v for v, l in STATUS_CHOICES)


#### SCORE_CHOICES ####

DEFAULT_SCORE_MAP = {
    0 : 'Not Compliant',
    1 : 'Needs Work',
    2 : 'Fully Compliant'
}

SCORE_MAP = getattr(settings, 'ASSESSMENT_SCORE_MAP', DEFAULT_SCORE_MAP)

# Map keys MUST be integers and MUST be unique
assert all(type(k) is int for k in SCORE_MAP) and len(SCORE_MAP) == len(set(SCORE_MAP))

SCORE_CHOICES = tuple( (key, value) for key, value in SCORE_MAP.items())