-- جدول المستخدمين (Users)
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL, -- الأدوار: admin, manager, accountant, user
    signature TEXT,
    phone TEXT,
    license_number TEXT,
    address TEXT,
    salary REAL -- الراتب الشهري
);

-- جدول القواطر (Trucks)
CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL UNIQUE,
    model TEXT,
    year INTEGER,
    status TEXT NOT NULL, -- مثل: In Service, Maintenance, Out of Service
    driver_id TEXT,
    FOREIGN KEY (driver_id) REFERENCES users(username)
);

-- جدول الصيانة (Maintenance)
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER NOT NULL,
    date DATE NOT NULL,
    type TEXT, -- نوع الصيانة (مثل: زيت، إطارات، محرك)
    description TEXT,
    cost REAL,
    FOREIGN KEY (truck_id) REFERENCES trucks(id)
);

-- جدول الوقود (Fuel)
CREATE TABLE IF NOT EXISTS fuel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER NOT NULL,
    date DATE NOT NULL,
    liters REAL NOT NULL,
    cost REAL NOT NULL,
    station TEXT,
    odometer INTEGER,
    FOREIGN KEY (truck_id) REFERENCES trucks(id)
);

-- جدول الشحنات (Shipments)
CREATE TABLE IF NOT EXISTS shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER NOT NULL,
    driver_username TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    load_weight REAL,
    revenue REAL,
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT NOT NULL, -- مثل: Pending, In Transit, Delivered
    FOREIGN KEY (truck_id) REFERENCES trucks(id),
    FOREIGN KEY (driver_username) REFERENCES users(username)
);

-- جدول المصاريف (Expenses)
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date DATE NOT NULL,
    category TEXT NOT NULL, -- مثل: Fuel, Toll, Repair, Salary
    amount REAL NOT NULL,
    description TEXT,
    truck_id INTEGER,
    FOREIGN KEY (truck_id) REFERENCES trucks(id)
);

-- جدول سجل المعاملات (Audit Log)
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL, -- نوع العملية: ADD_TRUCK, ADD_SHIPMENT, LOGIN, etc.
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES users(username)
);
