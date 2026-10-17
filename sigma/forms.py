from django import forms
from .models import Usuario, Monitoria, PrazoExcecao, AtendimentoDiario, EntregaMensal
from datetime import date
from django.core.exceptions import ValidationError
from django.utils import timezone

# ==========================================
# FORMULÁRIO DE CRIAÇÃO DE USUÁRIOS
# ==========================================
class UsuarioCreationForm(forms.ModelForm):
    class Meta:
        model = Usuario
        # Agora o Django respeitará estritamente esta lista (sem campos de senha injetados):
        fields = ('username', 'first_name', 'last_name', 'email', 'tipo_usuario', 'cpf', 'telefone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['tipo_usuario'].widget.attrs['class'] = 'form-select'


# ==========================================
# FORMULÁRIO DE VÍNCULO (MONITORIA)
# ==========================================
class MonitoriaForm(forms.ModelForm):
    class Meta:
        model = Monitoria
        fields = '__all__'
        
        widgets = {
            # Adicionado o format='%Y-%m-%d' para o navegador entender a data
            'data_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtra as listas para não misturar perfis
        self.fields['monitor'].queryset = Usuario.objects.filter(tipo_usuario='M').order_by('first_name')
        self.fields['professor'].queryset = Usuario.objects.filter(tipo_usuario='P').order_by('first_name')
        
        # Aplica o visual do Bootstrap
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            
        self.fields['monitor'].widget.attrs['class'] = 'form-select'
        self.fields['professor'].widget.attrs['class'] = 'form-select'
        
        if 'tipo_bolsa' in self.fields:
            self.fields['tipo_bolsa'].widget.attrs['class'] = 'form-select'

        # NOVO: Torna os campos bancários NÃO-obrigatórios no HTML
        # Isto permite que o nosso backend decida se deve cobrar ou não
        campos_bancarios = ['conta', 'agencia', 'banco', 'chave_pix']
        for campo in campos_bancarios:
            if campo in self.fields:
                self.fields[campo].required = False

    # TRAVAS DE SEGURANÇA E REGRA DE NEGÓCIO CONDICIONAL
    def clean(self):
        cleaned_data = super().clean()
        
        monitor = cleaned_data.get('monitor')
        professor = cleaned_data.get('professor')
        disciplina = cleaned_data.get('disciplina')
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        # Campos condicionais
        tipo_bolsa = cleaned_data.get('tipo_bolsa')
        conta = cleaned_data.get('conta')

        # ---------------------------------------------------------
        # NOVA REGRA: Validação Condicional de Conta Bancária
        # ---------------------------------------------------------
        # Se a bolsa for Remunerada (ajuste o 'R' para o valor exato que usa no seu model)
        if tipo_bolsa in ['Remunerada', 'R', 'remunerada'] and not conta:
            # O add_error coloca a mensagem vermelha EXATAMENTE por baixo do campo da conta
            self.add_error(
                'conta', 
                "⚠️ Aviso: Como a monitoria é remunerada, é obrigatório preencher os dados bancários para o pagamento."
            )
            
        # Limpeza inteligente: se a pessoa marcou "Voluntária" mas preencheu a conta por engano, apagamos
        elif tipo_bolsa in ['Voluntária', 'V', 'voluntaria'] and conta:
            cleaned_data['conta'] = ''

        # ---------------------------------------------------------
        # Regras de Datas
        # ---------------------------------------------------------
        if data_inicio and data_fim:
            hoje = timezone.now().date()

            if data_fim <= data_inicio:
                self.add_error('data_fim', "A data de fim da monitoria deve ser posterior à data de início.")

            if data_fim < hoje:
                self.add_error('data_fim', "Não é possível registrar um vínculo cuja vigência já terminou no passado.")

        # ---------------------------------------------------------
        # REGRA: Prevenção de Sobreposição de Datas (Conflito)
        # ---------------------------------------------------------
        if monitor and disciplina and data_inicio and data_fim:
            
            # A matemática da sobreposição de datas:
            # Duas datas cruzam-se se: o Início de A <= Fim de B, E o Fim de A >= Início de B
            vinculos_conflitantes = Monitoria.objects.filter(
                monitor=monitor,
                disciplina__iexact=disciplina,
                data_inicio__lte=data_fim, # Começou antes do nosso término
                data_fim__gte=data_inicio  # Terminou depois do nosso início
            )
            
            # Se for uma edição, excluímos o próprio vínculo da verificação
            if self.instance and self.instance.pk:
                vinculos_conflitantes = vinculos_conflitantes.exclude(pk=self.instance.pk)

            if vinculos_conflitantes.exists():
                mensagem_erro = (
                    f"CONFLITO DE DATAS: O estudante {monitor.first_name} já possui uma monitoria "
                    f"na disciplina de '{disciplina}' que entra em conflito com este período de datas. "
                    "Verifique se está a inserir as datas corretas para o novo semestre."
                )
                raise ValidationError(mensagem_erro)

        return cleaned_data


# ==========================================
# FORMULÁRIOS DO MONITOR
# ==========================================
class AtendimentoDiarioForm(forms.ModelForm):
    class Meta:
        model = AtendimentoDiario
        fields = ['data', 'hora_inicio', 'hora_fim', 'atividades_desenvolvidas', 'qtd_estudantes_presentes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'atividades_desenvolvidas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'qtd_estudantes_presentes': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class EntregaMensalForm(forms.ModelForm):
    mes_referencia = forms.DateField(
        widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month', 'class': 'form-control'}),
        input_formats=['%Y-%m']
    )

    class Meta:
        model = EntregaMensal
        fields = ['mes_referencia', 'total_alunos_presentes', 'arquivo_anexo_ii', 'arquivo_anexo_iii', 'arquivo_anexo_iv']
        widgets = {
            'total_alunos_presentes': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'arquivo_anexo_ii': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf,image/*'}),
            'arquivo_anexo_iii': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf,image/*'}),
            'arquivo_anexo_iv': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf,image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['arquivo_anexo_ii'].required = True
        self.fields['arquivo_anexo_iii'].required = True
        self.fields['arquivo_anexo_iv'].required = True


# ==========================================
# FORMULÁRIOS DE ADMINISTRAÇÃO E PRAZOS
# ==========================================
class PrazoExcecaoForm(forms.ModelForm):
    nova_data_limite = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = PrazoExcecao
        fields = ['mes_referencia', 'ano_referencia', 'nova_data_limite', 'motivo']
        widgets = {
            'mes_referencia': forms.Select(attrs={'class': 'form-select'}),
            'ano_referencia': forms.NumberInput(attrs={'class': 'form-control', 'min': '2024'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_nova_data_limite(self):
        data = self.cleaned_data.get('nova_data_limite')
        if data and data < date.today():
            raise ValidationError("Você não pode definir um prazo de tolerância com uma data que já passou.")
        return data
    

class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class UsuarioAdminUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'tipo_usuario']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tipo_usuario': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'username': 'Matrícula / SIAPE (Login)',
            'tipo_usuario': 'Perfil de Acesso'
        }