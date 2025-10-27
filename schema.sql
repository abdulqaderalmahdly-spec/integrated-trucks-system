-- جدول المستخدمين (Users)
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL, -- الأدوار: admin, manager, accountant, user
    signature TEXT
);

-- جدول القواطر (Trucks)
CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL UNIQUE,
    model TEXT,
    year INTEGER,
    status TEXT NOT NULL, -- مثل: In Service, Maintenance, Out of Service
    driver_id INTEGER,
    FOREIGN KEY (driver_id) REFERENCES users(username)
);

-- جدول الصيانة (Maintenance)
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_id INTEGER NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    cost REAL,
    FOREIGN KEY (truck_id) REFERENCES trucks(id)
);

-- يمكنك إضافة المزيد من الجداول هنا (مثل: الرحلات، العملاء، إلخ)
-- ...
