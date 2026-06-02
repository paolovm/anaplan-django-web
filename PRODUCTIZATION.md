# Roadmap de Produtização — Conector Anaplan (FlexThink)

> Documento-guia para transformar a ferramenta interna **anaplan-django-web**
> (hoje mono-cliente) em um **produto** da FlexThink.
> Escrito a partir da leitura do código atual. Use como referência viva — atualize a cada fase.

**Status atual:** ferramenta interna, mono-tenant, acoplada a um cliente (Forno de Minas).
**Objetivo:** produto multi-tenant, seguro, implantável e comercializável.

---

## 1. Sumário executivo

O "motor" do projeto é **reaproveitável**: cadastrar processos → ler arquivos → enviar ao
Anaplan via REST API v2 → disparar imports/processes → registrar log → notificar. O que falta
para virar produto é, em ordem de importância:

1. **Resolver a propriedade intelectual** (bloqueio nº 1, não técnico).
2. **Sanear segredos** expostos no repositório e histórico do git.
3. **Desacoplar do cliente** (tudo que hoje é fixo da Forno de Minas vira configuração).
4. **Multi-tenancy** (atender N clientes com isolamento de dados e credenciais).
5. **Cofre de credenciais + autenticação Anaplan moderna** (OAuth 2.0 / certificado).
6. **Arquivos via upload/nuvem com envio em chunks**.
7. **Camada de aplicação própria** (UI/API além do Django Admin) + **agendamento**.
8. **Higiene de engenharia** (Django suportado, testes, CI, Docker, observabilidade).

Estimativa de ordem de grandeza para um **MVP comercializável**: ~2–4 meses de 1 dev
sênior (ver §10, Roadmap por fases).

---

## 2. Diagnóstico do estado atual

### 2.1 O que o sistema faz
- App Django único (`integrador`) operado **inteiramente pelo Django Admin**
  (`views.py` está vazio).
- A ação de admin `carga_anaplan` (`integrador/admin.py`) lê **CSVs de uma pasta local**,
  envia ao Anaplan (REST API v2), dispara imports/processes, grava `Historico` e envia e-mail.
- Wrapper do Anaplan em `integrador/PyTools/anaplanTools.py` (derivado do sample de
  *Jesse Wilson / Anaplan Asia*), usando **Basic Auth** (`getTokenBasicAuth`).

### 2.2 Modelo de dados atual (`integrador/models.py`)
`Modelo` · `Processo` · `ProcessList` · `Execucao` · `ArquivosExecucao` ·
`ParametrosProcessList` · `ParametrosExecucao` · `Historico` (log).

### 2.3 Acoplamentos ao cliente (precisam virar configuração)
| Onde | Hardcoded |
|------|-----------|
| `AnaplanImportCaller.py` | login + senha Anaplan |
| `sendemail.py` | SMTP `mail.fornodeminas.com.br`, senha, destinatários |
| `admin.py` | caminho Windows `C:\Temp\IN` |
| `settings.py` | `SECRET_KEY` fixa, `DEBUG = True`, SQLite |
| `templates/admin/.../logo-forno.jpg` | marca do cliente |

### 2.4 Limitações técnicas
- **Django 3.1** (fora de suporte/inseguro) · **SQLite** · **sem testes** · **sem `requirements.txt`**.
- Mono-tenant: 1 banco, 1 modelo, 1 credencial.
- Envio de arquivo em **1 chunk só** (`sendData(..., 1, ...)`) → quebra em arquivos grandes.
- Tratamento de erro frágil: `except: pass`, `check_status` com `while True` (risco de loop
  infinito), `sleep()` usado sem import, sem timeouts/retries consistentes.
- `print()` no lugar de logging estruturado.

---

## 3. Pré-requisitos NÃO técnicos (resolver em paralelo)

### 3.1 Propriedade intelectual — bloqueio nº 1
A v1 foi feita **para um cliente** e a camada Django foi adicionada por um **desenvolvedor do
próprio cliente**. Comercializar isso exige clareza de titularidade. **Não é aconselhamento
jurídico** — consulte um advogado, mas encaminhe:

- [ ] Revisar o **contrato original** (obra sob encomenda? cessão de direitos? prestação de serviço?).
- [ ] Obter **cessão/licença por escrito** do cliente **e** do desenvolvedor que contribuiu, **ou**
- [ ] **Reescrever** as partes que não são suas (felizmente, são justamente os trechos
      específicos do cliente, que serão descartados de qualquer forma).
- [ ] Verificar a **licença do wrapper Anaplan** (sample de Jesse Wilson). Preferir a lib
      mantida [`anaplan-api`](https://pypi.org/project/anaplan-api/) ou conectores oficiais.

### 3.2 Segredos expostos — resolver já
Há **senhas reais** commitadas (e no histórico, commit `60f2878`): login/senha Anaplan,
senha de e-mail do cliente, `SECRET_KEY`.

- [ ] **Rotacionar (trocar) todas as senhas reais agora** — estão no histórico do git.
- [ ] Mover segredos para variáveis de ambiente / secret manager.
- [ ] Reescrever o histórico (ex.: `git filter-repo`) ou criar repositório novo limpo.

---

## 4. Arquitetura-alvo

### 4.1 Modelo de multi-tenancy
| Abordagem | Isolamento | Complexidade | Quando usar |
|-----------|-----------|--------------|-------------|
| **Row-level** (1 banco, `tenant_id` em tudo) | Lógico | Baixa | **Recomendado** para o início (mid-market, volume moderado) |
| Schema-per-tenant (`django-tenants`/Postgres) | Forte | Média | Clientes exigem isolamento forte |
| Banco/deploy por tenant | Máximo | Alta | Enterprise, requisitos de residência/compliance |

**Recomendação:** começar **row-level** com uma camada de *scoping* obrigatória por tenant
(middleware + managers que filtram por `organizacao`), e **criptografar segredos por tenant**
independentemente da abordagem. Migrar para schema-per-tenant só se um cliente exigir.

### 4.2 Modelo de dados alvo (evolução do atual)
```
Organizacao (tenant)
 ├─ Usuario (papéis: admin / operador / leitor)  ── pertence a 1+ Organizacao
 ├─ ConexaoAnaplan (workspace, model, credenciais CIFRADAS, tipo de auth)
 ├─ Processo / ProcessList / Parametros        (escopados por Organizacao)
 ├─ Execucao  ──► Job assíncrono (status, início/fim, quem disparou)
 │    └─ ArquivoExecucao (referência ao objeto em storage, não caminho local)
 └─ Historico / AuditLog (imutável, por tenant)
```
Os modelos atuais (`Modelo`, `ProcessList`, `Execucao`, etc.) viram **escopados por
`Organizacao`** (FK obrigatória) em vez de globais.

### 4.3 Credenciais e autenticação no Anaplan
- **Cofre:** guardar credenciais de cada tenant **cifradas em repouso** (envelope encryption
  com KMS — AWS KMS / Azure Key Vault / GCP KMS — ou `cryptography.Fernet` com a chave no
  secret manager). **Nunca** em texto puro nem em código.
- **Trocar Basic Auth** por **OAuth 2.0** ou **certificado (service account)**:
  - Basic Auth exige rotação de senha (30–90 dias) → inviável para produto.
  - Tokens Anaplan duram ~30–35 min → implementar **refresh automático** e cache de token.
- Abstrair num módulo `anaplan/client.py` com interface única
  (`authenticate`, `upload_file`, `run_action`, `get_status`) e testes — substituindo o
  wrapper atual.

### 4.4 Arquivos
- Entrada por **upload web/API** ou **storage em nuvem** (S3/Blob/GCS), não pasta local Windows.
- **Envio em chunks** ao Anaplan (pedaços ≤ ~50 MB; definir `chunkCount` real e fazer PUT de
  cada chunk) — corrige o envio de 1 chunk único atual.
- Validação de CSV (encoding, colunas, tamanho) antes do envio; retenção/expurgo configurável.

### 4.5 Camada de aplicação
- **UI própria** (cliente) + **API REST** (Django REST Framework) com autenticação, papéis,
  auditoria. Manter o **Django Admin** apenas para operação interna da FlexThink.
- **Agendamento e execução assíncrona:** a `Execucao` vira **job** (Celery + Redis/RabbitMQ,
  ou Django-Q). Agendamento via Celery beat/cron. Idempotência + retries + timeouts.
- **Observabilidade:** logging estruturado (substituir `print`), métricas e rastreio de erros
  (ex.: Sentry), status de cada execução visível ao cliente.

---

## 5. Segurança e conformidade

- [ ] Segredos fora do código (env / secret manager); `SECRET_KEY` por ambiente; `DEBUG=False`.
- [ ] HTTPS obrigatório; `ALLOWED_HOSTS`, cookies seguros, headers de segurança.
- [ ] Criptografia em repouso (credenciais Anaplan) e em trânsito.
- [ ] **Isolamento por tenant** testado (um tenant nunca lê dados de outro).
- [ ] **Log de auditoria** imutável (quem disparou o quê, quando).
- [ ] **LGPD** (clientes BR): base legal, contrato de tratamento de dados, residência de dados,
      direito de exclusão, contato do encarregado/DPO, política de retenção.
- [ ] RBAC (admin / operador / leitor) e, para enterprise, SSO (SAML/OIDC) no roadmap.

---

## 6. Stack-alvo e higiene de engenharia

| Item | Hoje | Alvo |
|------|------|------|
| Django | 3.1 (EOL) | **5.2 LTS** (a 4.2 chegou ao fim de vida em abr/2026; suporte da 5.2 até 2028) |
| Banco | SQLite | **PostgreSQL** |
| Dependências | nenhuma travada | `requirements.txt` / Poetry **pinado** |
| Config | hardcoded | **env vars** (`django-environ`) + `.env.example` |
| Assíncrono | — | **Celery + Redis** |
| Testes | nenhum | **pytest** + cobertura (alvo ≥70% no core) |
| CI/CD | — | **GitHub Actions** (lint + testes + build) |
| Empacotamento | — | **Docker** + docker-compose |
| Logs | `print` | logging estruturado + Sentry |

---

## 7. Plano de implantação (infra)

- **Contêineres:** app (gunicorn/uvicorn) + worker Celery + Postgres + Redis + storage de objetos.
- **Nuvem:** AWS / Azure / GCP (escolher 1). Residência de dados no **Brasil** se for argumento
  comercial/LGPD.
- **Ambientes:** dev → staging → produção, com secret manager por ambiente.
- **Backups** automáticos do Postgres + storage; **plano de DR** básico.
- **Provisionamento de tenant:** processo (idealmente automatizado) para criar uma nova
  `Organizacao`, usuários iniciais e conexão Anaplan.

---

## 8. Lado comercial / go-to-market (resumo)

- **Formato:** SaaS multi-tenant (receita recorrente, mais operação/compliance) ×
  self-hosted por cliente × conector empacotado. **Sugestão:** SaaS, começando enxuto.
- **Posicionamento:** complementa/concorre com Anaplan Connect, CloudWorks e Data Orchestrator.
  Diferencial provável: **"integração CSV/ERP → Anaplan, simples, para o mid-market sem TI pesada"**.
- **Validação:** 2–3 clientes *design partner* (a Forno de Minas pode ser o caso de referência,
  **se** a questão de PI estiver resolvida).
- **Precificação:** por tenant / por modelo Anaplan / por volume de execuções.
- **Necessário para vender:** documentação, suporte, onboarding, revisão de segurança.

---

## 9. Riscos principais

| Risco | Mitigação |
|-------|-----------|
| **PI** (código do cliente/dev) | Cessão por escrito **ou** reescrita das partes não-próprias |
| Segredos vazados no histórico | Rotacionar senhas + limpar histórico |
| Mudanças na API/auth do Anaplan | Abstrair cliente Anaplan + testes; usar lib mantida |
| Vazamento entre tenants | Scoping obrigatório + testes de isolamento |
| LGPD | Compliance desde o MVP, não depois |
| Escopo inflar ("tudo de uma vez") | Roadmap por fases (§10), MVP enxuto |

---

## 10. Roadmap por fases (milestones)

### Fase 0 — Fundação (1–2 semanas)
- [ ] Sanear segredos (env vars, `.env.example`, `.gitignore`, rotação de senhas).
- [ ] `requirements.txt` pinado; subir Django 3.1 → **5.2 LTS**; trocar SQLite→Postgres (dev).
- [ ] Remover acoplamentos do cliente (e-mail/SMTP/caminho/logo → configuração).
- [ ] Dockerizar; CI básica (lint + testes).

### Fase 1 — MVP multi-tenant (3–5 semanas)
- [ ] Modelo `Organizacao` + escopo por tenant em todos os modelos.
- [ ] `ConexaoAnaplan` com credenciais **cifradas**; cliente Anaplan abstraído + token cache.
- [ ] Upload de arquivos + envio **em chunks**; execução via job assíncrono (Celery).
- [ ] Autenticação de usuários + papéis; log de auditoria por tenant.

### Fase 2 — Produto vendável / Beta (3–4 semanas)
- [ ] UI/API própria (DRF) para o cliente; agendamento de execuções.
- [ ] OAuth 2.0 / certificado para o Anaplan.
- [ ] Observabilidade (Sentry, métricas); tratamento de erro robusto (retries/timeouts).
- [ ] Onboarding de tenant + documentação; revisão de segurança e LGPD.

### Fase 3 — GA / escala (contínuo)
- [ ] SSO (SAML/OIDC), billing, SLAs, painel de operação interna.
- [ ] Hardening, testes de carga, DR, certificações conforme demanda enterprise.

---

## 11. Próximos passos imediatos

1. **Jurídico:** acionar revisão de contrato/cessão de PI (em paralelo a tudo).
2. **Segurança:** rotacionar senhas e sanear o repositório (posso executar).
3. **Técnico:** rodar a **Fase 0** (fundação) — posso começar pelo saneamento de segredos +
   `requirements.txt` + remoção dos acoplamentos do cliente.

> Quer que eu já inicie a Fase 0 neste branch? Posso abrir as tarefas como checklist e
> implementar passo a passo.
