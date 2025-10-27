import sqlite3
import hashlib
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# التأكد من وجود المجلد
os.makedirs('instance', exist_ok=True)

conn = sqlite3.connect('instance/trucks.db')

# قائمة المستخدمين
# الترتيب: (username, password, full_name, role, signature)
users = [
    ('admin', hash_password('admin123'), 'مدير النظام', 'admin', 'مدير النظام - عبدالقادر مهدلي'),
    ('manager', hash_password('manager123'), 'مدير الفرع', 'manager', 'مدير الفرع'),
    ('accountant', hash_password('accountant123'), 'محاسب النظام', 'accountant', 'القسم المالي'),
    ('supervisor', hash_password('super123'), 'مشرف عام', 'manager', 'مشرف النظام')
]

print("جاري إضافة المستخدمين (المديرين والمحاسبين فقط)...")
for user_data in users:
    try:
        # يجب أن يتطابق عدد الأعمدة مع عدد القيم
        conn.execute(
            'INSERT OR IGNORE INTO users (username, password, full_name, role, signature) VALUES (?, ?, ?, ?, ?)',
            user_data
        )
        print(f'✅ {user_data[0]} - {user_data[2]}')
    except Exception as e:
        print(f'⚠️  {user_data[0]}: {e}')

# إضافة بعض السائقين الافتراضيين إلى جدول drivers الجديد
drivers = [
    ('أحمد علي', '777123456', 'DRV123456', 'صنعاء - حي التحرير', 500.00),
    ('محمد خالد', '777987654', 'DRV987654', 'عدن - المنصورة', 600.00),
    ('سالم عبده', '733112233', 'DRV332211', 'تعز - شارع جمال', 550.00)
]

print("\nجاري إضافة السائقين الافتراضيين...")
for driver_data in drivers:
    try:
        conn.execute(
            'INSERT OR IGNORE INTO drivers (full_name, phone, license_number, address, salary) VALUES (?, ?, ?, ?, ?)',
            driver_data
        )
        print(f'✅ {driver_data[0]}')
    except Exception as e:
        print(f'⚠️  {driver_data[0]}: {e}')

conn.commit()
conn.close()
print('👥 تم إعداد جميع المستخدمين والسائقين بنجاح!')
