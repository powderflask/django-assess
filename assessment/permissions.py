"""
Pluggable Permissions Module.
This default permissions module can be swapped out using ASSESSMENT_PERMISSIONS setting.
Defaults use django's built in content_type permissions for the AssessmentRecord model.

Functions used to control access to views (Permission Denied returned when false)
    and to enable/disable interactions in the templates.

Each function takes the request user and the view's kwargs as arguments,
    returns True iff user has the required permission for the given object(s).
"""
from django.apps import apps
appConfig = apps.get_app_config('assess')


def user_can_view_assessments(user, **kwargs):
    """ Return True iff given user is allowed to view the assessments """
    return not appConfig.settings.LOGIN_REQUIRED or user.is_authenticated


def user_can_create_assessment(user, **kwargs):
    """ Return True iff the given user can create new assessments """
    return user.is_staff or user.has_perm('assess.add_assessmentrecord')

def user_can_edit_assessment(user, **kwargs):
    """ Return True iff the given user can edit assessments """
    return user.is_staff or user.has_perm('assess.change_assessmentrecord')


def user_can_delete_assessment(user, **kwargs):
    """ Return True iff the given user can edit assessments """
    return user.is_staff or user.has_perm('assess.delete_assessmentrecord')
