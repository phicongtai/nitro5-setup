# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess
import os

class BtrfsSnapshot(ModuleBase):
    id = "btrfs_snapshot"
    name = "Btrfs Snapshot (Snapper & grub-btrfs)"
    description = "Cài đặt Snapper và grub-btrfs để tự động tạo snapshot hệ thống trước khi cập nhật phần mềm, cho phép khôi phục (rollback) trực tiếp từ màn hình boot GRUB."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        
        snapper_conf = (
            "sed -i 's/TIMELINE_LIMIT_HOURLY=\"[0-9]*\"/TIMELINE_LIMIT_HOURLY=\"5\"/g' /etc/snapper/configs/root && "
            "sed -i 's/TIMELINE_LIMIT_DAILY=\"[0-9]*\"/TIMELINE_LIMIT_DAILY=\"7\"/g' /etc/snapper/configs/root && "
            "sed -i 's/TIMELINE_LIMIT_WEEKLY=\"[0-9]*\"/TIMELINE_LIMIT_WEEKLY=\"4\"/g' /etc/snapper/configs/root && "
            "sed -i 's/TIMELINE_LIMIT_MONTHLY=\"[0-9]*\"/TIMELINE_LIMIT_MONTHLY=\"3\"/g' /etc/snapper/configs/root"
        )
        
        self.commands = [
            Command("dnf5 install -y snapper python3-dnf-plugin-snapper", "Cài đặt snapper và plugin snapper cho DNF", is_sudo=True),
            Command("snapper -c root create-config / 2>/dev/null || true", "Khởi tạo cấu hình Snapper cho phân vùng root", is_sudo=True),
            Command("dnf5 copr enable heitbaum/grub-btrfs -y", "Bật kho COPR heitbaum/grub-btrfs", is_sudo=True),
            Command("dnf5 install -y grub-btrfs", "Cài đặt công cụ tích hợp snapshot vào GRUB (grub-btrfs)", is_sudo=True),
            Command("systemctl enable --now grub-btrfsd", "Kích hoạt dịch vụ giám sát tự động cập nhật menu boot GRUB", is_sudo=True),
            Command(snapper_conf, "Cấu hình giới hạn lưu trữ snapshot timeline hợp lý", is_sudo=True),
            Command("systemctl enable --now snapper-timeline.timer snapper-cleanup.timer", "Kích hoạt các timers tự động dọn dẹp và sao lưu theo lịch của Snapper", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("systemctl is-active grub-btrfsd", shell=True, capture_output=True, text=True)
        snapper_ok = os.path.exists("/etc/snapper/configs/root")
        if "active" in res.stdout and snapper_ok:
            return CheckResult(True, "✓ OK", "Snapper & grub-btrfs đang hoạt động")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cấu hình Snapper hoặc grub-btrfs")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now grub-btrfsd snapper-timeline.timer snapper-cleanup.timer || true", "Tắt các dịch vụ snapshot và timer dọn dẹp", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y snapper python3-dnf-plugin-snapper grub-btrfs || true", "Gỡ bỏ các gói Snapper và grub-btrfs", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -rf /etc/snapper || true", "Xóa thư mục cấu hình Snapper", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 copr disable heitbaum/grub-btrfs -y || true", "Vô hiệu hóa kho COPR grub-btrfs", is_sudo=True, skip_on_error=True)
        ]


class FirewallDevPorts(ModuleBase):
    id = "firewall_dev_ports"
    name = "Mở cổng tường lửa cho Dev Server"
    description = "Mở các cổng phổ biến (3000, 5000, 8000) trên tường lửa Fedora Workstation để phát triển web cục bộ dễ dàng."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("firewall-cmd --zone=FedoraWorkstation --add-port=3000/tcp --permanent || firewall-cmd --zone=public --add-port=3000/tcp --permanent", "Mở cổng 3000/tcp", is_sudo=True),
            Command("firewall-cmd --zone=FedoraWorkstation --add-port=5000/tcp --permanent || firewall-cmd --zone=public --add-port=5000/tcp --permanent", "Mở cổng 5000/tcp", is_sudo=True),
            Command("firewall-cmd --zone=FedoraWorkstation --add-port=8000/tcp --permanent || firewall-cmd --zone=public --add-port=8000/tcp --permanent", "Mở cổng 8000/tcp", is_sudo=True),
            Command("firewall-cmd --reload", "Nạp lại cấu hình tường lửa để áp dụng ngay", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("firewall-cmd --list-ports", shell=True, capture_output=True, text=True)
        if "3000/tcp" in res.stdout and "5000/tcp" in res.stdout and "8000/tcp" in res.stdout:
            return CheckResult(True, "✓ OK", "Các cổng 3000, 5000, 8000 đã mở")
        return CheckResult(False, "✗ CHƯA MỞ", "Các cổng dev server chưa được mở")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("firewall-cmd --zone=FedoraWorkstation --remove-port=3000/tcp --permanent || firewall-cmd --zone=public --remove-port=3000/tcp --permanent || true", "Đóng cổng 3000/tcp", is_sudo=True, skip_on_error=True),
            ResetCommand("firewall-cmd --zone=FedoraWorkstation --remove-port=5000/tcp --permanent || firewall-cmd --zone=public --remove-port=5000/tcp --permanent || true", "Đóng cổng 5000/tcp", is_sudo=True, skip_on_error=True),
            ResetCommand("firewall-cmd --zone=FedoraWorkstation --remove-port=8000/tcp --permanent || firewall-cmd --zone=public --remove-port=8000/tcp --permanent || true", "Đóng cổng 8000/tcp", is_sudo=True, skip_on_error=True),
            ResetCommand("firewall-cmd --reload", "Nạp lại cấu hình tường lửa", is_sudo=True)
        ]


class EthernetEeeFix(ModuleBase):
    id = "ethernet_eee_fix"
    name = "Fix lỗi rớt mạng Ethernet Realtek Killer E2600"
    description = "Tắt chế độ Energy Efficient Ethernet (EEE) trên Realtek Killer E2600 để sửa triệt để lỗi rớt mạng ngẫu nhiên."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        
        script_content = (
            r"""cat > /etc/NetworkManager/dispatcher.d/99-disable-eee << 'EOF'
#!/bin/bash
if [ "$1" == "enp43s0" ] && [ "$2" == "up" ]; then
    /usr/sbin/ethtool --set-eee enp43s0 eee off
fi
EOF"""
        )
        
        self.commands = [
            Command("dnf5 install -y ethtool", "Cài đặt công cụ ethtool", is_sudo=True),
            Command("ethtool -i enp43s0 2>/dev/null || echo 'Không phát hiện cổng enp43s0'", "Kiểm tra driver card mạng enp43s0", is_sudo=False),
            Command(script_content, "Tạo NetworkManager dispatcher script tắt EEE", is_sudo=True),
            Command("chmod +x /etc/NetworkManager/dispatcher.d/99-disable-eee", "Cấp quyền thực thi cho dispatcher script", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        filepath = "/etc/NetworkManager/dispatcher.d/99-disable-eee"
        if os.path.exists(filepath) and os.access(filepath, os.X_OK):
            return CheckResult(True, "✓ OK", "Đã cấu hình tự động tắt EEE cho enp43s0")
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa tắt EEE hoặc thiếu kịch bản NM")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/NetworkManager/dispatcher.d/99-disable-eee || true", "Xóa script tắt EEE", is_sudo=True, skip_on_error=True)
        ]


class WebcamSetup(ModuleBase):
    id = "webcam_setup"
    name = "Cài đặt & Kiểm tra Webcam"
    description = "Đảm bảo cài đặt các thư viện v4l-utils và Cheese để sẵn sàng sử dụng và kiểm tra Webcam HD Acer."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y v4l-utils cheese", "Cài đặt v4l-utils và ứng dụng Cheese để test webcam", is_sudo=True),
            Command("v4l2-ctl --list-formats-ext -d /dev/video0 2>/dev/null || echo 'Không tìm thấy webcam /dev/video0'", "Kiểm tra định dạng camera hỗ trợ", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q cheese", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Cheese đã cài đặt, sẵn sàng kiểm tra camera")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Cheese chưa được cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y cheese v4l-utils || true", "Gỡ bỏ ứng dụng Cheese và v4l-utils", is_sudo=True, skip_on_error=True)
        ]


class ThunderboltPolicy(ModuleBase):
    id = "thunderbolt_policy"
    name = "Thunderbolt 4 Auto-Authorize"
    description = "Cấu hình bolt daemon tự động cấp quyền (auto-authorize) cho các thiết bị ngoại vi Thunderbolt 4 / USB4."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        
        conf_content = (
            r"""mkdir -p /etc/bolt && cat > /etc/bolt/bolt.conf << 'EOF'
[main]
DefaultPolicy=auto
EOF"""
        )
        
        self.commands = [
            Command("systemctl enable --now bolt || true", "Kích hoạt dịch vụ bolt", is_sudo=True, skip_on_error=True),
            Command(conf_content, "Cấu hình DefaultPolicy=auto cho Thunderbolt", is_sudo=True),
            Command("systemctl restart bolt || true", "Khởi động lại bolt daemon", is_sudo=True, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        filepath = "/etc/bolt/bolt.conf"
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                if "DefaultPolicy=auto" in content:
                    return CheckResult(True, "✓ OK", "Đã bật tự động kết nối Thunderbolt")
            except Exception:
                pass
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa bật chính sách auto-authorize")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/bolt/bolt.conf || true", "Xóa file cấu hình bolt.conf", is_sudo=True, skip_on_error=True),
            ResetCommand("systemctl restart bolt || true", "Khởi động lại dịch vụ bolt", is_sudo=True, skip_on_error=True)
        ]

# Danh sách xuất bản
MODULES = [
    BtrfsSnapshot,
    FirewallDevPorts,
    EthernetEeeFix,
    WebcamSetup,
    ThunderboltPolicy
]
