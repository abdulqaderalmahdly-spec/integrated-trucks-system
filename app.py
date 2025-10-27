import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
import hashlib
from functools import wraps
from datetime import datetime

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

def role_required(allowed_roles):
    """ديكوريتور للتحقق من صلاحية الدور"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') not in allowed_roles:
                flash('ليس لديك الصلاحية للوصول لهذه الصفحة.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- المسارات (Routes) ---

@app.route('/')
@login_required
def index():
    """الصفحة الرئيسية - عرض لوحة التحكم"""
    conn = get_db_connection()
    truck_count = conn.execute('SELECT COUNT(*) FROM trucks').fetchone()[0]
    shipment_count = conn.execute('SELECT COUNT(*) FROM shipments WHERE status = "In Transit"').fetchone()[0]
    conn.close()
    return render_template('index.html', truck_count=truck_count, shipment_count=shipment_count)

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
            session['full_name'] = user['full_name']
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
    session.pop('full_name', None)
    session.pop('role', None)
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('login'))

# --- مسارات إدارة القواطر ---

@app.route('/trucks')
@login_required
def trucks():
    """عرض قائمة القواطر"""
    conn = get_db_connection()
    trucks = conn.execute('SELECT * FROM trucks').fetchall()
    conn.close()
    return render_template('trucks.html', trucks=trucks)

@app.route('/trucks/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'manager'])
def add_truck():
    """إضافة قاطرة جديدة"""
    if request.method == 'POST':
        plate_number = request.form['plate_number']
        model = request.form['model']
        year = request.form['year']
        status = request.form['status']
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO trucks (plate_number, model, year, status) VALUES (?, ?, ?, ?)',
                         (plate_number, model, year, status))
            conn.commit()
            conn.close()
            flash('تمت إضافة القاطرة بنجاح.', 'success')
            return redirect(url_for('trucks'))
        except sqlite3.IntegrityError:
            flash('رقم اللوحة موجود بالفعل.', 'danger')
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')
            
    return render_template('add_truck.html')

# --- مسارات إدارة المستخدمين (السائقين) ---

@app.route('/drivers/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'manager'])
def add_driver():
    """إضافة سائق جديد (كمستخدم بدور 'user')"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        signature = request.form.get('signature', full_name)
        phone = request.form.get('phone')
        license_number = request.form.get('license_number')
        address = request.form.get('address')
        salary = request.form.get('salary')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password, full_name, role, signature, phone, license_number, address, salary) VALUES (?, ?, ?, "user", ?, ?, ?, ?, ?)',
                         (username, hash_password(password), full_name, signature, phone, license_number, address, salary))
            conn.commit()
            conn.close()
            flash(f'تمت إضافة السائق ({full_name}) بنجاح.', 'success')
            return redirect(url_for('index')) # يمكن توجيهه لصفحة قائمة السائقين لاحقاً
        except sqlite3.IntegrityError:
            flash('اسم المستخدم موجود بالفعل.', 'danger')
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')
            
    return render_template('add_driver.html')

# --- مسارات إدارة الشحنات ---

@app.route('/shipments/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'manager'])
def add_shipment():
    """إضافة شحنة جديدة"""
    conn = get_db_connection()
    trucks_list = conn.execute('SELECT id, plate_number FROM trucks WHERE status = "In Service"').fetchall()
    drivers_list = conn.execute('SELECT username, full_name FROM users WHERE role = "user"').fetchall()
    conn.close()
    
    if request.method == 'POST':
        truck_id = request.form['truck_id']
        driver_username = request.form['driver_username']
        origin = request.form['origin']
        destination = request.form['destination']
        load_weight = request.form['load_weight']
        revenue = request.form['revenue']
        start_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO shipments (truck_id, driver_username, origin, destination, load_weight, revenue, start_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, "In Transit")',
                         (truck_id, driver_username, origin, destination, load_weight, revenue, start_date))
            conn.commit()
            conn.close()
            flash('تمت إضافة الشحنة بنجاح وبدء الرحلة.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')

    return render_template('add_shipment.html', trucks=trucks_list, drivers=drivers_list)

# --- مسارات إدارة المصاريف ---

@app.route('/expenses/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'accountant'])
def add_expense():
    """إضافة مصاريف"""
    conn = get_db_connection()
    trucks_list = conn.execute('SELECT id, plate_number FROM trucks').fetchall()
    conn.close()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        expense_date = request.form['expense_date']
        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        truck_id = request.form.get('truck_id')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO expenses (expense_date, category, amount, description, truck_id) VALUES (?, ?, ?, ?, ?)',
                         (expense_date, category, amount, description, truck_id if truck_id else None))
            conn.commit()
            conn.close()
            flash('تم تسجيل المصروف بنجاح.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')
            
    categories = ['وقود', 'رسوم طرق', 'صيانة', 'رواتب', 'أخرى']
    return render_template('add_expense.html', trucks=trucks_list, categories=categories, today=today)

# --- مسارات التقارير ---

@app.route('/reports')
@login_required
@role_required(['admin', 'manager', 'accountant'])
def reports():
    """عرض التقارير الإجمالية"""
    conn = get_db_connection()
    
    # تقرير إجمالي الإيرادات والمصروفات
    total_revenue = conn.execute('SELECT SUM(revenue) FROM shipments WHERE status = "Delivered"').fetchone()[0] or 0
    total_expenses = conn.execute('SELECT SUM(amount) FROM expenses').fetchone()[0] or 0
    
    # تقرير الشحنات النشطة
    active_shipments = conn.execute('''
        SELECT s.origin, s.destination, t.plate_number, u.full_name as driver_name 
        FROM shipments s
        JOIN trucks t ON s.truck_id = t.id
        JOIN users u ON s.driver_username = u.username
        WHERE s.status = "In Transit"
    ''').fetchall()
    
    conn.close()
    
    report_data = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': total_revenue - total_expenses,
        'active_shipments': active_shipments
    }
    
    return render_template('reports.html', data=report_data)

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("⚠️ قاعدة البيانات غير موجودة. جاري التهيئة...")
        init_db()
        print("✅ تم تهيئة قاعدة البيانات. يرجى تشغيل add_users.py لإضافة المستخدمين.")
    
    app.run(host='0.0.0.0', port=5000)
