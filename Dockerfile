# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências Python (psycopg[binary] já traz a libpq; não precisa de toolchain).
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Código da aplicação
COPY . .

# Usuário não-root
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/anaplan/staticfiles \
    && chown -R appuser:appuser /app
USER appuser

# A raiz do projeto Django (onde fica manage.py / o pacote anaplan)
WORKDIR /app/anaplan

# Coleta de estáticos (admin + select2)
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Servidor WSGI de produção
CMD ["gunicorn", "anaplan.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
