# materials/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, F
from datetime import date, timedelta
from .models import Material, Category, UsageHistory
from .forms import MaterialForm, UsageHistoryForm
from django.utils import timezone


# --- Основные операции ---

@login_required
def material_create(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.user = request.user
            material.save()
            return redirect('material_list')
    else:
        form = MaterialForm()
    return render(request, 'materials/material_form.html', {'form': form, 'title': 'Добавить материал'})


@login_required
def material_update(request, pk):
    material = get_object_or_404(Material, pk=pk, user=request.user)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect('material_list')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'materials/material_form.html', {'form': form, 'title': f'Редактировать {material.name}'})


@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk, user=request.user)
    if request.method == 'POST':
        material.delete()
        return redirect('material_list')
    return render(request, 'materials/material_confirm_delete.html', {'material': material})


@login_required
def log_operation(request, pk):
    material = get_object_or_404(Material, pk=pk, user=request.user)

    if request.method == 'POST':
        form = UsageHistoryForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            operation_type = form.cleaned_data['operation_type']

            # Логика обновления остатка материала
            if operation_type == UsageHistory.OperationType.IN:
                material.current_quantity += quantity
            elif operation_type in [UsageHistory.OperationType.OUT, UsageHistory.OperationType.DISP]:
                # Проверка на отрицательный остаток
                if material.current_quantity < quantity:
                    form.add_error('quantity', f"Недостаточно запаса. Доступно: {material.current_quantity}")
                    return render(request, 'materials/log_operation_form.html', {'form': form, 'material': material})

                material.current_quantity -= quantity

            material.save()

            # Сохранение истории
            history = form.save(commit=False)
            history.material = material
            history.save()

            return redirect('material_list')
    else:
        form = UsageHistoryForm()

    return render(request, 'materials/log_operation_form.html', {'form': form, 'material': material})


@login_required
def material_history(request, pk):
    material = get_object_or_404(Material, pk=pk, user=request.user)
    history = UsageHistory.objects.filter(material=material).order_by('-operation_date', '-id')
    return render(request, 'materials/material_history.html', {'material': material, 'history': history})


# --- Список и Анализ (Здесь было ИСПРАВЛЕНИЕ и ДОБАВЛЕНИЕ) ---

@login_required
def material_list(request):
    """Список материалов с фильтрацией и цветовой маркировкой"""
    user = request.user
    queryset = Material.objects.filter(user=user)
    categories = Category.objects.filter(user=user).order_by('name')

    # Фильтры
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category')
    expiry_filter = request.GET.get('expiry')
    today = date.today()

    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | Q(article_number__icontains=search_query)
        )
    if category_id:
        queryset = queryset.filter(category_id=category_id)

    if expiry_filter == 'expired':
        queryset = queryset.filter(expiration_date__lt=today)
    elif expiry_filter == 'expires_soon':
        future_date = today + timedelta(days=30)
        queryset = queryset.filter(expiration_date__range=[today, future_date])
    elif expiry_filter == 'no_expiry':
        queryset = queryset.filter(expiration_date__isnull=True)

    materials = queryset.order_by('name')

    # 5. Добавляем цветовую маркировку и считаем статистику (ИСПРАВЛЕНИЕ)
    total_count = materials.count()
    critical_count = 0
    below_threshold_count = 0
    soon_expiry_count = 0

    for material in materials:
        is_critical = False
        is_warning = False  # <-- НОВАЯ ПЕРЕМЕННАЯ ДЛЯ ЖЕЛТОЙ ЗОНЫ

        # Проверяем количество (Критический остаток: 0)
        if material.current_quantity == 0:
            is_critical = True

        # Проверяем срок годности
        if material.expiration_date:
            days_left = (material.expiration_date - today).days

            if days_left < 0:
                is_critical = True  # Красный: Просрочен
                material.expiry_status = 'expired'
            elif days_left <= 30:
                soon_expiry_count += 1
                is_warning = True  # <-- Желтый: Скоро истекает
                material.expiry_status = 'soon'
            else:
                material.expiry_status = 'ok'

        # Проверяем порог (Если не критический (т.е. остаток > 0))
        if material.current_quantity < material.min_threshold and material.current_quantity > 0:
            below_threshold_count += 1
            is_warning = True  # <-- Желтый: Мало (Если еще не критично)

        # Устанавливаем цвет строки: ПРИОРИТЕТ is_critical > is_warning
        if is_critical:
            material.row_class = 'table-danger'  # КРАСНЫЙ
            critical_count += 1
        elif is_warning:
            material.row_class = 'table-warning'  # ЖЕЛТЫЙ
        else:
            material.row_class = 'table-light'

    context = {
        'materials': materials,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_expiry': expiry_filter,
        'total_count': total_count,
        'critical_count': critical_count,
        'below_threshold_count': below_threshold_count,
        'soon_expiry_count': soon_expiry_count,
    }

    return render(request, 'materials/material_list.html', context)


# --- НОВАЯ ФУНКЦИЯ: Отчет по оборачиваемости ---

# materials/views.py (Обновленная функция analytics_report)

@login_required
def analytics_report(request):
    """
    Расчет и отображение отчета по оборачиваемости, используя
    СКОРРЕКТИРОВАННЫЙ СРЕДНИЙ ЗАПАС за период, а не только текущий остаток.
    """
    user = request.user

    # 1. Определение периода
    days = int(request.GET.get('days', 90))
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # 2. Получение ВСЕХ операций (Приход и Расход/Списание) за период
    history_data = UsageHistory.objects.filter(
        material__user=user,
        operation_date__range=[start_date, end_date],
    ).values(
        'material__name',
        'material',
        'operation_type'
    ).annotate(
        total_quantity=Sum('quantity')
    )

    # Преобразуем данные истории в удобный словарь для каждого материала
    material_stats = {}
    for item in history_data:
        material_id = item['material']
        if material_id not in material_stats:
            material_stats[material_id] = {'usage': 0, 'income': 0}

        op_type = item['operation_type']

        if op_type == UsageHistory.OperationType.IN:
            material_stats[material_id]['income'] += item['total_quantity']
        else:  # OUT или DISP (Расход)
            material_stats[material_id]['usage'] += item['total_quantity']

    # 3. Расчет Среднего Запаса и Оборачиваемости
    report_data = []

    # Получаем все материалы, у которых была активность за период
    active_material_ids = material_stats.keys()
    materials = Material.objects.filter(pk__in=active_material_ids)

    for material in materials:
        stats = material_stats.get(material.pk, {'usage': 0, 'income': 0})
        total_usage = stats['usage']
        total_income = stats['income']
        current_stock = material.current_quantity

        # --- Ключевой расчет Среднего Запаса ---

        # Запас на конец периода (End Stock) = Текущий остаток (current_stock)
        end_stock = current_stock

        # Запас на начало периода (Start Stock) = End Stock + Расход - Приход
        start_stock = end_stock + total_usage - total_income

        # Средний запас (Average Stock) = (Start Stock + End Stock) / 2
        # Убедимся, что начальный запас не отрицательный (хотя это маловероятно, если учет верен)
        if start_stock < 0:
            start_stock = 0

        average_stock = (start_stock + end_stock) / 2

        # --- Расчет Оборачиваемости ---
        turnover = None

        # Избегаем деления на ноль и бессмысленных расчетов
        if average_stock > 0 and total_usage > 0:
            turnover = total_usage / average_stock

        report_data.append({
            'name': material.name,
            'total_usage': total_usage,
            'current_stock': current_stock,
            'average_stock': round(average_stock, 2),  # Добавлено для отображения
            'start_stock': round(start_stock, 2),  # Добавлено для отображения
            'turnover_rate': turnover,
            'material_id': material.pk,
        })

    # Сортировка по ставке оборачиваемости (от высокой к низкой)
    report_data.sort(key=lambda x: x['turnover_rate'] if x['turnover_rate'] is not None else -1, reverse=True)

    context = {
        'report_data': report_data,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        'report_title': f"Отчет по оборачиваемости (за {days} дней)",
    }

    return render(request, 'materials/analytics_report.html', context)