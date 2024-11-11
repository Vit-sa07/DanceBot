import telebot
from telebot import types
from django.utils import timezone
import os
import django
import pandas as pd
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()
from myapp.models import Student, DanceDirection, Lesson, Subscription, SingleSession

# Получение токена из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Инициализация бота с использованием токена из окружения
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    user = Student.objects.filter(chat_id=chat_id).first()
    if user:
        if user.is_admin:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                types.KeyboardButton('🔍 Проверить запросы на абонементы'),
                types.KeyboardButton('📊 Отчеты'),
                types.KeyboardButton('📅 Расписание'),
                types.KeyboardButton('🗓 Управление занятиями'),
                types.KeyboardButton('💃 Управление направлениями танца')
            )
            bot.send_message(chat_id, "Здравствуйте, Администратор!", reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                types.KeyboardButton('📚 Доступные уроки'),
                types.KeyboardButton('💳 Мой абонемент'),
                types.KeyboardButton('💳 Купить абонемент')
            )
            bot.send_message(chat_id, f"Здравствуйте, {user.full_name}! Добро пожаловать в бот.", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('Поделиться номером телефона', request_contact=True))
        bot.send_message(chat_id, "Пожалуйста, поделитесь своим номером телефона для регистрации.", reply_markup=markup)



@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    if message.contact:
        phone_number = message.contact.phone_number
        chat_id = message.chat.id
        bot.send_message(chat_id, "Пожалуйста, введите ваше ФИО для завершения регистрации.")
        bot.register_next_step_handler(message, lambda msg: register_user(msg, phone_number, chat_id))

def register_user(message, phone_number, chat_id):
    full_name = message.text.strip()
    if full_name:
        Student.objects.create(full_name=full_name, phone_number=phone_number, chat_id=chat_id, created_at=timezone.now())
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton('📚 Доступные уроки'),
            types.KeyboardButton('🗓 Записаться на урок'),
            types.KeyboardButton('💳 Купить абонемент')
        )
        bot.send_message(chat_id, f"Регистрация успешна! Добро пожаловать, {full_name}.", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Ошибка: ФИО не может быть пустым. Попробуйте снова.")


@bot.message_handler(func=lambda message: message.text == '📚 Доступные уроки')
def show_dance_directions(message):
    directions = DanceDirection.objects.all()
    if directions:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for direction in directions:
            markup.add(types.KeyboardButton(direction.name))
        markup.add(types.KeyboardButton('🔙 Назад'))
        bot.send_message(message.chat.id, "Выберите направление танца:", reply_markup=markup)
        bot.register_next_step_handler(message, select_lesson_time)
    else:
        bot.send_message(message.chat.id, "На данный момент направлений танца нет.")


def select_lesson_time(message):
    if message.text == '🔙 Назад':
        back_to_main_menu(message)
        return

    selected_direction = message.text
    dance_direction = DanceDirection.objects.filter(name=selected_direction).first()
    if dance_direction:
        lessons = Lesson.objects.filter(dance_direction=dance_direction)
        if lessons:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for lesson in lessons:
                lesson_info = f"{lesson.date} в {lesson.time}"
                markup.add(types.KeyboardButton(lesson_info))
            markup.add(types.KeyboardButton('🔙 Назад'))
            bot.send_message(message.chat.id, f"Выберите время для {selected_direction}:", reply_markup=markup)
            bot.register_next_step_handler(message, lambda msg: book_lesson(msg, dance_direction))
        else:
            bot.send_message(message.chat.id, f"На данный момент уроков по {selected_direction} нет.")
    else:
        bot.send_message(message.chat.id, "Выбранное направление не найдено. Пожалуйста, попробуйте снова.")


def book_lesson(message, dance_direction):
    if message.text == '🔙 Назад':
        show_dance_directions(message)
        return

    try:
        lesson_info = message.text.strip()

        if 'ID: ' not in lesson_info:
            raise ValueError("Неверный формат ввода. Ожидается формат с 'ID: '.")

        lesson_id_str = lesson_info.split('ID: ')[1].split()[0]

        lesson_id = int(lesson_id_str.replace(')', ''))

        lesson = Lesson.objects.get(id=lesson_id)
        student = Student.objects.get(chat_id=message.chat.id)
        subscription = Subscription.objects.filter(student=student, confirmed_by_admin=True).first()

        if subscription and subscription.sessions_remaining > 0:
            SingleSession.objects.create(student=student, lesson=lesson)
            subscription.sessions_remaining -= 1
            subscription.save()
            bot.send_message(message.chat.id,
                             f"Вы успешно записались на {lesson.dance_direction.name} {lesson.date} в {lesson.time}. Осталось занятий: {subscription.sessions_remaining}.")

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                types.KeyboardButton('📚 Доступные уроки'),
                types.KeyboardButton('💳 Мой абонемент'),
                types.KeyboardButton('💳 Купить абонемент')
            )
            bot.send_message(message.chat.id, "Возвращаюсь в главное меню.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "У вас недостаточно оставшихся занятий или нет активного абонемента.")
    except ValueError as ve:
        bot.send_message(message.chat.id, f"Ошибка! {ve}")
    except Lesson.DoesNotExist:
        bot.send_message(message.chat.id, "Ошибка! Занятие не найдено.")
    except Student.DoesNotExist:
        bot.send_message(message.chat.id, "Ошибка! Студент не найден. Пожалуйста, зарегистрируйтесь.")
    except IndexError:
        bot.send_message(message.chat.id, "Ошибка! Проверьте правильность введенных данных и повторите попытку.")


@bot.message_handler(func=lambda message: message.text == '💳 Купить абонемент')
def buy_subscription(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton('Абонемент на 4 занятия (2800 р)'),
        types.KeyboardButton('Абонемент на 8 занятий (5300 р)'),
        types.KeyboardButton('Разовое занятие (750 р)'),
        types.KeyboardButton('🔙 Назад')
    )
    bot.send_message(message.chat.id, "Выберите тип абонемента:", reply_markup=markup)
    bot.register_next_step_handler(message, process_subscription_selection)


@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
def back_to_main_menu(message):
    chat_id = message.chat.id
    user = Student.objects.filter(chat_id=chat_id).first()

    if user:
        if user.is_admin:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                types.KeyboardButton('🔍 Проверить запросы на абонементы'),
                types.KeyboardButton('📊 Отчеты'),
                types.KeyboardButton('📅 Расписание'),
                types.KeyboardButton('🗓 Управление занятиями'),
                types.KeyboardButton('💃 Управление направлениями танца')
            )
            bot.send_message(chat_id, "Главное меню администратора:", reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                types.KeyboardButton('📚 Доступные уроки'),
                types.KeyboardButton('💳 Мой абонемент'),
                types.KeyboardButton('💳 Купить абонемент')
            )
            bot.send_message(chat_id, "Главное меню:", reply_markup=markup)


def process_subscription_selection(message):
    student = Student.objects.get(chat_id=message.chat.id)
    if message.text == 'Абонемент на 4 занятия (2800 р)':
        subscription = Subscription.objects.create(
            student=student,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            sessions_remaining=4,
            type='4 занятий',
            confirmed_by_admin=False
        )
        notify_admins(subscription, message)
        bot.send_message(
            message.chat.id,
            "Ваш запрос на покупку абонемента на 4 занятия отправлен администратору. Пожалуйста, оплатите по номеру телефона администратора для подтверждения."
        )
    elif message.text == 'Абонемент на 8 занятий (5300 р)':
        subscription = Subscription.objects.create(
            student=student,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            sessions_remaining=8,
            type='8 занятий',
            confirmed_by_admin=False
        )
        notify_admins(subscription, message)
        bot.send_message(
            message.chat.id,
            "Ваш запрос на покупку абонемента на 8 занятий отправлен администратору. Пожалуйста, оплатите по номеру телефона администратора для подтверждения."
        )
    elif message.text == 'Разовое занятие (750 р)':
        subscription = Subscription.objects.create(
            student=student,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
            sessions_remaining=1,
            type='Разовое',
            confirmed_by_admin=False
        )
        notify_admins(subscription, message)
        bot.send_message(
            message.chat.id,
            "Ваш запрос на разовое занятие отправлен администратору. Пожалуйста, оплатите по номеру телефона администратора для подтверждения."
        )
    elif message.text == '🔙 Назад':
        back_to_main_menu(message)
    else:
        bot.send_message(message.chat.id, "Ошибка! Пожалуйста, выберите доступный тип абонемента.")


def notify_admins(subscription, message):
    admin_users = Student.objects.filter(is_admin=True)
    for admin in admin_users:
        bot.send_message(admin.chat_id, f"Новый запрос на абонемент от {subscription.student.full_name} ({subscription.student.phone_number}). Тип: {subscription.type}. Подтвердите его, если оплата получена.")


@bot.message_handler(func=lambda message: message.text == '🔍 Проверить запросы на абонементы')
def review_subscription_requests(message):
    admin_user = Student.objects.filter(chat_id=message.chat.id, is_admin=True).first()
    if admin_user:
        pending_subscriptions = Subscription.objects.filter(confirmed_by_admin=False)
        if pending_subscriptions.exists():
            for subscription in pending_subscriptions:
                approve_button = types.InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'approve_{subscription.id}')
                decline_button = types.InlineKeyboardButton(text='❌ Отклонить', callback_data=f'decline_{subscription.id}')
                markup = types.InlineKeyboardMarkup().add(approve_button, decline_button)
                bot.send_message(
                    message.chat.id,
                    f"Запрос от {subscription.student.full_name} ({subscription.student.phone_number}): {subscription.type}",
                    reply_markup=markup
                )
        else:
            bot.send_message(message.chat.id, "Нет ожидающих подтверждения запросов на абонементы.")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('decline_'))
def handle_admin_response(call):
    subscription_id = int(call.data.split('_')[1])
    subscription = Subscription.objects.get(id=subscription_id)

    if call.data.startswith('approve_'):
        subscription.confirmed_by_admin = True
        subscription.save()
        bot.send_message(call.message.chat.id, f"Запрос на абонемент для {subscription.student.full_name} подтвержден.")
        bot.send_message(subscription.student.chat_id, f"Ваш абонемент {subscription.type} подтвержден администратором.")
    elif call.data.startswith('decline_'):
        subscription.delete()
        bot.send_message(call.message.chat.id, f"Запрос на абонемент для {subscription.student.full_name} отклонен.")
        bot.send_message(subscription.student.chat_id, "Ваш запрос на абонемент был отклонен администратором.")


@bot.message_handler(func=lambda message: message.text == '📊 Отчеты')
def handle_reports(message):
    if Student.objects.filter(chat_id=message.chat.id, is_admin=True).exists():
        subscriptions = Subscription.objects.all()
        report_data = []
        for subscription in subscriptions:
            student = subscription.student
            lessons_attended = SingleSession.objects.filter(student=student).count()
            report_data.append({
                'ФИО': student.full_name,
                'Номер телефона': student.phone_number,
                'Тип абонемента': subscription.type,
                'Начало абонемента': subscription.start_date,
                'Окончание абонемента': subscription.end_date,
                'Занятий осталось': subscription.sessions_remaining,
                'Занятий посещено': lessons_attended
            })

        df = pd.DataFrame(report_data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Отчет')
        output.seek(0)

        bot.send_document(message.chat.id, document=output, visible_file_name='Отчет_занятий.xlsx')
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")


@bot.message_handler(func=lambda message: message.text == '🗓 Управление занятиями')
def handle_manage_lessons(message):
    if Student.objects.filter(chat_id=message.chat.id, is_admin=True).exists():
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('Добавить занятие', callback_data='select_direction_add_lesson'),
            types.InlineKeyboardButton('Удалить занятие', callback_data='select_direction_delete_lesson'),
            types.InlineKeyboardButton('Просмотреть все занятия', callback_data='view_lessons')
        )
        bot.send_message(message.chat.id, "Выберите действие для управления занятиями:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")


@bot.message_handler(func=lambda message: message.text == '💃 Управление направлениями танца')
def handle_manage_dance_directions(message):
    if Student.objects.filter(chat_id=message.chat.id, is_admin=True).exists():
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('Добавить направление', callback_data='add_direction'),
            types.InlineKeyboardButton('Удалить направление', callback_data='select_direction_delete_direction'),
            types.InlineKeyboardButton('Просмотреть все направления', callback_data='view_directions')
        )
        bot.send_message(message.chat.id, "Выберите действие для управления направлениями танца:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")


def show_dance_directions_inline(chat_id, action):
    directions = DanceDirection.objects.all()
    if directions.exists():
        markup = types.InlineKeyboardMarkup()
        for direction in directions:
            markup.add(types.InlineKeyboardButton(direction.name, callback_data=f'{action}_{direction.id}'))
        bot.send_message(chat_id, "Выберите направление танца:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Направлений танца пока нет.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_direction_') or call.data in ['add_direction', 'view_lessons', 'view_directions'])
def handle_admin_callbacks(call):
    if call.data.startswith('select_direction_add_lesson'):
        show_dance_directions_inline(call.message.chat.id, 'add_lesson')
    elif call.data.startswith('select_direction_delete_lesson'):
        show_dance_directions_inline(call.message.chat.id, 'select_delete_lesson')
    elif call.data.startswith('select_direction_delete_direction'):
        show_dance_directions_inline(call.message.chat.id, 'delete_direction')
    elif call.data == 'add_direction':
        bot.send_message(call.message.chat.id, "Введите название нового направления танца.")
        bot.register_next_step_handler(call.message, process_add_dance_direction)
    elif call.data == 'view_lessons':
        view_lessons(call.message)
    elif call.data == 'view_directions':
        view_dance_directions(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_lesson_'))
def process_add_lesson_callback(call):
    try:
        direction_id = int(call.data.split('_')[-1].replace(')', '').strip())
        direction = DanceDirection.objects.get(id=direction_id)
        bot.send_message(call.message.chat.id, f"Вы выбрали направление: {direction.name}. Теперь введите дату и время занятия в формате: YYYY-MM-DD, HH:MM")
        bot.register_next_step_handler(call.message, lambda msg: save_lesson(msg, direction))
    except ValueError:
        bot.send_message(call.message.chat.id, "Ошибка! Неверный формат ID.")
    except DanceDirection.DoesNotExist:
        bot.send_message(call.message.chat.id, "Ошибка! Указанное направление не найдено.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_delete_lesson'))
def handle_select_delete_lesson(call):
    try:
        lessons = Lesson.objects.all()
        if lessons.exists():
            markup = types.InlineKeyboardMarkup()
            for lesson in lessons:
                button_text = f"{lesson.date} {lesson.time} (ID: {lesson.id})"
                markup.add(types.InlineKeyboardButton(button_text, callback_data=f'delete_lesson_confirm_{lesson.id}'))
            bot.send_message(call.message.chat.id, "Выберите занятие для удаления:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "Занятий пока нет.")
    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка.")
        print(f"Произошла ошибка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_lesson_confirm'))
def process_delete_lesson(call):
    try:
        lesson_id = int(call.data.split('_')[-1])
        lesson = Lesson.objects.get(id=lesson_id)
        lesson.delete()
        bot.send_message(call.message.chat.id, f"Занятие с ID {lesson_id} успешно удалено.")
        bot.answer_callback_query(call.id, "Занятие удалено.")
    except Lesson.DoesNotExist:
        bot.send_message(call.message.chat.id, "Ошибка! Занятие не найдено.")
        bot.answer_callback_query(call.id, "Ошибка! Занятие не найдено.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Произошла ошибка при удалении занятия: {e}")
        bot.answer_callback_query(call.id, f"Ошибка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_direction_'))
def process_delete_dance_direction_callback(call):
    direction_id = int(call.data.split('_')[-1])
    try:
        direction = DanceDirection.objects.get(id=direction_id)
        direction.delete()
        bot.send_message(call.message.chat.id, f"Направление '{direction.name}' успешно удалено.")
    except DanceDirection.DoesNotExist:
        bot.send_message(call.message.chat.id, "Ошибка! Указанное направление не найдено.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_direction_'))
def handle_select_direction(call):
    direction_id = int(call.data.split('_')[-1])
    direction = DanceDirection.objects.get(id=direction_id)
    call.message.text = direction.name
    process_add_lesson(call.message)

def process_add_lesson(message):
    direction_name = message.text
    try:
        direction = DanceDirection.objects.get(name=direction_name)
        bot.send_message(message.chat.id, f"Вы выбрали направление: {direction_name}. Теперь введите дату и время занятия в формате: YYYY-MM-DD, HH:MM")
        bot.register_next_step_handler(message, lambda msg: save_lesson(msg, direction))
    except DanceDirection.DoesNotExist:
        bot.send_message(message.chat.id, "Ошибка! Указанное направление не найдено.")

def save_lesson(message, direction):
    try:
        date_str, time_str = message.text.split(', ')
        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        time = timezone.datetime.strptime(time_str, '%H:%M').time()
        lesson = Lesson.objects.create(dance_direction=direction, date=date, time=time)
        print(f"Отладка: добавлено занятие с ID {lesson.id}, direction_id={lesson.dance_direction.id}")
        bot.send_message(message.chat.id, f"Занятие по направлению '{direction.name}' успешно добавлено на {date} в {time}.")
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка! Неправильный формат даты и времени.")


def view_lessons(message):
    lessons = Lesson.objects.all()
    if lessons.exists():
        response = "Все занятия:\n"
        for lesson in lessons:
            response += f"ID: {lesson.id}, Направление: {lesson.dance_direction.name}, Дата: {lesson.date}, Время: {lesson.time}\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Занятий пока нет.")


def process_add_dance_direction(message):
    name = message.text.strip()
    if name:
        DanceDirection.objects.create(name=name)
        bot.send_message(message.chat.id, f"Направление '{name}' успешно добавлено.")
    else:
        bot.send_message(message.chat.id, "Ошибка! Название направления не может быть пустым.")


def view_dance_directions(message):
    directions = DanceDirection.objects.all()
    if directions.exists():
        response = "Все направления танца:\n"
        for direction in directions:
            response += f"{direction.name}\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Направлений танца пока нет.")


def process_delete_dance_direction(message):
    direction_name = message.text.strip()
    try:
        direction = DanceDirection.objects.get(name=direction_name)
        direction.delete()
        bot.send_message(message.chat.id, f"Направление '{direction_name}' успешно удалено.")
    except DanceDirection.DoesNotExist:
        bot.send_message(message.chat.id, "Ошибка! Указанное направление не найдено.")


@bot.message_handler(func=lambda message: message.text == '📅 Расписание')
def handle_view_schedule(message):
    if Student.objects.filter(chat_id=message.chat.id, is_admin=True).exists():
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('На день', callback_data='schedule_day'),
            types.InlineKeyboardButton('На неделю', callback_data='schedule_week'),
            types.InlineKeyboardButton('На месяц', callback_data='schedule_month')
        )
        bot.send_message(message.chat.id, "Выберите период для просмотра расписания:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для выполнения этой команды.")


@bot.callback_query_handler(func=lambda call: call.data in ['schedule_day', 'schedule_week', 'schedule_month'])
def show_schedule(call):
    from datetime import datetime, timedelta

    today = timezone.now().date()

    if call.data == 'schedule_day':
        start_date = today
        end_date = today
        period = 'день'
        period_emoji = '📅'
    elif call.data == 'schedule_week':
        start_date = today
        end_date = today + timedelta(days=6)
        period = 'неделю'
        period_emoji = '🗓'
    elif call.data == 'schedule_month':
        start_date = today
        end_date = (today + timedelta(days=30)).replace(day=1) - timedelta(days=1)
        period = 'месяц'
        period_emoji = '📆'

    lessons = Lesson.objects.filter(date__range=[start_date, end_date]).order_by('date', 'time')

    if lessons.exists():
        response = f"{period_emoji} Расписание на {period} (с {start_date} по {end_date}):\n"
        for lesson in lessons:
            lesson_time = lesson.time.strftime('%H:%M')
            participants = SingleSession.objects.filter(lesson=lesson).select_related('student')

            if participants.exists():
                participant_names = ', '.join([participant.student.full_name for participant in participants])
                response += f"🕒 {lesson.date} {lesson_time} - {lesson.dance_direction.name} 💃\n"
                response += f"👥 Участники: {participant_names}\n"
            else:
                response += f"🕒 {lesson.date} {lesson_time} - {lesson.dance_direction.name} 💃\n"
                response += "👥 Участники: никого нет\n"
    else:
        response = f"Нет занятий на выбранный период ({period})."

    bot.send_message(call.message.chat.id, response)
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.text == '💳 Мой абонемент')
def show_subscription_info(message):
    chat_id = message.chat.id
    student = Student.objects.filter(chat_id=chat_id).first()

    if student:
        subscription = Subscription.objects.filter(student=student, confirmed_by_admin=True).first()
        if subscription:
            response = (f"💳 Информация о вашем абонементе:\n"
                        f"Тип: {subscription.type}\n"
                        f"Начало: {subscription.start_date}\n"
                        f"Окончание: {subscription.end_date}\n"
                        f"Оставшиеся занятия: {subscription.sessions_remaining}\n")
        else:
            response = "У вас нет активного абонемента."
    else:
        response = "Ошибка! Студент не найден. Пожалуйста, зарегистрируйтесь."

    bot.send_message(chat_id, response)


bot.polling(none_stop=True)

