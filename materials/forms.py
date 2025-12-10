# materials/forms.py
from django import forms
from .models import Material, Category, UsageHistory

class MaterialForm(forms.ModelForm):
    class Meta:
        # Основана на нашей модели Material
        model = Material
        # Поля, которые пользователь будет заполнять
        fields = ['category', 'article_number', 'name', 'unit',
                  'expiration_date', 'current_quantity', 'min_threshold']
        # Виджет для выбора даты
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }

def __init__(self, *args, **kwargs):
    user = kwargs.pop('user', None)
    super().__init__(*args, **kwargs)
    if user:
        # Фильтруем категории по текущему пользователю
        # И делаем его необязательным для миграции
        self.fields['category'].queryset = Category.objects.filter(user=user)