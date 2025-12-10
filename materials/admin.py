from django.contrib import admin
from .models import Material, UsageHistory

admin.site.register(Material)
admin.site.register(UsageHistory)