from django.test import TestCase
from django.core.exceptions import PermissionDenied
from assessment.assess.permissions import permissions, get_permissions_context_from_request, permission_required
from assessment.tests import base


class BaseTestWithUsers(TestCase):
    """
        Test behaviours for Assessment Record CRUD views
    """
    def setUp(self):
        super().setUp()
        self.privilegedUser = base.create_user(username='privileged',
                                               permissions=('Can add Assessment Record', 'Can change Assessment Record', 'Can delete Assessment Record'))
        self.restrictedUser = base.create_user(username='restricted')

    def login(self, user):
        response = self.client.login(username=user.username, password='password')
        self.assertTrue(response)


class BasicPermissionsTests(BaseTestWithUsers):
    """
    Test default permissions functions
    """
    def test_user_can_view_assessments(self):
        self.assertFalse(permissions.user_can_view_assessments(base.anonymous_user()))
        self.assertTrue(permissions.user_can_view_assessments(self.restrictedUser))

    def test_user_can_create_assessment(self):
        self.assertFalse(permissions.user_can_create_assessment(self.restrictedUser))
        self.assertTrue(permissions.user_can_create_assessment(self.privilegedUser))

    def test_user_can_edit_assessment(self):
        self.assertFalse(permissions.user_can_edit_assessment(self.restrictedUser))
        self.assertTrue(permissions.user_can_edit_assessment(self.privilegedUser))

    def test_user_can_delete_assessment(self):
        self.assertFalse(permissions.user_can_delete_assessment(self.restrictedUser))
        self.assertTrue(permissions.user_can_delete_assessment(self.privilegedUser))


class PermissionsDecoratorTests(BaseTestWithUsers):
    """
    Test default permissions decorators
    """

    @permission_required(permissions.user_can_edit_assessment)
    class DummyView:
        kwargs={}
        def dispatch(self, request, **kwargs):
            return True
    dummy_view = DummyView()

    def test_permission_required_privilegedUser(self):
        request = lambda: None
        request.user = self.privilegedUser
        self.assertTrue(self.dummy_view.dispatch(request))

    def test_permission_required_restrictedUser(self):
        request = lambda: None
        request.user = self.restrictedUser
        self.assertRaises(PermissionDenied, self.dummy_view.dispatch, request=request)


class PermissionsContextProvidersTests(BaseTestWithUsers):
    """
    Test default permissions context providers
    """

    def test_privilegedUser(self):
        request = lambda: None
        request.user = self.privilegedUser

        context = get_permissions_context_from_request(request)
        self.assertIn('user_can_edit_assessment', context)
        self.assertTrue(context['user_can_edit_assessment']())

    def test_restrictedUser(self):
        request = lambda: None
        request.user = self.restrictedUser

        context = get_permissions_context_from_request(request)
        self.assertIn('user_can_edit_assessment', context)
        self.assertFalse(context['user_can_edit_assessment']())