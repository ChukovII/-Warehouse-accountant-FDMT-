from django.shortcuts import render, redirect, get_object_or_404
from .models import Material, Category
from .forms import MaterialForm
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta


@login_required
def material_list(request):
    """Список материалов с фильтрацией"""

    # 1. Получаем базовый набор материалов пользователя
    materials = Material.objects.filter(user=request.user)

    # 2. Получаем параметры фильтрации
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    expiry_filter = request.GET.get('expiry', '')
    today = date.today()

    # 3. Применяем фильтры
    if search_query:
        materials = materials.filter(
            name__icontains=search_query
        ) | materials.filter(
            article_number__icontains=search_query
        )

    if category_id:
        materials = materials.filter(category_id=category_id)

    if expiry_filter:
        if expiry_filter == 'expired':
            materials = materials.filter(expiration_date__lt=today)
        elif expiry_filter == 'expires_soon':
            soon_date = today + timedelta(days=30)
            materials = materials.filter(
                expiration_date__gte=today,
                expiration_date__lte=soon_date
            )
        elif expiry_filter == 'no_expiry':
            materials = materials.filter(expiration_date__isnull=True)

    # 4. Получаем категории для выпадающего списка
    categories = Category.objects.filter(user=request.user)

    # 5. Добавляем цветовую маркировку и считаем статистику (ТВОЙ КОД)
    total_count = materials.count()
    critical_count = 0
    below_threshold_count = 0
    soon_expiry_count = 0

    # В цикле for material in materials:
    for material in materials:
        is_critical = False

        # Проверяем количество
        if material.current_quantity == 0:
            is_critical = True
            material.quantity_status = 'none'

        # Проверяем срок годности
        if material.expiration_date:
            days_left = (material.expiration_date - today).days
            if days_left < 0:
                is_critical = True
                material.expiry_status = 'expired'
                material.expiry_label = 'Просрочен'
            elif days_left <= 30:
                material.expiry_status = 'soon'
                material.expiry_label = 'Скоро истекает'
                soon_expiry_count += 1
            else:
                material.expiry_status = 'ok'
                material.expiry_label = 'ОК'
        else:
            material.expiry_status = 'no_date'
            material.expiry_label = 'Не указан'

        # Проверяем порог (только если не критический)
        if material.current_quantity < material.min_threshold and material.current_quantity > 0:
            below_threshold_count += 1

        # Устанавливаем цвет строки
        if is_critical:
            material.row_class = 'table-danger'
            critical_count += 1
        elif material.current_quantity < material.min_threshold and material.current_quantity > 0:
            material.row_class = 'table-warning'
        else:
            material.row_class = 'table-light'

    # 6. Готовим контекст (ВАЖНО: ДОБАВЬ ЭТО!)
    context = {
        'materials': materials,
        'categories': categories,
        'today': today,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_expiry': expiry_filter,
        'total_count': total_count,
        'critical_count': critical_count,
        'below_threshold_count': below_threshold_count,
        'soon_expiry_count': soon_expiry_count,
    }

    return render(request, 'materials/material_list.html', context)

@login_required
def material_create(request):
    if request.method == 'POST':
        # Если данные отправлены (нажата кнопка "Сохранить")
        form = MaterialForm(request.POST)
        if form.is_valid():
            # НЕ сохраняем сразу, сначала присвоим владельца
            material = form.save(commit=False)
            material.user = request.user # <-- Присваиваем владельца
            material.save() # <-- Сохраняем в БД
            return redirect('material_list') # Возвращаем на главную страницу
    else:
        # Если просто открыли страницу (GET запрос)
        form = MaterialForm()

    context = {'form': form}
    return render(request, 'materials/material_form.html', context)

@login_required
def material_update(request, pk):
    # Получаем материал по ID (pk) И убеждаемся, что он принадлежит текущему пользователю
    material = get_object_or_404(Material, pk=pk, user=request.user)

    if request.method == 'POST':
        # При POST-запросе (сохранение изменений) используем instance=material
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect('material_list')
    else:
        # При GET-запросе (открытие страницы) показываем заполненную форму
        form = MaterialForm(instance=material)

    context = {'form': form, 'material': material, 'update': True}
    # Используем существующий шаблон material_form.html, который вы используете для "Добавить"
    return render(request, 'materials/material_form.html', context)

@login_required
def material_delete(request, pk):
    # Получаем материал по ID (pk) И убеждаемся, что он принадлежит текущему пользователю
    material = get_object_or_404(Material, pk=pk, user=request.user)

    if request.method == 'POST':
        # Если подтвердили удаление
        material.delete()
        return redirect('material_list')

    # Показываем шаблон подтверждения, который мы создадим далее
    return render(request, 'materials/material_confirm_delete.html', {'material': material})

@login_required
def material_history(request, pk):
    # 1. Получаем материал, принадлежащий пользователю
    material = get_object_or_404(Material, pk=pk, user=request.user)
    # 2. Получаем историю использования для этого материала (из модели UsageHistory)
    history = material.usagehistory_set.all()

    context = {
        'material': material,
        'history': history,
    }
    return render(request, 'materials/material_history.html', context)