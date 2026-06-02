from django.conf import settings

import integrador.PyTools.dataAcquisition as dtAquisicao


def envio_anaplan(model, diretorio, processList, dataList):
    """Envia os arquivos para o Anaplan usando a credencial configurada.

    NOTA: credencial única vinda das settings (mono-tenant). Será substituída
    pelo cofre de credenciais por tenant na Fase 1 do roadmap de produtização.
    """
    user = settings.ANAPLAN_EMAIL
    pwd = settings.ANAPLAN_PASSWORD

    importList = []

    dtAquisicao.main(user, pwd, model, dataList, importList, processList)
