from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.options import ModelAdmin

class LogEntryAdmin(ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message')
    list_filter = ('action_flag', 'content_type')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'
    readonly_fields = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message')

admin.site.register(LogEntry, LogEntryAdmin)