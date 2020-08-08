
from django.test import TestCase
from django.core.exceptions import ValidationError
from assessment.builder import choices, validators

class JsonChoiceValidatorsTests(TestCase):
    """
        Test behaviours for JSON choice validators
    """
    NOT_JSON = '{a:1, b:2, c:3}'   # not valid JSON - keys must be double quoted
    JSON_DICT = '{"a":"1", "b":"2", "c":"3"}'  # valid JSON dict, but not for scoring - values should be int
    JSON_INTS = '{"a":1, "b":2, "c":3}'  # valid JSON int dict, but not for scoring - values must be in range [0, 2]
    JSON_SCORES = '{"a":1, "b":2, "c":0}'  # valid JSON scoring dict

    def test_validate_JSON_dict(self):
        try:  # postive test
            validators.validate_JSON_dict(self.JSON_DICT)
        except ValidationError as e:
            self.assertTrue(False, 'Valid json dict raises ValidatationError')

        with self.assertRaises(ValidationError, msg='Invalid json dict does not raise ValidatationError') : # negative test
            validators.validate_JSON_dict(self.NOT_JSON)

    def test_validate_JSON_int_choices(self):
        try:  # postive test
            validators.validate_JSON_int_choices(self.JSON_INTS)
        except ValidationError as e:
            self.assertTrue(False, 'Valid json int choices dict raises ValidatationError')

        with self.assertRaises(ValidationError, msg='Invalid json int choices dict does not raise ValidatationError') : # negative test
            validators.validate_JSON_int_choices(self.JSON_DICT)

    def test_validate_JSON_scoring_choices(self):
        try:  # postive test
            validators.validate_JSON_scoring_choices(self.JSON_SCORES)
        except ValidationError as e:
            self.assertTrue(False, 'Valid json scoring choices dict raises ValidatationError')

        with self.assertRaises(ValidationError, msg='Invalid json scoring choices dict does not raise ValidatationError') : # negative test
            validators.validate_JSON_scoring_choices(self.JSON_INTS)
