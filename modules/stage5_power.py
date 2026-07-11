# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess
import os

class TlpPowerManagement(ModuleBase):
    id = "tlp_power_management"
    name = "Quản lý nguồn CPU & Hệ thống (TLP)"
    description = (
        "Cài đặt và cấu hình dịch vụ TLP thay thế cho tuned, "
        "tối ưu hóa điện năng tiêu thụ CPU Intel Gen 12 và GPU khi chạy pin."
    )
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        
        tlp_conf_content = (
            r"""cat > /etc/tlp.conf << 'EOF'
# --- CUSTOM TLP SETTINGS FOR ACER NITRO 5 ---
TLP_ENABLE=1
CPU_DRIVER_OPMODE_ON_AC=active
CPU_DRIVER_OPMODE_ON_BAT=active
CPU_SCALING_GOVERNOR_ON_AC=performance
CPU_SCALING_GOVERNOR_ON_BAT=powersave
CPU_ENERGY_PERF_POLICY_ON_AC=performance
CPU_ENERGY_PERF_POLICY_ON_BAT=power
CPU_BOOST_ON_AC=1
CPU_BOOST_ON_BAT=0
CPU_MAX_PERF_ON_AC=100
CPU_MAX_PERF_ON_BAT=60
PLATFORM_PROFILE_ON_AC=performance
PLATFORM_PROFILE_ON_BAT=low-power
START_CHARGE_THRESH_BAT0=75
STOP_CHARGE_THRESH_BAT0=80
USB_AUTOSUSPEND=1
WIFI_PWR_ON_AC=off
WIFI_PWR_ON_BAT=on
RUNTIME_PM_ON_AC=on
RUNTIME_PM_ON_BAT=auto
EOF"""
        )
        
        self.commands = [
            Command("dnf5 remove -y tuned tuned-ppd || true", "Gỡ bỏ tuned và tuned-ppd để tránh xung đột", is_sudo=True, skip_on_error=True),
            Command("dnf5 install -y tlp tlp-rdw", "Cài đặt TLP và tiện ích mở rộng", is_sudo=True),
            Command(tlp_conf_content, "Ghi cấu hình tối ưu TLP (/etc/tlp.conf)", is_sudo=True),
            Command("systemctl enable --now tlp", "Bật và khởi chạy dịch vụ TLP", is_sudo=True),
            Command("systemctl enable --now tlp-pd.service || true", "Kích hoạt tlp-pd.service để tương thích menu chọn chế độ GNOME", is_sudo=True, skip_on_error=True),
            Command("tlp start || true", "Áp dụng cấu hình TLP ngay lập tức", is_sudo=True, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("systemctl is-active tlp", shell=True, capture_output=True, text=True)
        if "active" in res.stdout:
            return CheckResult(True, "✓ OK", "TLP đang hoạt động ngầm")
        return CheckResult(False, "✗ CHƯA KÍCH HOẠT", "Dịch vụ TLP chưa chạy")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now tlp tlp-pd.service || true", "Dừng và vô hiệu hóa các dịch vụ TLP", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y tlp tlp-rdw || true", "Gỡ bỏ TLP", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /etc/tlp.conf || true", "Xóa file cấu hình TLP", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 install -y tuned tuned-ppd || true", "Cài đặt lại tuned và tuned-ppd mặc định", is_sudo=True, skip_on_error=True),
            ResetCommand("systemctl enable --now tuned || true", "Kích hoạt lại dịch vụ tuned", is_sudo=True, skip_on_error=True)
        ]


class BtrfsOptimize(ModuleBase):
    id = "btrfs_nvme"
    name = "Tối ưu hóa Btrfs NVMe SSD"
    description = "Thêm các tham số noatime, compress=zstd:1, space_cache=v2, discard=async vào fstab để tăng tốc độ I/O và kéo dài tuổi thọ SSD."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        cmd_backup = "cp /etc/fstab /etc/fstab.bak 2>/dev/null || true"
        cmd_btrfs = (
            "grep -q 'noatime' /etc/fstab || "
            "sed -i '/\\bbtrfs\\b/ s/\\bdefaults\\b/defaults,noatime/' /etc/fstab ; "
            "grep -q 'space_cache=v2' /etc/fstab || "
            "sed -i '/\\bbtrfs\\b/ s/compress=zstd:[0-9]*/compress=zstd:1,space_cache=v2/' /etc/fstab ; "
            "grep -q 'discard=async' /etc/fstab || "
            "sed -i '/\\bbtrfs\\b/ s/\\bcompress=/discard=async,compress=/' /etc/fstab"
        )
        self.commands = [
            Command(cmd_backup, "Sao lưu file /etc/fstab trước khi chỉnh sửa", is_sudo=True),
            Command(cmd_btrfs, "Tinh chỉnh tham số mount Btrfs trong /etc/fstab (an toàn, kiểm tra trước khi thêm)", is_sudo=True),
            Command("systemctl daemon-reload", "Tải lại systemd cấu hình mount", is_sudo=True),
            Command("mount -o remount,noatime / && mount -o remount,noatime /home || true", "Remount hệ thống tệp tin tức thời với tùy chọn noatime", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        root_ok = False
        home_ok = False
        if os.path.exists("/proc/mounts"):
            try:
                with open("/proc/mounts", "r") as f:
                    lines = f.readlines()
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        mount_point = parts[1]
                        options = parts[3].split(",")
                        if mount_point == "/":
                            if "noatime" in options and "discard=async" in options:
                                root_ok = True
                        elif mount_point == "/home":
                            if "noatime" in options and "discard=async" in options:
                                home_ok = True
            except Exception:
                pass

        fstab_ok = False
        if os.path.exists("/etc/fstab"):
            try:
                with open("/etc/fstab", "r") as f:
                    content = f.read()
                if "btrfs" in content:
                    if "noatime" in content and "discard=async" in content:
                        fstab_ok = True
                else:
                    fstab_ok = True
            except Exception:
                pass
        else:
            fstab_ok = True

        if root_ok and fstab_ok:
            msg = "Đã cấu hình và remount Btrfs với options tối ưu"
            if home_ok:
                msg += " (cả / và /home)"
            return CheckResult(True, "✓ OK", msg)
        return CheckResult(False, "✗ CHƯA TỐI ƯU", "Btrfs chưa được mount với options tối ưu (noatime, discard=async)")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("[ -f /etc/fstab.bak ] && mv /etc/fstab.bak /etc/fstab || (sed -i '/\\bbtrfs\\b/ s/noatime,//; s/discard=async,//; s/compress=zstd:[0-9]*,//; s/space_cache=v2,//' /etc/fstab || true)", "Khôi phục lại file /etc/fstab từ bản sao lưu hoặc gỡ các option", is_sudo=True, skip_on_error=True),
            ResetCommand("systemctl daemon-reload", "Tải lại cấu hình systemd mount", is_sudo=True),
            ResetCommand("mount -o remount / && mount -o remount /home || true", "Remount lại phân vùng hệ thống về mặc định", is_sudo=True, skip_on_error=True)
        ]


class FsTrimTimer(ModuleBase):
    id = "fstrim"
    name = "Kích hoạt TRIM cho ổ cứng SSD (fstrim.timer)"
    description = "Bật fstrim.timer định kỳ dọn dẹp các khối nhớ thừa trên ổ cứng SSD NVMe, giúp bảo vệ tuổi thọ SSD và giữ hiệu năng đọc ghi cao."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("systemctl enable --now fstrim.timer", "Kích hoạt fstrim.timer", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("systemctl is-active fstrim.timer", shell=True, capture_output=True, text=True)
        if "active" in res.stdout:
            return CheckResult(True, "✓ OK", "fstrim.timer đang hoạt động")
        return CheckResult(False, "✗ FAILED", "fstrim.timer chưa bật")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now fstrim.timer || true", "Vô hiệu hóa fstrim.timer", is_sudo=True, skip_on_error=True)
        ]


class SwappinessConfig(ModuleBase):
    id = "swappiness"
    name = "Tối ưu hóa RAM ảo (Chỉnh Swappiness động)"
    description = (
        "Tự động điều chỉnh Swappiness dựa trên dung lượng RAM và chế độ làm việc:\n"
        "AI/ML Research: dùng swappiness=60 để bảo vệ Page Cache cho dataset trên SSD.\n"
        "Desktop đa nhiệm: RAM <= 16GB dùng swappiness=100 (tối ưu zRAM), RAM > 16GB dùng swappiness=10."
    )
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        import json
        mem_gb = 16
        try:
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_kb = int(line.split()[1])
                            mem_gb = int(round(mem_kb / 1024.0 / 1024.0))
                            break
        except Exception:
            pass

        swappiness_mode = "aiml"
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    swappiness_mode = config_data.get("stage5", {}).get("swappiness_mode", "aiml")
            except Exception:
                pass

        if swappiness_mode == "aiml":
            swappiness_val = 60
        else:
            swappiness_val = 100 if mem_gb <= 16 else 10

        cmd_swappiness = f"echo 'vm.swappiness={swappiness_val}' | tee /etc/sysctl.d/99-nitro5.conf"

        self.commands = [
            Command("mkdir -p /etc/sysctl.d", "Tạo thư mục sysctl.d nếu chưa có", is_sudo=True),
            Command(cmd_swappiness, f"Thiết lập swappiness={swappiness_val} cho cấu hình {swappiness_mode.upper()} (RAM {mem_gb}GB)", is_sudo=True),
            Command("sysctl --system", "Nạp lại cấu hình sysctl hệ thống", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("cat /proc/sys/vm/swappiness", shell=True, capture_output=True, text=True)
        val = res.stdout.strip()
        return CheckResult(True, "✓ OK", f"Swappiness hiện tại: {val}")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/sysctl.d/99-nitro5.conf || true", "Xóa cấu hình swappiness tùy chỉnh", is_sudo=True, skip_on_error=True),
            ResetCommand("sysctl --system", "Nạp lại sysctl cấu hình hệ thống mặc định", is_sudo=True)
        ]


class IoSchedulerConfig(ModuleBase):
    id = "io_scheduler"
    name = "Tối ưu I/O Scheduler cho ổ SSD NVMe"
    description = "Thiết lập I/O Scheduler sang 'none' đối với các ổ NVMe để bỏ qua hàng đợi lập lịch trung gian CPU, tăng tối đa IOPS."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("echo 'ACTION==\"add|change\", KERNEL==\"nvme*\", ATTR{queue/scheduler}=\"none\"' | tee /etc/udev/rules.d/60-nvme-scheduler.rules", "Ghi udev rule cấu hình none scheduler cho NVMe", is_sudo=True),
            Command("udevadm control --reload-rules && udevadm trigger", "Nạp lại udev rules và áp dụng ngay", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        rule_path = "/etc/udev/rules.d/60-nvme-scheduler.rules"
        if os.path.exists(rule_path):
            return CheckResult(True, "✓ OK", "Đã ghi udev rule tối ưu")
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa tối ưu I/O scheduler")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/udev/rules.d/60-nvme-scheduler.rules || true", "Xóa udev rule lập lịch I/O NVMe", is_sudo=True, skip_on_error=True),
            ResetCommand("udevadm control --reload-rules && udevadm trigger", "Nạp lại udev rules và áp dụng cấu hình mặc định", is_sudo=True)
        ]


class UsbAutosuspendFix(ModuleBase):
    id = "usb_autosuspend_fix"
    name = "Sửa lỗi tự động ngắt chuột USB (USB Autosuspend Fix)"
    description = "Tạo udev rule vô hiệu hóa chế độ tự động ngắt nguồn (autosuspend) cho chuột gaming và thiết bị USB HID khác."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("mkdir -p /etc/udev/rules.d", "Tạo thư mục udev rules nếu chưa có", is_sudo=True),
            Command("echo -e '# Vô hiệu hóa USB autosuspend cho tất cả thiết bị USB HID/input\\nACTION==\"add\", SUBSYSTEM==\"usb\", DRIVERS==\"usbhid\", TEST==\"power/control\", ATTR{power/control}=\"on\"\\nACTION==\"add\", SUBSYSTEM==\"input\", TEST==\"power/control\", ATTR{power/control}=\"on\"' | tee /etc/udev/rules.d/50-usb-autosuspend.rules", "Ghi udev rule tắt USB autosuspend cho thiết bị đầu vào", is_sudo=True),
            Command("udevadm control --reload-rules && udevadm trigger", "Nạp lại udev rules và áp dụng cấu hình mới lập tức", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        rule_path = "/etc/udev/rules.d/50-usb-autosuspend.rules"
        if os.path.exists(rule_path):
            return CheckResult(True, "✓ OK", "Đã cấu hình udev rule vô hiệu hóa USB autosuspend")
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa cài đặt udev rule tắt USB autosuspend")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/udev/rules.d/50-usb-autosuspend.rules || true", "Xóa udev rule ngắt nguồn USB", is_sudo=True, skip_on_error=True),
            ResetCommand("udevadm control --reload-rules && udevadm trigger", "Nạp lại udev rules", is_sudo=True)
        ]


class ZramOptimize(ModuleBase):
    id = "zram_optimize"
    name = "Tối ưu hóa RAM ảo với zRAM (zstd compressed swap)"
    description = "Cấu hình zram-generator sử dụng thuật toán zstd, kích thước swap bằng 1/2 dung lượng RAM vật lý."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y zram-generator", "Cài đặt zram-generator", is_sudo=True),
            Command("echo -e '[zram0]\\nzram-size = ram / 2\\ncompression-algorithm = zstd\\nswap-priority = 100' | tee /etc/systemd/zram-generator.conf", "Tạo file cấu hình zram-generator.conf dùng zstd", is_sudo=True),
            Command("systemctl daemon-reload && systemctl restart systemd-zram-setup@zram0", "Khởi động và kích hoạt cấu hình zram0 mới", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        conf_path = "/etc/systemd/zram-generator.conf"
        if os.path.exists(conf_path):
            try:
                with open(conf_path, "r") as f:
                    content = f.read()
                if "compression-algorithm = zstd" in content and "zram-size = ram / 2" in content:
                    res = subprocess.run("zramctl 2>/dev/null", shell=True, capture_output=True, text=True)
                    if "zram0" in res.stdout:
                        return CheckResult(True, "✓ OK", "zRAM hoạt động (zstd, kích thước = RAM/2)")
            except Exception:
                pass
        return CheckResult(False, "✗ CHƯA TỐI ƯU", "Chưa cấu hình zram-generator tối ưu zstd")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/systemd/zram-generator.conf || true", "Xóa file cấu hình zram-generator", is_sudo=True, skip_on_error=True),
            ResetCommand("systemctl daemon-reload && systemctl stop systemd-zram-setup@zram0 || true", "Dừng dịch vụ zram0 setup", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y zram-generator || true", "Gỡ bỏ zram-generator", is_sudo=True, skip_on_error=True)
        ]


class AnanicyCpp(ModuleBase):
    id = "ananicy_cpp"
    name = "Ananicy-CPP (CPU task scheduler/priority)"
    description = "Trình lập lịch tác vụ tự động điều phối độ ưu tiên của CPU cho các ứng dụng đang chạy giúp giảm giật lag UI trên GNOME."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 copr enable -y bieszczaders/kernel-cachyos-addons", "Kích hoạt kho COPR bieszczaders/kernel-cachyos-addons chứa ananicy-cpp", is_sudo=True),
            Command("dnf5 install -y ananicy-cpp", "Cài đặt ananicy-cpp", is_sudo=True),
            Command("systemctl enable --now ananicy-cpp", "Kích hoạt dịch vụ ananicy-cpp", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("systemctl is-active ananicy-cpp 2>/dev/null", shell=True, capture_output=True, text=True)
        if "active" in res.stdout:
            return CheckResult(True, "✓ OK", "Dịch vụ ananicy-cpp đang chạy")
        if os.path.exists("/usr/bin/ananicy-cpp"):
            return CheckResult(True, "✓ OK", "Đã cài đặt ananicy-cpp (chưa chạy dịch vụ)")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Không tìm thấy ananicy-cpp")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now ananicy-cpp || true", "Dừng và vô hiệu hóa dịch vụ ananicy-cpp", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y ananicy-cpp || true", "Gỡ bỏ ananicy-cpp", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 copr disable -y bieszczaders/kernel-cachyos-addons || true", "Vô hiệu hóa kho COPR bieszczaders/kernel-cachyos-addons", is_sudo=True, skip_on_error=True)
        ]


class DirtyRatioConfig(ModuleBase):
    id = "dirty_ratio"
    name = "Tối ưu write-back SSD NVMe (dirty_ratio)"
    description = (
        "Cấu hình vm.dirty_ratio=20 và vm.dirty_background_ratio=10 để giảm thời gian "
        "dữ liệu nằm trong page cache trước khi flush xuống SSD NVMe."
    )
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command(
                "mkdir -p /etc/sysctl.d && "
                "echo -e 'vm.dirty_ratio=20\\nvm.dirty_background_ratio=10\\nvm.vfs_cache_pressure=50' "
                "| tee /etc/sysctl.d/99-nitro5-nvme.conf && sysctl --system",
                "Cấu hình dirty_ratio tối ưu cho SSD NVMe (dirty_ratio=20, background=10, cache_pressure=50)",
                is_sudo=True
            ),
        ]

    def validate(self) -> CheckResult:
        conf_path = "/etc/sysctl.d/99-nitro5-nvme.conf"
        if os.path.exists(conf_path):
            try:
                with open(conf_path, "r") as f:
                    content = f.read()
                if "dirty_ratio=20" in content:
                    return CheckResult(True, "✓ OK", "dirty_ratio=20, dirty_bg=10, vfs_cache=50 (NVMe Gen4 tối ưu)")
            except Exception:
                pass
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa tối ưu dirty_ratio cho NVMe")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/sysctl.d/99-nitro5-nvme.conf || true", "Xóa file cấu hình dirty_ratio cho NVMe", is_sudo=True, skip_on_error=True),
            ResetCommand("sysctl --system", "Nạp lại sysctl cấu hình hệ thống mặc định", is_sudo=True)
        ]


# Danh sách xuất bản
MODULES = [
    TlpPowerManagement,
    BtrfsOptimize,
    UsbAutosuspendFix,
    FsTrimTimer,
    SwappinessConfig,
    IoSchedulerConfig,
    ZramOptimize,
    DirtyRatioConfig,
    AnanicyCpp,
]
