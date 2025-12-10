# materials/forms.py
from django import forms
from .models import Material

class MaterialForm(forms.ModelForm):
    class Meta:
        # Основана на нашей модели Material
        model = Material
        # Поля, которые пользователь будет заполнять
        fields = ['name', 'current_quantity', 'min_threshold', 'unit']
        # Поле 'user' мы заполним автоматически, поэтому его тут нет