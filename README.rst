
Assessments
===========

Basic custom assessments as a reusable django app.

Use Case:
 * you are creating a QC/QA program for assessing a business process or organization units
 * you want to assess 1 or more "activties" within the process or units;
 * for each activity, an assessment is performed in 1 or more categories;
 * each assessment category presents 1 or more assessment questions;
 * each question presents 1 or more metrics by which the question is assessed;

Features:
 * Assessment Builder - you define the process, categories, questions, and metrics  (django admin tool)
 * Assessment Tool - basic navigation, and CRUD for doing assessments; swappable assessment "subject" model
 * Assessment ScoreCards - summarize and score across a set of assessments
 * plugin permissions settings

Dependencies:
 * python 3.5+
 * django 2+
 * `django-ordered-model <https://pypi.org/project/django-ordered-model/>`_
 * `django-tables2 <https://pypi.org/project/django-tables2/>`_
 * `django-filter <https://pypi.org/project/django-filter/>`_
Opt-in:
 * `django-private-storage <https://pypi.org/project/django-private-storage/>`_


Get Me Some of That
-------------------
* `Source Code <https://github.com/powderflask/django_assess>`_
* `Read The Docs <https://django-assess.readthedocs.io/en/latest/>`_
* `Issues <https://github.com/powderflask/django_assess/issues>`_
* `PiPy <https://pypi.org/project/django-assess>`_


`MIT license <https://github.com/powderflask/django_assess/blob/master/LICENSE>`_


< Detailed documentation is in the "docs" directory. > (TODO)


Quick start
-----------

* `pip install -r requirements.txt`
* `python3 setup.py test`   (to run app test suite)

1. Add assessment apps to your INSTALLED_APPS setting::

    INSTALLED_APPS = [
        ...
        'assessment.builder.apps.BuilderConfig',
        'assessment.assess.apps.PrivateAssessConfig',   # or PublicAssessConfig for public assessments
        'assessment.scorecards.apps.ScorecardConfig',
    ]

2. Include the assessment URLconf in your project urls.py::

    path('assessments/', include('assessment.urls')),

3. Run `python manage.py migrate` to create the assessment models (and superuser).

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to run the demo app and build some Assessments;
   or, optionally, load supplied demo assessment matrix::

    python3 demo/manage.py loaddata demo/fixtures.json

5. Visit http://127.0.0.1:8000/assessments/ to browse your assessments by activity and category.


Next Steps
----------

See the demo project for some ideas on how to configure and use Assessment apps.

 * add assessment/base.html to your templates to override the base template.

   * Assessment views are rendered within `{% block content %}`


License
-------

The code is available under the MIT License (see LICENSE).
