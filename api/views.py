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
        if 'feature_y' not in model_params:
            model_params['feature_y'] = 'V14' # Default
        # ---------------------

        # Validaciones DBSCAN
        if job_type == 'DB':
            if 'eps' in model_params: model_params['eps'] = float(model_params['eps'])
            if 'min_samples' in model_params: model_params['min_samples'] = int(model_params['min_samples'])

        top_n = request.data.get('top_n_features', 10)
        try: top_n = int(top_n)
        except: top_n = 10
