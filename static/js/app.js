// هذا الملف مخصص لوظائف JavaScript المتقدمة مثل الطباعة والتصدير.
// تم نقل وظائف سجل المعاملات (loadAuditLog, searchAuditLog, exportAuditLog) مؤقتاً إلى audit_log.html.

// وظيفة الطباعة (لأغراض العرض)
function printSection(elementId) {
    const printContent = document.getElementById(elementId).innerHTML;
    const originalContent = document.body.innerHTML;

    // إخفاء العناصر التي لا نريد طباعتها
    const noPrintElements = document.querySelectorAll('.no-print');
    noPrintElements.forEach(el => el.style.display = 'none');

    // إعداد محتوى الطباعة
    document.body.innerHTML = `
        <html dir="rtl">
        <head>
            <title>تقرير</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.rtl.min.css">
            <style>
                body { margin: 20px; }
                .print-header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 10px; }
                .print-date { font-weight: bold; }
                .table { width: 100%; }
                @media print {
                    .no-print { display: none !important; }
                }
            </style>
        </head>
        <body>
            <div class="print-header">
                <h2>نظام إدارة القواطر المتكامل</h2>
                <p>تاريخ الطباعة: <span class="print-date">${new Date().toLocaleDateString('ar-EG')}</span></p>
            </div>
            ${printContent}
        </body>
        </html>
    `;

    window.print();
    
    // إعادة المحتوى الأصلي بعد الطباعة
    document.body.innerHTML = originalContent;
    window.location.reload(); // إعادة تحميل الصفحة لاستعادة الوظائف
}

// وظيفة الطباعة المتقدمة (للفواتير) - مثال
// يجب أن تكون هذه الوظيفة في app.py أو يتم جلب البيانات لها من API
// function generateMaintenanceInvoice(maintenanceData) { ... }

