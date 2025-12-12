# core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    # ГЛАВНЫЙ МАРШРУТ: Перенаправление с корня на список материалов
    path('', RedirectView.as_view(url='/materials/list/', permanent=False)),

    path('admin/', admin.site.urls),

    # Маршруты приложения materials
    path('materials/', include('materials.urls')),

    # ИСПРАВЛЕНИЕ: Подключаем allauth.urls
    # Это важно! Именно эта строка заставляет Django искать шаблоны в папке 'account/'
    path('accounts/', include('allauth.urls')),
]