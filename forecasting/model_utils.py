# forecasting/model_utils.py

import pandas as pd
from materials.models import UsageHistory, Material  # Импортируем наши модели
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import timedelta

def get_historical_usage_data(material_id, days=180):
    """
    Извлекает данные расхода (OUT и DISP) для материала
    за указанное количество дней и подготавливает временной ряд.
    """
    try:
        material = Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        return None

    # Определяем операции, которые являются расходом
    usage_types = [UsageHistory.OperationType.OUT, UsageHistory.OperationType.DISP]

    # 1. Запрос данных из UsageHistory
    history_queryset = UsageHistory.objects.filter(
        material=material,
        operation_type__in=usage_types
    ).values('operation_date', 'quantity').order_by('operation_date')

    # 2. Преобразование в DataFrame
    if not history_queryset:
        return pd.DataFrame(columns=['date', 'usage_qty'])

    df = pd.DataFrame(list(history_queryset))

    # Переименовываем столбцы для удобства
    df = df.rename(columns={'operation_date': 'date', 'quantity': 'usage_qty'})

    # *** КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Конвертируем дату в формат datetime Pandas ***
    df['date'] = pd.to_datetime(df['date'])

    # Теперь, когда даты преобразованы, устанавливаем индекс
    df = df.set_index('date')

    # 3. Агрегация по дням
    # Группируем расход по дате (если в один день было несколько операций)
    daily_data = df['usage_qty'].resample('D').sum().fillna(
        0)  # 'D' - ежедневно, fillna(0) - где нет операций, ставим 0

    # 4. Фильтрация по периоду (180 дней по умолчанию)
    end_date = pd.to_datetime('today').normalize()
    start_date = end_date - pd.Timedelta(days=days)

    # Создаем полный диапазон дат, чтобы не было пропусков
    full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Объединяем с полным диапазоном, чтобы заполнить нулями дни без операций
    daily_data = daily_data.reindex(full_date_range, fill_value=0)

    # Возвращаем DataFrame с датами и ежедневным расходом
    return daily_data.reset_index().rename(columns={'index': 'date', 'usage_qty': 'usage_qty'})


def predict_usage(df_historical, days_to_predict=30):
    """
    Обучает простую модель Linear Regression на исторических данных
    и прогнозирует расход на N дней вперед.

    :param df_historical: DataFrame с данными 'date' и 'usage_qty'.
    :param days_to_predict: Количество дней для прогнозирования.
    :return: Прогнозируемый общий расход за весь период (float).
    """
    if df_historical.empty or df_historical['usage_qty'].sum() == 0:
        return 0.0

    # 1. Подготовка данных для обучения
    # X - номер дня (от 0 до N-1)
    df_historical['day_index'] = np.arange(len(df_historical))
    X = df_historical[['day_index']]
    # Y - фактический расход
    Y = df_historical['usage_qty']

    # 2. Обучение модели
    model = LinearRegression()
    model.fit(X, Y)

    # 3. Подготовка данных для прогноза
    # Начинаем прогнозировать сразу после последнего дня в обучающей выборке
    last_day_index = len(df_historical) - 1

    # X_future - индексы дней, которые мы хотим предсказать
    X_future = np.arange(last_day_index + 1, last_day_index + 1 + days_to_predict).reshape(-1, 1)

    # 4. Прогнозирование
    predictions = model.predict(X_future)

    # Прогноз не может быть отрицательным
    predictions[predictions < 0] = 0

    # Суммируем прогнозируемый расход за весь период
    predicted_total_usage = np.sum(predictions)

    return predicted_total_usage


# --- НОВАЯ ГЛАВНАЯ ФУНКЦИЯ ---

def get_recommendation(material_id, days_to_forecast=30):
    """
    Основная функция, которая возвращает прогноз и рекомендации.
    """
    # 1. Получаем исторические данные
    df_usage = get_historical_usage_data(material_id, days=180)  # Используем 180 дней истории

    # 2. Прогнозируем расход
    predicted_usage = predict_usage(df_usage, days_to_forecast)

    try:
        material = Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        return {'error': 'Материал не найден'}

    # 3. Расчет текущего состояния
    current_stock = material.current_quantity
    min_threshold = material.min_threshold

    # 4. Расчет рекомендуемого запаса
    # Рекомендуемый запас должен покрывать прогнозируемый расход плюс минимальный порог
    recommended_stock = predicted_usage + min_threshold

    # 5. Генерация рекомендации
    recommendation = ""
    action = "NONE"  # NONE, PURCHASE, DISPOSE
    quantity_delta = 0

    # Анализ 1: Закупка
    if current_stock < recommended_stock:
        quantity_to_buy = recommended_stock - current_stock
        recommendation = f"Рекомендуется закупить {round(quantity_to_buy, 2)} {material.unit} для покрытия прогнозируемого спроса и поддержания минимального запаса."
        action = "PURCHASE"
        quantity_delta = round(quantity_to_buy, 2)

    # Анализ 2: Списание (Если запас сильно превышает рекомендуемый)
    elif current_stock > recommended_stock * 2:  # Если текущий запас в 2 раза больше, чем нужно
        # Также проверяем срок годности (если он скоро истекает)
        if material.expiration_date and (material.expiration_date - timedelta(days=days_to_forecast)).days < 60:
            recommendation = f"Запас сильно превышает прогнозируемый спрос. Рекомендуется рассмотреть списание части запаса ({material.name}) или использование его в ближайшее время, учитывая срок годности."
            action = "DISPOSE"
            # Мы не будем автоматически предлагать количество для списания, так как это сложный вопрос

    else:
        recommendation = "Текущий запас в пределах нормы. Дополнительных действий не требуется."

    return {
        'material_name': material.name,
        'current_stock': current_stock,
        'predicted_usage': round(predicted_usage, 2),
        'recommended_stock': round(recommended_stock, 2),
        'recommendation': recommendation,
        'action': action,
        'quantity_delta': quantity_delta,
        'days_to_forecast': days_to_forecast,
    }