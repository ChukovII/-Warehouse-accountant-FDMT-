# materials/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.material_list, name='material_list'),
    path('add/', views.material_create, name='material_create'),
    path('<int:pk>/history/', views.material_history, name='material_history'),
    path('<int:pk>/log/', views.log_operation, name='log_operation'),
    path('edit/<int:pk>/', views.material_update, name='material_update'),
    path('delete/<int:pk>/', views.material_delete, name='material_delete')
]