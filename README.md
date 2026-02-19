### Запуск

1) Скопируй env:
```bash
cp .env.example .env
# впиши FAL_API_KEY_PRIMARY
```

2) Подними сервис:
```bash
docker compose up --build
```

API: http://localhost:8000  
Prometheus: http://localhost:9090  
Метрики: http://localhost:8000/metrics

### Авторизация
Все запросы кроме /auth требуют заголовок:
`X-API-Key: <key>`

### Регистрация
POST /auth/register
```json
{"external_user_id":"fd6ede7b-af96-4d52-8964-d4a4101297e2"}
```

### Пополнение
POST /payments/webhook  
Headers: `X-Webhook-Secret: payments-secret`
```json
{"external_user_id":"fd6ede7b-af96-4d52-8964-d4a4101297e2","amount":100}
```

### Генерация
POST /generations/videos
```json
{"prompt":"...","input_image_url":"https://...png","callback_url":"https://client/hook"}
```

GET /generations/{id} — статус и результат.

### Требования
- Асинхронный API (FastAPI)
- Очередь задач ARQ (Redis)
- Жизненный цикл задач: created/queued/processing/completed/failed
- Резерв токенов + списание при успехе + возврат при ошибке
- Retry задач и polling статуса
- Исходящие webhooks через outbox: 5 попыток, интервал 15s
- Rate limit 10/min + бан 60s
- Prometheus метрики + access logs с ротацией 7 дней
- Failover провайдера через circuit breaker (primary/secondary)
