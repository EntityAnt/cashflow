# Инструкция по установке и запуску веб-сервиса для управления движением денежных средств (ДДС)

---
### Требования:
- Python 3.8+
- PostgreSQL 12+
- Poetry 1.5+
---
### Шаги установки:

1. Клонировать репозиторий:
   git clone https://github.com/EntityAnt/cashflow.git

   cd cashflow-app

2. Установить зависимости и создать виртуальное окружение через poetry:  
   - poetry install

3. Активировать виртуальное окружение:  

   - poetry shell

4. Переименовать файл .env.sample в .env и заполнить его

5. Создать базу данных PostgresQL

   - Применить миграции:
```bash
        python manage.py migrate    
```

6. Создать суперпользователя (для доступа к админке):
```bash
        python manage.py create_admin
```

7. Запустить сервер разработки:
```bash
        python manage.py runserver
```

8. Открыть в браузере:
   http://127.0.0.1:8000/
---
### Дополнительные команды:

- Обновление зависимостей: poetry update

- Создание фикстур: python manage.py dumpdata --indent=4 > fixtures/initial_data.json

- Загрузка фикстур: python manage.py loaddata fixtures/initial_data.json

- Документация по API
  * http://127.0.0.1:8000/redoc/
  * http://127.0.0.1:8000/swagger/


Конфигурация БД:
    - Для тестов используется SQLite, для приложения PostgreSQL.