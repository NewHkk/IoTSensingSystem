from django.contrib import admin
from .models import Node, NodeMessage
from import_export import resources
from import_export.admin import  ImportExportModelAdmin
# Register your models here.



class NodeMessageResource(resources.ModelResource):
    class Meta:
        model = NodeMessage

class NodemessageAdmin(ImportExportModelAdmin):
    resources = [NodeMessage]


admin.site.register(Node)
#admin.site.register(NodeMessage)
admin.site.register(NodeMessage,NodemessageAdmin)