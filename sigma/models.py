from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. MODELO DE USUÁRIO (Base para todos os acessos)
class Usuario(AbstractUser):
    TIPO_CHOICES = (
        ('M', 'Monitor'),
        ('P', 'Professor Orientador'),
        ('A', 'Setor Pedagógico'),
    )
    tipo_usuario = models.CharField(max_length=1, choices=TIPO_CHOICES)
    cpf = models.CharField(max_length=14, blank=True, null=True) #[cite: 3]
    telefone = models.CharField(max_length=15, blank=True, null=True) # Celular/Whatsapp[cite: 3]
    
    def __str__(self):
        return self.get_full_name() or self.username

# 2. VÍNCULO DE MONITORIA (Referente ao Anexo I - Termo de Compromisso)[cite: 3]
class Monitoria(models.Model):
    edital = models.CharField(max_length=50) # Ex: 522/2026[cite: 3]
    monitor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='monitorias_aluno') #[cite: 3]
    professor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='monitorias_orientador') #[cite: 3]
    curso = models.CharField(max_length=100) # Ex: Sistemas de Informação[cite: 3]
    disciplina = models.CharField(max_length=100) # Ex: Introdução a Programação[cite: 2]
    tipo_bolsa = models.CharField(max_length=20, choices=(('R', 'Remunerada'), ('V', 'Voluntária'))) #[cite: 3]
    valor_bolsa = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True) # Ex: R$ 385,00[cite: 3]
    data_inicio = models.DateField() #[cite: 3]
    data_fim = models.DateField() #[cite: 3]
    
    # Dados Bancários do Monitor[cite: 3]
    banco = models.CharField(max_length=50, blank=True, null=True) #[cite: 3]
    agencia = models.CharField(max_length=10, blank=True, null=True) #[cite: 3]
    conta = models.CharField(max_length=20, blank=True, null=True) #[cite: 3]

# 3. PLANO DE TRABALHO (Referente ao Anexo III - Gerado Automaticamente)
class PlanoTrabalhoMensal(models.Model):
    monitoria = models.ForeignKey(Monitoria, on_delete=models.CASCADE) #
    mes_referencia = models.DateField() # Representa o mês/ano
    
    # Preenchimento em conjunto
    atividades_propostas = models.TextField(help_text="Preenchido pelo Professor") #
    atividades_realizadas = models.TextField(help_text="Preenchido pelo Monitor") #[cite: 1]

# 4. REGISTRO DIÁRIO DE ATENDIMENTO (Alimenta o Anexo IV)[cite: 1]
class AtendimentoDiario(models.Model):
    monitoria = models.ForeignKey(Monitoria, on_delete=models.CASCADE) #[cite: 1]
    data = models.DateField() #[cite: 1]
    hora_inicio = models.TimeField() #[cite: 1]
    hora_fim = models.TimeField() #[cite: 1]
    atividades_desenvolvidas = models.TextField() #[cite: 1]
    qtd_estudantes_presentes = models.IntegerField(help_text="Monitor declara a quantidade de presentes") 

# 5. CONSOLIDAÇÃO MENSAL (Envio dos 3 Anexos)
class EntregaMensal(models.Model):
    STATUS_CHOICES = (
        ('P', 'Pendente'),
        ('A', 'Aprovado pelo Professor'),
        ('R', 'Recusado (Necessita Ajuste)'),
        ('F', 'Auditado e Arquivado'),
    )
    monitoria = models.ForeignKey(Monitoria, on_delete=models.CASCADE)
    mes_referencia = models.DateField()
    
    data_envio = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    # Campo para o relatório e dashboard
    total_alunos_presentes = models.PositiveIntegerField(
        default=0, 
        help_text="Total de estudantes frequentes no presente mês"
    )
    
    # Ficheiros dos 3 anexos
    arquivo_anexo_ii = models.FileField(upload_to='anexos_frequencia/anexo_ii/', help_text="Registro de Frequência Mensal assinado")
    arquivo_anexo_iii = models.FileField(upload_to='anexos_frequencia/anexo_iii/', blank=True, null=True, help_text="Plano de Trabalho Mensal")
    arquivo_anexo_iv = models.FileField(upload_to='anexos_frequencia/anexo_iv/', blank=True, null=True, help_text="Declaração Mensal")
    
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    feedback_professor = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Entrega de {self.mes_referencia.strftime('%m/%Y')} - {self.monitoria.monitor.get_full_name()}"

# 6. AVALIAÇÃO SEMESTRAL DO MONITOR (Referente ao Anexo V)[cite: 2]
class AvaliacaoSemestral(models.Model):
    monitoria = models.ForeignKey(Monitoria, on_delete=models.CASCADE) #[cite: 2]
    cumpriu_plano = models.BooleanField(default=True) #[cite: 2]
    motivo_nao_cumprimento = models.TextField(blank=True, null=True) #[cite: 2]
    
    # Notas: E=Excelente, B=Bom, R=Regular, F=Fraco[cite: 2]
    nota_responsabilidade = models.CharField(max_length=1) #[cite: 2]
    nota_planejamento = models.CharField(max_length=1) #[cite: 2]
    nota_relacionamento = models.CharField(max_length=1) #[cite: 2]
    nota_conhecimento = models.CharField(max_length=1) #[cite: 2]
    nota_criatividade = models.CharField(max_length=1) #[cite: 2]
    nota_iniciativa = models.CharField(max_length=1) #[cite: 2]
    nota_autodesenvolvimento = models.CharField(max_length=1) #[cite: 2]
    nota_autocritica = models.CharField(max_length=1) #[cite: 2]
    
    parecer = models.TextField() #[cite: 2]
    avaliacao_final = models.CharField(max_length=1) #[cite: 2]
    recomenda_novamente = models.BooleanField() #[cite: 2]

# 7. AVALIAÇÃO DO PROGRAMA (Referente ao Anexo VI)[cite: 3]
class AvaliacaoPrograma(models.Model):
    monitoria = models.ForeignKey(Monitoria, on_delete=models.CASCADE) #[cite: 3]
    qtd_atendidos = models.IntegerField() #[cite: 3]
    qtd_matriculados = models.IntegerField() #[cite: 3]
    qtd_aprovados = models.IntegerField() #[cite: 3]
    qtd_desistentes = models.IntegerField() #[cite: 3]
    pontos_positivos = models.TextField() #[cite: 3]
    pontos_negativos = models.TextField() #[cite: 3]
    sugestoes = models.TextField() #[cite: 3]
    parecer_colegiado = models.TextField() #[cite: 3]


class Prazo(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título do Prazo (Ex: Relatório de Maio)")
    data_limite = models.DateField(verbose_name="Data Limite")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição/Aviso")
    ativo = models.BooleanField(default=True, verbose_name="Prazo Ativo?")

    def __str__(self):
        return f"{self.titulo} - {self.data_limite.strftime('%d/%m/%Y')}"