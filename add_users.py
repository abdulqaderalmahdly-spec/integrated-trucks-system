import sqlite3
import hashlib
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# التأكد من وجود المجلد
os.makedirs('instance', exist_ok=True)

# يجب التأكد من أن ملف قاعدة البيانات موجود وأن جدول المستخدمين (users) تم إنشاؤه مسبقًا
# بما أننا لا نملك ملف app.py أو كود إنشاء قاعدة البيانات، سنفترض أن الجدول موجود.
# إذا لم يكن موجودًا، فإن محاولة الإدراج ستفشل.
# لغرض الحفظ في المستودع، سنقوم بحفظ الكود كما هو.

conn = sqlite3.connect('instance/trucks.db')

# إنشاء جدول المستخدمين إذا لم يكن موجودًا (افتراضًا)
conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        full_name TEXT,
        role TEXT,
        signature TEXT
    )
''')

# قائمة المستخدمين
users = [
    ('admin', hash_password('admin123'), 'مدير النظام', 'admin', 'مدير النظام - عبدالقادر مهدلي'),
    ('manager', hash_password('manager123'), 'مدير الفرع', 'manager', 'مدير الفرع'),
    ('accountant', hash_password('accountant123'), 'محاسب النظام', 'accountant', 'القسم المالي'),
    ('user1', hash_password('user1123'), 'مستخدم عادي', 'user', 'مستخدم النظام'),
    ('driver1', hash_password('driver123'), 'سائق رئيسي', 'user', 'سائق معتمد'),
    ('supervisor', hash_password('super123'), 'مشرف عام', 'manager', 'مشرف النظام')
]

print("جاري إضافة المستخدمين...")
for username, password_hash, full_name, role, signature in users:
    try:
        conn.execute(
            'INSERT OR IGNORE INTO users (username, password, full_name, role, signature) VALUES (?, ?, ?, ?, ?)',
            (username, password_hash, full_name, role, signature)
        )
        print(f'✅ {username} - {full_name}')
    except Exception as e:
        print(f'⚠️  {username}: {e}')

conn.commit()
conn.close()
print('👥 تم إعداد جميع المستخدمين بنجاح!')
