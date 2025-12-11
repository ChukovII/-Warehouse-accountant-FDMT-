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

class UsageForm(forms.ModelForm):
    # Мы скрываем поле material, так как будем передавать его через URL (pk)
    # Мы скрываем user, так как присвоим его в views.py

    # Добавляем поле, чтобы пользователь мог выбрать, какую операцию он совершает
    operation_type = forms.ChoiceField(
        choices=[
            ('IN', 'Приход (Закупка)'),
            ('OUT', 'Расход (Отгрузка)'),
            ('DISP', 'Списание (Брак/Просрочка)'),
        ],
        label="Тип операции",
        widget=forms.RadioSelect # Удобные радио-кнопки
    )

    class Meta:
        model = UsageHistory
        fields = ['operation_type', 'quantity', 'date', 'comment']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}), # Удобный календарь
        }