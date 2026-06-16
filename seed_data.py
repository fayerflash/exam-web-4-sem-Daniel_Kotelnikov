"""
Запуск: python seed_data.py
Наполняет БД: типы питания, 40+ блюд, 30 учеников, записи питания по месяцам (6 мес.)
"""
import os, sys, django, random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_canteen.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User
from canteen.models import MealType, Dish, StudentProfile, MealRecord, Payment

# ── 1. Типы питания ──────────────────────────────────────────────────────────
MEAL_TYPES_DATA = [
    ('Завтрак',  '08:00', '09:00'),
    ('Обед',     '12:00', '13:30'),
    ('Полдник',  '15:00', '15:30'),
    ('Ужин',     '18:00', '19:00'),
]

meal_types = {}
for name, start, end in MEAL_TYPES_DATA:
    mt, _ = MealType.objects.get_or_create(
        name=name,
        defaults={'start_time': start, 'end_time': end}
    )
    meal_types[name] = mt
print(f"✓ Типов питания: {MealType.objects.count()}")

# ── 2. Блюда (40+ штук) ──────────────────────────────────────────────────────
DISHES = [
    # --- Завтрак ---
    ('Овсяная каша с ягодами',      'Завтрак',  45,  'Классическая овсянка на молоке с клубникой и черникой', 320),
    ('Гречневая каша с маслом',     'Завтрак',  40,  'Рассыпчатая гречка с топлёным маслом',                  290),
    ('Омлет с сыром',               'Завтрак',  55,  'Пышный омлет из 2 яиц с твёрдым сыром',                 380),
    ('Творожная запеканка',         'Завтрак',  50,  'Нежная запеканка из творога с изюмом',                  350),
    ('Блины со сметаной',           'Завтрак',  60,  'Тонкие блины, 3 шт., подаются со сметаной',             410),
    ('Сырники с вареньем',          'Завтрак',  65,  'Жареные сырники из творога с клубничным вареньем',      430),
    ('Манная каша с маслом',        'Завтрак',  35,  'Нежная манка на молоке с кусочком масла',               270),
    ('Яйцо варёное + хлеб',        'Завтрак',  30,  'Яйцо вкрутую, хлеб пшеничный, масло',                  210),
    ('Пшённая каша с тыквой',       'Завтрак',  42,  'Пшённая каша на молоке с тыквенным пюре',               300),
    ('Кукурузная каша',             'Завтрак',  40,  'Кукурузная каша на молоке с маслом',                    280),

    # --- Обед ---
    ('Борщ со сметаной',            'Обед',     70,  'Наваристый борщ со свёклой, капустой и сметаной',       420),
    ('Щи из свежей капусты',        'Обед',     65,  'Лёгкие щи на курином бульоне',                          380),
    ('Куриный суп с лапшой',        'Обед',     60,  'Суп на куриного бульоне с домашней лапшой',             350),
    ('Рассольник',                  'Обед',     65,  'Суп с перловкой и солёными огурцами',                   360),
    ('Гороховый суп',               'Обед',     55,  'Густой гороховый суп с копчёностями',                   390),
    ('Котлета с картофельным пюре', 'Обед',     85,  'Котлета мясная, пюре из картофеля, подлива',            520),
    ('Тефтели в томатном соусе',    'Обед',     80,  'Тефтели из говядины в томатно-сметанном соусе',         480),
    ('Рыба запечённая с рисом',     'Обед',     90,  'Минтай, запечённый в духовке, с отварным рисом',        440),
    ('Гуляш с макаронами',          'Обед',     85,  'Говяжий гуляш с подливой и макаронами',                 510),
    ('Куриная грудка с гречкой',    'Обед',     95,  'Запечённая куриная грудка с гречневым гарниром',        480),
    ('Плов с курицей',              'Обед',     90,  'Классический плов с куриным мясом и специями',          550),
    ('Запечённая свинина с овощами','Обед',    100,  'Свинина, запечённая с картофелем и морковью',           590),
    ('Макароны по-флотски',         'Обед',     75,  'Макароны с тушёным мясным фаршем',                      490),
    ('Биточки из индейки',          'Обед',     88,  'Паровые биточки из индейки с овощным гарниром',         430),
    ('Голубцы со сметаной',         'Обед',     92,  'Фаршированные капустные голубцы под сметанным соусом',  510),

    # --- Полдник ---
    ('Кефир + булочка',             'Полдник',  30,  'Стакан кефира 1%, сдобная булочка',                     280),
    ('Ряженка + печенье',           'Полдник',  28,  'Стакан ряженки с галетным печеньем',                    260),
    ('Йогурт фруктовый',            'Полдник',  35,  'Йогурт с кусочками персика или клубники, 125 г',        180),
    ('Фруктовый салат',             'Полдник',  40,  'Яблоко, банан, киви, заправленные йогуртом',            210),
    ('Молоко + хлеб с маслом',      'Полдник',  25,  'Стакан тёплого молока, хлеб с маслом',                  230),

    # --- Ужин ---
    ('Вареники с картошкой',        'Ужин',     65,  'Домашние вареники с картофельно-луковой начинкой',      420),
    ('Пельмени со сметаной',        'Ужин',     70,  'Отварные пельмени из говядины со сметаной',             480),
    ('Запеканка из макарон',        'Ужин',     60,  'Макаронная запеканка с яйцом и сыром',                  400),
    ('Рисовая каша с изюмом',       'Ужин',     50,  'Рисовая молочная каша с изюмом и маслом',               340),
    ('Омлет с овощами',             'Ужин',     58,  'Омлет с болгарским перцем, помидором и зеленью',        350),
    ('Картофельные зразы',          'Ужин',     68,  'Зразы с мясным фаршем, жаренные на масле',              460),
    ('Тушёная капуста с мясом',     'Ужин',     72,  'Тушёная белокочанная капуста с говядиной',              410),
    ('Рыбные котлеты с пюре',       'Ужин',     78,  'Котлеты из трески с картофельным пюре',                 430),
    ('Гречка с грибным соусом',     'Ужин',     62,  'Гречневая каша с грибным подливом',                     370),
    ('Творог со сметаной',          'Ужин',     45,  'Порция творога 9% со сметаной и сахаром',               310),
]

created_dishes = []
for name, mt_name, price, desc, cal in DISHES:
    d, _ = Dish.objects.get_or_create(
        name=name,
        defaults={
            'meal_type': meal_types[mt_name],
            'price': price,
            'description': desc,
            'calories': cal,
            'is_available': True,
        }
    )
    created_dishes.append(d)
print(f"✓ Блюд в базе: {Dish.objects.count()}")

# ── 3. Ученики (30 человек) ───────────────────────────────────────────────────
STUDENTS = [
    ('ivan_petrov',      'Иван',       'Петров',     '9А'),
    ('maria_sidorova',   'Мария',      'Сидорова',   '9А'),
    ('alexey_kozlov',    'Алексей',    'Козлов',     '9А'),
    ('elena_volkova',    'Елена',      'Волкова',    '9Б'),
    ('dmitry_novikov',   'Дмитрий',    'Новиков',    '9Б'),
    ('anna_morozova',    'Анна',       'Морозова',   '9Б'),
    ('sergey_lebedev',   'Сергей',     'Лебедев',    '10А'),
    ('natalia_fedorova', 'Наталья',    'Фёдорова',   '10А'),
    ('mikhail_orlov',    'Михаил',     'Орлов',      '10А'),
    ('oksana_titova',    'Оксана',     'Титова',     '10Б'),
    ('pavel_karpov',     'Павел',      'Карпов',     '10Б'),
    ('yulia_zhukova',    'Юлия',       'Жукова',     '10Б'),
    ('artem_sokolov',    'Артём',      'Соколов',    '11А'),
    ('polina_guseva',    'Полина',     'Гусева',     '11А'),
    ('nikita_egorov',    'Никита',     'Егоров',     '11А'),
    ('kristina_fomina',  'Кристина',   'Фомина',     '11Б'),
    ('andrey_kiselev',   'Андрей',     'Кисилёв',    '11Б'),
    ('tatyana_nikitin',  'Татьяна',    'Никитина',   '11Б'),
    ('roman_stepanov',   'Роман',      'Степанов',   '8А'),
    ('daria_makarova',   'Дарья',      'Макарова',   '8А'),
    ('igor_korolev',     'Игорь',      'Королёв',    '8А'),
    ('svetlana_popova',  'Светлана',   'Попова',     '8Б'),
    ('victor_menshov',   'Виктор',     'Меньшов',    '8Б'),
    ('alina_smirnova',   'Алина',      'Смирнова',   '8Б'),
    ('kirill_baranov',   'Кирилл',     'Баранов',    '7А'),
    ('vera_filatova',    'Вера',       'Филатова',   '7А'),
    ('oleg_ryabov',      'Олег',       'Рябов',      '7А'),
    ('marina_komova',    'Марина',     'Комова',     '7Б'),
    ('boris_savelyev',   'Борис',      'Савельев',   '7Б'),
    ('irina_gavrilova',  'Ирина',      'Гаврилова',  '7Б'),
]

student_profiles = []
for username, first, last, cls in STUDENTS:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'first_name': first, 'last_name': last}
    )
    if created:
        user.set_password('school2025')
        user.save()
    profile, _ = StudentProfile.objects.get_or_create(
        user=user,
        defaults={'class_name': cls, 'balance': random.randint(500, 3000)}
    )
    student_profiles.append(profile)
print(f"✓ Учеников в базе: {StudentProfile.objects.count()}")

# ── 4. Логика популярности блюд (топ-5 будут явными лидерами) ─────────────────
# Топ-5 блюд — им присваиваем высокий вес заказов
all_dishes = list(Dish.objects.all())
dishes_by_name = {d.name: d for d in all_dishes}

TOP_5_DISHES = [
    'Борщ со сметаной',
    'Котлета с картофельным пюре',
    'Куриный суп с лапшой',
    'Блины со сметаной',
    'Гуляш с макаронами',
]

# Вес для случайного выбора: топ-5 получают вес 8, остальные — 1
dish_weights = []
for d in all_dishes:
    dish_weights.append(8 if d.name in TOP_5_DISHES else 1)

# ── 5. Топ-5 учеников: им дадим значительно больше записей ───────────────────
TOP_5_STUDENTS_IDX = [0, 3, 6, 12, 22]  # ivan, elena, sergey, artem, victor
student_weights = []
for i, s in enumerate(student_profiles):
    student_weights.append(6 if i in TOP_5_STUDENTS_IDX else 1)

# ── 6. Записи питания за 6 месяцев ────────────────────────────────────────────
today = date.today()
start_date = date(today.year - 1 if today.month <= 6 else today.year,
                  (today.month - 6) % 12 or 12, 1)

# Не создаём дубли — сначала удаляем старые seed-данные если нужно
existing_count = MealRecord.objects.count()
print(f"  Существующих записей питания: {existing_count}")

new_records = 0
cur = start_date
while cur <= today:
    # пропускаем выходные
    if cur.weekday() >= 5:
        cur += timedelta(days=1)
        continue

    # В каждый рабочий день — обед обязателен, завтрак и ужин — реже
    for meal_slot in ['Завтрак', 'Обед', 'Полдник', 'Ужин']:
        prob = {'Завтрак': 0.55, 'Обед': 0.90, 'Полдник': 0.40, 'Ужин': 0.30}[meal_slot]
        slot_dishes = [d for d in all_dishes if d.meal_type.name == meal_slot]
        slot_weights = [dish_weights[all_dishes.index(d)] for d in slot_dishes]
        if not slot_dishes:
            continue

        for i, student in enumerate(student_profiles):
            w = student_weights[i]
            adjusted_prob = min(prob * (1 + 0.3 * (w - 1)), 1.0)
            if random.random() > adjusted_prob:
                continue
            if MealRecord.objects.filter(student=student, date=cur,
                                         dish__meal_type__name=meal_slot).exists():
                continue
            dish = random.choices(slot_dishes, weights=slot_weights, k=1)[0]
            MealRecord.objects.create(
                student=student, dish=dish, date=cur, is_received=True
            )
            new_records += 1

    cur += timedelta(days=1)

print(f"✓ Новых записей питания создано: {new_records}")
print(f"  Всего MealRecord: {MealRecord.objects.count()}")

# ── 7. Платежи (пополнение баланса) ──────────────────────────────────────────
new_payments = 0
cur = start_date
while cur <= today:
    if cur.weekday() >= 5:
        cur += timedelta(days=7 - cur.weekday())
        continue
    # Раз в 2 недели случайные студенты пополняют баланс
    if cur.day in (1, 15):
        for student in random.sample(student_profiles, k=random.randint(8, 20)):
            amount = random.choice([500, 1000, 1500, 2000])
            if not Payment.objects.filter(student=student,
                                          created_at__date=cur).exists():
                Payment.objects.create(student=student, amount=amount)
                student.balance += amount
                student.save()
                new_payments += 1
    cur += timedelta(days=1)

print(f"✓ Новых платежей создано: {new_payments}")
print(f"  Всего Payment: {Payment.objects.count()}")

# ── 8. Итоговая статистика ────────────────────────────────────────────────────
from django.db.models import Count
print("\n─── Топ-5 блюд по заказам ───")
top_dishes = (MealRecord.objects
              .filter(is_received=True)
              .values('dish__name')
              .annotate(cnt=Count('id'))
              .order_by('-cnt')[:5])
for r in top_dishes:
    print(f"  {r['dish__name']}: {r['cnt']} порций")

print("\n─── Топ-5 учеников по порциям ───")
top_students = (MealRecord.objects
                .filter(is_received=True)
                .values('student__user__first_name', 'student__user__last_name',
                        'student__class_name')
                .annotate(cnt=Count('id'))
                .order_by('-cnt')[:5])
for r in top_students:
    print(f"  {r['student__user__first_name']} {r['student__user__last_name']} "
          f"({r['student__class_name']}): {r['cnt']} порций")
