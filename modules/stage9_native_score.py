# -*- coding: utf-8 -*-
import os
import subprocess
import re

def get_kernel_version():
    try:
        release = os.uname().release
        # Extract major.minor
        match = re.match(r'^(\d+)\.(\d+)', release)
        if match:
            return float(f"{match.group(1)}.{match.group(2)}")
    except Exception:
        pass
    return 0.0

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
        return res.returncode == 0, res.stdout.strip()
    except Exception:
        return False, ""

def calculate_score():
    checks = []
    total_score = 0
    
    # --- NVIDIA (Max 25) ---
    # 1. akmod-nvidia loaded (10 pts)
    nvidia_loaded, _ = run_cmd("lsmod | grep -q '^nvidia'")
    checks.append({
        "category": "NVIDIA & GPU",
        "name": "NVIDIA Driver Loaded",
        "score": 10 if nvidia_loaded else 0,
        "max": 10,
        "status": nvidia_loaded,
        "detail": "Driver nhân NVIDIA hoạt động" if nvidia_loaded else "Driver nhân NVIDIA chưa được nạp"
    })
    
    # 2. EnvyControl mode is hybrid (8 pts)
    _, mode_out = run_cmd("envycontrol -q")
    is_hybrid = "hybrid" in mode_out.lower()
    checks.append({
        "category": "NVIDIA & GPU",
        "name": "EnvyControl Hybrid Mode",
        "score": 8 if is_hybrid else 0,
        "max": 8,
        "status": is_hybrid,
        "detail": f"Chế độ hiện tại: {mode_out}" if mode_out else "EnvyControl chưa được cấu hình"
    })
    
    # 3. Switcheroo running (7 pts)
    switcheroo_active, _ = run_cmd("systemctl is-active switcheroo-control")
    checks.append({
        "category": "NVIDIA & GPU",
        "name": "Switcheroo Control Service",
        "score": 7 if switcheroo_active else 0,
        "max": 7,
        "status": switcheroo_active,
        "detail": "Dịch vụ Switcheroo đang chạy" if switcheroo_active else "Dịch vụ Switcheroo dừng"
    })

    # --- THERMAL (Max 20) ---
    # 4. thermald active (8 pts)
    thermald_active, _ = run_cmd("systemctl is-active thermald")
    checks.append({
        "category": "Nhiệt độ & Quạt",
        "name": "Intel Thermal Daemon (thermald)",
        "score": 8 if thermald_active else 0,
        "max": 8,
        "status": thermald_active,
        "detail": "Dịch vụ thermald đang chạy" if thermald_active else "Dịch vụ thermald chưa kích hoạt"
    })
    
    # 5. sensors detected coretemp (7 pts)
    sensors_ok, sensors_out = run_cmd("sensors")
    coretemp_detected = "coretemp" in sensors_out.lower() or "temp" in sensors_out.lower()
    checks.append({
        "category": "Nhiệt độ & Quạt",
        "name": "Hardware Temperature Sensors",
        "score": 7 if (sensors_ok and coretemp_detected) else 0,
        "max": 7,
        "status": sensors_ok and coretemp_detected,
        "detail": "Phát hiện cảm biến nhiệt độ CPU/GPU" if coretemp_detected else "Không tìm thấy cảm biến nhiệt độ"
    })
    
    # 6. linuwu_sense loaded (5 pts)
    linuwu_loaded, _ = run_cmd("lsmod | grep -q 'linuwu_sense'")
    checks.append({
        "category": "Nhiệt độ & Quạt",
        "name": "Linuwu-Sense WMI Driver",
        "score": 5 if linuwu_loaded else 0,
        "max": 5,
        "status": linuwu_loaded,
        "detail": "WMI driver kiểm soát quạt/LED đã nạp" if linuwu_loaded else "Chưa nạp driver linuwu_sense"
    })

    # --- POWER & SSD & RAM (Max 25) ---
    # 7. TLP active (8 pts)
    tlp_active, _ = run_cmd("systemctl is-active tlp")
    checks.append({
        "category": "Nguồn & SSD & RAM",
        "name": "TLP Power Management",
        "score": 8 if tlp_active else 0,
        "max": 8,
        "status": tlp_active,
        "detail": "Dịch vụ TLP đang chạy ngầm" if tlp_active else "Dịch vụ TLP chưa chạy"
    })
    
    # 8. zRAM active (7 pts)
    zram_ok, zram_out = run_cmd("zramctl")
    zram_active = zram_ok and "zram0" in zram_out
    checks.append({
        "category": "Nguồn & SSD & RAM",
        "name": "zRAM Virtual Memory Swap",
        "score": 7 if zram_active else 0,
        "max": 7,
        "status": zram_active,
        "detail": "zRAM đã được cấu hình và hoạt động" if zram_active else "zRAM chưa được cấu hình"
    })
    
    # 9. fstrim.timer active (5 pts)
    fstrim_active, _ = run_cmd("systemctl is-active fstrim.timer")
    checks.append({
        "category": "Nguồn & SSD & RAM",
        "name": "fstrim SSD Timer",
        "score": 5 if fstrim_active else 0,
        "max": 5,
        "status": fstrim_active,
        "detail": "Đã lên lịch TRIM SSD định kỳ" if fstrim_active else "Chưa bật fstrim.timer"
    })
    
    # 10. I/O scheduler none for NVMe (5 pts)
    scheduler_none = False
    try:
        # Find any nvme scheduler attribute
        for d in os.listdir("/sys/block"):
            if d.startswith("nvme"):
                sched_path = f"/sys/block/{d}/queue/scheduler"
                if os.path.exists(sched_path):
                    with open(sched_path, "r") as f:
                        sched_content = f.read()
                    if "[none]" in sched_content:
                        scheduler_none = True
                        break
    except Exception:
        pass
    checks.append({
        "category": "Nguồn & SSD & RAM",
        "name": "NVMe I/O Scheduler (none)",
        "score": 5 if scheduler_none else 0,
        "max": 5,
        "status": scheduler_none,
        "detail": "Lập lịch NVMe đã chuyển sang 'none'" if scheduler_none else "Scheduler chưa tối ưu"
    })

    # --- KERNEL PARAMETERS (Max 15) ---
    # Read cmdline once
    cmdline_ok, cmdline_content = run_cmd("cat /proc/cmdline")
    
    # 11. mem_sleep_default=deep (5 pts)
    deep_sleep = "mem_sleep_default=deep" in cmdline_content
    checks.append({
        "category": "Nhân Kernel & GRUB",
        "name": "Kernel Deep Sleep (S3)",
        "score": 5 if deep_sleep else 0,
        "max": 5,
        "status": deep_sleep,
        "detail": "Đã ép dùng Deep Sleep chống hao pin" if deep_sleep else "Chưa kích hoạt S3 Sleep mặc định"
    })
    
    # 12. pci=noaer (5 pts)
    noaer = "pci=noaer" in cmdline_content
    checks.append({
        "category": "Nhân Kernel & GRUB",
        "name": "PCIe AER Warning Suppress",
        "score": 5 if noaer else 0,
        "max": 5,
        "status": noaer,
        "detail": "Đã tắt cảnh báo rác PCIe AER" if noaer else "Chưa tắt cảnh báo lỗi rác PCIe"
    })
    
    # 13. Kernel >= 6.8 (5 pts)
    k_ver = get_kernel_version()
    k_ok = k_ver >= 6.8
    checks.append({
        "category": "Nhân Kernel & GRUB",
        "name": "Kernel Version Core Support",
        "score": 5 if k_ok else 0,
        "max": 5,
        "status": k_ok,
        "detail": f"Phiên bản kernel đang chạy: {k_ver}" if k_ok else f"Kernel cũ ({k_ver}) có thể thiếu tính năng"
    })

    # --- MULTIMEDIA & AUDIO (Max 10) ---
    # 14. PipeWire running (5 pts)
    pipewire_active, _ = run_cmd("pgrep -x pipewire")
    checks.append({
        "category": "Đa phương tiện & Âm thanh",
        "name": "PipeWire Audio Server",
        "score": 5 if pipewire_active else 0,
        "max": 5,
        "status": pipewire_active,
        "detail": "Máy chủ PipeWire đang hoạt động" if pipewire_active else "Không phát hiện tiến trình PipeWire"
    })
    
    # 15. FFmpeg full (5 pts)
    _, ffmpeg_ver = run_cmd("ffmpeg -version")
    ffmpeg_full = "rpmfusion" in ffmpeg_ver.lower()
    checks.append({
        "category": "Đa phương tiện & Âm thanh",
        "name": "RPM Fusion FFmpeg Codec",
        "score": 5 if ffmpeg_full else 0,
        "max": 5,
        "status": ffmpeg_full,
        "detail": "Đã tráo đổi bản FFmpeg đầy đủ" if ffmpeg_full else "Chưa đổi sang FFmpeg đầy đủ"
    })

    # --- INPUT/LOCALIZATION (Max 5) ---
    # 16. fcitx5 running (5 pts)
    fcitx_active, _ = run_cmd("pgrep -x fcitx5")
    checks.append({
        "category": "Bộ gõ Tiếng Việt",
        "name": "Fcitx5 Input Framework",
        "score": 5 if fcitx_active else 0,
        "max": 5,
        "status": fcitx_active,
        "detail": "Fcitx5 đang chạy nền" if fcitx_active else "Fcitx5 chưa chạy"
    })

    total_score = sum(c["score"] for c in checks)
    return total_score, checks
