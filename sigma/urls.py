from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import RecuperarSenhaForm  # Importa o nosso novo formulário

urlpatterns = [
    # ----------------------------------------------------
    # Autenticação e Rotas Gerais
    # ----------------------------------------------------
    path('', views.login_view, name='login'),
    path('sair/', views.logout_view, name='logout'),
    path('perfil/', views.meu_perfil, name='meu_perfil'),
    
    # Rota de recuperação atualizada com o form_class
    path('recuperar-senha/', auth_views.PasswordResetView.as_view(
        template_name='sigma/recuperar_senha/form.html',
        form_class=RecuperarSenhaForm
    ), name='password_reset'),
    
    path('recuperar-senha/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='sigma/recuperar_senha/enviado.html'), name='password_reset_done'),
    path('recuperar-senha/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='sigma/recuperar_senha/confirmar.html'), name='password_reset_confirm'),
    path('recuperar-senha/concluido/', auth_views.PasswordResetCompleteView.as_view(template_name='sigma/recuperar_senha/concluido.html'), name='password_reset_complete'),
    
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
    path('pedagogico/usuarios/editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('pedagogico/usuarios/<int:usuario_id>/status/', views.alternar_status_usuario, name='alternar_status_usuario'),
    path('pedagogico/usuarios/<int:usuario_id>/excluir/', views.excluir_usuario, name='excluir_usuario'),
    
    path('pedagogico/monitorias/nova/', views.criar_monitoria, name='criar_monitoria'),
    path('pedagogico/monitorias/editar/<int:monitoria_id>/', views.editar_monitoria, name='editar_monitoria'),
    path('pedagogico/monitorias/excluir/<int:monitoria_id>/', views.excluir_monitoria, name='excluir_monitoria'),
    
    path('pedagogico/prazos/', views.gerenciar_prazos, name='gerenciar_prazos'),
    path('pedagogico/prazos/excluir/<int:prazo_id>/', views.excluir_prazo, name='excluir_prazo'),
    
    path('pedagogico/auditoria/', views.auditoria_documentos, name='auditoria_documentos'),
    path('pedagogico/auditoria/<int:entrega_id>/<str:acao>/', views.processar_auditoria, name='processar_auditoria'),
    
    path('pedagogico/relatorio/', views.relatorio_mensal, name='relatorio_mensal'),
    path('pedagogico/notificar-atrasados/', views.notificar_atrasados, name='notificar_atrasados'),
]