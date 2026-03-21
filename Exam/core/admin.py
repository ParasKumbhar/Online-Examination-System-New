from django.contrib import admin
from .models import IPWhitelist, LoginAudit, AuditLog

@admin.register(IPWhitelist)
class IPWhitelistAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'user', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('ip_address', 'description')

@admin.register(LoginAudit)
class LoginAuditAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'success', 'suspicious', 'timestamp')
    list_filter = ('success', 'suspicious', 'timestamp')
    search_fields = ('user__username', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'target_model', 'target_id', 'success', 'timestamp')
    list_filter = ('action', 'success', 'timestamp')
    search_fields = ('user__username', 'ip_address', 'action')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)


