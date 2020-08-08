from collections import namedtuple
from django.apps import AppConfig
import django.conf
from assessment import settings


def Map(type_name, **kwargs):
    # Returns a simple map of kwargs object
    mapType = namedtuple(type_name, kwargs.keys(),)
    return mapType(**kwargs)


class BaseAssessConfig(AppConfig):
    name = 'assessment.assess'
    verbose_name = 'Assessments'

    # Default settings for the document_catalogue app.
    settings = Map(
        'default_settings',
        SUBJECT_MODEL = settings.ASSESSMENT_SUBJECT_MODEL,
        SUBJECT_ORDER_BY = settings.ASSESSMENT_SUBJECT_ORDER_BY,
        SCORE_CLASSES = settings.ASSESSMENT_SCORE_CLASSES,
        PERMISSIONS=settings.ASSESSMENT_PERMISSIONS,
    )


class PublicAssessConfig(BaseAssessConfig):
    """ App config for publicly accessible assessments with publicly accessible supporting documents """
    settings = Map(
        "public_settings",
        USE_PRIVATE_FILES = False,
        LOGIN_REQUIRED = getattr(django.conf.settings,
                                 'ASSESSMENT_LOGIN_REQUIRED', False),
        **BaseAssessConfig.settings._asdict()
    )


class PrivateAssessConfig(BaseAssessConfig):
    """ App config for private assessments with strictly private supporting documents """
    settings = Map(
        "public_settings",
        USE_PRIVATE_FILES = True,
        LOGIN_REQUIRED = getattr(django.conf.settings,
                                 'ASSESSMENT_LOGIN_REQUIRED', True),
        **BaseAssessConfig.settings._asdict()
    )
