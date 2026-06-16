from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from .models import (
    MealType, Dish, StudentProfile, MealRecord,
    Review, Product, PurchaseRequest, Payment,
)

admin.site.site_header = "Школьная столовая"
admin.site.site_title = "Администрирование"
admin.site.index_title = "Управление системой"


# ── User + StudentProfile inline ──────────────────────────────────────────────

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name = "Профиль ученика"
    verbose_name_plural = "Профиль ученика"
    fields = ('class_name', 'allergies', 'other_allergies', 'dietary_preferences', 'balance')

class CustomUserAdmin(UserAdmin):
    inlines = [StudentProfileInline]
    list_display = ('username', 'get_full_name', 'email', 'get_role', 'is_active')
    list_filter = ('is_superuser', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    @admin.display(description='Роль')
    def get_role(self, obj):
        if obj.is_superuser:
            return format_html('<span style="color:#7c3aed;font-weight:600;">👑 Администратор</span>')
        if obj.is_staff:
            return format_html('<span style="color:#059669;font-weight:600;">🍳 Повар</span>')
        return format_html('<span style="color:#2563eb;">👨‍🎓 Ученик</span>')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ── MealType ──────────────────────────────────────────────────────────────────

@admin.register(MealType)
class MealTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')


# ── Dish ──────────────────────────────────────────────────────────────────────

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal_type', 'price', 'calories', 'get_status')
    list_filter = ('meal_type', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('price', 'calories')
    ordering = ('meal_type', 'name')
    fields = ('name', 'meal_type', 'price', 'calories', 'description', 'is_available')

    @admin.display(description='Статус', boolean=False)
    def get_status(self, obj):
        if obj.is_available:
            return mark_safe('<span style="color:#059669;font-weight:600;">✅ Доступно</span>')
        return mark_safe('<span style="color:#dc2626;">❌ Недоступно</span>')

    actions = ['make_available', 'make_unavailable']

    @admin.action(description='Сделать доступными')
    def make_available(self, request, queryset):
        queryset.update(is_available=True)
        self.message_user(request, f'Обновлено: {queryset.count()} блюд')

    @admin.action(description='Сделать недоступными')
    def make_unavailable(self, request, queryset):
        queryset.update(is_available=False)
        self.message_user(request, f'Обновлено: {queryset.count()} блюд')


# ── StudentProfile ────────────────────────────────────────────────────────────

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    fields = ('amount', 'created_at')
    readonly_fields = ('created_at',)
    verbose_name = "Пополнение баланса"
    verbose_name_plural = "Пополнения баланса"

class MealRecordInline(admin.TabularInline):
    model = MealRecord
    extra = 0
    fields = ('dish', 'date', 'is_received', 'received_at')
    readonly_fields = ('received_at',)
    verbose_name = "Запись питания"
    verbose_name_plural = "Записи питания"
    show_change_link = True

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'class_name', 'allergies', 'get_balance', 'get_meals_count')
    list_filter = ('class_name', 'allergies')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'class_name')
    list_editable = ('class_name',)
    ordering = ('class_name', 'user__last_name')
    inlines = [PaymentInline, MealRecordInline]
    fields = ('user', 'class_name', 'allergies', 'other_allergies', 'dietary_preferences', 'balance')
    readonly_fields = ('user',)

    @admin.display(description='ФИО', ordering='user__last_name')
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description='Баланс')
    def get_balance(self, obj):
        color = '#059669' if obj.balance >= 0 else '#dc2626'
        return format_html('<span style="color:{};font-weight:600;">{} ₽</span>', color, obj.balance)

    @admin.display(description='Порций получено')
    def get_meals_count(self, obj):
        return MealRecord.objects.filter(student=obj, is_received=True).count()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# ── MealRecord ────────────────────────────────────────────────────────────────

@admin.register(MealRecord)
class MealRecordAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'get_class', 'dish', 'date', 'is_received', 'get_status', 'received_at')
    list_filter = ('is_received', 'date', 'dish__meal_type', 'student__class_name')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'dish__name')
    date_hierarchy = 'date'
    list_editable = ('is_received',)
    ordering = ('-date', 'student__class_name')

    @admin.display(description='Ученик', ordering='student__user__last_name')
    def get_student(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username

    @admin.display(description='Класс')
    def get_class(self, obj):
        return obj.student.class_name

    @admin.display(description='Статус')
    def get_status(self, obj):
        if obj.is_received:
            return mark_safe('<span style="color:#059669;font-weight:600;">✅ Получено</span>')
        return mark_safe('<span style="color:#9ca3af;">⏳ Не получено</span>')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student__user', 'dish', 'dish__meal_type'
        )


# ── Review ────────────────────────────────────────────────────────────────────

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'dish', 'get_stars', 'comment', 'created_at')
    list_filter = ('rating', 'dish')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'dish__name', 'comment')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    @admin.display(description='Ученик')
    def get_student(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username

    @admin.display(description='Оценка')
    def get_stars(self, obj):
        stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span title="{}/5">{}</span>', obj.rating, stars)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user', 'dish')


# ── Product ───────────────────────────────────────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_quantity', 'unit', 'min_quantity', 'get_stock_status')
    search_fields = ('name',)
    list_editable = ('min_quantity',)
    ordering = ('name',)

    @admin.display(description='Остаток')
    def get_quantity(self, obj):
        color = '#dc2626' if obj.quantity <= obj.min_quantity else '#059669'
        return format_html('<span style="color:{};font-weight:600;">{} {}</span>', color, obj.quantity, obj.unit)

    @admin.display(description='Статус склада')
    def get_stock_status(self, obj):
        if obj.quantity <= obj.min_quantity:
            return mark_safe('<span style="color:#dc2626;font-weight:600;">⚠️ Мало</span>')
        return mark_safe('<span style="color:#059669;">✅ В норме</span>')


# ── PurchaseRequest ───────────────────────────────────────────────────────────

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'get_status_badge', 'created_by', 'approved_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product__name', 'reason', 'created_by__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'approved_by')
    ordering = ('-created_at',)
    fields = ('product', 'quantity', 'reason', 'status', 'created_by', 'approved_by', 'created_at', 'updated_at')

    @admin.display(description='Статус')
    def get_status_badge(self, obj):
        colors = {
            'pending':  ('#d97706', '⏳ На рассмотрении'),
            'approved': ('#059669', '✅ Согласована'),
            'rejected': ('#dc2626', '❌ Отклонена'),
            'completed':('#7c3aed', '✔️ Выполнена'),
        }
        color, label = colors.get(obj.status, ('#6b7280', obj.status))
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, label)

    actions = ['approve_requests', 'reject_requests', 'mark_completed']

    @admin.action(description='✅ Согласовать выбранные заявки')
    def approve_requests(self, request, queryset):
        pending = queryset.filter(status='pending')
        for pr in pending:
            pr.status = 'approved'
            pr.approved_by = request.user
            pr.save()
            pr.product.quantity += pr.quantity
            pr.product.save()
        self.message_user(request, f'Согласовано: {pending.count()} заявок')

    @admin.action(description='❌ Отклонить выбранные заявки')
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'Отклонено: {updated} заявок')

    @admin.action(description='✔️ Пометить как выполненные')
    def mark_completed(self, request, queryset):
        updated = queryset.filter(status='approved').update(status='completed')
        self.message_user(request, f'Выполнено: {updated} заявок')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'created_by', 'approved_by')


# ── Payment ───────────────────────────────────────────────────────────────────

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'get_class', 'amount', 'created_at')
    list_filter = ('created_at', 'student__class_name')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__user__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    @admin.display(description='Ученик', ordering='student__user__last_name')
    def get_student(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username

    @admin.display(description='Класс')
    def get_class(self, obj):
        return obj.student.class_name

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user')
