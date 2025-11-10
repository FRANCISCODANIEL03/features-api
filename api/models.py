# api/models.py
import uuid
from django.db import models

class FeatureSelectionJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        RUNNING = 'RUNNING', 'Ejecutando'
        COMPLETE = 'COMPLETE', 'Completo'
        FAILED = 'FAILED', 'Falló'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    
    # Parámetros para el modelo base
    model_params = models.JSONField(default=dict)
    
    # Cuántas características seleccionar
    top_n_features = models.IntegerField(default=10)
    
    # Dónde se guardarán los resultados
    results = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FeatureSelection Job {self.id} - {self.status}"