import sqlite3
import hashlib
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# التأكد من وجود المجلد
os.makedirs('instance', exist_ok=True)

conn = sqlite3.connect('instance/trucks.db')

# إنشاء جدول المستخدمين إذا لم يكن موجودًا (افتراضًا)
conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL, -- الأدوار: admin, manager, accountant, user
        signature TEXT,
        phone TEXT,
        license_number TEXT,
        address TEXT,
        salary REAL
    )
''')

# قائمة المستخدمين
# الترتيب الجديد: (username, password, full_name, role, signature, phone, license_number, address, salary)
users = [
    ('admin', hash_password('admin123'), 'مدير النظام', 'admin', 'مدير النظام - عبدالقادر مهدلي', None, None, None, None),
    ('manager', hash_password('manager123'), 'مدير الفرع', 'manager', 'مدير الفرع', None, None, None, None),
    ('accountant', hash_password('accountant123'), 'محاسب النظام', 'accountant', 'القسم المالي', None, None, None, None),
    ('user1', hash_password('user1123'), 'مستخدم عادي', 'user', 'مستخدم النظام', '777123456', 'DRV123456', 'صنعاء', 500.00),
    ('driver1', hash_password('driver123'), 'سائق رئيسي', 'user', 'سائق معتمد', '777987654', 'DRV987654', 'عدن', 600.00),
    ('supervisor', hash_password('super123'), 'مشرف عام', 'manager', 'مشرف النظام', None, None, None, None)
]

print("جاري إضافة المستخدمين...")
for user_data in users:
    try:
        # يجب أن يتطابق عدد الأعمدة مع عدد القيم
        conn.execute(
            'INSERT OR IGNORE INTO users (username, password, full_name, role, signature, phone, license_number, address, salary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            user_data
        )
        print(f'✅ {user_data[0]} - {user_data[2]}')
    except Exception as e:
        print(f'⚠️  {user_data[0]}: {e}')

conn.commit()
conn.close()
print('👥 تم إعداد جميع المستخدمين بنجاح!')
