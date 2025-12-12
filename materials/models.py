# materials/models.py

from django.db import models
from django.db.models import TextChoices  # <-- НОВЫЙ ИМПОРТ
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Material(models.Model):
    # Константы для единиц измерения
    UNIT_CHOICES = [
        ('шт.', 'Штуки'),
        ('кг', 'Килограммы'),
        ('л', 'Литры'),
        ('м', 'Метры'),
    ]
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True,
                                 verbose_name="Категория")
    article_number = models.CharField(max_length=50, unique=True,
                                      verbose_name="Артикул", null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True,
                                       verbose_name="Срок годности")

    # Основные поля:
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец склада", null=True)
    name = models.CharField(max_length=200, verbose_name="Название материала")
    current_quantity = models.FloatField(default=0, verbose_name="Текущее количество")
    min_threshold = models.FloatField(default=10, verbose_name="Минимальный порог")
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES,
                            verbose_name="Ед. измерения", default='шт.')

    def __str__(self):
        return f"{self.name} ({self.article_number})"

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"


class UsageHistory(models.Model):
    # 1. Определяем класс для типов операций (НОВАЯ СТРУКТУРА ДЛЯ views.py)
    class OperationType(TextChoices):
        IN = 'IN', 'Приход (Закупка)'
        OUT = 'OUT', 'Расход (Выдача)'
        DISP = 'DISP', 'Списание (Брак/Просрочка)'

    # Связь с таблицей Material.
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="Материал")

    # Поле 'date' из старой версии. В forms.py используется 'operation_date'
    date = models.DateField(verbose_name="Дата операции", default=timezone.now)

    # Поле 'operation_date' для ручного ввода
    operation_date = models.DateField(default=timezone.now, verbose_name="Дата операции")

    quantity = models.FloatField(verbose_name="Количество")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сотрудник")

    # Тип операции, использующий новый класс TextChoices
    operation_type = models.CharField(
        max_length=4,
        choices=OperationType.choices,
        verbose_name="Тип операции",
        default=OperationType.OUT
    )

    class Meta:
        verbose_name = "История операций"
        verbose_name_plural = "История операций"
        ordering = ['-date']

    def __str__(self):
        # Используем get_operation_type_display() для красивого отображения
        return f"{self.material.name} | {self.get_operation_type_display()} {self.quantity} от {self.date}"