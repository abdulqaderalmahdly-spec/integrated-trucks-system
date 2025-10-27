#!/bin/bash

# ألوان للواجهة
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# دالة لعرض العنوان
show_header() {
    clear
    echo -e "${BLUE}"
    echo "🚛 نظام إدارة القواطر المتكامل"
    echo "📱 نظام المشاركة والوصول عن بعد"
    echo -e "${NC}========================================"
}

# دالة للتحقق من تشغيل النظام
check_system_running() {
    if ! pgrep -f "python app.py" > /dev/null; then
        echo -e "${YELLOW}⚠️  النظام غير شغال. جاري التشغيل...${NC}"
        python app.py > system.log 2>&1 &
        sleep 8
        if pgrep -f "python app.py" > /dev/null; then
            echo -e "${GREEN}✅ تم تشغيل النظام بنجاح${NC}"
            return 0
        else
            echo -e "${RED}❌ فشل في تشغيل النظام${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}✅ النظام يعمل بالفعل${NC}"
        return 0
    fi
}

# دالة للحصول على IP المحلي
get_local_ip() {
    echo -e "${BLUE}🔍 جاري البحث عن عنوان IP...${NC}"
    
    # محاولات متعددة للحصول على IP
    IP=""
    
    # المحاولة الأولى: ifconfig
    IP=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n1)
    
    # المحاولة الثانية: ip addr
    if [ -z "$IP" ]; then
        IP=$(ip addr show 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n1)
    fi
    
    # المحاولة الثالثة: netstat
    if [ -z "$IP" ]; then
        IP=$(netstat -rn 2>/dev/null | grep -E '^0.0.0.0' | awk '{print $2}' | head -n1)
    fi
    
    echo "$IP"
}

# دالة لعرض معلومات المستخدمين
show_users_info() {
    echo -e "${BLUE}🔐 بيانات الدخول المتاحة:${NC}"
    echo "   👤 admin / admin123        (مدير عام - صلاحيات كاملة)"
    echo "   👤 manager / manager123    (مدير فرع)"
    echo "   👤 accountant / accountant123 (محاسب)"
    echo "   👤 user1 / user1123        (مستخدم عادي)"
    echo ""
    echo -e "${YELLOW}📞 للدعم: عبدالقادر مهدلي - 737254619${NC}"
    echo ""
}

# دالة للمشاركة المحلية
local_sharing() {
    show_header
    echo -e "${GREEN}🌐 مشاركة محلية (نفس الشبكة)${NC}"
    echo "========================================"
    
    if ! check_system_running; then
        return 1
    fi
    
    IP=$(get_local_ip)
    
    if [ -n "$IP" ]; then
        echo -e "${GREEN}✅ تم العثور على عنوان IP${NC}"
        echo ""
        echo -e "${BLUE}📋 شارك هذا الرابط مع المستخدمين في نفس الشبكة:${NC}"
        echo -e "${YELLOW}   http://$IP:5000${NC}"
        echo ""
        show_users_info
        echo -e "${RED}⏹️  اضغط Ctrl+C لإيقاف النظام${NC}"
        echo ""
        
        # عرض سجل النظام في الوقت الحقيقي
        echo -e "${BLUE}📊 سجل النظام (للمراقبة):${NC}"
        tail -f system.log &
        TAIL_PID=$!
        
        wait
        kill $TAIL_PID 2>/dev/null
    else
        echo -e "${RED}❌ لم يتم العثور على عنوان IP${NC}"
        echo "⚠️  تأكد من:"
        echo "   - أنك متصل بـ Wi-Fi"
        echo "   - أن الجهاز الآخر في نفس الشبكة"
        echo "   - جرب إعادة تشغيل الـ Wi-Fi"
    fi
}

# دالة للمشاركة العامة باستخدام Cloudflare
public_sharing_cloudflare() {
    show_header
    echo -e "${GREEN}🌍 مشاركة عامة (لأي شخص في العالم)${NC}"
    echo "========================================"
    
    if ! check_system_running; then
        return 1
    fi
    
    # تحميل cloudflared إذا لم يكن موجوداً
    if [ ! -f "cloudflared" ]; then
        echo -e "${BLUE}📥 جاري تحميل Cloudflare Tunnel...${NC}"
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
        if [ $? -eq 0 ]; then
            mv cloudflared-linux-arm64 cloudflared
            chmod +x cloudflared
            echo -e "${GREEN}✅ تم تحميل Cloudflare Tunnel${NC}"
        else
            echo -e "${RED}❌ فشل في تحميل Cloudflare Tunnel${NC}"
            return 1
        fi
    fi
    
    echo -e "${BLUE}🚀 جاري إنشاء نفق آمن...${NC}"
    echo -e "${YELLOW}⏳ قد يستغرق هذا بضع ثواني...${NC}"
    
    # تشغيل cloudflared
    ./cloudflared tunnel --url http://localhost:5000 > cloudflare.log 2>&1 &
    CLOUDFLARE_PID=$!
    sleep 10
    
    # محاولة الحصول على الرابط
    PUBLIC_URL=$(grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' cloudflare.log | head -1)
    
    if [ -n "$PUBLIC_URL" ]; then
        echo -e "${GREEN}✅ تم إنشاء الرابط العام بنجاح!${NC}"
        echo ""
        echo -e "${BLUE}🌐 شارك هذا الرابط مع أي شخص في العالم:${NC}"
        echo -e "${YELLOW}   $PUBLIC_URL${NC}"
        echo ""
        show_users_info
        echo -e "${RED}⏹️  اضغط Ctrl+C لإيقاف المشاركة${NC}"
        echo ""
        echo -e "${BLUE}📊 سجل Cloudflare:${NC}"
        tail -f cloudflare.log &
        TAIL_PID=$!
        
        wait
        kill $CLOUDFLARE_PID $TAIL_PID 2>/dev/null
    else
        echo -e "${RED}❌ فشل في إنشاء الرابط العام${NC}"
        echo "🔧 جرب الخيار 1 للمشاركة المحلية"
        kill $CLOUDFLARE_PID 2>/dev/null
        return 1
    fi
}

# دالة للمشاركة العامة باستخدام Serveo (بديل)
public_sharing_serveo() {
    show_header
    echo -e "${GREEN}🌍 مشاركة عامة (بديل)${NC}"
    echo "========================================"
    
    if ! check_system_running; then
        return 1
    fi
    
    echo -e "${BLUE}🚀 جاري الاتصال بـ Serveo...${NC}"
    echo -e "${YELLOW}⏳ قد يستغرق هذا حتى 30 ثانية...${NC}"
    
    # تشغيل serveo
    ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:5000 serveo.net > serveo.log 2>&1 &
    SERVER_PID=$!
    sleep 15
    
    # محاولة الحصول على الرابط
    PUBLIC_URL=$(grep -o 'https://[a-zA-Z0-9]*\.serveo\.net' serveo.log | head -1)
    
    if [ -n "$PUBLIC_URL" ]; then
        echo -e "${GREEN}✅ تم إنشاء الرابط العام بنجاح!${NC}"
        echo ""
        echo -e "${BLUE}🌐 شارك هذا الرابط مع أي شخص في العالم:${NC}"
        echo -e "${YELLOW}   $PUBLIC_URL${NC}"
        echo ""
        show_users_info
        echo -e "${RED}⏹️  اضغط Ctrl+C لإيقاف المشاركة${NC}"
        echo ""
        echo -e "${BLUE}📊 سجل Serveo:${NC}"
        tail -f serveo.log &
        TAIL_PID=$!
        
        wait
        kill $SERVER_PID $TAIL_PID 2>/dev/null
    else
        echo -e "${RED}❌ فشل في إنشاء الرابط العام${NC}"
        echo "🔧 جرب الخيار 1 للمشاركة المحلية"
        kill $SERVER_PID 2>/dev/null
        return 1
    }
}

# القائمة الرئيسية
main_menu() {
    while true; do
        show_header
        echo -e "${BLUE}🎯 اختر طريقة المشاركة:${NC}"
        echo ""
        echo -e "1) 📱 ${GREEN}مشاركة محلية${NC} (نفس الـ Wi-Fi - أسرع)"
        echo -e "2) 🌐 ${YELLOW}مشاركة عامة${NC} (Cloudflare - موثوق)"
        echo -e "3) 🔄 ${BLUE}مشاركة عامة${NC} (Serveo - بديل)"
        echo -e "4) 🔧 ${RED}إدارة النظام${NC}"
        echo -e "5) ❌ ${RED}خروج${NC}"
        echo ""
        
        read -p "اختر رقم الخيار [1-5]: " choice
        
        case $choice in
            1)
                local_sharing
                ;;
            2)
                public_sharing_cloudflare
                ;;
            3)
                public_sharing_serveo
                ;;
            4)
                system_management
                ;;
            5)
                echo -e "${GREEN}👋 مع السلامة!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ اختيار غير صحيح${NC}"
                sleep 2
                ;;
        esac
        
        echo ""
        read -p "اضغط Enter للعودة إلى القائمة الرئيسية..."
    done
}

# دالة إدارة النظام
system_management() {
    show_header
    echo -e "${BLUE}🔧 إدارة النظام${NC}"
    echo "========================================"
    
    echo ""
    echo -e "1) 🔄 ${GREEN}إعادة تشغيل النظام${NC}"
    echo -e "2) 📊 ${BLUE}عرض سجل النظام${NC}"
    echo -e "3) 🧹 ${YELLOW}تنظيف السجلات${NC}"
    echo -e "4) 🔙 ${NC}عودة للقائمة الرئيسية"
    echo ""
    
    read -p "اختر رقم الخيار [1-4]: " choice
    
    case $choice in
        1)
            echo -e "${YELLOW}🔄 جاري إعادة تشغيل النظام...${NC}"
            pkill -f "python app.py"
            sleep 3
            python app.py > system.log 2>&1 &
            sleep 5
            if pgrep -f "python app.py" > /dev/null; then
                echo -e "${GREEN}✅ تم إعادة التشغيل بنجاح${NC}"
            else
                echo -e "${RED}❌ فشل في إعادة التشغيل${NC}"
            fi
            ;;
        2)
            echo -e "${BLUE}📊 سجل النظام:${NC}"
            echo "========================================"
            tail -20 system.log
            ;;
        3)
            echo -e "${YELLOW}🧹 جاري تنظيف السجلات...${NC}"
            > system.log
            > cloudflare.log
            > serveo.log
            echo -e "${GREEN}✅ تم تنظيف السجلات${NC}"
            ;;
        4)
            return
            ;;
        *)
            echo -e "${RED}❌ اختيار غير صحيح${NC}"
            ;;
    esac
    
    read -p "اضغط Enter للمتابعة..."
}

# تنظيف العمليات عند الخروج
cleanup() {
    echo -e "${YELLOW}🔄 جاري إيقاف جميع العمليات...${NC}"
    pkill -f "python app.py"
    pkill -f "cloudflared"
    pkill -f "serveo.net"
    pkill -f "tail -f"
    echo -e "${GREEN}✅ تم التنظيف${NC}"
    exit 0
}

# التعامل مع إشارة الخروج
trap cleanup SIGINT SIGTERM

# بدء البرنامج
main_menu
