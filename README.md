# DevService — настройка вебхука OnlyonePays

Этот проект разворачивает backend на FastAPI, который обслуживает витрину и принимает вебхуки от платёжного провайдера OnlyonePays. Ниже приведён подробный план, что требуется сделать на сервере Timeweb Cloud, и как проверить, что всё работает.

## 1. План действий

1. **Подготовить сервер**
   - Подключить домен к инстансу в Timeweb Cloud и выпустить SSL-сертификат (например, через встроенный мастер или `certbot`).
   - Открыть 80/443 порты в правилах файрвола.

2. **Развернуть проект**
   - Установить системные пакеты: `sudo apt update && sudo apt install -y git docker docker-compose-plugin`.
   - Клонировать репозиторий: `git clone <repo_url> && cd DevService`.

3. **Сконфигурировать окружение**
   - Создать файл `backend/.env` на основе `backend/.env.example` и прописать:
     ```env
     MONGO_URL=mongodb://mongodb:27017
     DB_NAME=prod_database
    WEBHOOK_REDIRECT_URL=https://cb.boogienwoogie.com/webhook/tbank
     ```
   - Значение `WEBHOOK_REDIRECT_URL` — адрес, куда OnlyonePays хочет получить 307-редирект при проверке.
     Для проекта заказчик предоставляет прокси `https://cb.boogienwoogie.com/webhook/tbank`, который
     после перенаправления отвечает `200 OK` и JSON `{"error":"webhook data is invalid"}`.

4. **Запустить сервисы**
   - `docker compose up -d` — поднимет FastAPI-приложение и MongoDB.
   - Проверить, что контейнеры запущены: `docker compose ps`.

5. **Настроить обратное проксирование**
   - Если используется Nginx, настроить прокси на локальный порт 8000: `proxy_pass http://127.0.0.1:8000;`.
   - Убедиться, что домен выдаёт валидный сертификат.

6. **Прописать вебхук в кабинете OnlyonePays**
- В поле *Webhook URL* указать `https://www.e-devservice.ru/api/webhook/transactions`.
   - После успешной проверки в поле *Домен витрины* оставить тот же боевой домен `https://www.e-devservice.ru/` (или другой, на котором развёрнут ваш проект), чтобы платежи шли в продакшн-витрину.
   - Нажать «Проверить webhook». Первый запрос вернёт `307` на `WEBHOOK_REDIRECT_URL`, после чего проверка считается пройденной.

7. **Проверить рабочий режим**
   - Выполнить проверочный вызов (до подтверждения в OnlyonePays):
     ```bash
     curl -i -X POST https://www.e-devservice.ru/api/webhook/transactions
     ```
     Ожидаем `307 Temporary Redirect` на адрес из `WEBHOOK_REDIRECT_URL`.
     Чтобы увидеть ответ от прокси заказчика, добавьте флаг `-L`:
     ```bash
     curl -iL -X POST https://www.e-devservice.ru/api/webhook/transactions
     ```
     Итоговый ответ после редиректа должен быть `200 OK` с телом `{"error":"webhook data is invalid"}` — это сигнал,
     что проверка прокси прошла успешно.
   - После успешной проверки отправить боевой POST с JSON-полезной нагрузкой:
     ```bash
     curl -i -X POST https://www.e-devservice.ru/api/webhook/transactions \
       -H 'Content-Type: application/json' \
       -d '{"id":"test","eventType":"transaction.paid"}'
     ```
     Ответ должен быть `200 OK` с `saved_event_id`, а событие появится в MongoDB (`webhook_events`).

## 2. Что делает backend

### Поведение эндпоинта `/api/webhook/transactions`

- При первом запросе (проверка) возвращает `307 Temporary Redirect` на URL из `WEBHOOK_REDIRECT_URL`, одновременно помечая, что проверка пройдена.
- При последующих запросах:
  - Валидирует JSON-тело.
  - Сохраняет событие в коллекцию `webhook_events` (содержит payload, заголовки, время получения).
  - Возвращает `200 OK` и ID сохранённого события.

### Где хранится состояние

- Коллекция `webhook_state` содержит запись `_id = "webhook_verification"`, в которой фиксируется, что проверка пройдена, и время `verified_at`.

## 3. Проверка работоспособности

1. Посмотреть логи backend: `docker compose logs -f app`.
2. Убедиться, что коллекции появились:
   ```bash
   docker compose exec mongodb mongosh --eval 'db.getSiblingDB("prod_database").webhook_events.find().limit(1).pretty()'
   ```
3. При необходимости сбросить проверку, удалив запись:
   ```bash
   docker compose exec mongodb mongosh --eval 'db.getSiblingDB("prod_database").webhook_state.deleteMany({})'
   ```

С таким планом можно быстро развернуть вебхук и показать заказчику рабочий результат.
