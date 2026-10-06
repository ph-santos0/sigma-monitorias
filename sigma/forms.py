from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Monitoria,Prazo

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
# FORMULÁRIO DE PRAZOS (PEDAGÓGICO)
# ==========================================
class PrazoForm(forms.ModelForm):
    class Meta:
        model = Prazo
        fields = '__all__'
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Entrega de Frequência - Junho'}),
            'data_limite': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }