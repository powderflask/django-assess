import json

from django.core.exceptions import ValidationError
from assessment.builder import choices


def validate_JSON_dict(value):
    """ validates if value JSON decodes to a Python dict """
    try:
        d = json.loads(value)
        if type(d) is not dict:
            raise ValidationError('%(value)s is not a JSON dictionary', params={'value': value})
    except json.decoder.JSONDecodeError as e:
        raise ValidationError('%(value)s is not a valid JSON: %(e)s', params={'value' : value, 'e':e})


def validate_JSON_int_choices(value):
    """ validates if value JSON decodes to a Python dict where all values are integers """
    validate_JSON_dict(value)
    d = json.loads(value)
    if not all(type(v) is int for v in d.values()):
        raise ValidationError('%(value)s does not map every choice to an integer value', params={'value' : value})


def validate_JSON_scoring_choices(value):
    """ validates if value JSON decodes to a Python dict where all values are valid scores """
    validate_JSON_dict(value)
    validate_JSON_int_choices(value)
    d = json.loads(value)
    if not all(v in choices.SCORE_MAP for v in d.values()):
        raise ValidationError('%(value)s does not map each choice to a score in %(scores)s',
                              params={'value' : value, 'scores':(score for score in choices.SCORE_MAP)})


