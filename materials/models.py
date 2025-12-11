from django.db import models
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
                                      verbose_name="Артикул", null=True, blank=True)  # Сделаем необязательным пока
    expiration_date = models.DateField(null=True, blank=True,
                                       verbose_name="Срок годности")

    # Старые/Обновленные поля:
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец склада", null=True)
    name = models.CharField(max_length=200, verbose_name="Название материала")
    current_quantity = models.FloatField(default=0, verbose_name="Текущее количество")
    min_threshold = models.FloatField(default=10, verbose_name="Минимальный порог")
    unit = models.CharField(max_length=5, choices=UNIT_CHOICES,
                            verbose_name="Ед. измерения", default='шт.')  # Обновили max_length и добавили choices

    def __str__(self):
        # Изменено для отображения Артикула
        return f"{self.name} ({self.article_number})"

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"

# 2. Таблица истории (Для обучения ИИ)
class UsageHistory(models.Model):
    # Константы для типов операций
    OPERATION_CHOICES = [
        ('IN', 'Приход (Закупка)'),
        ('OUT', 'Расход (Продажа/Производство)'),
        ('DISP', 'Списание (Брак/Просрочка)'),
        # ('MOVE', 'Перемещение', пока не делаем)
    ]
    # Связь с таблицей Material. Если удалим материал — удалится и история (CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="Материал")
    date = models.DateField(verbose_name="Дата операции", default=timezone.now)
    # Поле для записи количества (всегда положительное)
    quantity = models.FloatField(verbose_name="Количество")
    # Тип операции (обязательно для отчетности)
    operation_type = models.CharField(max_length=5, choices=OPERATION_CHOICES, verbose_name="Тип операции")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сотрудник")
    operation_type = models.CharField(
        max_length=4,
        choices=OPERATION_CHOICES,
        verbose_name="Тип операции",
        default='OUT'
    )
    class Meta:
        verbose_name = "История операций"
        verbose_name_plural = "История операций"
        ordering = ['-date']

    def __str__(self):
        return f"{self.material.name} | {self.operation_type} {self.quantity} от {self.date}"