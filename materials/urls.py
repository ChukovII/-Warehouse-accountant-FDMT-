# materials/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Материалы: Возвращаем 'list/'
    path('list/', views.material_list, name='material_list'),
    path('create/', views.material_create, name='material_create'),
    path('<int:pk>/update/', views.material_update, name='material_update'),
    path('<int:pk>/delete/', views.material_delete, name='material_delete'),

    # Операции и История
    path('<int:pk>/log/', views.log_operation, name='log_operation'),
    path('<int:pk>/history/', views.material_history, name='material_history'),

    # Отчеты и Аналитика
    path('reports/analytics/', views.analytics_report, name='analytics_report'),
    path('forecast/<int:pk>/', views.material_forecast, name='material_forecast'),
]