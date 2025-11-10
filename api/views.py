# api/views.py
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FeatureSelectionJob
from .tasks import run_feature_selection_job

def frontend_view(request):
    """ Sirve el archivo frontend/index.html """
    return render(request, "index.html")

class StartJobView(APIView):
    """ Inicia un nuevo trabajo de selección de características. """
    def post(self, request, *args, **kwargs):
        model_params = request.data.get('model_params', {})
        top_n_features = request.data.get('top_n_features', 10) # Default a 10

        try:
            top_n_features = int(top_n_features)
            if top_n_features <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'El parámetro "top_n_features" debe ser un entero positivo.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job = FeatureSelectionJob.objects.create(
            model_params=model_params,
            top_n_features=top_n_features,
        )

        run_feature_selection_job.delay(job.id)

        return Response(
            {
                'message': 'Trabajo de selección de características recibido.',
                'job_id': job.id,
                'status': job.status,
                'status_url': request.build_absolute_uri(f'/api/status/{job.id}/')
            },
            status=status.HTTP_202_ACCEPTED
        )

class JobStatusView(APIView):
    """ Consulta el estado y resultado de un trabajo. """
    def get(self, request, job_id, *args, **kwargs):
        try:
            job = FeatureSelectionJob.objects.get(id=job_id)
        except FeatureSelectionJob.DoesNotExist:
            return Response(
                {'error': 'Trabajo no encontrado.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        response_data = {
            'job_id': job.id,
            'status': job.status,
            'top_n_features': job.top_n_features,
            'model_params_base': job.model_params,
            'created_at': job.created_at,
            'updated_at': job.updated_at,
            'results': job.results,
            'error_message': job.error_message,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)