# core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    # ГЛАВНЫЙ МАРШРУТ: Используем '/materials/list/' (permanent=False для избежания кэша)
    path('', RedirectView.as_view(url='/materials/list/', permanent=False)),

    path('admin/', admin.site.urls),

    # Все маршруты приложения materials
    path('materials/', include('materials.urls')),

    # Маршруты для пользователей/авторизации (ЗДЕСЬ ОПРЕДЕЛЕН МАРШРУТ 'logout')
    path('accounts/', include('django.contrib.auth.urls')),
]