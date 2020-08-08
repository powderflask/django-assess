from django.conf import settings
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # path('builder/', include('assessment.builder.urls')),

    path('assessments/', include('assessment.assess.urls')),

    path('accounts/', include('django.contrib.auth.urls')),

    path('private-media/', include('private_storage.urls')),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()