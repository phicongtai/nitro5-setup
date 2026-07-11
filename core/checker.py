# -*- coding: utf-8 -*-
import subprocess
import os

def check_all():
    report = []
    
    # 1. OS Check
    os_detail = "Fedora Workstation"
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_detail = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass
    report.append({"feature": "Hệ điều hành", "status": "✓ OK", "detail": os_detail})
    
    # 2. Secure Boot Check
    sb_status = "✗ FAILED"
    sb_detail = "Không thể kiểm tra"
    try:
        res = subprocess.run("mokutil --sb-state", shell=True, capture_output=True, text=True)
        if "enabled" in res.stdout.lower():
            sb_status = "⚠ WARNING"
            sb_detail = "Đang BẬT (Cần đăng ký MOK khi cài driver NVIDIA)"
        else:
            sb_status = "✓ OK"
            sb_detail = "Đang TẮT (Không cần MOK)"
    except Exception:
        sb_status = "✓ OK"
        sb_detail = "Không có mokutil / Secure Boot tắt"
    report.append({"feature": "Secure Boot", "status": sb_status, "detail": sb_detail})
    
    # 3. GPU Check
    gpu_status = "✗ FAILED"
    gpu_detail = "Không tìm thấy GPU dời"
    try:
        res = subprocess.run("lspci | grep -i nvidia", shell=True, capture_output=True, text=True)
        if res.stdout:
            gpu_status = "✓ OK"
            gpu_detail = "NVIDIA dGPU: " + res.stdout.strip().split(":")[-1].strip()
    except Exception:
        pass
    report.append({"feature": "Card đồ họa NVIDIA", "status": gpu_status, "detail": gpu_detail})
    
    # 4. TLP Status
    tlp_status = "✗ FAILED"
    tlp_detail = "Dịch vụ TLP chưa hoạt động"
    try:
        res = subprocess.run("systemctl is-active tlp", shell=True, capture_output=True, text=True)
        if "active" in res.stdout.lower():
            tlp_status = "✓ OK"
            tlp_detail = "Dịch vụ TLP đang chạy ngầm"
    except Exception:
        pass
    report.append({"feature": "Quản lý nguồn TLP", "status": tlp_status, "detail": tlp_detail})

    # 5. Backlight driver
    bl_status = "✗ FAILED"
    bl_detail = "Chưa cấu hình backlight native"
    if os.path.exists("/sys/class/backlight"):
        dirs = os.listdir("/sys/class/backlight")
        if dirs:
            bl_status = "✓ OK"
            bl_detail = f"Đang sử dụng: {', '.join(dirs)}"
    report.append({"feature": "Trình điều khiển độ sáng", "status": bl_status, "detail": bl_detail})

    return report
