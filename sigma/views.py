from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Usuario, Monitoria, EntregaMensal,PrazoExcecao
from .forms import UsuarioCreationForm,MonitoriaForm,PrazoExcecaoForm, UsuarioAdminUpdateForm

from .forms import UsuarioCreationForm, MonitoriaForm, EntregaMensalForm

from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Monitoria, EntregaMensal
from .forms import EntregaMensalForm

from .models import PrazoExcecao
from .forms import PrazoExcecaoForm
import calendar
from datetime import date, timedelta

import csv
from django.http import HttpResponse

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UsuarioUpdateForm

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

import string
import random
from django.core.mail import send_mail
from django.conf import settings

from django.views.decorators.http import require_POST


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Monitoria
from .forms import MonitoriaForm


def obter_prazo_do_mes(ano, mes):
    """
    Retorna a data limite. Se houver exceção cadastrada, usa ela.
    Caso contrário, calcula matematicamente o 5º dia útil (segunda a sexta).
    """
    excecao = PrazoExcecao.objects.filter(ano_referencia=ano, mes_referencia=mes).first()
    if excecao:
        return excecao.nova_data_limite
        
    # Calcula 5º dia útil
    dia = 1
    dias_uteis = 0
    while dias_uteis < 5:
        # 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
        if date(ano, mes, dia).weekday() < 5: 
            dias_uteis += 1
        if dias_uteis < 5:
            dia += 1
            
    return date(ano, mes, dia)


# =====================================================================
# 1. AUTENTICAÇÃO E ROTAS GERAIS
# =====================================================================

def login_view(request):
    # Se o usuário já estiver logado, manda direto para o dashboard
    if request.user.is_authenticated:
        return redirecionar_dashboard(request.user)

    if request.method == 'POST':
        # O Setor Pedagógico pode usar o CPF, Matrícula ou Email como 'username' no momento de cadastrar.
        usuario_digitado = request.POST.get('username') 
        senha_digitada = request.POST.get('password')

        user = authenticate(request, username=usuario_digitado, password=senha_digitada)

        if user is not None:
            login(request, user)
            return redirecionar_dashboard(user)
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'sigma/login.html')


def redirecionar_dashboard(user):
    """Função auxiliar para checar o tipo de usuário e redirecionar"""
    if user.tipo_usuario == 'A':
        return redirect('dashboard_pedagogico')
    elif user.tipo_usuario == 'P':
        return redirect('dashboard_professor')
    elif user.tipo_usuario == 'M':
        return redirect('dashboard_monitor')
    else:
        # Se for o superuser criado no terminal, manda pro admin nativo
        return redirect('/admin/')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def meu_perfil(request):
    # Essa tela serve para todos os usuários (Monitor, Professor e Pedagógico)
    return render(request, 'sigma/meu_perfil.html')

@login_required
def meu_perfil(request):
    if request.method == 'POST':
        # Se o utilizador clicou no botão de atualizar os dados
        if 'atualizar_perfil' in request.POST:
            form_perfil = UsuarioUpdateForm(request.POST, instance=request.user)
            form_senha = PasswordChangeForm(request.user)
            if form_perfil.is_valid():
                form_perfil.save()
                messages.success(request, 'Os seus dados foram atualizados com sucesso!')
                return redirect('meu_perfil')
                
        # Se o utilizador clicou no botão de alterar a palavra-passe
        elif 'alterar_senha' in request.POST:
            form_perfil = UsuarioUpdateForm(instance=request.user)
            form_senha = PasswordChangeForm(request.user, request.POST)
            if form_senha.is_valid():
                user = form_senha.save()
                # Esta linha impede que o utilizador seja deslogado após mudar a password
                update_session_auth_hash(request, user) 
                messages.success(request, 'Palavra-passe alterada com segurança!')
                return redirect('meu_perfil')
            else:
                messages.error(request, 'Erro ao alterar a palavra-passe. Verifique se os campos coincidem e se a senha é forte o suficiente.')
    else:
        form_perfil = UsuarioUpdateForm(instance=request.user)
        form_senha = PasswordChangeForm(request.user)

    return render(request, 'sigma/meu_perfil.html', {
        'form_perfil': form_perfil,
        'form_senha': form_senha
    })



# =====================================================================
# 2. SETOR DO MONITOR (ESTUDANTE)
# =====================================================================

@login_required
def dashboard_monitor(request):
    if request.user.tipo_usuario != 'M':
        return redirect('login')
        
    monitoria = Monitoria.objects.filter(monitor=request.user).first()
    entregas = []
    avisos = []
    
    resumo = {'status': 'Nenhum vínculo', 'cor': 'text-secondary', 'prazo': '-'}

    if monitoria:
        entregas = EntregaMensal.objects.filter(monitoria=monitoria).order_by('-mes_referencia')
        hoje = date.today()
        
        # =================================================================
        # 1. VARREDURA INTELIGENTE (Da data_inicio até o mês passado)
        # =================================================================
        # Pega a data_inicio que o Pedagógico cadastrou e normaliza pro dia 1
        data_iter = monitoria.data_inicio.replace(day=1) 
        mes_atual = hoje.replace(day=1)
        
        # Faz um loop mês a mês até o mês em que estamos
        while data_iter <= mes_atual:
            # Para a varredura se já passou da data final do contrato
            if data_iter > monitoria.data_fim.replace(day=1):
                break
                
            mes_str = data_iter.strftime('%m/%Y')
            
            # Prazo limite: Dia 10 do MÊS SEGUINTE
            mes_seg = data_iter.month + 1 if data_iter.month < 12 else 1
            ano_seg = data_iter.year if data_iter.month < 12 else data_iter.year + 1
            prazo = obter_prazo_do_mes(ano_seg, mes_seg)
            
            # Procura se o aluno enviou documento para este mês específico
            entrega_existe = entregas.filter(mes_referencia__year=data_iter.year, mes_referencia__month=data_iter.month).first()
            
            if not entrega_existe:
                # Se não enviou e já passou do dia 10
                if hoje > prazo:
                    avisos.append(f"ALERTA: Documentação de {mes_str} está ATRASADA! O prazo encerrou em {prazo.strftime('%d/%m/%Y')}.")
                else:
                    # Se não enviou, mas ainda estamos antes do dia 10 (ex: mês passado recém fechado)
                    if data_iter < mes_atual:
                        dias_restantes = (prazo - hoje).days
                        avisos.append(f"Lembrete: Faltam {dias_restantes} dias para enviar a documentação de {mes_str}.")
            
            # Avança 1 mês no loop
            if data_iter.month == 12:
                data_iter = data_iter.replace(year=data_iter.year+1, month=1)
            else:
                data_iter = data_iter.replace(month=data_iter.month+1)

        # =================================================================
        # 2. STATUS DO CARD PRINCIPAL (Foco em atrasos ou no mês anterior)
        # =================================================================
        mes_passado = hoje.month - 1 if hoje.month > 1 else 12
        ano_passado = hoje.year if hoje.month > 1 else hoje.year - 1
        prazo_limite_mes_passado = obter_prazo_do_mes(hoje.year, hoje.month)
        
        entrega_mes_passado = entregas.filter(mes_referencia__year=ano_passado, mes_referencia__month=mes_passado).first()
        tem_atraso_real = any("ATRASADA" in aviso for aviso in avisos)
        
        if not entrega_mes_passado and hoje <= prazo_limite_mes_passado:
            resumo = {'status': f'Aguardando Envio', 'cor': 'text-warning', 'prazo': prazo_limite_mes_passado.strftime('%d/%m/%Y')}
        elif entrega_mes_passado:
            if entrega_mes_passado.status == 'P':
                resumo = {'status': 'Aguardando Orientador', 'cor': 'text-primary', 'prazo': 'Em análise inicial'}
            elif entrega_mes_passado.status == 'A':
                resumo = {'status': 'Aguardando Pedagógico', 'cor': 'text-info', 'prazo': 'Em auditoria final'}
            elif entrega_mes_passado.status == 'F':
                resumo = {'status': 'Tudo em dia!', 'cor': 'text-success', 'prazo': 'Auditado e arquivado'}
            elif entrega_mes_passado.status == 'R':
                resumo = {'status': 'Recusado (Ajuste Necessário)', 'cor': 'text-danger', 'prazo': 'Ajuste Imediato'}
        else:
            resumo = {'status': 'Em andamento', 'cor': 'text-secondary', 'prazo': '-'}

        # =================================================================
        # 3. TAGS NA TABELA E RECUSAS (Sempre no topo da lista)
        # =================================================================
        for entrega in entregas:
            mes_seg = entrega.mes_referencia.month + 1 if entrega.mes_referencia.month < 12 else 1
            ano_seg = entrega.mes_referencia.year if entrega.mes_referencia.month < 12 else entrega.mes_referencia.year + 1
            prazo_da_entrega = obter_prazo_do_mes(ano_seg, mes_seg)
            
            # Checa se o campo "data_envio" (que adicionamos) é maior que o dia 10
            if entrega.data_envio:
                entrega.foi_entregue_com_atraso = entrega.data_envio.date() > prazo_da_entrega
            else:
                entrega.foi_entregue_com_atraso = False
                
            # Verifica recusas e insere no Início da lista de avisos para chamar atenção
            if entrega.status == 'R':
                mes_nome = entrega.mes_referencia.strftime('%m/%Y')
                avisos.insert(0, f'URGENTE: Documentos de {mes_nome} recusados! Motivo: "{entrega.feedback_professor}". Utilize o botão Editar para reenviar.')

    contexto = {
        'monitoria': monitoria,
        'entregas': entregas,
        'avisos': avisos,
        'resumo': resumo,
    }
    return render(request, 'sigma/monitor/dashboard_monitor.html', contexto)

@login_required
def enviar_documento(request):
    if request.user.tipo_usuario != 'M':
        return redirect('login')

    monitoria = Monitoria.objects.filter(monitor=request.user).first()

    if request.method == 'POST':
        form = EntregaMensalForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Pega a data informada no formulário
            data_informada = form.cleaned_data['mes_referencia']
            
            # 2. Força a data para o dia 1º do mês selecionado
            mes_normalizado = data_informada.replace(day=1)
            
            # 3. TRAVA ABSOLUTA: Verifica a igualdade exata da data normalizada
            if EntregaMensal.objects.filter(monitoria=monitoria, mes_referencia=mes_normalizado).exists():
                messages.error(request, f'Você já fez uma submissão para o mês {mes_normalizado.strftime("%m/%Y")}. Utilize o botão "Editar" na tela inicial para fazer alterações.')
                return redirect('dashboard_monitor')

            entrega = form.save(commit=False)
            entrega.monitoria = monitoria
            entrega.mes_referencia = mes_normalizado # Salva sempre como dia 1
            entrega.status = 'P'
            entrega.save()
            
            messages.success(request, 'Documentos submetidos com sucesso!')
            return redirect('dashboard_monitor')
    else:
        form = EntregaMensalForm()

    return render(request, 'sigma/monitor/enviar_documento.html', {'form': form, 'monitoria': monitoria, 'editando': False})

@login_required
def editar_documento(request, entrega_id):
    if request.user.tipo_usuario != 'M':
        return redirect('login')

    entrega = get_object_or_404(EntregaMensal, id=entrega_id, monitoria__monitor=request.user)
    
    if entrega.status in ['A', 'F']:
        messages.error(request, 'Documentos já em posse do setor pedagógico ou arquivados não podem ser alterados.')
        return redirect('dashboard_monitor')

    if request.method == 'POST':
        form = EntregaMensalForm(request.POST, request.FILES, instance=entrega)
        if form.is_valid():
            # 1. Normaliza a data editada para o dia 1º
            data_informada = form.cleaned_data['mes_referencia']
            mes_normalizado = data_informada.replace(day=1)
            
            # 2. Trava garantindo que ele não editou a data para bater com outro mês que já existe
            if EntregaMensal.objects.filter(monitoria=entrega.monitoria, mes_referencia=mes_normalizado).exclude(id=entrega.id).exists():
                messages.error(request, 'Você já possui outra submissão separada para este mês. Edite a submissão correta.')
                return render(request, 'sigma/monitor/enviar_documento.html', {'form': form, 'monitoria': entrega.monitoria, 'editando': True})

            entrega_salva = form.save(commit=False)
            entrega_salva.mes_referencia = mes_normalizado # Salva sempre como dia 1
            entrega_salva.status = 'P' # Volta para Pendente
            entrega_salva.save()
            
            messages.success(request, 'Documento atualizado e reenviado!')
            return redirect('dashboard_monitor')
    else:
        form = EntregaMensalForm(instance=entrega)

    return render(request, 'sigma/monitor/enviar_documento.html', {'form': form, 'monitoria': entrega.monitoria, 'editando': True})

@login_required
def excluir_documento(request, entrega_id):
    if request.user.tipo_usuario != 'M':
        return redirect('login')

    # Busca a entrega garantindo que é do aluno logado
    entrega = get_object_or_404(EntregaMensal, id=entrega_id, monitoria__monitor=request.user)
    
    # Trava de segurança: Documento aprovado não pode ser excluído
    if entrega.status in ['A', 'F']:
        messages.error(request, 'Documentos já em posse do setor pedagógico ou arquivados não podem ser alterados.')
        return redirect('dashboard_monitor')

    # Exclui o registro do banco de dados
    entrega.delete()
    messages.success(request, 'Submissão excluída com sucesso!')
    return redirect('dashboard_monitor')


# =====================================================================
# 3. SETOR DO PROFESSOR ORIENTADOR
# =====================================================================

@login_required
def dashboard_professor(request):
    if request.user.tipo_usuario != 'P':
        return redirect('login')

    # 1. Busca todas as monitorias do professor
    monitorias = Monitoria.objects.filter(professor=request.user)
    
    # 2. Busca as entregas com status 'P' (Pendente) ordenadas pela data
    entregas_pendentes = EntregaMensal.objects.filter(monitoria__in=monitorias, status='P').order_by('mes_referencia')
    
    # 3. Adiciona uma "etiqueta" rápida para o HTML saber se o aluno está com pendência
    for monitoria in monitorias:
        monitoria.tem_pendencia = EntregaMensal.objects.filter(monitoria=monitoria, status='P').exists()
    
    contexto = {
        'monitorias': monitorias,
        'entregas_pendentes': entregas_pendentes,
        'qtd_pendentes': entregas_pendentes.count(),
    }
    return render(request, 'sigma/professor/dashboard_professor.html', contexto)

@login_required
@require_POST
def avaliar_entrega(request, entrega_id, acao):
    if request.user.tipo_usuario != 'P' and not request.user.is_superuser:
        return redirect('login')

    entrega = get_object_or_404(EntregaMensal, id=entrega_id)
    
    # Segurança extra: o professor só pode avaliar as entregas dos SEUS alunos
    if entrega.monitoria.professor != request.user and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para avaliar este documento.')
        return redirect('meus_monitores')

    monitor = entrega.monitoria.monitor
    nome_monitor = monitor.first_name
    mes_ref = entrega.mes_referencia.strftime('%m/%Y') if entrega.mes_referencia else 'Mês atual'

    # Acção 1: Aprovar
    if acao == 'aprovar':
        if entrega.status == 'P':
            entrega.status = 'A' # Aprovado pelo Professor, vai para o Pedagógico
            entrega.feedback_professor = '' # Limpa feedbacks antigos, se existirem
            entrega.save()
            
            try:
                send_mail(
                    subject=f'[SIGMA] Documentação Aprovada - {entrega.monitoria.disciplina}',
                    message=f'Olá {nome_monitor},\n\nA sua documentação referente a {mes_ref} foi APROVADA pelo professor {request.user.first_name} e já foi encaminhada para análise do Setor Pedagógico.\n\nAtenciosamente,\nEquipe SIGMA',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[monitor.email],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(request, f'Documentação de {nome_monitor} aprovada e enviada para o Setor Pedagógico!')
            
    # Acção 2: Recusar (Devolver ao aluno)
    elif acao == 'recusar':
        if entrega.status == 'P':
            motivo = request.POST.get('motivo_recusa')
            if motivo:
                entrega.status = 'R' # Recusado, volta para o aluno
                entrega.feedback_professor = motivo
                entrega.save()
                
                try:
                    send_mail(
                        subject=f'[SIGMA] Documentação Recusada - Correção Necessária',
                        message=f'Olá {nome_monitor},\n\nA sua documentação referente a {mes_ref} ({entrega.monitoria.disciplina}) foi RECUSADA pelo professor {request.user.first_name}.\n\nMotivo/Feedback:\n"{motivo}"\n\nPor favor, acesse o sistema SIGMA, faça as correções e reenvie os documentos o mais breve possível.\n\nAtenciosamente,\nEquipe SIGMA',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[monitor.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass

                messages.warning(request, f'Documentação de {nome_monitor} recusada e devolvida para correção.')
            else:
                messages.error(request, 'É obrigatório informar o motivo da recusa.')

    # Acção 3: Reverter Aprovação (Puxar de volta para o professor)
    elif acao == 'reverter':
        if entrega.status == 'A':
            entrega.status = 'P' # Volta para Pendente na mesa do Professor
            entrega.save()
            messages.info(request, f'Aprovação revertida! A documentação de {nome_monitor} voltou para a sua caixa de entrada.')
        elif entrega.status == 'F':
            messages.error(request, 'Não é possível reverter: O Setor Pedagógico já arquivou e finalizou esta entrega.')

    # RETORNO DA VIEW (Fica totalmente alinhado à esquerda, fora dos "if/elif" acima)
    if acao == 'reverter':
        # Ao reverter do histórico, o professor continua no histórico
        return redirect('historico_monitor', monitoria_id=entrega.monitoria.id)
    else:
        # Ao aprovar/recusar, volta dinamicamente para a tela onde ele estava
        url_origem = request.META.get('HTTP_REFERER', 'meus_monitores')
        return redirect(url_origem)


@login_required
def historico_monitor(request, monitoria_id):
    # 1. Puxa a monitoria apenas pelo ID (sem restringir logo ao professor)
    monitoria = get_object_or_404(Monitoria, id=monitoria_id)
    
    # 2. Trava de Segurança: Só o Professor dono da monitoria OU o Pedagógico (Admin) podem ver
    eh_professor_dono = (request.user == monitoria.professor)
    eh_pedagogico = (request.user.tipo_usuario == 'A' or request.user.is_superuser)
    
    if not (eh_professor_dono or eh_pedagogico):
        messages.error(request, 'Você não tem permissão para aceder ao histórico deste monitor.')
        # Tenta devolver o usuário não autorizado para o seu painel correspondente
        if request.user.tipo_usuario == 'P':
            return redirect('dashboard_professor')
        elif request.user.tipo_usuario == 'M':
            return redirect('dashboard_monitor')
        else:
            return redirect('login')

    # 3. Se passou pela segurança, carrega as entregas normalmente
    entregas = EntregaMensal.objects.filter(monitoria=monitoria).order_by('-mes_referencia')
    
    contexto = {
        'monitoria': monitoria,
        'entregas': entregas
    }
    return render(request, 'sigma/professor/historico_monitor.html', contexto)


@login_required
def avaliacoes_pendentes(request):
    if request.user.tipo_usuario != 'P':
        return redirect('login')
    
    entregas = EntregaMensal.objects.filter(monitoria__professor=request.user, status='P').order_by('mes_referencia')
    return render(request, 'sigma/professor/avaliacoes_pendentes.html', {'entregas_pendentes': entregas})


@login_required
def meus_monitores(request):
    if request.user.tipo_usuario != 'P':
        return redirect('login')
        
    monitorias = Monitoria.objects.filter(professor=request.user)
    
    # Injeta a etiqueta de pendência aqui também para a tela de lista de monitores
    for monitoria in monitorias:
        monitoria.tem_pendencia = EntregaMensal.objects.filter(monitoria=monitoria, status='P').exists()
        
    return render(request, 'sigma/professor/meus_monitores.html', {'monitorias': monitorias})


# =====================================================================
# 4. SETOR PEDAGÓGICO (ADMINISTRAÇÃO)
# =====================================================================

@login_required
def dashboard_pedagogico(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    # Estatísticas gerais para os cards da tela inicial
    total_monitores = Usuario.objects.filter(tipo_usuario='M').count()
    total_professores = Usuario.objects.filter(tipo_usuario='P').count()
    
    # Busca quantos documentos os professores aprovaram e estão esperando a canetada final do Pedagógico
    auditorias_pendentes = EntregaMensal.objects.filter(status='A').count()
    
    contexto = {
        'total_monitores': total_monitores,
        'total_professores': total_professores,
        'auditorias_pendentes': auditorias_pendentes,
    }
    return render(request, 'sigma/pedagogico/dashboard_pedagogico.html', contexto)

@login_required
def editar_usuario(request, usuario_id):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')
        
    usuario_alvo = get_object_or_404(Usuario, id=usuario_id)
    
    # NOVA TRAVA: Impede a edição de administradores
    if usuario_alvo.is_superuser:
        messages.error(request, 'Acesso negado. Apenas a equipa de TI pode editar contas de Administradores do Sistema.')
        return redirect('listar_usuarios')
    
    if request.method == 'POST':
        form = UsuarioAdminUpdateForm(request.POST, instance=usuario_alvo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Os dados do usuário {usuario_alvo.username} foram atualizados com sucesso!')
            return redirect('listar_usuarios')
    else:
        form = UsuarioAdminUpdateForm(instance=usuario_alvo)
        
    return render(request, 'sigma/pedagogico/editar_usuario.html', {
        'form': form, 
        'usuario_alvo': usuario_alvo
    })


@login_required
def listar_usuarios(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        messages.error(request, 'Acesso restrito ao Setor Pedagógico.')
        return redirect('login')
    
    # Busca todos os usuários do banco, ordenados por nome
    usuarios = Usuario.objects.all().order_by('first_name')
    return render(request, 'sigma/pedagogico/listar_usuarios.html', {'usuarios': usuarios})


@login_required
def criar_usuario(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            # 1. Não salva na base de dados imediatamente (commit=False)
            novo_usuario = form.save(commit=False)
            
            # 2. Gera uma password aleatória segura (8 caracteres: letras e números)
            caracteres = string.ascii_letters + string.digits
            senha_gerada = ''.join(random.choice(caracteres) for i in range(8))
            
            # 3. Define a password criptografada no Django
            novo_usuario.set_password(senha_gerada)
            novo_usuario.save() # Agora sim, salva no banco de dados

            # 4. Define o Perfil para o texto do e-mail
            perfil_nome = "Monitor(a)"
            if novo_usuario.tipo_usuario == 'P':
                perfil_nome = "Professor(a) Orientador(a)"
            elif novo_usuario.tipo_usuario == 'A':
                perfil_nome = "Membro do Setor Pedagógico"

            # 5. Prepara o E-mail de Boas-vindas
            assunto = 'Bem-vindo ao SIGMA - As suas credenciais de acesso'
            mensagem = (
                f"Olá {novo_usuario.first_name},\n\n"
                f"A sua conta de {perfil_nome} foi criada com sucesso no Sistema de Gestão de Monitorias (SIGMA) do IFMG.\n\n"
                f"Aqui estão as suas credenciais de acesso:\n"
                f"--------------------------------------------------\n"
                f"Login (Matrícula/SIAPE): {novo_usuario.username}\n"
                f"Palavra-passe temporária: {senha_gerada}\n"
                f"--------------------------------------------------\n\n"
                f"Por favor, aceda ao sistema e troque a sua palavra-passe no menu 'O Meu Perfil' logo no primeiro acesso por questões de segurança.\n\n"
                f"Atenciosamente,\n"
                f"Setor Pedagógico - IFMG Campus São João Evangelista"
            )

            # 6. Dispara o E-mail
            try:
                send_mail(
                    subject=assunto,
                    message=mensagem,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[novo_usuario.email],
                    fail_silently=False,
                )
                messages.success(request, f'Usuário {novo_usuario.username} criado e e-mail com a senha enviado com sucesso!')
            except Exception as e:
                # Se a internet cair, a conta foi criada, mas a senha não foi enviada.
                messages.warning(request, f'Aviso: O usuário {novo_usuario.username} foi criado (Senha: {senha_gerada}), mas falhou o envio do e-mail. Por favor, informe-o manualmente.')
            
            return redirect('listar_usuarios')
    else:
        form = UsuarioCreationForm()
        
    return render(request, 'sigma/pedagogico/criar_usuario.html', {'form': form})

@login_required
def criar_monitoria(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    # Busca todos os vínculos existentes, ordenados pela data de início mais recente
    vinculos_existentes = Monitoria.objects.all().order_by('-data_inicio')

    if request.method == 'POST':
        form = MonitoriaForm(request.POST)
        if form.is_valid():
            nova_monitoria = form.save()
            
            # --- LÓGICA DE E-MAIL ---
            professor = nova_monitoria.professor
            aluno = nova_monitoria.monitor
            disciplina = nova_monitoria.disciplina
            assunto = f'SIGMA - Novo Vínculo de Monitoria: {disciplina}'
            mensagem = (
                f"Olá Prof. {professor.first_name} e Monitor(a) {aluno.first_name},\n\n"
                f"Informamos que o Setor Pedagógico acabou de estabelecer um novo vínculo de monitoria no sistema SIGMA.\n\n"
                f"Detalhes do Vínculo:\n"
                f"--------------------------------------------------\n"
                f"Professor Orientador: {professor.get_full_name() or professor.username}\n"
                f"Estudante/Monitor: {aluno.get_full_name() or aluno.username}\n"
                f"Disciplina Alocada: {disciplina}\n"
                f"Período de vigência: {nova_monitoria.data_inicio.strftime('%d/%m/%Y')} até {nova_monitoria.data_fim.strftime('%d/%m/%Y')}\n"
                f"--------------------------------------------------\n\n"
                f"A partir de agora, o monitor já pode submeter os relatórios mensais através do seu painel no SIGMA.\n\n"
                f"Atenciosamente,\n"
                f"Setor Pedagógico - IFMG Campus São João Evangelista"
            )
            try:
                send_mail(assunto, mensagem, settings.DEFAULT_FROM_EMAIL, [professor.email, aluno.email], fail_silently=False)
                messages.success(request, f'Vínculo criado! Notificações enviadas para {professor.first_name} e {aluno.first_name}.')
            except Exception as e:
                messages.warning(request, f'Vínculo criado no sistema, mas falhou o alerta por e-mail. Erro: {e}')
            
            # Após criar, recarrega a mesma página (para ver o vínculo na lista)
            return redirect('criar_monitoria') 
        else:
            # 1. Verifica se existe aquele erro geral (ex: Conflito de Datas)
            if form.non_field_errors():
                erro_exato = form.non_field_errors()[0]
                messages.error(request, erro_exato)
            else:
                # 2. Se não houver erro geral, foi algum campo em branco ou data invertida
                messages.error(request, 'Não foi possível salvar. Verifique os campos assinalados a vermelho.')
    else:
        form = MonitoriaForm()
        
    contexto = {
        'form': form,
        'vinculos': vinculos_existentes
    }
    return render(request, 'sigma/pedagogico/criar_monitoria.html', contexto)

@login_required
def gerenciar_prazos(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':
        form = PrazoExcecaoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exceção de prazo cadastrada! O sistema já atualizou a data para os alunos.')
            return redirect('gerenciar_prazos')
    else:
        # Preenche com o mês e ano atuais por padrão
        hoje = date.today()
        form = PrazoExcecaoForm(initial={'mes_referencia': hoje.month, 'ano_referencia': hoje.year})

    prazos = PrazoExcecao.objects.all().order_by('-ano_referencia', '-mes_referencia')
    return render(request, 'sigma/pedagogico/prazos.html', {'form': form, 'prazos': prazos})

@login_required
def relatorio_mensal(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    formato = request.GET.get('formato') # Vai receber 'pdf' ou 'csv'

    if not mes or not ano:
        messages.error(request, 'Selecione o mês e o ano para gerar o relatório.')
        return redirect('dashboard_pedagogico')
        
    mes = int(mes)
    ano = int(ano)

    # Busca todas as monitorias ativas para cruzar com as entregas
    monitorias = Monitoria.objects.all()
    
    entregas_relatorio = []
    total_submissoes = 0
    
    for monitoria in monitorias:
        entrega = EntregaMensal.objects.filter(
            monitoria=monitoria,
            mes_referencia__year=ano,
            mes_referencia__month=mes
        ).first()
        
        nome_monitor = monitoria.monitor.get_full_name() or monitoria.monitor.username
        
        if entrega:
            total_submissoes += 1
            entregas_relatorio.append({
                'monitor_nome': nome_monitor,
                'curso': monitoria.curso,
                'disciplina': monitoria.disciplina,
                'professor_nome': monitoria.professor.get_full_name(),
                'alunos_atendidos': entrega.total_alunos_presentes,
                'status': entrega.status,
                'status_display': entrega.get_status_display()
            })
        else:
            # Caso o monitor NÃO tenha enviado nada no mês
            entregas_relatorio.append({
                'monitor_nome': nome_monitor,
                'curso': monitoria.curso,
                'disciplina': monitoria.disciplina,
                'professor_nome': monitoria.professor.get_full_name(),
                'alunos_atendidos': '-',
                'status': 'N',
                'status_display': 'Não Enviado'
            })
            
    # Ordena alfabeticamente pelo nome do monitor
    entregas_relatorio = sorted(entregas_relatorio, key=lambda x: x['monitor_nome'])

    # OPÇÃO 1: GERAR PLANILHA EXCEL (CSV)
    if formato == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="relatorio_sigma_{mes}_{ano}.csv"'
        
        # Adiciona o BOM do UTF-8 para o Excel ler os acentos brasileiros
        response.write(u'\ufeff'.encode('utf8'))
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Monitor', 'Curso', 'Disciplina', 'Orientador', 'Alunos Atendidos', 'Status da Documentação'])

        for e in entregas_relatorio:
            writer.writerow([
                e['monitor_nome'],
                e['curso'],
                e['disciplina'],
                e['professor_nome'],
                e['alunos_atendidos'],
                e['status_display']
            ])
        return response

    # OPÇÃO 2: GERAR PDF VIA NAVEGADOR
    meses_nomes = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    contexto = {
        'entregas': entregas_relatorio,
        'mes_nome': meses_nomes.get(mes, str(mes)),
        'ano': ano,
        'total_entregas': total_submissoes, # Conta apenas quem realmente enviou
        'data_hoje': date.today()
    }
    return render(request, 'sigma/pedagogico/relatorio_pdf.html', contexto)

# ==========================================
# AUDITORIA DE DOCUMENTOS (PEDAGÓGICO)
# ==========================================
@login_required
def auditoria_documentos(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    # Busca apenas os documentos que o professor já aprovou (status = 'A')
    documentos_pendentes = EntregaMensal.objects.filter(status='A').order_by('mes_referencia')
    
    # Busca os últimos 10 documentos já auditados para histórico
    documentos_auditados = EntregaMensal.objects.filter(status='F').order_by('-mes_referencia')[:10]

    return render(request, 'sigma/pedagogico/auditoria.html', {
        'documentos_pendentes': documentos_pendentes,
        'documentos_auditados': documentos_auditados
    })

@login_required
def processar_auditoria(request, entrega_id, acao):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    entrega = get_object_or_404(EntregaMensal, id=entrega_id)
    aluno = entrega.monitoria.monitor
    mes_ano = entrega.mes_referencia.strftime('%m/%Y')

    if acao == 'aprovar':
        entrega.status = 'F' # Muda para Auditado e Arquivado
        entrega.save()
        
        # --- E-MAIL DE APROVAÇÃO (AUDITORIA) ---
        assunto = f'SIGMA - Sucesso: Documentação de {mes_ano} Aprovada!'
        mensagem = (
            f"Olá {aluno.first_name},\n\n"
            f"Os seus relatórios referentes ao mês {mes_ano} "
            f"foram verificados e APROVADOS com sucesso pelo Setor Pedagógico.\n\n"
            f"Os seus documentos foram arquivados no sistema e o fluxo de {mes_ano} está concluído.\n\n "
            f"Atenciosamente,\n"
            f"Setor Pedagógico - IFMG Campus São João Evangelista"
        )
        try:
            send_mail(subject=assunto, message=mensagem, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[aluno.email], fail_silently=False)
            messages.success(request, f'Documentação auditada e arquivada! E-mail de confirmação enviado para {aluno.first_name}.')
        except Exception as e:
            messages.warning(request, f'Documentação arquivada, mas falhou o envio do e-mail de confirmação. Erro: {e}')
        
    elif acao == 'recusar' and request.method == 'POST':
        motivo = request.POST.get('motivo_recusa')
        entrega.status = 'R' # Devolve para o status "Recusado"
        entrega.feedback_professor = f"[REPROVADO PELA AUDITORIA PEDAGÓGICA]: {motivo}"
        entrega.save()
        
        # --- E-MAIL DE RECUSA (AUDITORIA) ---
        assunto = f'SIGMA - URGENTE: Documentação de {mes_ano} Recusada pela Auditoria'
        mensagem = (
            f"Olá {aluno.first_name},\n\n"
            f"A sua documentação de monitoria de {mes_ano} foi devolvida durante a AUDITORIA FINAL do Setor Pedagógico.\n\n"
            f"Motivo da recusa: {motivo}\n\n"
            f"Aceda ao SIGMA imediatamente para substituir os ficheiros e enviar novamente para avaliação.\n\n"
            f"Atenciosamente,\n"
            f"Setor Pedagógico - IFMG Campus São João Evangelista"
        )
        try:
            send_mail(subject=assunto, message=mensagem, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[aluno.email], fail_silently=False)
            messages.success(request, f'Documento devolvido ao monitor e e-mail de alerta enviado para {aluno.first_name}.')
        except Exception as e:
            messages.warning(request, f'Documento devolvido, mas houve falha ao enviar o e-mail de alerta. Erro: {e}')

    # --- NOVA AÇÃO: REVERTER ARQUIVAMENTO ---
    elif acao == 'reverter':
        entrega.status = 'A' # Devolve para "Aguardando Auditoria"
        entrega.save()
        # Não enviamos e-mail aqui para não assustar o aluno à toa com uma ação administrativa interna
        messages.success(request, f'Arquivamento revertido! O documento de {aluno.first_name} voltou para a aba de Análise Pendente.')

    return redirect('auditoria_documentos')

@login_required
@require_POST # Esta é a nova linha de proteção
def excluir_prazo(request, prazo_id):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    prazo = get_object_or_404(PrazoExcecao, id=prazo_id)
    prazo.delete()
    
    messages.success(request, 'Exceção removida! O sistema voltou a calcular o 5º dia útil automaticamente para este mês.')
    return redirect('gerenciar_prazos')

@login_required
@require_POST
def notificar_atrasados(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    tipo_notificacao = request.POST.get('tipo_notificacao', 'aviso')
    
    hoje = date.today()
    
    # 1. Define qual é o MÊS ALVO dependendo do botão clicado
    if tipo_notificacao == 'aviso':
        # Preventivo: lembra o aluno sobre o documento do MÊS ATUAL
        mes_alvo = hoje.month
        ano_alvo = hoje.year
    else:
        # Atrasado: cobra o aluno sobre o documento do MÊS PASSADO
        if hoje.month == 1:
            mes_alvo = 12
            ano_alvo = hoje.year - 1
        else:
            mes_alvo = hoje.month - 1
            ano_alvo = hoje.year

    # 2. Descobre qual é o primeiro e o último dia do mês alvo
    ultimo_dia_mes = calendar.monthrange(ano_alvo, mes_alvo)[1]
    inicio_mes_alvo = date(ano_alvo, mes_alvo, 1)
    fim_mes_alvo = date(ano_alvo, mes_alvo, ultimo_dia_mes)

    # 3. FILTRO CRUCIAL: Só busca monitorias ativas NO MÊS ALVO
    monitorias_ativas = Monitoria.objects.filter(
        data_inicio__lte=fim_mes_alvo,
        data_fim__gte=inicio_mes_alvo
    )
    
    notificados = 0
    alunos_notificados = set()

    for monitoria in monitorias_ativas:
        # Verifica se o monitor entregou para O MÊS ALVO
        entregou = EntregaMensal.objects.filter(
            monitoria=monitoria,
            mes_referencia__month=mes_alvo,
            mes_referencia__year=ano_alvo
        ).exists()

        if not entregou:
            aluno = monitoria.monitor
            
            # Evita enviar 2 emails se o aluno tiver 2 disciplinas pendentes
            if aluno.id in alunos_notificados:
                continue
            
            if tipo_notificacao == 'atraso':
                assunto = f'SIGMA - URGENTE: Documentação de {mes_alvo:02d}/{ano_alvo} em Atraso'
                mensagem = (
                    f"Olá {aluno.first_name},\n\n"
                    f"Atenção! Verificamos no SIGMA que o prazo limite (5º dia útil deste mês) para a entrega da sua documentação "
                    f"de monitoria referente ao mês {mes_alvo:02d}/{ano_alvo} JÁ EXPIROU.\n\n"
                    f"O não envio imediato da folha de frequência e relatórios comprometerá o pagamento "
                    f"da sua bolsa.\n\n"
                    f"Aceda ao SIGMA agora mesmo e regularize a sua situação de forma urgente.\n\n"
                    f"Atenciosamente,\n"
                    f"Setor Pedagógico - IFMG Campus São João Evangelista"
                )
            else: # 'aviso'
                assunto = f'SIGMA - Lembrete Preventivo: Documentação de {mes_alvo:02d}/{ano_alvo}'
                mensagem = (
                    f"Olá {aluno.first_name},\n\n"
                    f"Este é um lembrete preventivo do sistema SIGMA referente ao envio da sua documentação "
                    f"de monitoria do mês {mes_alvo:02d}/{ano_alvo}.\n\n"
                    f"Lembre-se de enviar a sua folha de frequência e anexos até ao 5º dia útil do PRÓXIMO mês para "
                    f"garantir o processamento correto do pagamento da sua bolsa.\n\n"
                    f"Caso já tenha efetuado o envio, por favor ignore esta mensagem.\n\n"
                    f"Atenciosamente,\n"
                    f"Setor Pedagógico - IFMG Campus São João Evangelista"
                )

            try:
                send_mail(assunto, mensagem, settings.DEFAULT_FROM_EMAIL, [aluno.email], fail_silently=True)
                alunos_notificados.add(aluno.id)
                notificados += 1
            except:
                pass

    # 4. Mensagem de feedback dinâmico
    if notificados > 0:
        tipo_texto = "de cobrança (atraso)" if tipo_notificacao == 'atraso' else "preventivos"
        messages.success(request, f'Sucesso! {notificados} monitores receberam e-mails {tipo_texto} referentes ao mês {mes_alvo:02d}/{ano_alvo}.')
    else:
        messages.info(request, f'Nenhum monitor está pendente para o mês de {mes_alvo:02d}/{ano_alvo}.')

    return redirect('dashboard_pedagogico')

@login_required
@require_POST
def excluir_monitoria(request, monitoria_id):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')
        
    monitoria = get_object_or_404(Monitoria, id=monitoria_id)
    disciplina = monitoria.disciplina
    aluno = monitoria.monitor.first_name
    monitoria.delete()
    
    messages.success(request, f'Vínculo de {aluno} na disciplina {disciplina} foi cancelado/excluído com sucesso.')
    return redirect('criar_monitoria')

@login_required
def editar_monitoria(request, monitoria_id):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')
        
    monitoria = get_object_or_404(Monitoria, id=monitoria_id)
    
    if request.method == 'POST':
        # Instancia o formulário com os novos dados submetidos E a instância existente
        form = MonitoriaForm(request.POST, instance=monitoria)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Vínculo de {monitoria.monitor.first_name} atualizado com sucesso!')
            return redirect('criar_monitoria') # Volta para a tabela
        else:
            # 1. Verifica se existe aquele erro geral (ex: Conflito de Datas)
            if form.non_field_errors():
                # Pega na primeira mensagem de erro geral e envia para o balão de alerta
                erro_exato = form.non_field_errors()[0]
                messages.error(request, erro_exato)
            else:
                # 2. Se não houver erro geral, foi algum campo em branco ou data invertida
                messages.error(request, 'Não foi possível salvar. Verifique os campos assinalados a vermelho.')
    else:
        # Primeiro acesso: carrega os dados atuais do banco
        form = MonitoriaForm(instance=monitoria)
        
    contexto = {
        'form': form,
        'monitoria': monitoria,
        'editando': True
    }
    
    # A página é renderizada. Se foi POST e falhou, o `form` aqui dentro tem a lista de `non_field_errors`.
    return render(request, 'sigma/pedagogico/criar_monitoria.html', contexto)