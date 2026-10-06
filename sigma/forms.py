from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Monitoria
from .models import AtendimentoDiario, EntregaMensal

# ==========================================
# FORMULÁRIO DE CRIAÇÃO DE USUÁRIOS
# ==========================================
class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
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
        # A palavra mágica '__all__' força a exibição de absolutamente todos os campos do Model
        fields = '__all__'
        
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtra as listas suspensas
        self.fields['monitor'].queryset = Usuario.objects.filter(tipo_usuario='M').order_by('first_name')
        self.fields['professor'].queryset = Usuario.objects.filter(tipo_usuario='P').order_by('first_name')
        
        # Aplica o visual do Bootstrap a todos os campos gerados
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            
        self.fields['monitor'].widget.attrs['class'] = 'form-select'
        self.fields['professor'].widget.attrs['class'] = 'form-select'
        
        # Se o campo tipo_bolsa existir, aplica o visual
        if 'tipo_bolsa' in self.fields:
            self.fields['tipo_bolsa'].widget.attrs['class'] = 'form-select'
            
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
    # Sobrescrevemos o campo para aceitar e mostrar apenas Ano e Mês (ex: 2026-10)
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
        
        # OBRIGATORIEDADE DOS 3 ANEXOS:
        # Garante que o formulário não é submetido sem os três ficheiros anexados.
        # Ao editar, o Django reconhecerá que os ficheiros já existem e não bloqueará a ação.
        self.fields['arquivo_anexo_ii'].required = True
        self.fields['arquivo_anexo_iii'].required = True
        self.fields['arquivo_anexo_iv'].required = True