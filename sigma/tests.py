from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from sigma.models import Usuario, Monitoria
from sigma.forms import MonitoriaForm

class MonitoriaFormTest(TestCase):
    """
    Suíte de testes unitários para o formulário de criação de Vínculos de Monitoria.
    O objetivo é garantir que as regras de negócio e de integridade de dados 
    sejam respeitadas antes da persistência na base de dados.
    """

    def setUp(self):
        """
        Ambiente de Teste (Setup):
        Cria utilizadores fictícios (Monitor e Professor) e define as datas base 
        que serão utilizadas em todos os cenários de teste abaixo.
        """
        self.monitor = Usuario.objects.create_user(
            username='1111111', 
            first_name='João', 
            tipo_usuario='M',
            email='joao@aluno.ifmg.edu.br',
            password='senha_segura123'
        )
        
        self.professor = Usuario.objects.create_user(
            username='2222222', 
            first_name='Carlos', 
            tipo_usuario='P',
            email='carlos@ifmg.edu.br',
            password='senha_segura123'
        )
        
        # Datas relativas para evitar que os testes quebrem no futuro
        self.hoje = timezone.now().date()
        self.daqui_a_um_mes = self.hoje + timedelta(days=30)
        
    def test_form_valido_criacao_normal(self):
        """
        Cenário Ideal (Caminho Feliz): 
        Testa se o sistema aceita a criação de um vínculo com todos os dados preenchidos corretamente.
        """
        dados = {
            'monitor': self.monitor.id,
            'professor': self.professor.id,
            'disciplina': 'Algoritmos e Estrutura de Dados',
            'curso': 'Sistemas de Informação',
            'tipo_bolsa': 'V',
            'edital': 'Edital 01/2026', 
            'data_inicio': self.hoje.strftime('%Y-%m-%d'),
            'data_fim': self.daqui_a_um_mes.strftime('%Y-%m-%d'),
        }
        form = MonitoriaForm(data=dados)
        
        # O formulário deve ser válido (True)
        self.assertTrue(form.is_valid())

    def test_erro_datas_invertidas(self):
        """
        Regra de Negócio 1:
        Garante que o sistema bloqueia a criação de uma monitoria onde a data de fim 
        é cronologicamente anterior à data de início.
        """
        dados = {
            'monitor': self.monitor.id,
            'professor': self.professor.id,
            'disciplina': 'Banco de Dados',
            'curso': 'Sistemas de Informação',
            'tipo_bolsa': 'V',
            'edital': 'Edital 01/2026',
            'data_inicio': self.daqui_a_um_mes.strftime('%Y-%m-%d'), # Início no futuro
            'data_fim': self.hoje.strftime('%Y-%m-%d'),              # Fim hoje (Invertido)
        }
        form = MonitoriaForm(data=dados)
        
        # O formulário DEVE ser inválido
        self.assertFalse(form.is_valid())
        # O erro deve ser disparado especificamente no campo 'data_fim'
        self.assertIn('data_fim', form.errors)

    def test_erro_vinculo_no_passado(self):
        """
        Regra de Negócio 2:
        Garante que o setor pedagógico não consegue registrar um vínculo cuja 
        vigência já terminou (data_fim menor que a data atual).
        """
        ontem = self.hoje - timedelta(days=1)
        mes_passado = self.hoje - timedelta(days=30)
        
        dados = {
            'monitor': self.monitor.id,
            'professor': self.professor.id,
            'disciplina': 'Redes de Computadores',
            'curso': 'Sistemas de Informação',
            'tipo_bolsa': 'V',
            'edital': 'Edital 01/2026',
            'data_inicio': mes_passado.strftime('%Y-%m-%d'),
            'data_fim': ontem.strftime('%Y-%m-%d'), # Vínculo expirou ontem
        }
        form = MonitoriaForm(data=dados)
        
        self.assertFalse(form.is_valid())
        self.assertIn('data_fim', form.errors)

    def test_erro_conflito_de_datas(self):
        """
        Regra de Negócio 3 (Anti-Duplicação Inteligente):
        Testa o bloqueio de sobreposição de datas. O mesmo aluno não pode ser 
        alocado na mesma disciplina em períodos que se cruzam.
        """
        # 1. Simula a existência de um vínculo ativo na base de dados
        Monitoria.objects.create(
            monitor=self.monitor,
            professor=self.professor,
            disciplina='Engenharia de Software',
            curso='Sistemas de Informação',
            tipo_bolsa='V',
            edital='Edital 01/2026',
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=60) # Dura 2 meses
        )
        
        # 2. Tenta submeter um novo formulário para a mesma disciplina com datas sobrepostas
        dados_conflitantes = {
            'monitor': self.monitor.id,
            'professor': self.professor.id,
            'disciplina': 'Engenharia de Software',
            'curso': 'Sistemas de Informação',
            'tipo_bolsa': 'V',
            'edital': 'Edital 01/2026',
            'data_inicio': (self.hoje + timedelta(days=10)).strftime('%Y-%m-%d'), 
            'data_fim': (self.hoje + timedelta(days=40)).strftime('%Y-%m-%d'),
        }
        
        form = MonitoriaForm(data=dados_conflitantes)
        
        # O formulário DEVE falhar
        self.assertFalse(form.is_valid()) 
        
        # Verifica se o erro gerado é o nosso alerta customizado de conflito
        erros_gerais = form.non_field_errors()
        self.assertTrue(any('CONFLITO DE DATAS' in erro for erro in erros_gerais))