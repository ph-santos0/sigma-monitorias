
# SIGMA: Sistema Integrado de Gestão de Monitorias Acadêmicas

Projeto desenvolvido como Trabalho de Conclusão de Curso (TCC) do Bacharelado em Sistemas de Informação no IFMG - Campus São João Evangelista.

## Objetivo

Desenvolver uma plataforma web para gerenciamento das monitorias acadêmicas do IFMG, automatizando o fluxo burocrático através do cadastro de monitorias, envio e acompanhamento da documentação mensal, controle rigoroso de prazos com regras de negócio, notificações automáticas por e-mail e gestão de permissões.

## Tecnologias

- **Backend:** Python (Django)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js
- **Banco de Dados:** SQLite (Desenvolvimento/Testes)

## Funcionalidades

- **Controle de Perfis:** Interfaces e permissões dedicadas para Monitor, Professor e Pedagógico.
- **Notificações Inteligentes:** Alertas dinâmicos no dashboard baseados em prazos do mês corrente e atrasos.
- **Dashboards:** Resumo visual de pendencias e dados ativos.
- **Relatórios:** Relatorios gerados em PDF e CSV

---

## Rodar o projeto localmente

Siga os passos abaixo. Os comandos estão em blocos separados para facilitar a cópia direta.

### 1. Clonar o repositório

```bash
git clone https://github.com/ph-santos0/sigma-monitorias.git
cd sigma-monitorias
```

### 2. Criar e ativar o ambiente virtual

```bat
python -m venv venv
venv\\Scripts\\activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar o banco de dados e os usuários de teste

Este comando cria as tabelas e gera automaticamente os usuários fictícios e os vínculos necessários para testar o sistema:

```bash
python manage.py migrate
python manage.py setup_test
```

### 5. Rodar o servidor local

```bash
python manage.py runserver
```

### 6. Acessar o sistema

Abra o navegador e acesse:

http://127.0.0.1:8000

---

## 🔑 Usuários de teste disponíveis

Após executar o comando `python manage.py setup_test`, os seguintes usuários estarão disponíveis:

| Perfil | Usuário (login) | Senha |
|---|---|---|
| Setor Pedagógico | `pedagogico` | `123` |
| Professor / Orientador | `professor` | `123` |
| Monitor / Estudante | `monitor` | `123` |
| Super Admin | `admin` | `123` |
