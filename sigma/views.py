from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Usuario, Monitoria, EntregaMensal
from .forms import UsuarioCreationForm,MonitoriaForm

from .forms import UsuarioCreationForm, MonitoriaForm, EntregaMensalForm

from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Monitoria, EntregaMensal
from .forms import EntregaMensalForm


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
            prazo = date(ano_seg, mes_seg, 10)
            
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
        prazo_limite_mes_passado = date(hoje.year, hoje.month, 10)
        
        entrega_mes_passado = entregas.filter(mes_referencia__year=ano_passado, mes_referencia__month=mes_passado).first()
        
        if not entrega_mes_passado and hoje <= prazo_limite_mes_passado:
            resumo = {'status': f'Aguardando Envio ({mes_passado:02d}/{ano_passado})', 'cor': 'text-warning', 'prazo': prazo_limite_mes_passado.strftime('%d/%m/%Y')}
        elif entrega_mes_passado:
            if entrega_mes_passado.status == 'P':
                resumo = {'status': 'Aguardando Aprovação', 'cor': 'text-primary', 'prazo': 'Em análise'}
            elif entrega_mes_passado.status == 'R':
                resumo = {'status': 'Recusado (Ajuste Necessário)', 'cor': 'text-danger', 'prazo': 'Ajuste Imediato'}
            elif entrega_mes_passado.status == 'A':
                resumo = {'status': 'Tudo em dia!', 'cor': 'text-success', 'prazo': 'Documentos aprovados'}
        else:
            resumo = {'status': 'Em andamento', 'cor': 'text-secondary', 'prazo': '-'}

        # =================================================================
        # 3. TAGS NA TABELA E RECUSAS (Sempre no topo da lista)
        # =================================================================
        for entrega in entregas:
            mes_seg = entrega.mes_referencia.month + 1 if entrega.mes_referencia.month < 12 else 1
            ano_seg = entrega.mes_referencia.year if entrega.mes_referencia.month < 12 else entrega.mes_referencia.year + 1
            prazo_da_entrega = date(ano_seg, mes_seg, 10)
            
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
    
    if entrega.status == 'A':
        messages.error(request, 'Documentos já aprovados não podem ser editados.')
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
    if entrega.status == 'A':
        messages.error(request, 'Documentos já aprovados não podem ser excluídos.')
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
    # Apenas Setor Pedagógico pode acessar essa tela
    if request.user.tipo_usuario != 'A' and not request.user.is_superuser:
        messages.error(request, 'Acesso restrito ao Setor Pedagógico.')
        return redirect('login')

    if request.method == 'POST':
        form = MonitoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vínculo de monitoria criado com sucesso!')
            return redirect('dashboard_pedagogico')
    else:
        form = MonitoriaForm()
        
    return render(request, 'sigma/pedagogico/criar_monitoria.html', {'form': form})