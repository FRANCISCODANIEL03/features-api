# api/models.py (CORREGIDO)
import uuid
from django.db import models

class FeatureSelectionJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        RUNNING = 'RUNNING', 'Ejecutando'
        COMPLETE = 'COMPLETE', 'Completo'
        FAILED = 'FAILED', 'Falló'

    class JobType(models.TextChoices):
        RANDOM_FOREST = 'RF', 'Random Forest (Selección de Características)'
        KMEANS = 'KM', 'Clustering (K-Means)'
        DBSCAN = 'DB', 'Clustering (DBSCAN)' 

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    
    job_type = models.CharField(max_length=10, choices=JobType.choices, default=JobType.RANDOM_FOREST)
    
    model_params = models.JSONField(default=dict)
    top_n_features = models.IntegerField(default=7)
    
    results = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_type} Job {self.id} - {self.status}"