from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from sigma.models import Usuario, Monitoria

class Command(BaseCommand):
    help = 'Limpa o banco e cria usuários de teste e vínculos para avaliação do TCC.'

    def handle(self, *args, **kwargs):
        # 1. TRAVA DE SEGURANÇA: Impede apagar o banco se estiver em produção
        if not settings.DEBUG:
            raise CommandError("CUIDADO: O sistema não está em modo DEBUG. Comando abortado para evitar perda de dados reais.")

        self.stdout.write('Limpando todo o banco de dados (Usuários e Vínculos)...')
        # O CASCADE do Django encarrega-se de apagar Monitorias e Entregas ligadas a estes utilizadores
        Usuario.objects.all().delete()

        self.stdout.write('Criando novos usuários...')

        # 0. Superusuário (Admin Mestre)
        Usuario.objects.create_superuser(
            username='admin',
            password='123',
            email='admin@ifmg.edu.br',
            first_name='Admin',
            last_name='Sistema'
        )

        # 1. Usuário do Setor Pedagógico
        Usuario.objects.create_user(
            username='pedagogico',
            password='123',
            first_name='Ana',
            last_name='Pedagógica',
            email='pedagogico@ifmg.edu.br',
            tipo_usuario='A'
        )

        # 2. Usuário Professor
        professor = Usuario.objects.create_user(
            username='professor',
            password='123',
            first_name='Carlos',
            last_name='Orientador',
            email='professor@ifmg.edu.br',
            tipo_usuario='P'
        )

        # 3. Usuário Monitor
        monitor = Usuario.objects.create_user(
            username='monitor',
            password='123',
            first_name='Pedro',
            last_name='Estudante',
            email='monitor@ifmg.edu.br',
            tipo_usuario='M'
        )

        # 2. DADO DE TESTE: Cria um vínculo automático para o Dashboard não ficar vazio
        self.stdout.write('Criando vínculo de monitoria de teste...')
        Monitoria.objects.create(
            monitor=monitor,
            professor=professor,
            disciplina='Algoritmos e Estrutura de Dados',
            curso='Sistemas de Informação',
            tipo_bolsa='V',
            edital='Edital 01/2026',
            data_inicio=timezone.now().date(),
            data_fim=timezone.now().date() + timedelta(days=120)
        )

        # Feedback no terminal
        self.stdout.write(self.style.SUCCESS('\n--- AMBIENTE DE TESTES CONFIGURADO COM SUCESSO ---'))
        self.stdout.write(self.style.WARNING('Setor Pedagógico -> Usuário: pedagogico | Senha: 123'))
        self.stdout.write(self.style.WARNING('Professor        -> Usuário: professor  | Senha: 123'))
        self.stdout.write(self.style.WARNING('Monitor          -> Usuário: monitor    | Senha: 123'))
        self.stdout.write(self.style.WARNING('Superusuário     -> Usuário: admin      | Senha: 123'))
        self.stdout.write(self.style.SUCCESS('\n* Um vínculo de monitoria em AED foi gerado automaticamente!'))
        self.stdout.write('\n')