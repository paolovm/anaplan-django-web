"""Testes do app integrador.

Demonstra três níveis de "visibilidade" testável:
  1. Modelos (camada de dados) — rápido, sem mocks, documenta o domínio.
  2. Notificação por e-mail — usa o backend de teste do Django (mail.outbox).
  3. Cliente Anaplan — SEM tocar a rede real, com mock de `requests`.
     (É assim que se testa um conector de API: simulando as respostas.)
"""
import base64
import json
from unittest.mock import MagicMock, patch

from django.core import mail
from django.test import TestCase, override_settings

from integrador.models import (
    Execucao,
    Historico,
    Modelo,
    ProcessList,
    Processo,
)
from integrador.PyTools.anaplanTools import (
    anaplanImport,
    convertbase64,
    parse_task_response,
)
from integrador.PyTools.sendemail import sendEmail


class ModeloTests(TestCase):
    """Camada de dados: criação, __str__ e relacionamentos."""

    def setUp(self):
        self.modelo = Modelo.objects.create(descricao="Vendas")

    def test_modelo_str(self):
        self.assertEqual(str(self.modelo), "Vendas")

    def test_timestamps_preenchidos_no_save(self):
        self.assertIsNotNone(self.modelo.data)
        self.assertIsNotNone(self.modelo.hora)

    def test_processo_relacionamento(self):
        processo = Processo.objects.create(nome="Carga Diária", modelo=self.modelo)
        self.assertEqual(str(processo), "Carga Diária")
        self.assertEqual(processo.modelo, self.modelo)
        self.assertIn(processo, self.modelo.modelo_processo.all())

    def test_processlist_str(self):
        pl = ProcessList.objects.create(
            descricao="Importar Vendas",
            nome_processo_anaplan="Imp Vendas",
            modelo=self.modelo,
        )
        self.assertEqual(str(pl), "Importar Vendas")

    def test_execucao_many_to_many(self):
        pl = ProcessList.objects.create(
            descricao="Importar Vendas",
            nome_processo_anaplan="Imp Vendas",
            modelo=self.modelo,
        )
        execucao = Execucao.objects.create(descricao="Exec 1", pasta_arquivos="/tmp")
        execucao.processlist.add(pl)
        self.assertEqual(str(execucao), "Exec 1")
        self.assertEqual(execucao.processlist.count(), 1)

    def test_historico_str_e_nome_processo(self):
        processo = Processo.objects.create(nome="Carga Diária", modelo=self.modelo)
        hist = Historico.objects.create(
            processo=processo, situacao="ANAPLAN", observacao="ok"
        )
        self.assertEqual(str(hist), "ANAPLAN")
        self.assertEqual(hist.nome_processo(), "Carga Diária")


class EmailNotificationTests(TestCase):
    """A notificação por e-mail (desacoplada) é testável via mail.outbox."""

    @override_settings(
        EMAIL_HOST="smtp.example.com",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        ANAPLAN_NOTIFY_RECIPIENTS=["ops@example.com"],
    )
    def test_envia_quando_configurado(self):
        sendEmail("Carga OK", "Tudo certo")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Carga OK")
        self.assertEqual(msg.body, "Tudo certo")
        self.assertEqual(msg.to, ["ops@example.com"])
        self.assertEqual(msg.from_email, "noreply@example.com")

    @override_settings(EMAIL_HOST="smtp.example.com", ANAPLAN_NOTIFY_RECIPIENTS=[])
    def test_nao_envia_sem_destinatarios(self):
        sendEmail("Assunto", "Corpo")
        self.assertEqual(len(mail.outbox), 0)


class AnaplanToolsTests(TestCase):
    """O conector Anaplan é testável SEM rede real — basta simular `requests`."""

    def test_convertbase64(self):
        self.assertEqual(
            convertbase64("user:pass"),
            base64.b64encode(b"user:pass").decode("utf-8"),
        )

    @patch("integrador.PyTools.anaplanTools.requests")
    def test_get_token_basic_auth_sem_rede(self, mock_requests):
        resposta = MagicMock()
        resposta.content = json.dumps({"tokenInfo": {"tokenValue": "TOK123"}})
        mock_requests.post.return_value = resposta

        token = anaplanImport.getTokenBasicAuth("user@example.com", "secret")

        self.assertEqual(token, "TOK123")
        mock_requests.post.assert_called_once()
        url = mock_requests.post.call_args.args[0]
        headers = mock_requests.post.call_args.kwargs["headers"]
        self.assertEqual(url, "https://auth.anaplan.com/token/authenticate")
        self.assertTrue(headers["Authorization"].startswith("Basic "))

    def test_parse_task_response_falha(self):
        results = {
            "currentStep": "Failed.",
            "result": {
                "failureDumpAvailable": False,
                "details": [{"localMessageText": "coluna invalida"}],
            },
        }
        saida = parse_task_response(results, "http://x", "task1", {})
        self.assertIn("coluna invalida", saida)
        self.assertIn("failed", saida.lower())
