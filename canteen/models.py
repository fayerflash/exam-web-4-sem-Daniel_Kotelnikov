from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date

class MealType(models.Model):
    name = models.CharField('Название', max_length=50)
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Тип питания'
        verbose_name_plural = 'Типы питания'

class Dish(models.Model):
    name = models.CharField('Название', max_length=200)
    meal_type = models.ForeignKey(MealType, on_delete=models.CASCADE, verbose_name='Тип питания')
    price = models.DecimalField('Цена', max_digits=8, decimal_places=2)
    description = models.TextField('Описание', blank=True)
    calories = models.IntegerField('Калории', blank=True, null=True)
    is_available = models.BooleanField('Доступно', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.price} руб."
    
    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'

class StudentProfile(models.Model):
    ALLERGY_CHOICES = [
        ('none', 'Нет аллергий'),
        ('milk', 'Молочные продукты'),
        ('gluten', 'Глютен'),
        ('nuts', 'Орехи'),
        ('eggs', 'Яйца'),
        ('fish', 'Рыба'),
        ('other', 'Другое'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    class_name = models.CharField('Класс', max_length=10)
    allergies = models.CharField('Аллергии', max_length=20, choices=ALLERGY_CHOICES, default='none')
    other_allergies = models.TextField('Другие аллергии', blank=True)
    dietary_preferences = models.TextField('Пищевые предпочтения', blank=True)
    balance = models.DecimalField('Баланс', max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.class_name}"
    
    class Meta:
        verbose_name = 'Профиль ученика'
        verbose_name_plural = 'Профили учеников'

class MealRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, verbose_name='Ученик')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, verbose_name='Блюдо')
    date = models.DateField('Дата', default=date.today)
    is_received = models.BooleanField('Получено', default=False)
    received_at = models.DateTimeField('Время получения', blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.dish.name} - {self.date}"
    
    class Meta:
        verbose_name = 'Учет питания'
        verbose_name_plural = 'Учет питания'

class Review(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, verbose_name='Ученик')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, verbose_name='Блюдо')
    rating = models.IntegerField('Оценка', validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.dish.name} - {self.rating}/5"
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

class Product(models.Model):
    name = models.CharField('Название', max_length=200)
    unit = models.CharField('Единица измерения', max_length=20)
    quantity = models.DecimalField('Остаток', max_digits=10, decimal_places=2, default=0)
    min_quantity = models.DecimalField('Минимальный остаток', max_digits=10, decimal_places=2, default=10)
    
    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit}"
    
    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Согласована'),
        ('rejected', 'Отклонена'),
        ('completed', 'Выполнена'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт')
    quantity = models.DecimalField('Количество', max_digits=10, decimal_places=2)
    reason = models.TextField('Причина закупки')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Кто создал', related_name='created_requests')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Кто согласовал', related_name='approved_requests')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    def __str__(self):
        return f"Заявка на {self.product.name} - {self.status}"
    
    class Meta:
        verbose_name = 'Заявка на закупку'
        verbose_name_plural = 'Заявки на закупку'

class Payment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, verbose_name='Ученик')
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    def __str__(self):
        return f"Платеж {self.student.user.get_full_name()} - {self.amount} руб."
    
    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'