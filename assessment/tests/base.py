"""
     Base classes used to setup testing fixtures
"""
import itertools

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import AnonymousUser, User, Permission
from django.utils.text import slugify
from assessment.builder import models, choices
from assessment.assess import models as record_models, choices as record_choices
from assessment import settings


def anonymous_user():
    return AnonymousUser()


def create_user(username='myUser', permissions=()):
    """
        Factory function to create and return a single user with the given iterable of permissions.
        Common Assessment permissions:  ('Can build assessment', 'Can edit assessment', 'Can delete assessment')
    """
    user = User.objects.create_user(
        first_name=username.capitalize(), last_name="Lastname", email="{username}@example.com".format(username=username),
        username=username, password="password",
    )
    if permissions:
        permissions = Permission.objects.filter(name__in=permissions)
        user.user_permissions.set(permissions)

    return user


def create_assessment_categories(activity_names=('Activity 1', 'Activity 2', 'Activity 3',),
                                 topic_names=('Topic A', 'Topic B', 'Topic C',),
                                 description_template='This is the description for {slug}'):
    """
        Factory function to create and return a set of AssessmentCategory objects,
        and related Activities and Topics, defined by all activity x topic pairs.
    """
    def create_activity(label):
        slug = slugify(label)
        return models.Activity.objects.create(label=label, slug=slug,
                                              description=description_template.format(slug=slug),
                                              status=choices.ACTIVE_STATUS)

    def create_topic(label):
        slug = slugify(label)
        return models.Topic.objects.create(label=label, slug=slug,
                                           description=description_template.format(slug=slug),
                                           status=choices.ACTIVE_STATUS)

    def create_category(activity, topic):
        slug = slugify('{activity}-{topic}'.format(activity=activity, topic=topic))
        return models.AssessmentCategory.objects.create(activity=activity, topic=topic, slug=slug,
                                                        description=description_template.format(slug=slug),
                                                        status=choices.ACTIVE_STATUS)

    activities = (create_activity(name) for name in activity_names)
    topics = (create_topic(name) for name in topic_names)
    categories = []
    for activity, topic in set(itertools.product(activities, topics)):
        categories.append( create_category(activity, topic) )

    return categories


def create_refdoc(category, label, url='https://example.com/docs/Zaphod.txt', description_template='RefDoc description for {label}'):
    return models.ReferenceDocument.objects.create(
        category=category,
        label=label,
        url=url,
        description=description_template.format(label=label)
    )


def create_question(category, label, description_template='Description for Question {label}'):
    return models.AssessmentQuestion.objects.create(
        category=category,
        label=label,
        description=description_template.format(label=label),
        status=choices.ACTIVE_STATUS,
    )


def create_metric_choice_type(label, choice_map='{"non-compliant":0, "needs work":1, "fully compliant":2}'):
    return models.MetricChoicesType.objects.create(
        label=label,
        choice_map=choice_map,
    )


def create_metric(question, label, metric_choices=None, description_template='Description for Metric {label}'):
    metric_choices = metric_choices or create_metric_choice_type('Choices for {question}'.format(question=label))
    return models.AssessmentMetric.objects.create(
        question=question,
        label=label,
        choices=metric_choices,
        description=description_template.format(label=label),
    )

def create_question_metric_set(category, question_label, num_metrics):
    question = create_question(category, question_label)
    for i in range(num_metrics):
        create_metric(question, 'Metric {i} for question {question}'.format(i=i, question=question_label))

def create_assessment_group(user, activity=None, topic=None, as_draft=True, assessment_type='qa'):
    xor = lambda a, b : (a or b) and not (a and b)
    assert xor(activity, topic), 'Assessment Groups must be for Activity XOR Topic'
    assessment_set = record_models.AssessmentGroup.objects.create(
        activity=activity, topic=topic,
        assessor=user,
        assessment_type=assessment_type,
        status=record_choices.DRAFT_STATUS if as_draft else record_choices.COMPLETE_STATUS
    )
    return assessment_set

def create_assessment(user, category, label, as_draft=False, assessment_type='qa', description_template='Assessment description for {label}'):
    assessment = record_models.AssessmentRecord(
        category=category,
        last_edited_by=user,
        assessor=user,
        assessment_type=assessment_type,
        status=record_choices.DRAFT_STATUS if as_draft else record_choices.COMPLETE_STATUS
    )
    assessment.save()

    _ = record_models.AssessmentSubject.objects.create(
        record=assessment,
        label=label,
        description=description_template.format(label=label),
    )
    return assessment


def create_score(assessment, metric, applicable=True, score=1, comments='Comments for metric score'):
    return record_models.MetricScore.objects.create(
        assessment=assessment,
        metric=metric,
        applicable=applicable,
        score=score,
        comments=comments
    )


##### Supporting Documents with file uploads #####


def generate_simple_uploaded_file(filename, file_type='txt'):
    if file_type is 'txt':
        return SimpleUploadedFile(filename, b'Hello World')

    if file_type is 'html':
        return SimpleUploadedFile(filename, b'<!DOCTYPE html><html><head></head><body><p>Hello World</p></body></html>')

    raise Exception("Don't know how to generate file of type %s"%file_type)


def create_support_document_attach(filename='hello.txt', file_type='txt', score=None):
    document = record_models.SupportingDoc.objects.create(
        score=score or record_models.MetricScore.objects.all().first(),
        document_location=record_choices.DOCUMENT_LOCATION_ATTACHED,
        description=('Description for attached file {filename}.{file_type}'.format(filename=filename, file_type=file_type)),
        file=generate_simple_uploaded_file(filename, file_type),
    )
    return document


def create_support_document_link(url='https://example.com/docs/beeblebrox.pdf', score=None):
    document = record_models.SupportingDoc.objects.create(
        score=score or record_models.MetricScore.objects.all().first(),
        document_location=record_choices.DOCUMENT_LOCATION_LINK,
        description=('Description for linked doc {url}'.format(url=url)),
        url=url,
    )
    return document
