from itertools import groupby
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from assessment import settings
from assessment.assess import models, choices
from assessment.tests import base


class BaseAssessmentTests(TestCase):
    """ Shared behaviours across Assessment model tests"""

    TEST_ASSESSMENT_LABEL = 'Test Assessment'

    def setUp(self):
        super().setUp()
        self.categories = base.create_assessment_categories()
        self.category = self.categories[0]
        base.create_question_metric_set(self.category, 'Question 1', 1)
        base.create_question_metric_set(self.category, 'Question 2', 2)
        self.user = base.create_user('Assessor')
        self.assessment = base.create_assessment(self.user, self.category, self.TEST_ASSESSMENT_LABEL)
        self.draft_assessment = base.create_assessment(self.user, self.category,
                                                       self.TEST_ASSESSMENT_LABEL, as_draft=True)


class AssessmentRecordTests(BaseAssessmentTests):
    """
        Test basic behaviours for AssessmentRecord model
    """
    def test_record_queryset(self):
        self.assertEqual(models.AssessmentRecord.objects.drafts().count(), 1)
        drafts = models.AssessmentRecord.objects.drafts()
        for r in drafts:
            self.assertEqual(r.status, choices.DRAFT_STATUS)
        self.assertEqual(models.AssessmentRecord.objects.complete().count(), 1)
        complete = models.AssessmentRecord.objects.complete()
        for r in complete:
            self.assertEqual(r.status, choices.COMPLETE_STATUS)

    def test_get_urls(self):
        url = self.assessment.get_absolute_url()
        self.assertIn(str(self.assessment.pk), url)
        self.assertIn('detail', url)
        url = self.assessment.get_update_url()
        self.assertIn(str(self.assessment.pk), url)
        self.assertIn('update', url)
        url = self.assessment.get_delete_url()
        self.assertIn(str(self.assessment.pk), url)
        self.assertIn('delete', url)

    def test_has_subject(self):
        self.assertTrue(self.assessment.has_subject)
        orphan_assessment = models.AssessmentRecord(
            category=self.category,
            last_edited_by=self.user,
            assessor=self.user,
            assessment_type='qa',
            status=choices.DRAFT_STATUS
        )
        orphan_assessment.save()
        self.assertFalse(orphan_assessment.has_subject)

    def test_subject_reverse_lookup(self):
        self.assertEqual(self.assessment.subject.label, self.TEST_ASSESSMENT_LABEL)

    def test_create_metric_score_set(self):
        """ Simply saving an assessment creates a complete set of metric scores """
        questions = self.assessment.category.question_set.all()
        metrics = [metric for q in questions for metric in q.metric_set.all()]
        metric_scores = self.assessment.score_set.all()
        self.assertEqual(len(metrics), len(metric_scores))
        self.assertEqual(set(metrics), set(score.metric for score in metric_scores))

    def test_assessment_score(self):
        # Scores only exist after the Assessments for the group are created
        scores = self.assessment.score_set.all()
        for score in scores:
            score.score = 1
            score.save()
        self.assertEqual(self.assessment.assessment_score(), 1)
        score = scores[0]
        score.score = 2
        score.save()
        self.assertGreater(self.assessment.assessment_score(), 1)

    def test_scores_by_question(self):
        scores = self.assessment.scores_by_question()
        q_groups = groupby(scores, lambda score: score.metric.question)
        questions = [q for q, group in q_groups]
        self.assertEqual(len(questions), len(set(questions)))

    def test_metric_set(self):
        category_metrics = models.AssessmentMetric.objects.filter(question__category=self.assessment.category)
        metric_set = self.assessment.metric_set.all()
        self.assertEqual(set(metric_set), set(category_metrics))

    def test_no_assessment_group(self):
        self.assertFalse(self.assessment.is_in_assessment_group())
        self.assertEqual(len(self.assessment.group_assessments()), 1)
    # assessment_groups are tested in AssessmentGroup tests

    def test_score_class(self):
        scores = self.assessment.score_set.all()
        for score in scores:
            score.score = 1
            score.save()
        self.assertEqual(self.assessment.score_class, settings.ASSESSMENT_SCORE_CLASSES[1][1])
        for score in scores:
            score.score = 100
            score.save()
        self.assertEqual(self.assessment.score_class, settings.ASSESSMENT_SCORE_CLASSES[-1][1])


class AssessmentGroupTests(BaseAssessmentTests):
    """
        Test basic behaviours for AssessmentGroup model
    """
    def setUp(self):
        super().setUp()
        self.topic_group = base.create_assessment_group(self.user, topic=self.category.topic, as_draft=False)
        self.activity_group = base.create_assessment_group(self.user, activity=self.category.activity)

    def test_group_queryset(self):
        self.assertEqual(models.AssessmentGroup.objects.drafts().count(), 1)
        drafts = models.AssessmentGroup.objects.drafts()
        for g in drafts:
            self.assertEqual(g.status, choices.DRAFT_STATUS)
        self.assertEqual(models.AssessmentGroup.objects.complete().count(), 1)
        complete = models.AssessmentGroup.objects.complete()
        for g in complete:
            self.assertEqual(g.status, choices.COMPLETE_STATUS)

    def test_get_urls(self):
        url = self.activity_group.get_absolute_url()
        self.assertIn(str(self.activity_group.pk), url)
        self.assertIn('detail', url)
        url = self.activity_group.get_update_url()
        self.assertIn(str(self.activity_group.pk), url)
        self.assertIn('update', url)
        url = self.activity_group.get_delete_url()
        self.assertIn(str(self.activity_group.pk), url)
        self.assertIn('delete', url)

    def test_clean(self):
        try:
            self.activity_group.clean()
        except ValidationError as v:
            self.assertTrue(False, 'Validation Failed: {}'.format(v))
        with self.assertRaises(ValidationError, msg='Inconsistent group does not raise ValidationError'):
            self.topic_group.activity = self.category.activity
            self.topic_group.clean()
            self.topic_group.topic = self.topic_group.activity = None
            self.topic_group.clean()

    def test_is_group_type(self):
        self.assertTrue(self.topic_group.is_topic_group)
        self.assertTrue(self.activity_group.is_activity_group)
        self.assertFalse(self.topic_group.is_activity_group)
        self.assertFalse(self.activity_group.is_topic_group)

    def test_category_set(self):
        category_set = models.AssessmentCategory.objects.filter(activity=self.category.activity)
        self.assertEqual(set(self.activity_group.category_set), set(category_set))

    def test_metric_set(self):
        qs = models.AssessmentMetric.objects
        activity_metrics = qs.filter(question__category__activity=self.activity_group.activity)
        self.assertEqual(set(self.activity_group.metric_set), set(activity_metrics))

    def test_score_set(self):
        # Scores only exist after the Assessments for the group are created
        self.activity_group.create_assessment_set_from_template(self.assessment)
        qs = models.MetricScore.objects
        activity_scores = qs.filter(assessment__in=self.activity_group.assessment_set.all())
        self.assertEqual(set(self.activity_group.score_set), set(activity_scores))

    def test_assessment_score(self):
        # Scores only exist after the Assessments for the group are created
        self.activity_group.create_assessment_set_from_template(self.assessment)
        scores = self.activity_group.score_set.all()
        for score in scores:
            score.score = 1
            score.save()
        self.assertEqual(self.activity_group.assessment_score(), 1)
        score = scores[0]
        score.score = 2
        score.save()
        self.assertGreater(self.activity_group.assessment_score(), 1)

    def test_scores_by_question(self):
        # Scores only exist after the Assessments for the group are created
        self.activity_group.create_assessment_set_from_template(self.assessment)
        scores = self.activity_group.scores_by_question()
        q_groups = groupby(scores, lambda score: score.metric.question)
        questions = [q for q, group in q_groups]
        self.assertEqual(len(questions), len(set(questions)))

    def test_create_assessment_set(self):
        self.activity_group.create_assessment_set_from_template(self.assessment)
        assessment_categories = (a.category for a in self.activity_group.assessment_set.all())
        self.assertEqual(set(self.activity_group.category_set), set(assessment_categories))
        self.assertTrue(all(a.status == self.activity_group.status for a in self.activity_group.assessment_set.all()))

    def test_save(self):
        # Saving a group updates all its assessment's status
        self.activity_group.create_assessment_set_from_template(self.assessment)
        self.assertTrue(all(a.status == choices.DRAFT_STATUS for a in self.activity_group.assessment_set.all()))
        self.activity_group.status = choices.COMPLETE_STATUS
        self.activity_group.save()
        self.assertTrue(all(a.status == choices.COMPLETE_STATUS for a in self.activity_group.assessment_set.all()))

    def test_assessment_group(self):
        self.activity_group.create_assessment_set_from_template(self.assessment)
        group_assessment = self.activity_group.assessment_set.first()
        self.assertTrue(group_assessment.is_in_assessment_group())
        self.assertEqual(set(group_assessment.group_assessments()), set(self.activity_group.assessment_set.all()))
    # assessment with no group is tested in AssessmentRecord tests

    def test_score_class(self):
        self.activity_group.create_assessment_set_from_template(self.assessment)
        scores = self.activity_group.score_set.all()
        for score in scores:
            score.score = 1
            score.save()
        self.assertEqual(self.activity_group.score_class, settings.ASSESSMENT_SCORE_CLASSES[1][1])
        for score in scores:
            score.score = 100
            score.save()
        self.assertEqual(self.activity_group.score_class, settings.ASSESSMENT_SCORE_CLASSES[-1][1])


class MetricScoreTestsBase(BaseAssessmentTests):
    def setUp(self):
        super().setUp()
        self.question = base.create_question(self.category, 'Test Question')
        self.choice_type = base.create_metric_choice_type('Test Choices')
        self.metric = base.create_metric(self.question, 'Test Metric', self.choice_type)
        self.score = base.create_score(self.assessment, self.metric, score=2)


class MetricScoreTests(MetricScoreTestsBase):
    """
        Test basic behaviours for MetricScore model
    """
    def test_clean(self):
        try:
            self.score.clean()
        except ValidationError as v:
            self.assertTrue(False, 'Validation Failed: {}'.format(v))
        with self.assertRaises(ValidationError, msg='Invalid score does not raise ValidationError'):
            invalid_score = base.create_score(self.assessment, self.metric, score=1)
            invalid_score.score = -1
            invalid_score.clean()
        with self.assertRaises(ValidationError, msg='Inconsistent assessment does not raise ValidationError'):
            other_assessment = base.create_assessment(self.user, self.categories[-1], 'Other Assessment')
            self.score.assessment = other_assessment
            self.score.clean()


class SupportingDocTests(MetricScoreTestsBase):
    """
        Test basic behaviours for SupportingDoc model
    """
    FILENAME = 'Zaphod.txt'

    def test_supporting_doc_directory_path(self):
        instance = lambda: None  # a mutable null object
        instance.score = self.score
        path = models.supporting_doc_directory_path(instance, self.FILENAME)
        self.assertIn(self.category.slug, path)
        self.assertIn(self.metric.slug, path)
        self.assertIn(self.FILENAME, path)

    def test_create_attach(self):
        url = 'https://example.com/abc/123'
        link = base.create_support_document_link(url=url)
        doc = models.SupportingDoc.objects.get(pk=link.pk)
        self.assertEqual(doc.url, url)
        self.assertEqual(doc.href, doc.url)

    def test_create_file(self):
        filename = 'slartibartfast'
        file = base.create_support_document_attach(filename=filename)
        doc = models.SupportingDoc.objects.get(pk=file.pk)
        self.assertIn(filename, doc.file.name)
        self.assertIn(filename, doc.file.url)
        self.assertEqual(doc.href, doc.file.url)

    def test_private_storage(self):
        doc = base.create_support_document_attach()
        self.assertIn(django_settings.PRIVATE_STORAGE_ROOT, doc.file.path)
