# api/urls.py
from django.urls import path
from .views import StartJobView, JobStatusView

urlpatterns = [
    path('start/', StartJobView.as_view(), name='start_job'),
    path('status/<uuid:job_id>/', JobStatusView.as_view(), name='job_status'),
]