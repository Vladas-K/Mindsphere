# Mindsphere

Каталог программ мероприятий DI EVENT и рабочий раздел сотрудников на Django.
Посетители видят опубликованные программы; сотрудники после входа могут создавать,
редактировать и удалять мероприятия, просматривать внутренние описания и менять пароль.
Учётные записи создаёт администратор.

**Стек:** Python 3.12, Django 6.1.3, SQLite. Зависимости закреплены в `requirements.txt`.

## Установка и запуск

Команды выполняются из корня проекта на macOS/Linux. Для новой установки:

```bash
python3.12 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python sphere/manage.py migrate
venv/bin/python sphere/manage.py createsuperuser
venv/bin/python sphere/manage.py runserver
```

Если `venv` уже существует, пересоздавать его не нужно.

- Каталог: http://127.0.0.1:8000/
- Вход сотрудников: http://127.0.0.1:8000/auth/login/
- Админка: http://127.0.0.1:8000/admin/

## Данные каталога

Тексты, пользователи и настройки мероприятий хранятся в `sphere/db.sqlite3`,
загруженные изображения — в `sphere/media/`. Они исключены из Git:
для резервного копирования и переноса сайта нужны **база и media вместе**.
Обычные изменения выполняются через сайт или админку.

Для заполнения новой базы исходными 21 программами:

```bash
venv/bin/python sphere/manage.py load_catalog --replace
```

Команда использует `sphere/events/catalog_source.json` и исходные иллюстрации.
**Повторный запуск перезаписывает публичные поля исходных программ**,
а `--replace` снимает остальные программы с публикации. Для обновления
отредактированного сайта эту команду не используют.

## Проверки

```bash
venv/bin/python -m pip check
venv/bin/python sphere/manage.py check
venv/bin/python sphere/manage.py makemigrations --check --dry-run
venv/bin/python sphere/manage.py test events.tests users core.tests
```

Полный набор, включая pytest-тесты, после установки зависимостей:

```bash
cd sphere
../venv/bin/python -m pytest
```

## Развёртывание

Локальный запуск использует `config.settings`, серверный — `config.production`.
На сервере подготовьте `.env` по `.env.example`: задайте секрет и разрешённые домены.
Вход и формы требуют HTTPS. Для Beget используются `.htaccess` и `passenger_wsgi.py`;
путь `PassengerPython` должен соответствовать серверному окружению.

Перед обновлением сохраняйте базу и media. Серверные команды запускайте
с `--settings=config.production`; после изменения статики выполняйте `collectstatic`,
после обновления кода перезапускайте Passenger. Локальные базу и `venv`
поверх серверных не копируют.

Автор: Владас Куодис.
