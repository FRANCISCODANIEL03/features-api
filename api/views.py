from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FeatureSelectionJob
from .tasks import run_analysis_job

def frontend_view(request):
    return render(request, "index.html")

class StartJobView(APIView):
    def post(self, request, *args, **kwargs):
        job_type = request.data.get('job_type', 'RF')
        model_params = request.data.get('model_params', {})
        
        # --- CAPTURAR EJES ---
        # Aseguramos que existan en model_params si el frontend no los mandó bien
        if 'feature_x' not in model_params:
            model_params['feature_x'] = 'V10' # Default