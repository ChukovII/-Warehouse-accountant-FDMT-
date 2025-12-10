from django.contrib import admin
from .models import Material, UsageHistory, Category
admin.site.register(Category)
admin.site.register(Material)
admin.site.register(UsageHistory)