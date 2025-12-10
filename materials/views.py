from django.shortcuts import render, redirect, get_object_or_404
from .models import Material
from .forms import MaterialForm
from django.contrib.auth.decorators import login_required

@login_required
def material_list(request):
    # 1. Получаем все материалы из Базы Данных
    materials = Material.objects.filter(user=request.user)

    # 2. Готовим данные для передачи в шаблон (контекст)
    context = {
        'materials': materials
    }

    # 3. Отдаем пользователю HTML-шаблон с этими данными
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