from django.contrib import admin
from .models import Student, DanceDirection, Lesson, Subscription, SingleSession, AdminLog

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'created_at')
    search_fields = ('full_name', 'phone_number')
    list_filter = ('created_at',)

@admin.register(DanceDirection)
class DanceDirectionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('dance_direction', 'date', 'time', 'max_participants')
    list_filter = ('dance_direction', 'date')
    search_fields = ('dance_direction__name',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('student', 'start_date', 'end_date', 'sessions_remaining', 'type', 'confirmed_by_admin')
    list_filter = ('type', 'confirmed_by_admin')
    search_fields = ('student__full_name', 'type')

@admin.register(SingleSession)
class SingleSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'attended')
    list_filter = ('attended',)
    search_fields = ('student__full_name', 'lesson__dance_direction__name')

@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('admin_name', 'action', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('admin_name', 'action')
