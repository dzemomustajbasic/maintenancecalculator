from django.contrib import admin
from .models import GptResult, CalculationResult

def delete_files(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()  # This will call the `delete` method of the model, which includes file deletion

delete_files.short_description = "Delete selected files"

class GptResultAdmin(admin.ModelAdmin):
    list_display = ('filename', 'model_used', 'created_at')
    search_fields = ('filename', 'model_used', 'prompt')
    list_filter = ('model_used', 'created_at')  # Optional: Add filters for easier navigation
    actions = [delete_files]  # Add the delete_files action to the admin panel

class CalculationResultAdmin(admin.ModelAdmin):
    list_display = ('filename', 'created_at')
    search_fields = ('filename',)
    actions = [delete_files]  # Add the delete_files action to the admin panel

admin.site.register(GptResult, GptResultAdmin)
admin.site.register(CalculationResult, CalculationResultAdmin)
