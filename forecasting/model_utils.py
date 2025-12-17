import pandas as pd
from materials.models import UsageHistory, Material
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import timedelta, date
import requests
import uuid
import urllib3
import warnings

# Отключаем лишние предупреждения в консоли
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ШАГ 1: Вставь сюда свой Authorization key
AUTH_DATA = "MDE5YjJkNjgtNzcxNC03YWM4LWJiYTEtNTAyYzQxOTcyYmRjOjM5MDQyNmM5LTNmY2YtNDZjYi1hOTkwLTIzNTJhOGFjODhiNw=="


def get_giga_token():
    """Получает Access Token (действует 30 минут)"""
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {AUTH_DATA}'
    }
    payload = {'scope': 'GIGACHAT_API_PERS'}
    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response.json().get('access_token')
    except Exception:
        return None


def get_historical_usage_data(material_id, days=180):
    try:
        material = Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        return None
    usage_types = [UsageHistory.OperationType.OUT, UsageHistory.OperationType.DISP]
    history_queryset = UsageHistory.objects.filter(
        material=material,
        operation_type__in=usage_types
    ).values('operation_date', 'quantity').order_by('operation_date')
    if not history_queryset:
        return pd.DataFrame(columns=['date', 'usage_qty'])
    df = pd.DataFrame(list(history_queryset))
    df = df.rename(columns={'operation_date': 'date', 'quantity': 'usage_qty'})
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    daily_data = df['usage_qty'].resample('D').sum().fillna(0)
    end_date = pd.to_datetime('today').normalize()
    start_date = end_date - pd.Timedelta(days=days)
    full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    daily_data = daily_data.reindex(full_date_range, fill_value=0)
    return daily_data.reset_index().rename(columns={'index': 'date', 'usage_qty': 'usage_qty'})


def predict_usage(df_historical, days_to_predict=30):
    if df_historical.empty or df_historical['usage_qty'].sum() == 0:
        return 0.0
    df_historical['day_index'] = np.arange(len(df_historical))
    # Используем values для предотвращения UserWarning о именах признаков
    X = df_historical[['day_index']].values
    Y = df_historical['usage_qty'].values
    model = LinearRegression()
    model.fit(X, Y)
    last_day_index = len(df_historical) - 1
    X_future = np.arange(last_day_index + 1, last_day_index + 1 + days_to_predict).reshape(-1, 1)
    predictions = model.predict(X_future)
    predictions[predictions < 0] = 0
    return np.sum(predictions)


def get_recommendation(material_id, days_to_forecast=30):
    df_usage = get_historical_usage_data(material_id, days=180)
    predicted_usage = predict_usage(df_usage, days_to_forecast)

    try:
        material = Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        return {'error': 'Материал не найден'}

    current_stock = material.current_quantity
    recommended_stock = predicted_usage + material.min_threshold

    # --- ИСПРАВЛЕННЫЙ БЛОК ГРАФИКА ---
    # Делаем копию и принудительно переводим в datetime, чтобы избежать AttributeError
    recent_history = df_usage.tail(30).copy()
    recent_history['date'] = pd.to_datetime(recent_history['date'])

    chart_labels = recent_history['date'].dt.strftime('%d.%m').tolist()
    chart_data = recent_history['usage_qty'].tolist()

    # 2. СЕЗОННОСТЬ И ТРЕНД
    last_month_usage = df_usage['usage_qty'].tail(30).mean()
    overall_avg = df_usage['usage_qty'].mean()
    trend = "растущий" if last_month_usage > overall_avg else "стабильный"

    # 3. ОЦЕНКА РИСКА БРАКА
    risk_level = "Низкий"
    if material.expiration_date:
        days_to_expiry = (material.expiration_date - date.today()).days
        if days_to_expiry < 14:
            risk_level = "Критический (срок истекает)"
        elif days_to_expiry < 60:
            risk_level = "Средний"

    # 4. ВЫЯВЛЕНИЕ АНОМАЛИЙ
    anomaly_detected = "Нет"
    if predicted_usage < 1 and current_stock < material.min_threshold:
        anomaly_detected = "Резкое снижение остатков без зафиксированного расхода"

    quantity_delta = max(0, recommended_stock - current_stock)
    display_delta = int(np.ceil(quantity_delta))
    action = "PURCHASE" if current_stock < recommended_stock else "NONE"

    token = get_giga_token()
    if token:
        prompt = (
            f"Ты — эксперт-аналитик склада. Данные по '{material.name}':\n"
            f"- Тренд: {trend}, Риск брака: {risk_level}, Аномалии: {anomaly_detected}.\n"
            f"- Запас: {current_stock}, Прогноз: {round(predicted_usage, 2)}.\n"
            f"Дай краткий совет (до 20 слов): нужно ли закупать {display_delta} ед. и есть ли риски."
        )

        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
        payload = {"model": "GigaChat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.5}

        try:
            res = requests.post("https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                                headers=headers, json=payload, verify=False)
            raw_text = res.json()['choices'][0]['message']['content']
            recommendation_text = raw_text.replace('*', '')
        except Exception:
            recommendation_text = "Ошибка ИИ-анализа. Рекомендуется ручная проверка."
    else:
        recommendation_text = "ИИ временно недоступен. Используйте математический прогноз."

    return {
        'material_name': material.name,
        'current_stock': current_stock,
        'predicted_usage': round(predicted_usage, 2),
        'recommended_stock': round(recommended_stock, 2),
        'recommendation_text': recommendation_text,
        'action': action,
        'days_to_forecast': days_to_forecast,
        'quantity_delta': round(quantity_delta, 2),
        'stock_status_percent': min(100,
                                    int((current_stock / recommended_stock) * 100)) if recommended_stock > 0 else 100,
        'risk_level': risk_level,
        'trend': trend,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }