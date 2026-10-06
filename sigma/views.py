from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Usuario, Monitoria, EntregaMensal,Prazo
from .forms import UsuarioCreationForm,MonitoriaForm,PrazoForm


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


# =====================================================================
# 2. SETOR DO MONITOR (ESTUDANTE)
# =====================================================================

@login_required
def dashboard_monitor(request):
    # Trava de segurança opcional
    if request.user.tipo_usuario != 'M':
        return redirecionar_dashboard(request.user)
        
    return render(request, 'sigma/monitor/dashboard_monitor.html')


# =====================================================================
# 3. SETOR DO PROFESSOR ORIENTADOR
# =====================================================================

@login_required
def dashboard_professor(request):
    if request.user.tipo_usuario != 'P':
        return redirecionar_dashboard(request.user)

    # 1. Busca todas as monitorias do professor
    monitorias = Monitoria.objects.filter(professor=request.user)
    
    # 2. Busca apenas as entregas com status 'P' (Pendente)
    entregas_pendentes = EntregaMensal.objects.filter(monitoria__in=monitorias, status='P')
    
    contexto = {
        'monitorias': monitorias,
        'entregas_pendentes': entregas_pendentes,
        'qtd_pendentes': entregas_pendentes.count(),
    }
    return render(request, 'sigma/professor/dashboard_professor.html', contexto)


@login_required
def avaliar_entrega(request, entrega_id, acao):
    # Garante que o professor só pode avaliar documentos dos próprios alunos
    entrega = get_object_or_404(EntregaMensal, id=entrega_id, monitoria__professor=request.user)
    
    if acao == 'aprovar':
        entrega.status = 'A'
        entrega.feedback_professor = ''
        entrega.save()
        messages.success(request, f'Documento de {entrega.monitoria.monitor.get_full_name()} aprovado!')
        
    elif acao == 'recusar' and request.method == 'POST':
        motivo = request.POST.get('motivo_recusa')
        entrega.status = 'R'
        entrega.feedback_professor = motivo
        entrega.save()
        messages.error(request, f'Documento devolvido para {entrega.monitoria.monitor.get_full_name()} para ajustes.')
        
    # Redireciona de volta para a página anterior (dashboard ou lista de avaliações)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_professor'))


@login_required
def historico_monitor(request, monitoria_id):
    # Busca a monitoria, garantindo que o aluno pertence ao professor logado
    monitoria = get_object_or_404(Monitoria, id=monitoria_id, professor=request.user)
    
    # Busca o histórico completo, ordenado da mais recente para a mais antiga
    entregas = EntregaMensal.objects.filter(monitoria=monitoria).order_by('-mes_referencia')
    
    contexto = {
        'monitoria': monitoria,
        'entregas': entregas
    }
    return render(request, 'sigma/professor/historico_monitor.html', contexto)


@login_required
def avaliacoes_pendentes(request):
    if request.user.tipo_usuario != 'P':
        return redirecionar_dashboard(request.user)
    
    entregas = EntregaMensal.objects.filter(monitoria__professor=request.user, status='P')
    return render(request, 'sigma/professor/avaliacoes_pendentes.html', {'entregas_pendentes': entregas})


@login_required
def meus_monitores(request):
    if request.user.tipo_usuario != 'P':
        return redirecionar_dashboard(request.user)
        
    monitorias = Monitoria.objects.filter(professor=request.user)
    return render(request, 'sigma/professor/meus_monitores.html', {'monitorias': monitorias})


# =====================================================================
# 4. SETOR PEDAGÓGICO (ADMINISTRAÇÃO)
# =====================================================================

@login_required
def dashboard_pedagogico(request):
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirecionar_dashboard(request.user)

    # Conta quantos usuários existem de cada tipo no banco de dados
    total_monitores = Usuario.objects.filter(tipo_usuario='M').count()
    total_professores = Usuario.objects.filter(tipo_usuario='P').count()
    
    contexto = {
        'total_monitores': total_monitores,
        'total_professores': total_professores,
    }
    return render(request, 'sigma/pedagogico/dashboard_pedagogico.html', contexto)


@login_required
def listar_usuarios(request):
    # Trava de segurança
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        messages.error(request, 'Acesso restrito ao Setor Pedagógico.')
        return redirect('login')
    
    # Busca todos os usuários do banco, ordenados por nome
    usuarios = Usuario.objects.all().order_by('first_name')
    return render(request, 'sigma/pedagogico/listar_usuarios.html', {'usuarios': usuarios})


@login_required
def criar_usuario(request):
    # Trava de segurança
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Novo usuário cadastrado com sucesso!')
            return redirect('listar_usuarios')
    else:
        form = UsuarioCreationForm()
        
    return render(request, 'sigma/pedagogico/criar_usuario.html', {'form': form})

@login_required
def criar_monitoria(request):
    if request.method == 'POST':
        form = MonitoriaForm(request.POST)
        if form.is_valid():
            # Só tenta gravar se todos os campos (incluindo as datas) estiverem preenchidos
            form.save()
            messages.success(request, 'Vínculo criado com sucesso!')
            return redirect('dashboard_pedagogico')
        else:
            # Se faltar algo, devolve um erro visual no ecrã em vez de rebentar a base de dados
            messages.error(request, 'Erro de validação. Verifique se preencheu todos os campos, incluindo as datas.')
    else:
        form = MonitoriaForm()
        
    return render(request, 'sigma/pedagogico/criar_monitoria.html', {'form': form})

def gerenciar_prazos(request):
    # Proteção: Apenas setor pedagógico ('A' = Admin/Pedagógico) pode acessar
    if request.user.tipo_usuario != 'A':
        return redirect('login')

    if request.method == 'POST':
        form = PrazoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Novo prazo cadastrado com sucesso!')
            return redirect('gerenciar_prazos')
        else:
            messages.error(request, 'Erro ao criar prazo. Verifique os campos.')
    else:
        form = PrazoForm()

    # Busca todos os prazos cadastrados, ordenando pelos mais próximos
    prazos = Prazo.objects.all().order_by('data_limite')
    
    return render(request, 'sigma/pedagogico/prazos.html', {'form': form, 'prazos': prazos})

# ==========================================
# AUDITORIA DE DOCUMENTOS (PEDAGÓGICO)
# ==========================================
def auditoria_documentos(request):
    if request.user.tipo_usuario != 'A':
        return redirect('login')

    # Busca apenas os documentos que o professor já aprovou (status = 'A')
    documentos_pendentes = EntregaMensal.objects.filter(status='A').order_by('mes_referencia')
    
    # Busca os últimos 5 documentos já auditados para histórico
    documentos_auditados = EntregaMensal.objects.filter(status='F').order_by('-mes_referencia')[:5]

    return render(request, 'sigma/pedagogico/auditoria.html', {
        'documentos_pendentes': documentos_pendentes,
        'documentos_auditados': documentos_auditados
    })

def processar_auditoria(request, entrega_id, acao):
    if request.user.tipo_usuario != 'A':
        return redirect('login')

    entrega = get_object_or_404(EntregaMensal, id=entrega_id)

    if acao == 'aprovar':
        entrega.status = 'F' # Muda para Auditado e Arquivado
        entrega.save()
        messages.success(request, 'Documento auditado e arquivado com sucesso!')
        
    elif acao == 'recusar' and request.method == 'POST':
        motivo = request.POST.get('motivo_recusa')
        entrega.status = 'R' # Devolve para o status "Recusado" para o aluno corrigir
        entrega.feedback_professor = f"[REPROVADO PELA AUDITORIA PEDAGÓGICA]: {motivo}"
        entrega.save()
        messages.error(request, 'Documento recusado e devolvido ao monitor.')

    return redirect('auditoria_documentos')