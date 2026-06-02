# HANDOVER — Produtização do Conector Anaplan (FlexThink)

> **Comece por aqui** para retomar o trabalho. Este documento é o ponto de parada da frente
> de produtização: o que foi decidido, o que foi feito, o estado do repositório, as pendências
> e o próximo passo.
>
> **Frente pausada em:** 2026-06-02 · **Branch:** `claude/tender-galileo-n6oRA`

---

## TL;DR (estado atual)
- O projeto era uma ferramenta interna mono-cliente (Forno de Minas). O objetivo é virar um
  **produto self-service** da FlexThink.
- **Fase 0 (fundação) concluída e verificada** (Django 5.2, segredos fora do código, Docker, CI verde, 11 testes).
- Falta retomar na **Fase 1 (MVP multi-tenant)** quando quiser.
- ⚠️ **Há ações que só você pode fazer** — ver "Pendências do Paolo".

---

## 1. O Norte (para onde vamos)
> Ser a forma mais simples de uma equipe de planejamento/FP&A **carregar dados na sua plataforma**
> — **Anaplan** primeiro, depois **IBM Planning Analytics (TM1)** — de modo **self-service**.

**Modelo:** "product-led, consulting-assisted" — produto self-service que também é motor de novos
clientes para a consultoria da FlexThink. Detalhes completos em **`PRODUCTIZATION.md`** (seção "✦ Norte").

### Decisões já tomadas
| Tema | Decisão |
|---|---|
| Ambição | Produto que reforça a consultoria **e** traz novos clientes (não lifestyle puro, não venture) |
| Mercado | **Anaplan** primeiro → depois **IBM Planning Analytics (TM1)** |
| Entrega | **SaaS self-service** (consultoria como upsell) |
| Stack | Django **5.2 LTS** + Postgres + Docker; DRF/Celery previstos na Fase 1 |
| Multi-tenant | Começar **row-level** (escopo por `Organizacao`) |
| Arquitetura | **Adaptadores de plataforma** — Anaplan é o 1º; TM1 entra sem reescrever o núcleo |

---

## 2. O que foi entregue (Fase 0)
Commits nesta frente (mais recente primeiro):

| Commit | O quê |
|---|---|
| `f78a011` | `ARQUITETURA.md` — como o Django funciona e o que envolve o conector |
| `f671a25` | `DESENVOLVIMENTO.md` (como rodar/testar) + correção da leitura do `.env` |
| `5a8ff20` | Primeira suíte de **testes** (11, todos verdes) |
| `0d126a3` | **Docker** + **CI** (GitHub Actions) |
| `3d958a5` | Config por ambiente, **remoção de segredos**, upgrade **Django 3.1 → 5.2.14** |
| `1bad79b` | Norte (visão/objetivo comercial) no roadmap |
| `ac723a3` | Correção do alvo de upgrade para 5.2 LTS |
| `8238a39` | Roadmap de produtização inicial |

**Verificado rodando** (venv com Django 5.2.14): `manage.py check` sem avisos, migração `0014`
aplicada, **11 testes OK**, CI verde no push.

---

## 3. Mapa dos documentos
| Arquivo | Para quê |
|---|---|
| **`HANDOVER.md`** (este) | Ponto de partida para retomar |
| **`PRODUCTIZATION.md`** | Roadmap completo: Norte, arquitetura-alvo, fases, riscos |
| **`ARQUITETURA.md`** | Como o Django funciona e o que foi construído ao redor do conector |
| **`DESENVOLVIMENTO.md`** | Como rodar o projeto e os testes localmente |

---

## 4. Entendendo o Django (para decidir)
**Django cuida do "prédio" (encanamento web); você cuida do seu negócio (a integração Anaplan).**
Ele entrega prontos: roteamento, banco via ORM, migrations, **Admin automático** (é toda a UI
hoje), login/permissões, segurança (CSRF/XSS/SQLi) e um ecossistema plugável (DRF p/ APIs,
Celery p/ jobs, django-tenants p/ multi-tenant).

**O que reusar × reescrever × investir:**
- **Reusar:** tudo que o Django já faz (não reinventar).
- **Reescrever:** a camada Django atual do cliente (`models.py`, `admin.py`…) ao migrar para multi-tenant.
- **Investir:** sua lógica Anaplan (camada de adaptador) + a experiência do cliente (UI/API self-service).

---

## 5. ⚠️ Pendências do Paolo (só você pode fazer)
- [ ] **Rotacionar as senhas** que vazaram no histórico do git — o repositório é **público**:
      `Number28` (sua, Anaplan/flexthink) e a senha de e-mail do cliente. O código atual já não
      tem segredos, mas o **histórico** ainda os contém.
- [ ] **Propriedade intelectual:** conseguir um "ok" por escrito do **Cleber** (dev do cliente,
      `rcleber@outlook.com.br`) — útil para due diligence futura. Risco prático baixo segundo seu relato.
- [ ] (Opcional) Definir os **números dos marcos** do Norte (clientes/leads/MRR).

---

## 6. Achados importantes (procedência)
Com base no git e no seu repo original **`paolovm/AnaplanConnector`**:
- Toda a pasta do conector foi commitada **de uma vez** pelo **Cleber** em 2021-01-04 (`60f2878`),
  então o git aponta a autoria para ele — sua autoria do v0 é **anterior** a este repositório.
- **`util.py` não existe** no seu repo original → provavelmente foi o Cleber que o criou.
- Seu original **tinha `crypt.py`/`decrypt.py`** (criptografia de credenciais) que **não** vieram
  para a versão Django — justamente a que deixou credenciais em texto puro. Ou seja: sua ideia de
  cofre de credenciais (Fase 1) **já existia no seu v0**.
- A base REST (`anaplanTools.py`) é derivada do *sample* oficial do Anaplan (Jesse Wilson) —
  verificar a licença ao comercializar.

---

## 7. Próximo passo ao retomar — Fase 1 (MVP multi-tenant)
Quando voltar a esta frente:
1. Modelo `Organizacao` (tenant) + escopo por tenant em todos os modelos.
2. **Cofre de credenciais cifradas** por tenant (recuperar a ideia do `crypt.py` original).
3. Extrair o conector para uma **camada de adaptador** (`autenticar / enviar_arquivo / rodar_ação / status`),
   com Anaplan como primeiro adaptador — testável isoladamente.
4. Upload de arquivos + envio **em chunks**; execução como job assíncrono (Celery).
5. Autenticação de usuários + papéis; log de auditoria por tenant.

Detalhe e checklists completos em `PRODUCTIZATION.md` (§10).

### Como retomar o ambiente
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
cd anaplan && python manage.py test    # confirma que está tudo verde
```
(Ver `DESENVOLVIMENTO.md` para mais.)
