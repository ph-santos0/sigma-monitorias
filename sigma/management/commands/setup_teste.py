from django.core.management.base import BaseCommand
from sigma.models import Usuario

class Command(BaseCommand):
    help = 'Limpa o banco e cria usuários de teste, incluindo o superusuário.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Limpando todo o banco de usuários...')
        # Apaga TODOS os usuários para começar do zero absoluto
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
        Usuario.objects.create_user(
            username='professor',
            password='123',
            first_name='Carlos',
            last_name='Orientador',
            email='professor@ifmg.edu.br',
            tipo_usuario='P'
        )

        # 3. Usuário Monitor
        Usuario.objects.create_user(
            username='monitor',
            password='123',
            first_name='Pedro',
            last_name='Estudante',
            email='monitor@ifmg.edu.br',
            tipo_usuario='M'
        )

        # Feedback no terminal
        self.stdout.write(self.style.SUCCESS('\n--- AMBIENTE DE TESTES CONFIGURADO COM SUCESSO ---'))
        self.stdout.write(self.style.WARNING('Superusuário     -> Usuário: admin      | Senha: 123'))
        self.stdout.write(self.style.WARNING('Setor Pedagógico -> Usuário: pedagogico | Senha: 123'))
        self.stdout.write(self.style.WARNING('Professor        -> Usuário: professor  | Senha: 123'))
        self.stdout.write(self.style.WARNING('Monitor          -> Usuário: monitor    | Senha: 123'))
        self.stdout.write('\n')