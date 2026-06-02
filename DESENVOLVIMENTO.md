# Desenvolvimento — rodar o projeto e os testes localmente

Guia rápido para levantar o ambiente e **executar os testes você mesmo**.
O comando de teste é o mesmo hoje e nas próximas fases — não muda conforme a suíte cresce.

## Pré-requisitos
- Python 3.11+ (o projeto roda em Django 5.2)
- Git
- (opcional) Docker, se preferir não instalar Python

## 1. Pegar o código
```bash
git clone <url-do-repo>
cd anaplan-django-web
git checkout claude/tender-galileo-n6oRA   # branch de trabalho
```
Se você já tem o repo: `git fetch origin && git checkout claude/tender-galileo-n6oRA`.

## 2. Ambiente Python
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
```
Para só rodar os testes, os valores padrão do `.env` já bastam.

## 3. Rodar os testes  ← a resposta direta
```bash
cd anaplan
python manage.py test
```
Saída esperada: `Ran 11 tests ... OK`.

### Variações úteis
| Objetivo | Comando |
|---|---|
| Mais detalhe | `python manage.py test -v 2` |
| Só uma classe | `python manage.py test integrador.tests.AnaplanToolsTests` |
| Só um teste | `python manage.py test integrador.tests.AnaplanToolsTests.test_convertbase64` |
| Parar no 1º erro | `python manage.py test --failfast` |

## 4. Ver quanto está coberto (opcional)
```bash
pip install coverage
coverage run manage.py test
coverage report -m          # tabela no terminal
coverage html               # gera htmlcov/index.html (abra no navegador)
```

## 5. Rodar o app (admin) localmente
```bash
cd anaplan
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# acesse http://127.0.0.1:8000/anaplan/
```

## Alternativa: tudo via Docker (sem instalar Python)
```bash
# Rodar os testes:
docker compose run --rm web python manage.py test
# Subir o app + Postgres:
docker compose up --build       # http://localhost:8000/anaplan/
```

## Na CI
A cada push, o GitHub Actions (`.github/workflows/ci.yml`) roda `manage.py check`,
confere as migrações e executa `manage.py test`. Veja a aba **Actions** do repositório.
