from django.test import TestCase
from django.urls import reverse
from assessment.tests import base


class BaseTestWithUsers(TestCase):
    """
        Test behaviours for Assessment Record CRUD views
    """
    def setUp(self):
        super().setUp()
        self.categories = base.create_assessment_categories()
        self.category = self.categories[0]
        base.create_question_metric_set(self.category, 'Question 1', 1)
        base.create_question_metric_set(self.category, 'Question 2', 2)
        self.privilegedUser = base.create_user(username='privileged',
                                               permissions=('Can add Assessment Record', 'Can change Assessment Record', 'Can delete Assessment Record'))
        self.restrictedUser = base.create_user(username='restricted')
        self.assessment = base.create_assessment(self.privilegedUser, self.category, "Test Assessment")
        self.draft_assessment = base.create_assessment(self.privilegedUser, self.category, "Draft Assessment", as_draft=True)

    def login(self, user):
        response = self.client.login(username=user.username, password='password')
        self.assertTrue(response)


class SuccessAssessmentCategoryViewTests(BaseTestWithUsers):
    """
        SUCCESS -- test correctly privileged user makes perfectly reasonable requests
    """
    def test_matrix_view(self):
        # Anonymous users can view the matrix, but nothing else.
        url = reverse('assessment.assess:matrix')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Matrix view returned non-success status code.")
        for cat in self.categories:
            self.assertContains(response, cat.label, msg_prefix="Matrix view doesn't show all categories.")

    def test_activity_view(self):
        # Any logged in user can view assessments
        self.login(self.restrictedUser)
        activity = self.category.activity
        url = reverse('assessment.assess:activity', args=(activity.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Activity view returned non-success status code.")
        self.assertContains(response, activity.label, msg_prefix="Activity view doesn't show activity.")

    def test_topic_view(self):
        # Any logged in user can view assessments
        self.login(self.restrictedUser)
        topic = self.category.topic
        url = reverse('assessment.assess:topic', args=(topic.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Topic view returned non-success status code.")
        self.assertContains(response, topic.label, msg_prefix="Topic view doesn't show topic.")

    def test_category_view(self):
        # Any logged in user can view assessments
        self.login(self.restrictedUser)
        url = reverse('assessment.assess:category', args=(self.category.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Category view returned non-success status code.")
        self.assertContains(response, self.category.label, msg_prefix="Category view doesn't show category.")



class DeniedAssessmentCategoryViewTests(BaseTestWithUsers) :
    """
        DENIED -- test under-privileged user or otherwise makes unreasonable requests
    """
    def test_activity_view(self):
        activity = self.category.activity
        url = reverse('assessment.assess:activity', args=(activity.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")

    def test_topic_view(self):
        topic = self.category.topic
        url = reverse('assessment.assess:topic', args=(topic.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")

    def test_category_view(self):
        url = reverse('assessment.assess:category', args=(self.category.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")


class SuccessAssessmentRecordViewTests(BaseTestWithUsers):
    """
        SUCCESS -- test correctly privileged user makes perfectly reasonable requests
    """
    def test_record_create_view(self):
        self.login(self.privilegedUser)
        url = reverse('assessment.assess:create', args=(self.category.slug, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Create view returned non-success status code.")
        self.assertContains(response, 'form', msg_prefix="Detail view doesn't show a form.")

    def test_record_detail_view(self):
        # Any authenticated user can view records
        self.login(self.restrictedUser)
        url = self.assessment.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Detail view returned non-success status code.")
        self.assertContains(response, self.assessment.subject.label, msg_prefix="Detail view doesn't show assessment.")

    def test_record_update_view(self):
        self.login(self.privilegedUser)
        url = self.assessment.get_update_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Update view returned non-success status code.")
        self.assertContains(response, self.assessment.subject.label, msg_prefix="Detail view doesn't show assessment.")
        self.assertContains(response, 'form', msg_prefix="Detail view doesn't show form.")

    def test_record_delete_view(self):
        self.login(self.privilegedUser)
        url = self.assessment.get_delete_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Delete view returned non-success status code.")
        self.assertContains(response, self.assessment.subject.label, msg_prefix="Delete view doesn't show assessment.")
        self.assertContains(response, 'Confirm Delete', msg_prefix="Delete view doesn't show confirmation.")
        self.assertContains(response, 'form', msg_prefix="Delete view doesn't show form.")


class DeniedAssessmentRecordViewTests(BaseTestWithUsers):
    """
        DENIED -- test under-privileged user or otherwise makes unreasonable requests
    """
    def test_record_create_view(self):
        self.login(self.restrictedUser)
        url = reverse('assessment.assess:create', args=(self.category.slug, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")

    def test_record_detail_view(self):
        # Anonymous users cannot view assessment records
        url = self.assessment.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")

    def test_record_update_view(self):
        self.login(self.restrictedUser)
        url = self.assessment.get_update_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")

    def test_record_delete_view(self):
        self.login(self.restrictedUser)
        url = self.assessment.get_delete_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")


class SuccessAssessmentGroupViewTests(BaseTestWithUsers):
    """
        SUCCESS -- test correctly privileged user makes perfectly reasonable requests
    """
    def setUp(self):
        super().setUp()
        self.topic_group = base.create_assessment_group(self.privilegedUser, topic=self.category.topic, as_draft=False)
        self.activity_group = base.create_assessment_group(self.privilegedUser, activity=self.category.activity)
        self.activity_group.create_assessment_set_from_template(self.assessment)

    def test_group_create_view(self):
        self.login(self.privilegedUser)
        url = reverse('assessment.assess:group-create', args=(self.category.topic.slug, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Create view returned non-success status code.")
        self.assertContains(response, 'form', msg_prefix="Detail view doesn't show a form.")

    def test_group_detail_view(self):
        # Any authenticated user can view records
        self.login(self.restrictedUser)
        url = self.activity_group.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Detail view returned non-success status code.")
        self.assertContains(response, self.assessment.subject.label, msg_prefix="Detail view doesn't show assessment.")

    def test_group_update_view(self):
        self.login(self.privilegedUser)
        url = self.activity_group.get_update_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Update view returned non-success status code.")
        label = self.activity_group.activity.label
        self.assertContains(response, label, msg_prefix="Detail view doesn't show grout type.")
        self.assertContains(response, 'form', msg_prefix="Detail view doesn't show form.")

    def test_group_delete_view(self):
        self.login(self.privilegedUser)
        url = self.activity_group.get_delete_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "Delete view returned non-success status code.")
        label = self.activity_group.activity.label
        self.assertContains(response, label, msg_prefix="Delete view doesn't show grout type.")
        self.assertContains(response, 'Confirm Delete', msg_prefix="Delete view doesn't show confirmation.")
        self.assertContains(response, 'form', msg_prefix="Delete view doesn't show form.")


class DeniedAssessmentGroupViewTests(BaseTestWithUsers):
    """
        DENIED -- test under-privileged user or otherwise makes unreasonable requests
    """
    def setUp(self):
        super().setUp()
        self.topic_group = base.create_assessment_group(self.privilegedUser, topic=self.category.topic, as_draft=False)
        self.activity_group = base.create_assessment_group(self.privilegedUser, activity=self.category.activity)
        self.activity_group.create_assessment_set_from_template(self.assessment)

    def test_group_create_view(self):
        self.login(self.restrictedUser)
        url = reverse('assessment.assess:group-create', args=(self.category.topic.slug, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")

    def test_group_detail_view(self):
        # Anonymous users cannot view assessment records
        url = self.activity_group.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")

    def test_group_update_view(self):
        self.login(self.restrictedUser)
        url = self.activity_group.get_update_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")

    def test_group_delete_view(self):
        self.login(self.restrictedUser)
        url = self.activity_group.get_delete_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403, "View returned non-denied status code for anonymous user.")
