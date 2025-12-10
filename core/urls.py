"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Административная панель (самый специфичный)
    path('admin/', admin.site.urls),

    # 2. Адреса для регистрации, входа, выхода (allauth)
    # Это специфичный маршрут, начинающийся с 'accounts/'
    path('accounts/', include('allauth.urls')),

    # 3. Адреса вашего приложения materials
    # ВАЖНО: Маршрут '' (корень) должен идти ПОСЛЕДНИМ, чтобы не перехватывать другие адреса.
    path('', include('materials.urls')),
]
