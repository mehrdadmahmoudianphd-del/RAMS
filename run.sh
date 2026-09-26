#!/bin/bash
cd "$(dirname "$0")"
echo "════════════════════════════════════════════════"
echo "  سامانه لجستیک معکوس و ارتقای مدیریت دارایی فیزیکی"
echo "════════════════════════════════════════════════"
echo ""
echo "  محلی:   http://localhost:8501"
echo "  شبکه:   http://$(hostname -I 2>/dev/null | awk '{print $1}'):8501"
echo ""
# 0.0.0.0 یعنی از دستگاه‌های دیگر در شبکه هم باز می‌شود
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
