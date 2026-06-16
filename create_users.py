import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_canteen.settings')
import django
django.setup()
from django.contrib.auth.models import User
from canteen.models import StudentProfile, MealType, Product

if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    admin.first_name = 'Администратор'
    admin.last_name = 'Системы'
    admin.save()
    print("Суперпользователь admin создан")

if not User.objects.filter(username='user').exists():
    user = User.objects.create_user('user', 'user@example.com', 'user')
    user.first_name = 'Иван'
    user.last_name = 'Петров'
    user.save()
    StudentProfile.objects.create(
        user=user,
        class_name='10А',
        allergies='none',
        balance=5000
    )
    print("Пользователь user создан (ученик)")

if not User.objects.filter(username='povar').exists():
    povar = User.objects.create_user('povar', 'povar@example.com', 'povar')
    povar.first_name = 'Мария'
    povar.last_name = 'Иванова'
    povar.is_staff = True
    povar.save()
    print("Пользователь povar создан (повар)")

if MealType.objects.count() == 0:
    MealType.objects.create(name='Завтрак', start_time='08:00', end_time='10:00')
    MealType.objects.create(name='Обед', start_time='12:00', end_time='14:00')
    print("Типы питания созданы")

if Product.objects.count() == 0:
    Product.objects.create(name='Картофель', unit='кг', quantity=100, min_quantity=20)
    Product.objects.create(name='Мясо', unit='кг', quantity=50, min_quantity=10)
    Product.objects.create(name='Молоко', unit='л', quantity=80, min_quantity=15)
    print("Продукты созданы")

print("Готово!")