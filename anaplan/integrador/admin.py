import os

from django.conf import settings
from django.contrib import admin
from .models import *
from django.forms import TextInput, Textarea
from django.db import models
from django.shortcuts import redirect
from integrador.AnaplanImportCaller import envio_anaplan

# Register your models here.

@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    search_fields = ['descricao']

class ParametrosProcessListInline(admin.TabularInline):
    model = ParametrosProcessList


class ParametrosExecucaoListInline(admin.TabularInline):
    model = ParametrosExecucao



class ArquivosExecucaoInline(admin.StackedInline):
    model = ArquivosExecucao



@admin.register(Execucao)
class ExecucaoAdmin(admin.ModelAdmin):
    actions = ['carga_anaplan']
    autocomplete_fields = ['processlist']
    search_fields = ['descricao', 'processlist__descricao']
    list_filter = ['processlist__descricao']
    list_display = ['descricao']
    ordering = ['-hora']

    inlines = [
        ParametrosExecucaoListInline,
    ]

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'90'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':80})},
    }

    def carga_anaplan(self, request, queryset):
        l_process_list = []
        d_process_list = {}
        l_process_list_final = []
        l_arquivos = []
        s_modelo = ""

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        for obj in queryset:
            for process_list in obj.processlist.all():  
                for param_process_list in process_list.parametros_processlist.all():       
                   d_process_list[param_process_list.chave] = param_process_list.valor     
                   #l_process_list.append({param_process_list.chave: param_process_list.valor})
                print(d_process_list)
                s_modelo = process_list.modelo.descricao
                l_process_list_final.append([process_list.nome_processo_anaplan, d_process_list])
                #d_process_list.clear()
                #l_process_list = []
            for arquivos in ParametrosExecucao.objects.filter(execucao=obj):
                caminho = os.path.join(settings.ANAPLAN_IMPORT_DIR, arquivos.arquivo_forno)
                l_arquivos.append([arquivos.arquivo_anaplan, caminho])
            #print(getatt[r(obj, "id"))
            #print([getattr(obj, field) for field in field_names])
            envio_anaplan(s_modelo, obj.pasta_arquivos, l_process_list_final, l_arquivos)
            #Historico.objects.create(execucao =obj, situacao="ENVIADO PARA PROCESSAMENTO", observacao="Arquivos Enviados com Sucesso")
           
        return redirect('/anaplan/integrador/historico/')



'''
@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    
    actions = ['carga_anaplan']

    def carga_anaplan(self, request, queryset):
        l_process_list = []
        l_process_list_final = []

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        for obj in queryset:
            print(obj.id)
            print(obj.modelo.descricao)
            for process_list in ProcessList.objects.filter(modelo=obj.modelo):
               for param_process_list in process_list.parametros_processlist.all():
                   l_process_list.append({param_process_list.chave: param_process_list.valor})
               l_process_list_final.append([process_list.descricao, l_process_list])
               l_process_list = []
            #print(getatt[r(obj, "id"))
            #print([getattr(obj, field) for field in field_names])
            envio_anaplan(obj.modelo.descricao, obj.diretorio, l_process_list_final)
            Historico.objects.create(processo =obj, situacao="ENVIADO PARA PROCESSAMENTO", observacao="Arquivos Enviados com Sucesso")
        return redirect('/anaplan/integrador/historico/')

'''
@admin.register(Historico)
class HistoricoAdmin(admin.ModelAdmin):
    
    def has_add_permission(self, request):
        return False
    
    list_display = ['hora', 'situacao', 'observacao']
    search_fields = ['situacao']
    list_filter = ['situacao']
    ordering = ['-hora']


@admin.register(ProcessList)
class ProcessListAdmin(admin.ModelAdmin):

    inlines = [
        ParametrosProcessListInline
    ]

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'90'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':80})},
    }

    list_display = ['modelo', 'descricao', 'nome_processo_anaplan']
    search_fields = ['descricao', 'modelo__descricao', 'nome_processo_anaplan']
    list_filter = ['modelo__descricao']
    ordering = ['-hora']