from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import HttpResponse
from datetime import datetime, timedelta, date
from .models import *
import csv

def is_admin(user):
    return user.is_superuser or user.is_staff

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'canteen/login.html')

def user_logout(request):
    logout(request)
    return redirect('user_login')

def index(request):
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = date.today()
    context = {
        'total_students': StudentProfile.objects.count(),
        'total_dishes': Dish.objects.count(),
        'total_payments': Payment.objects.filter(created_at__date=today).aggregate(Sum('amount'))['amount__sum'] or 0,
        'today_meals': MealRecord.objects.filter(date=today, is_received=True).count(),
        'pending_requests': PurchaseRequest.objects.filter(status='pending').count(),
        'total_revenue': Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'recent_payments': Payment.objects.select_related('student__user').order_by('-created_at')[:10],
        'recent_requests': PurchaseRequest.objects.select_related('product', 'created_by').order_by('-created_at')[:10],
    }
    return render(request, 'canteen/admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_statistics(request):
    today = date.today()
    payments_by_day = []
    for i in range(30):
        day = today - timedelta(days=i)
        day_payments = Payment.objects.filter(created_at__date=day).aggregate(Sum('amount'))['amount__sum'] or 0
        payments_by_day.append({'date': day, 'amount': float(day_payments)})
    
    class_stats = StudentProfile.objects.values('class_name').annotate(
        count=Count('id'),
        total_payments=Sum('payment__amount')
    )
    
    popular_dishes = MealRecord.objects.filter(is_received=True).values('dish__name', 'dish__price').annotate(
        total_ordered=Count('id')
    ).order_by('-total_ordered')[:10]
    
    context = {
        'payments_by_day': payments_by_day,
        'total_revenue': Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'class_stats': class_stats,
        'total_students': StudentProfile.objects.count(),
        'total_meals': MealRecord.objects.filter(is_received=True).count(),
        'popular_dishes': popular_dishes,
    }
    return render(request, 'canteen/admin/statistics.html', context)

@login_required
@user_passes_test(is_admin)
def admin_purchase_requests(request):
    requests = PurchaseRequest.objects.select_related('product', 'created_by', 'approved_by').all().order_by('-created_at')
    products = Product.objects.all()
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        reason = request.POST.get('reason')
        product = get_object_or_404(Product, id=product_id)
        PurchaseRequest.objects.create(
            product=product,
            quantity=quantity,
            reason=reason,
            created_by=request.user
        )
        messages.success(request, f'Заявка на {product.name} создана')
        return redirect('admin_purchase_requests')
    
    return render(request, 'canteen/admin/purchase_requests.html', {'requests': requests, 'products': products})

@login_required
@user_passes_test(is_admin)
def approve_purchase_request(request, request_id):
    purchase_request = get_object_or_404(PurchaseRequest, id=request_id)
    purchase_request.status = 'approved'
    purchase_request.approved_by = request.user
    purchase_request.save()
    product = purchase_request.product
    product.quantity += purchase_request.quantity
    product.save()
    messages.success(request, f'Заявка на {purchase_request.product.name} согласована')
    return redirect('admin_purchase_requests')

@login_required
@user_passes_test(is_admin)
def reject_purchase_request(request, request_id):
    purchase_request = get_object_or_404(PurchaseRequest, id=request_id)
    purchase_request.status = 'rejected'
    purchase_request.approved_by = request.user
    purchase_request.save()
    messages.warning(request, f'Заявка на {purchase_request.product.name} отклонена')
    return redirect('admin_purchase_requests')

@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    return render(request, 'canteen/admin/reports.html')

@login_required
@user_passes_test(is_admin)
def report_meals(request):
    if request.method != 'POST':
        return redirect('admin_reports')

    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    if not start_date or not end_date:
        messages.error(request, 'Выберите даты для отчёта')
        return redirect('admin_reports')

    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    records = MealRecord.objects.filter(
        date__gte=start, date__lte=end, is_received=True
    ).select_related('student__user', 'dish', 'dish__meal_type')

    total_meals = records.count()
    total_cost = records.aggregate(total=Sum('dish__price'))['total'] or 0

    by_day = records.values('date').annotate(
        count=Count('id'),
        cost=Sum('dish__price')
    ).order_by('date')

    by_class = records.values('student__class_name').annotate(
        count=Count('id'),
        cost=Sum('dish__price')
    ).order_by('student__class_name')

    by_dish = records.values('dish__name', 'dish__price', 'dish__meal_type__name').annotate(
        count=Count('id'),
        total=Sum('dish__price')
    ).order_by('-count')

    by_student = records.values(
        'student__id',
        'student__user__first_name',
        'student__user__last_name',
        'student__user__username',
        'student__class_name',
    ).annotate(
        count=Count('id'),
        cost=Sum('dish__price')
    ).order_by('-count')

    unique_students = records.values('student__id').distinct().count()
    avg_per_student = round(total_meals / unique_students, 1) if unique_students else 0
    avg_cost = round(float(total_cost) / total_meals, 2) if total_meals else 0

    top_dishes   = list(by_dish)[:5]
    top_students = list(by_student)[:5]

    context = {
        'start_date': start,
        'end_date': end,
        'total_meals': total_meals,
        'total_cost': total_cost,
        'unique_students': unique_students,
        'avg_per_student': avg_per_student,
        'avg_cost': avg_cost,
        'by_day': by_day,
        'by_class': by_class,
        'by_dish': by_dish,
        'by_student': by_student,
        'top_dishes': top_dishes,
        'top_students': top_students,
    }
    return render(request, 'canteen/admin/report_meals.html', context)


@login_required
@user_passes_test(is_admin)
def report_costs(request):
    if request.method != 'POST':
        return redirect('admin_reports')

    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    if not start_date or not end_date:
        messages.error(request, 'Выберите даты для отчёта')
        return redirect('admin_reports')

    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    payments = Payment.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end
    ).select_related('student__user')

    meal_records = MealRecord.objects.filter(
        date__gte=start, date__lte=end, is_received=True
    ).select_related('student__user', 'dish')

    total_deposits = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_meal_cost = meal_records.aggregate(total=Sum('dish__price'))['total'] or 0

    payments_by_day = payments.values('created_at__date').annotate(
        amount=Sum('amount'),
        count=Count('id')
    ).order_by('created_at__date')

    meals_by_day = meal_records.values('date').annotate(
        cost=Sum('dish__price'),
        count=Count('id')
    ).order_by('date')

    dep_by_student = {
        item['student_id']: item
        for item in payments.values('student_id').annotate(deposits=Sum('amount'))
    }
    cost_by_student = {
        item['student_id']: item
        for item in meal_records.values('student_id').annotate(
            meal_cost=Sum('dish__price'), meals=Count('id')
        )
    }

    all_ids = set(dep_by_student) | set(cost_by_student)
    students_data = []
    for sid in all_ids:
        try:
            profile = StudentProfile.objects.select_related('user').get(id=sid)
        except StudentProfile.DoesNotExist:
            continue
        name = profile.user.get_full_name() or profile.user.username
        deposits = dep_by_student.get(sid, {}).get('deposits') or 0
        meal_cost = cost_by_student.get(sid, {}).get('meal_cost') or 0
        meals = cost_by_student.get(sid, {}).get('meals') or 0
        students_data.append({
            'name': name,
            'class_name': profile.class_name,
            'deposits': deposits,
            'meal_cost': meal_cost,
            'meals': meals,
            'net': deposits - meal_cost,
        })
    students_data.sort(key=lambda x: (x['class_name'], x['name']))

    context = {
        'start_date': start,
        'end_date': end,
        'total_deposits': total_deposits,
        'total_meal_cost': total_meal_cost,
        'net': total_deposits - total_meal_cost,
        'payments_count': payments.count(),
        'meals_count': meal_records.count(),
        'payments_by_day': payments_by_day,
        'meals_by_day': meals_by_day,
        'students_data': students_data,
    }
    return render(request, 'canteen/admin/report_costs.html', context)

@login_required
@user_passes_test(is_admin)
def admin_students(request):
    students = StudentProfile.objects.select_related('user').all()
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')
        student = get_object_or_404(StudentProfile, id=student_id)
        if action == 'delete':
            user = student.user
            student.delete()
            user.delete()
            messages.success(request, 'Ученик удален')
        elif action == 'add_balance':
            amount = float(request.POST.get('amount', 0))
            student.balance += amount
            student.save()
            Payment.objects.create(student=student, amount=amount)
            messages.success(request, f'Баланс пополнен на {amount} руб.')
        return redirect('admin_students')
    return render(request, 'canteen/admin/students.html', {'students': students})

@login_required
@user_passes_test(is_admin)
def admin_dishes(request):
    dishes = Dish.objects.select_related('meal_type').all()
    meal_types = MealType.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            Dish.objects.create(
                name=request.POST.get('name'),
                meal_type_id=request.POST.get('meal_type'),
                price=request.POST.get('price'),
                description=request.POST.get('description'),
                is_available=request.POST.get('is_available') == 'on'
            )
            messages.success(request, 'Блюдо добавлено')
        elif action == 'delete':
            Dish.objects.filter(id=request.POST.get('dish_id')).delete()
            messages.success(request, 'Блюдо удалено')
        return redirect('admin_dishes')
    
    return render(request, 'canteen/admin/dishes.html', {'dishes': dishes, 'meal_types': meal_types})

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all()
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, id=user_id)
        
        if action == 'make_admin':
            target_user.is_staff = True
            target_user.is_superuser = True
            target_user.save()
            messages.success(request, f'{target_user.username} назначен администратором')
        elif action == 'remove_admin':
            target_user.is_staff = False
            target_user.is_superuser = False
            target_user.save()
            messages.success(request, f'Права администратора у {target_user.username} отозваны')
        elif action == 'make_povar':
            target_user.is_staff = True
            target_user.save()
            messages.success(request, f'{target_user.username} назначен поваром')
        elif action == 'delete':
            if target_user != request.user:
                target_user.delete()
                messages.success(request, 'Пользователь удален')
        return redirect('admin_users')
    return render(request, 'canteen/admin/users.html', {'users': users})