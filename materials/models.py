from django.db import models
from django.contrib.auth.models import User

# 1. Таблица материалов (Товары на складе)
class Material(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец склада", null=True)
    name = models.CharField(max_length=200, verbose_name="Название материала")
    # Текущее количество на складе
    current_quantity = models.FloatField(default=0, verbose_name="Текущее количество")
    # Минимальный порог (если меньше — нужно закупать)
    min_threshold = models.FloatField(default=10, verbose_name="Минимальный порог")
    # Единица измерения (кг, шт, литры)
    unit = models.CharField(max_length=20, default="шт.", verbose_name="Ед. измерения")

    def __str__(self):
        return f"{self.name} ({self.current_quantity} {self.unit})"

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"


# 2. Таблица истории (Для обучения ИИ)
class UsageHistory(models.Model):
    # Связь с таблицей Material. Если удалим материал — удалится и история (CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="Материал")
    date = models.DateField(verbose_name="Дата расхода")
    quantity_used = models.FloatField(verbose_name="Расход")

    def __str__(self):
        return f"{self.date}: {self.material.name} - {self.quantity_used}"

    class Meta:
        verbose_name = "Запись расхода"
        verbose_name_plural = "История расходов"