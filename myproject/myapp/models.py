from django.db import models
from django.utils import timezone


class Student(models.Model):
    full_name = models.CharField(max_length=255, verbose_name='Полное имя')
    phone_number = models.CharField(max_length=15, unique=True, verbose_name='Номер телефона')
    chat_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name='ID чата')
    is_admin = models.BooleanField(default=False, verbose_name='Является администратором')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'


class DanceDirection(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Направление танца'
        verbose_name_plural = 'Направления танцев'


class Lesson(models.Model):
    dance_direction = models.ForeignKey(DanceDirection, on_delete=models.CASCADE, default=1, verbose_name='Направление танца')
    date = models.DateField(default=timezone.now, verbose_name='Дата')
    time = models.TimeField(default='00:00', verbose_name='Время')
    max_participants = models.IntegerField(default=10, verbose_name='Максимум участников')

    def __str__(self):
        return f"{self.dance_direction.name} - {self.date} в {self.time}"

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'


class Subscription(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='Студент')
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(verbose_name='Дата окончания')
    sessions_remaining = models.IntegerField(verbose_name='Оставшиеся занятия')
    type = models.CharField(max_length=20, choices=[('4 занятий', '4 занятий'), ('8 занятий', '8 занятий')], verbose_name='Тип')
    confirmed_by_admin = models.BooleanField(default=False, verbose_name='Подтверждено администратором')

    def __str__(self):
        return f"{self.student.full_name} - {self.type}"

    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'


class SingleSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='Студент')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Занятие')
    attended = models.BooleanField(default=False, verbose_name='Присутствовал')

    def __str__(self):
        return f"{self.student.full_name} - {self.lesson}"

    class Meta:
        verbose_name = 'Единичное посещение'
        verbose_name_plural = 'Единичные посещения'


class AdminLog(models.Model):
    admin_name = models.CharField(max_length=255, verbose_name='Имя администратора')
    action = models.TextField(verbose_name='Действие')
    timestamp = models.DateTimeField(default=timezone.now, verbose_name='Время действия')

    def __str__(self):
        return f"{self.admin_name} - {self.action} в {self.timestamp}"

    class Meta:
        verbose_name = 'Лог администратора'
        verbose_name_plural = 'Логи администраторов'
