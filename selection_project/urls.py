# selection_project/urls.py
from django.contrib import admin
from django.urls import path, include
from api.views import frontend_view # Importa la vista del frontend

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', frontend_view, name='frontend'), # Sirve el frontend en la raíz
]