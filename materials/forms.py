# materials/forms.py

from django import forms
from .models import Material, UsageHistory
from datetime import date  # <-- ДОБАВЛЕН ИМПОРТ date


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            'name',
            'article_number',
            'category',
            'current_quantity',
            'min_threshold',
            'unit',
            'expiration_date'
        ]


class UsageHistoryForm(forms.ModelForm):
    """
    Форма для регистрации операций прихода/расхода (IN/OUT/DISP).
    """

    class Meta:
        model = UsageHistory
        fields = [
            'quantity',
            'operation_type',
            'comment',
            'operation_date'
        ]
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ИСПРАВЛЕНИЕ 1: Устанавливаем текущую дату по умолчанию, чтобы она отображалась
        # Это решает проблему "пропавшей" даты
        if self.initial.get('operation_date') is None:
            self.initial['operation_date'] = date.today()

        # ИСПРАВЛЕНИЕ 2: Используем класс OperationType для choices
        self.fields['operation_type'].choices = UsageHistory.OperationType.choices