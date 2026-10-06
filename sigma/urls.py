from django.urls import path
from . import views

urlpatterns = [
    # ----------------------------------------------------
    # Autenticação e Rotas Gerais
    # ----------------------------------------------------
    path('', views.login_view, name='login'),
    path('sair/', views.logout_view, name='logout'),
    path('perfil/', views.meu_perfil, name='meu_perfil'),
    
    # ----------------------------------------------------
    # Rotas do Monitor (Estudante)
    # ----------------------------------------------------
    path('monitor/', views.dashboard_monitor, name='dashboard_monitor'),
    path('monitor/enviar-documento/', views.enviar_documento, name='enviar_documento'),
    path('monitor/editar-documento/<int:entrega_id>/', views.editar_documento, name='editar_documento'),
    path('monitor/excluir-documento/<int:entrega_id>/', views.excluir_documento, name='excluir_documento'),
    
    # ----------------------------------------------------
    # Rotas do Professor Orientador
    # ----------------------------------------------------
    path('professor/', views.dashboard_professor, name='dashboard_professor'),
    path('professor/avaliar/<int:entrega_id>/<str:acao>/', views.avaliar_entrega, name='avaliar_entrega'),
    path('professor/historico/<int:monitoria_id>/', views.historico_monitor, name='historico_monitor'),
    path('professor/avaliacoes/', views.avaliacoes_pendentes, name='avaliacoes_pendentes'),
    path('professor/monitores/', views.meus_monitores, name='meus_monitores'),
    
    # ----------------------------------------------------
    # Rotas do Setor Pedagógico
    # ----------------------------------------------------
    path('pedagogico/', views.dashboard_pedagogico, name='dashboard_pedagogico'),
    path('pedagogico/usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('pedagogico/usuarios/novo/', views.criar_usuario, name='criar_usuario'),
    path('pedagogico/monitorias/nova/', views.criar_monitoria, name='criar_monitoria'),
    
    # ----------------------------------------------------
    # Rotas do Monitor (Estudante)
    # ----------------------------------------------------
    path('monitor/', views.dashboard_monitor, name='dashboard_monitor'),
    path('monitor/enviar-documento/', views.enviar_documento, name='enviar_documento'),
]