-- جدول المستخدمين (للمديرين والمحاسبين فقط)
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL, -- admin, manager, accountant
    signature TEXT
);

-- جدول السائقين (بيانات السائقين فقط، بدون حساب دخول)
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT,
    license_number TEXT,
    address TEXT,
    salary REAL DEFAULT 0.0
);

-- جدول معاملات السائقين (مدين/دائن)
CREATE TABLE IF NOT EXISTS driver_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL, -- DEBIT (مدين - سلفة/خصم) أو CREDIT (دائن - راتب/مكافأة)
    amount REAL NOT NULL,
    description TEXT,
    FOREIGN KEY (driver_id) REFERENCES drivers (id)
);

-- جدول القواطر
CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    status TEXT NOT NULL, -- In Service, Maintenance, Out of Service
    driver_id INTEGER, -- السائق المخصص (اختياري)
    FOREIGN KEY (driver_id) REFERENCES drivers (id)
);

-- جدول الشحنات
CREATE TABLE IF NOT EXISTS shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    load_weight REAL,
    revenue REAL NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    status TEXT NOT NULL, -- In Transit, Delivered, Cancelled
    FOREIGN KEY (truck_id) REFERENCES trucks (id),
    FOREIGN KEY (driver_id) REFERENCES drivers (id)
);

-- جدول المصاريف
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    truck_id INTEGER,
    driver_id INTEGER, -- السائق الذي دفع المصروف (لربطه بحسابه)
    FOREIGN KEY (truck_id) REFERENCES trucks (id),
    FOREIGN KEY (driver_id) REFERENCES drivers (id)
);

-- جدول الصيانة
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    cost REAL NOT NULL,
    description TEXT,
    FOREIGN KEY (truck_id) REFERENCES trucks (id)
);

-- جدول الوقود
CREATE TABLE IF NOT EXISTS fuel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    liters REAL NOT NULL,
    cost REAL NOT NULL,
    station TEXT,
    odometer INTEGER,
    FOREIGN KEY (truck_id) REFERENCES trucks (id)
);

-- سجل المعاملات (Audit Log)
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT
);
