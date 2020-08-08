
from django.test import TestCase
from django.core.exceptions import ValidationError
from assessment.builder import models, choices
from assessment.tests import base


class CategoryTests(TestCase):
    """
        Test basic behaviours for AssessmentCategory model
    """
    def setUp(self):
        super().setUp()
        self.categories=base.create_assessment_categories()

    def test_get_absolute_url(self):
        cat = self.categories[0]
        url = cat.get_absolute_url()
        self.assertIn(cat.slug, url)

    def test_question_count(self):
        categories = models.AssessmentCategory.objects.all()
        for cat in categories:
            self.assertEqual(cat.question_count(), 0, 'Category with no questions returns non-zero question_count.')
        cat = categories[0]
        self.question = base.create_question(cat, 'Test Question')
        self.assertEqual(cat.question_count(), 1, 'Category with 1 question returns different question_count.')

    def test_status(self):
        categories = models.AssessmentCategory.objects.all()
        for cat in categories:
            self.assertTrue(cat.is_active, 'Category with active status returns is_active as False.')
        inactive = [choice for choice, label in choices.STATUS_CHOICES if choice is not choices.ACTIVE_STATUS]
        for status in inactive:
            categories[0].status = status
            self.assertFalse(categories[0].is_active, 'Category with inactive status returns is_active as True.')

class ReferenceDocument(TestCase):
    """
        Test basic behaviours for ReferenceDocument model
    """
    def setUp(self):
        super().setUp()
        self.categories=base.create_assessment_categories()
        self.category = self.categories[0]
        self.refdoc = base.create_refdoc(self.category, 'Test Reference Doc')

    def test_create(self):
        refdoc = base.create_refdoc(self.category, 'Yet Another Reference Doc')
        self.assertEqual(models.ReferenceDocument.objects.all().count(), 2)

class QuestionTests(TestCase):
    """
        Test basic behaviours for AssessmentQuestion model
    """
    def setUp(self):
        super().setUp()
        self.categories=base.create_assessment_categories()
        self.category = self.categories[0]
        self.question = base.create_question(self.category, 'Test Question')

    def test_metric_count(self):
        questions = models.AssessmentQuestion.objects.all()
        for q in questions:
            self.assertEqual(q.metric_count(), 0, 'Question with no metrics returns non-zero metric_count.')

    def test_status(self):
        questions = models.AssessmentQuestion.objects.all()
        for q in questions:
            self.assertTrue(q.is_active, 'Question with active status returns is_active as False.')
        inactive = [choice for choice, label in choices.STATUS_CHOICES if choice is not choices.ACTIVE_STATUS]
        for status in inactive:
            questions[0].status = status
            self.assertFalse(questions[0].is_active, 'Question with inactive status returns is_active as True.')


class MetricChoiceTypeTests(TestCase):
    """
        Test basic behaviours for MetricChoiceType model
    """
    def setUp(self):
        super().setUp()
        self.choice_type = base.create_metric_choice_type('Test Choices')
        self.valid_values = tuple(choices.SCORE_MAP)
        self.invalid_values = (min(self.valid_values)-1, max(self.valid_values)+1)

    def test_choices(self):
        choice_type = base.create_metric_choice_type('Some Choices', '{"a":0, "b":1, "c":2}' )
        self.assertEqual(choice_type.choices, ((0, 'a'), (1,'b'), (2,'c')))

    def test_validate(self):
        for i in self.valid_values:
            self.assertTrue(self.choice_type.validate(i))
        for i in self.invalid_values:
            self.assertFalse(self.choice_type.validate(i))

    def test_validators(self):
        with self.assertRaises(ValidationError, msg='Invalid json choices dict does not raise ValidatationError') :
            choices = models.MetricChoicesType(label='Invalid Choices', choice_map='{"a":"0", "b":1}')
            choices.full_clean()
        with self.assertRaises(ValidationError, msg='Invalid json choices dict does not raise ValidatationError') :
            choice_map = '{"a":%s, "b":%s}'%(self.valid_values[0], self.invalid_values[0])
            choices = models.MetricChoicesType(label='Invalid Choices', choice_map=choice_map)
            choices.full_clean()


class AssessmentMetricTests(TestCase):
    """
        Test basic behaviours for AssessmentQuestion model
    """
    def setUp(self):
        super().setUp()
        self.categories=base.create_assessment_categories()
        self.category = self.categories[0]
        self.question = base.create_question(self.category, 'Test Question')
        self.choice_type = base.create_metric_choice_type('Test Choices')
        self.metric = base.create_metric(self.question, 'Test Metric', self.choice_type)
        self.valid_values = tuple(choices.SCORE_MAP)
        self.invalid_values = (min(self.valid_values)-1, max(self.valid_values)+1)

    def test_manager(self):
        metrics = models.AssessmentMetric.objects.for_category(self.category.id)
        self.assertEqual(metrics.count(), 1)
        self.assertEqual(metrics[0].pk, self.metric.pk)

    def test_validate(self):
        for i in self.valid_values:
            self.assertTrue(self.metric.validate(i))
        for i in self.invalid_values:
            self.assertFalse(self.metric.validate(i))


class ActiveManagerTests(TestCase):
    """
        Test basic behaviours of ActiveManager
    """
    def setUp(self):
        super().setUp()
        self.categories=base.create_assessment_categories()

    def test_active(self):
        inactive = [choice for choice, label in choices.STATUS_CHOICES if choice is not choices.ACTIVE_STATUS]
        for i in range(0, len(inactive)):
            self.categories[i].status = inactive[i]
            self.categories[i].save()

        active_categories = models.AssessmentCategory.active.all()
        self.assertEqual(len(active_categories), len(self.categories)-len(inactive))
        for cat in active_categories:
            self.assertTrue(cat.is_active, 'ActiveManager returning non-active items.')
