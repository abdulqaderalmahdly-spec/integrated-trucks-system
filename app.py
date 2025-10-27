import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
import hashlib
from functools import wraps
from datetime import datetime
import csv
import io
# استيراد مكتبة PDF
from xhtml2pdf import pisa

# --- إعدادات التطبيق ---
app = Flask(__name__, static_folder='static')
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

def log_action(user_id, action, details):
    """تسجيل العملية في سجل المعاملات"""
    conn = get_db_connection()
    conn.execute('INSERT INTO audit_log (user_id, action, details) VALUES (?, ?, ?)',
                 (user_id, action, details))
    conn.commit()
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

def render_pdf(html_content, filename):
    """تحويل محتوى HTML إلى ملف PDF قابل للتحميل"""
    # تهيئة ملف الإخراج
    result_file = io.BytesIO()

    # تحويل HTML إلى PDF
    pisa_status = pisa.CreatePDF(
        html_content,                # محتوى HTML
        dest=result_file,            # ملف الإخراج
        encoding='utf-8'             # الترميز
    )

    # إذا لم يكن هناك خطأ في التحويل
    if not pisa_status.err:
        response = make_response(result_file.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.pdf'
        return response
    
    return "حدث خطأ أثناء إنشاء ملف PDF", 500

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
            log_action(user['username'], 'LOGIN', f'تم تسجيل الدخول بنجاح من {request.remote_addr}')
            flash(f'مرحباً بك، {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    log_action(session['username'], 'LOGOUT', 'تم تسجيل الخروج')
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
    # ربط القاطرة باسم السائق
    trucks = conn.execute('''
        SELECT t.*, d.full_name as driver_name 
        FROM trucks t 
        LEFT JOIN drivers d ON t.driver_id = d.id
    ''').fetchall()
    conn.close()
    return render_template('trucks.html', trucks=trucks)

@app.route('/trucks/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'manager'])
def add_truck():
    """إضافة قاطرة جديدة"""
    conn = get_db_connection()
    drivers_list = conn.execute('SELECT id, full_name FROM drivers').fetchall()
    conn.close()
    
    if request.method == 'POST':
        plate_number = request.form['plate_number']
        model = request.form['model']
        year = request.form['year']
        status = request.form['status']
        driver_id = request.form.get('driver_id')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO trucks (plate_number, model, year, status, driver_id) VALUES (?, ?, ?, ?, ?)',
                         (plate_number, model, year, status, driver_id if driver_id else None))
            conn.commit()
            conn.close()
            log_action(session['username'], 'ADD_TRUCK', f'إضافة قاطرة جديدة: {plate_number} - {model}')
            flash('تمت إضافة القاطرة بنجاح.', 'success')
            return redirect(url_for('trucks'))
        except sqlite3.IntegrityError:
            flash('رقم اللوحة موجود بالفعل.', 'danger')
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')
            
    return render_template('add_truck.html', drivers=drivers_list)

# --- مسارات إدارة السائقين (البيانات فقط) ---

@app.route('/drivers/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'manager'])
def add_driver():
    """إضافة بيانات سائق جديد (بدون حساب دخول)"""
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form.get('phone')
        license_number = request.form.get('license_number')
        address = request.form.get('address')
        salary = request.form.get('salary')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO drivers (full_name, phone, license_number, address, salary) VALUES (?, ?, ?, ?, ?)',
                         (full_name, phone, license_number, address, salary))
            conn.commit()
            conn.close()
            log_action(session['username'], 'ADD_DRIVER_DATA', f'إضافة بيانات سائق جديد: {full_name}')
            flash(f'تمت إضافة السائق ({full_name}) بنجاح.', 'success')
            return redirect(url_for('index'))
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
    trucks_list = conn.execute('SELECT id, plate_number, driver_id FROM trucks WHERE status = "In Service"').fetchall()
    drivers_list = conn.execute('SELECT id, full_name FROM drivers').fetchall()
    conn.close()
    
    if request.method == 'POST':
        truck_id = request.form['truck_id']
        driver_id = request.form['driver_id'] # تم تغيير driver_username إلى driver_id
        origin = request.form['origin']
        destination = request.form['destination']
        load_weight = request.form['load_weight']
        revenue = request.form['revenue']
        start_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO shipments (truck_id, driver_id, origin, destination, load_weight, revenue, start_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, "In Transit")',
                         (truck_id, driver_id, origin, destination, load_weight, revenue, start_date))
            conn.commit()
            conn.close()
            log_action(session['username'], 'ADD_SHIPMENT', f'بدء شحنة جديدة: من {origin} إلى {destination}، القاطرة: {truck_id}')
            flash('تمت إضافة الشحنة بنجاح وبدء الرحلة.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')

    return render_template('add_shipment.html', trucks=trucks_list, drivers=drivers_list)

# --- مسارات إدارة الصيانة ---

@app.route('/maintenance/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'manager'])
def add_maintenance():
    """إضافة صيانة جديدة"""
    conn = get_db_connection()
    trucks_list = conn.execute('SELECT id, plate_number FROM trucks').fetchall()
    conn.close()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        truck_id = request.form['truck_id']
        date = request.form['date']
        type = request.form['type']
        cost = request.form['cost']
        description = request.form['description']
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO maintenance (truck_id, date, type, cost, description) VALUES (?, ?, ?, ?, ?)',
                         (truck_id, date, type, cost, description))
            conn.commit()
            conn.close()
            log_action(session['username'], 'ADD_MAINTENANCE', f'تسجيل صيانة: {type} للقاطرة {truck_id} بتكلفة {cost}')
            flash('تم تسجيل الصيانة بنجاح.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')
            
    return render_template('add_maintenance.html', trucks=trucks_list, today=today)

# --- مسارات إدارة الوقود ---

@app.route('/fuel/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'manager'])
def add_fuel():
    """إضافة تعبئة وقود جديدة"""
    conn = get_db_connection()
    trucks_list = conn.execute('SELECT id, plate_number FROM trucks').fetchall()
    conn.close()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        truck_id = request.form['truck_id']
        date = request.form['date']
        liters = request.form['liters']
        cost = request.form['cost']
        station = request.form['station']
        odometer = request.form.get('odometer')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO fuel (truck_id, date, liters, cost, station, odometer) VALUES (?, ?, ?, ?, ?, ?)',
                         (truck_id, date, liters, cost, station, odometer if odometer else None))
            conn.commit()
            conn.close()
            log_action(session['username'], 'ADD_FUEL', f'تسجيل وقود: {liters} لتر للقاطرة {truck_id} بتكلفة {cost}')
            flash('تم تسجيل الوقود بنجاح.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')
            
    return render_template('add_fuel.html', trucks=trucks_list, today=today)

# --- مسارات إدارة المصاريف ---

@app.route('/expenses/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'accountant'])
def add_expense():
    """إضافة مصاريف"""
    conn = get_db_connection()
    trucks_list = conn.execute('SELECT id, plate_number FROM trucks').fetchall()
    drivers_list = conn.execute('SELECT id, full_name FROM drivers').fetchall()
    conn.close()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        expense_date = request.form['expense_date']
        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        truck_id = request.form.get('truck_id')
        driver_id = request.form.get('driver_id') # حقل جديد
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO expenses (expense_date, category, amount, description, truck_id, driver_id) VALUES (?, ?, ?, ?, ?, ?)',
                         (expense_date, category, amount, description, truck_id if truck_id else None, driver_id if driver_id else None))
            conn.commit()
            
            # تسجيل المصروف كمعاملة دائنة للسائق (المرحلة 3)
            if driver_id:
                conn.execute('INSERT INTO driver_transactions (driver_id, date, type, amount, description) VALUES (?, ?, ?, ?, ?)',
                             (driver_id, expense_date, 'CREDIT', amount, f'مصروف مدفوع: {category}'))
                conn.commit()
            
            conn.close()
            log_action(session['username'], 'ADD_EXPENSE', f'تسجيل مصروف: {category} بمبلغ {amount}')
            flash('تم تسجيل المصروف بنجاح.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')
            
    categories = ['وقود', 'رسوم طرق', 'صيانة', 'رواتب', 'أخرى']
    return render_template('add_expense.html', trucks=trucks_list, categories=categories, today=today, drivers=drivers_list)

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
        SELECT s.origin, s.destination, t.plate_number, d.full_name as driver_name 
        FROM shipments s
        JOIN trucks t ON s.truck_id = t.id
        JOIN drivers d ON s.driver_id = d.id
        WHERE s.status = "In Transit"
    ''').fetchall()
    
    conn.close()
    
    report_data = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': total_revenue - total_expenses,
        'active_shipments': active_shipments,
        'report_title': 'التقرير المالي والتشغيلي العام',
        'generated_by': session.get('full_name', 'غير معروف'),
        'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('reports.html', data=report_data)

@app.route('/reports/pdf')
@login_required
@role_required(['admin', 'manager', 'accountant'])
def reports_pdf():
    """توليد التقرير المالي كملف PDF"""
    conn = get_db_connection()
    
    # جلب نفس بيانات التقرير
    total_revenue = conn.execute('SELECT SUM(revenue) FROM shipments WHERE status = "Delivered"').fetchone()[0] or 0
    total_expenses = conn.execute('SELECT SUM(amount) FROM expenses').fetchone()[0] or 0
    
    active_shipments = conn.execute('''
        SELECT s.origin, s.destination, t.plate_number, d.full_name as driver_name 
        FROM shipments s
        JOIN trucks t ON s.truck_id = t.id
        JOIN drivers d ON s.driver_id = d.id
        WHERE s.status = "In Transit"
    ''').fetchall()
    
    conn.close()
    
    report_data = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': total_revenue - total_expenses,
        'active_shipments': active_shipments,
        'report_title': 'التقرير المالي والتشغيلي العام',
        'generated_by': session.get('full_name', 'غير معروف'),
        'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # استخدام قالب مخصص للطباعة
    html = render_template('reports_pdf.html', data=report_data)
    
    return render_pdf(html, 'التقرير_المالي_العام')

# --- مسارات سجل المعاملات (Audit Log) ---

@app.route('/audit-log')
@login_required
@role_required(['admin', 'manager'])
def audit_log():
    """عرض سجل المعاملات"""
    return render_template('audit_log.html')

@app.route('/api/audit-log')
@login_required
@role_required(['admin', 'manager'])
def get_audit_log():
    """API لجلب سجل المعاملات"""
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify([dict(log) for log in logs])

@app.route('/api/audit-log/search')
@login_required
@role_required(['admin', 'manager'])
def search_audit_log():
    """API للبحث في سجل المعاملات"""
    query = request.args.get('q', '')
    conn = get_db_connection()
    logs = conn.execute('''
        SELECT * FROM audit_log 
        WHERE action LIKE ? OR details LIKE ? OR user_id LIKE ?
        ORDER BY timestamp DESC LIMIT 100
    ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    return jsonify([dict(log) for log in logs])

@app.route('/api/export/audit-log')
@login_required
@role_required(['admin', 'manager'])
def export_audit_log():
    """API لتصدير سجل المعاملات إلى CSV"""
    conn = get_db_connection()
    logs = conn.execute('SELECT timestamp, user_id, action, details FROM audit_log ORDER BY timestamp DESC').fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['التاريخ والوقت', 'المستخدم', 'العملية', 'التفاصيل'])
    
    for log in logs:
        writer.writerow(log)
    
    output.seek(0)
    return app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=audit-log-{datetime.now().strftime("%Y-%m-%d")}.csv'}
    )


# --- مسارات حسابات السائقين ---

@app.route('/drivers/account/<int:driver_id>')
@login_required
@role_required(['admin', 'accountant'])
def driver_account(driver_id):
    """عرض كشف حساب السائق"""
    conn = get_db_connection()
    driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,)).fetchone()
    
    if not driver:
        flash('السائق غير موجود.', 'danger')
        return redirect(url_for('index'))
        
    transactions = conn.execute('SELECT * FROM driver_transactions WHERE driver_id = ? ORDER BY date DESC, id DESC', (driver_id,)).fetchall()
    
    # حساب الرصيد
    balance = 0
    for t in transactions:
        if t['type'] == 'CREDIT':
            balance += t['amount']
        elif t['type'] == 'DEBIT':
            balance -= t['amount']
            
    conn.close()
    
    return render_template('driver_account.html', driver=driver, transactions=transactions, balance=balance)

@app.route('/drivers/add_transaction/<int:driver_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'accountant'])
def add_driver_transaction(driver_id):
    """إضافة معاملة مالية للسائق (سلفة، مكافأة)"""
    conn = get_db_connection()
    driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,)).fetchone()
    conn.close()
    
    if not driver:
        flash('السائق غير موجود.', 'danger')
        return redirect(url_for('index'))
        
    today = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        date = request.form['date']
        type = request.form['type'] # DEBIT (سلفة) أو CREDIT (مكافأة)
        amount = request.form['amount']
        description = request.form['description']
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO driver_transactions (driver_id, date, type, amount, description) VALUES (?, ?, ?, ?, ?)',
                         (driver_id, date, type, amount, description))
            conn.commit()
            conn.close()
            log_action(session['username'], 'ADD_DRIVER_TRANS', f'إضافة معاملة {type} للسائق {driver["full_name"]} بمبلغ {amount}')
            flash('تم تسجيل المعاملة بنجاح.', 'success')
            return redirect(url_for('driver_account', driver_id=driver_id))
        except Exception as e:
            flash(f'حدث خطأ: {e}', 'danger')
            
    return render_template('add_driver_transaction.html', driver=driver, today=today)

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("⚠️ قاعدة البيانات غير موجودة. جاري التهيئة...")
        init_db()
        print("✅ تم تهيئة قاعدة البيانات. يرجى تشغيل add_users.py لإضافة المستخدمين والسائقين.")
    
    app.run(host='0.0.0.0', port=5000)
