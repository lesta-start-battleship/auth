# API для регистрации, авторизации, аутентификации и работой с данными пользователя в игре "Морской бой"

## Описание

Позволяет произвести регистрацию по логину и паролю, через Yandex или Google. Управлять пользовательскими данными.

## Структура проекта

```
auth
├── app
|   └── authorization                               # Авторизация и регистрация
|       └── oauth                                   # Авторизация через OAuth
|           └── google                              # Авторизация через Google
|           |   ├── __init__.py
|           |   ├── api_routs.py                    # Роуты для авторизации через Google
|           |   └── services.py                     # Сервисы для авторизации через Google
|           └── yandex                              # Авторизация через Yandex
|           |   ├── __init__.py
|           |   ├── api_routs.py                    # Роуты для авторизации через Yandex
|           |   └── services.py                     # Сервисы для авторизации через Yandex
|           ├── __init__.py
|           ├── device_cache.py                     # Кэш для устройств
|           ├── services.py                         # Сервисы для авторизации через OAuth
|
│       ├── __init__.py
│       ├── auth.py                                 # Роуты для авторизации и регистрации по логину и паролю
│       ├── schemas.py                              # Схемы для авторизации и регистрации по логину и паролю
│       ├── services.py                             # Сервисы для авторизации и регистрации по логину и паролю
|
│       ├── currencies                              # Валюты
│       |   ├── __init__.py
│       |   ├── routs.py                            # Роуты для валют
│       |   ├── schemas.py                          # Схемы для валют
│       |   └── services.py                         # Сервисы для валют
|
│       ├── database                                # База данных
│       |   ├── __init__.py
│       |   ├── database.py                         # База данных
│       |   └── models.py                           # Модели для базы данных
|
│       ├── kafka                                   # Кафка
│       |   └── handlers                            # Хендлеры для Кафки
│       |       ├── __init__.py
│       |       └── guild                           # Хендлеры для гильдии
│       |       |   ├── __init__.py
│       |       |   ├── guild_war_compensate.py
│       |       |   └── guild_war_declare.py
│       |       └── shop                            # Хендлеры для магазина
│       |           ├── __init__.py
│       |           ├── balance_compensate.py
│       |           └── balance_reserve.py
│       |   ├── __init__.py
│       |   ├── consumer.py                         # Классы для потребителя Кафки
│       |   ├── producer.py                         # Классы для производителя Кафки
│       |   └── services.py                         # Сервисы для Кафки
|
│       ├── migration                               # Миграции
│       |   ├── env.py
│       |   ├── script.py.mako
│       |   └── versions
|
│       ├── users                                   # Пользователи
│       |   ├── __init__.py
│       |   ├── schemas.py                          # Схемы для пользователей
│       |   ├── services.py                         # Сервисы для пользователей
│       |   └── users.py                            # Роуты для пользователей
│   
│   ├── __init__.py
│   ├── admin.py                                    # Админ панель
│   ├── alembic.ini                                 # Конфигурация альбемик
│   ├── api_doc.yaml                                # API документация
│   ├── config.py                                   # Конфигурация приложения
│   ├── decorators.py                               # Декораторы
│   ├── errors.py                                   # Ошибки
│   ├── extensions.py                               # Расширения
│   ├── init_oauth.py                               # Инициализация OAuth
│   ├── main.py                                     # Главный файл
│   ├── signals.py                                  # Сигналы
|
├── .gitignore
├── auth-deployment.yaml                            # Скрипт для деплоя
├── CHANGELOG.md                                    # История изменений
├── config_kuber.yaml.example                       # Шаблон конфигурации для приложения в Kubernetes
├── dockerfile                                      # Dockerfile
├── ingress.yaml                                    # Ingress
├── k3s-docker-build.sh                             # Скрипт для сборки Docker
├── letsencrypt.yaml                                # SSL
├── project_deployment.yaml                         # Файл для деплоя
├── README.md
├── requirements.txt                                # Зависимости
├── secret_kuber.yaml.example                       # Шаблон секретов для приложения в Kubernetes
```


## Запуск на Ubuntu 22.04 (Название команд может отличаться в зависимости от сборки на чем разворачивается проект Debian, Alpine, Linux и т.д.)

Для запуска приложения необходимо:

1. Создать и заполнить файлы config_kuber.yaml и secret_kuber.yaml по примерам config_kuber.yaml.example и secret_kuber.yaml.example
   - Для наполнения файлов необходимо обратиться к документации Google, Yandex и почтового провайдера для получения необходимых данных
2. Сделать файл project_development.sh исполняемым, командой `chmod +x project_development.sh`
3. Запустить скрипт командой `./project_development.sh`
4. Проверить запуск приложения командой `sudo kubectl get pods`

## API документация

Документация доступна по адресу: http://localhost:ваш_порт/apidocs

## Стэк технологий

- Python
- Python-jose
- Python-dotenv
- Flask
- Flask-JWT-Extended
- Flask-Admin
- Flask-Mail
- Flasgger
- PostgreSQL
- SQLAlchemy
- Psycopg2-binary
- Redis
- Kubernetes
- Alembic
- Pydantic
