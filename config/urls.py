from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rota para o painel nativo do Django
    path('admin/', admin.site.urls),
    
    # Manda todas as outras requisições para o arquivo urls.py do app 'sigma'
    path('', include('sigma.urls')),
]

# Libera o acesso aos arquivos enviados (Media) durante o ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)