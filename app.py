import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
import hashlib
from functools import wraps

# --- إعدادات التطبيق ---
app = Flask(__name__)
app.secret_key = 'your_secret_key_for_session_management' # يجب تغييرها في بيئة الإنتاج
DATABASE = os.path.join(app.root_path, 'instance', 'trucks.db')

# --- دوال مساعدة ---
def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    if not os.path.exists(os.path.join(app.root_path, 'instance')):
        os.makedirs(os.path.join(app.root_path, 'instance'))
        
    conn = get_db_connection()
    with app.open_resource('schema.sql', mode='r') as f:
        conn.executescript(f.read())
    conn.close()

def login_required(f):
    """ديكوريتور للتحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('الرجاء تسجيل الدخول للوصول لهذه الصفحة.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- المسارات (Routes) ---

@app.route('/')
@login_required
def index():
    """الصفحة الرئيسية - عرض لوحة التحكم"""
    conn = get_db_connection()
    # مثال: جلب عدد القواطر
    truck_count = conn.execute('SELECT COUNT(*) FROM trucks').fetchone()[0]
    conn.close()
    return render_template('index.html', user=session['username'], role=session['role'], truck_count=truck_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                            (username, hash_password(password))).fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'مرحباً بك، {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('role', None)
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('login'))

# --- مسارات إدارة القواطر (مثال) ---

@app.route('/trucks')
@login_required
def trucks():
    """عرض قائمة القواطر"""
    conn = get_db_connection()
    trucks = conn.execute('SELECT * FROM trucks').fetchall()
    conn.close()
    return render_template('trucks.html', trucks=trucks)

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    # التأكد من تهيئة قاعدة البيانات قبل التشغيل
    if not os.path.exists(DATABASE):
        print("⚠️ قاعدة البيانات غير موجودة. جاري التهيئة...")
        init_db()
        # بعد التهيئة، يمكن تشغيل add_users.py لإضافة المستخدمين الافتراضيين
        print("✅ تم تهيئة قاعدة البيانات. يرجى تشغيل add_users.py لإضافة المستخدمين.")
    
    # تشغيل التطبيق على المنفذ 5000 (المنفذ الافتراضي في سكريبت المشاركة)
    app.run(host='0.0.0.0', port=5000)
