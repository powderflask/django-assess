from django.urls import path
from . import views

app_name = 'assessment.assess'

urlpatterns = [
    # path('', TemplateView.as_view(template_name="index.html"), name='home'),

    path('matrix/', views.AssessmentMatrixView.as_view(), name='matrix'),

    path('activity/<slug:slug>/', views.ActivityView.as_view(), name='activity'),

    path('topic/<slug:slug>/', views.TopicView.as_view(), name='topic'),

    path('category/<slug:slug>/', views.AssessmentCategoryView.as_view(), name='category'),

    # CRUD views for individual Assessment records
    path('create/<slug:slug>/', views.AssessmentRecordCreateView.as_view(), name='create'),

    path('detail/<int:pk>/', views.AssessmentRecordDetailView.as_view(), name='detail'),

    path('update/<int:pk>/', views.AssessmentRecordUpdateView.as_view(), name='update'),

    path('delete/<int:pk>/', views.AssessmentRecordDeleteView.as_view(), name='delete'),

    # CRUD views for Assessment groups
    path('create/group/<slug:slug>/', views.AssessmentGroupCreateView.as_view(), name='group-create'),

    path('detail/group/<int:pk>/', views.AssessmentGroupDetailView.as_view(), name='group-detail'),

    path('update/group/<int:pk>/', views.AssessmentGroupUpdateView.as_view(), name='group-update'),

    path('delete/group/<int:pk>/', views.AssessmentGroupDeleteView.as_view(), name='group-delete'),

]
