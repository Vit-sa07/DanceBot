# DanceBot

**DanceBot** — это многофункциональный Telegram-бот и веб-приложение на Django для управления танцевальными занятиями, абонементами и участниками. Проект предназначен для упрощения взаимодействия между администрацией танцевальной студии и учениками.

**DanceBot** is a multifunctional Telegram bot and Django-based web application for managing dance classes, subscriptions, and participants. This project aims to simplify interactions between the dance studio administration and students.

## Основные возможности / Main Features

### Для учеников / For Students:
- Просмотр доступных направлений танцев. / View available dance directions.
- Запись на занятия. / Register for classes.
- Просмотр информации о своих абонементах. / View subscription details.
- Покупка новых абонементов. / Purchase new subscriptions.

### Для администраторов / For Administrators:
- Управление заявками на абонементы. / Manage subscription requests.
- Просмотр отчетов по студентам и занятиям. / View reports on students and classes.
- Управление расписанием занятий. / Manage class schedules.
- Просмотр записанных учеников на занятия. / View students registered for classes.

## Установка и запуск проекта / Installation and Running the Project

### Требования / Requirements

- Python 3.10+
- Docker и Docker Compose / Docker and Docker Compose

### Запуск в Docker / Running with Docker

1. Клонируйте репозиторий: / Clone the repository:

    ```bash
    git clone https://github.com/your-username/DanceBot.git
    cd DanceBot
    ```

2. Создайте файл `.env` и добавьте в него переменные окружения: / Create a `.env` file and add the environment variables:

    ```env
    DJANGO_SECRET_KEY=your-very-secure-and-long-secret-key
    TELEGRAM_BOT_TOKEN=your-telegram-bot-token
    ```

3. Соберите и запустите контейнеры Docker: / Build and start Docker containers:

    ```bash
    docker-compose up --build
    ```

4. Приложение будет доступно по адресу `http://localhost:8001`, а бот будет работать в фоне. / The application will be available at `http://localhost:8001`, and the bot will run in the background.

## Использование / Usage

- Администраторы могут управлять уроками и просматривать списки учеников. / Administrators can manage classes and view student lists.
- Ученики могут записываться на занятия и управлять своими абонементами через Telegram-бота. / Students can register for classes and manage their subscriptions via the Telegram bot.

## Переменные окружения / Environment Variables

- `DJANGO_SECRET_KEY` — секретный ключ Django. / Django secret key.
- `TELEGRAM_BOT_TOKEN` — токен для работы Telegram-бота. / Telegram bot token.

## Контакты / Contact

Если у вас есть вопросы или предложения, свяжитесь со мной по электронной почте: [sevav1507@gmail.com](mailto:sevav1507@gmail.com). / If you have any questions or suggestions, feel free to contact me at [sevav1507@gmail.com](mailto:sevav1507@gmail.com).
