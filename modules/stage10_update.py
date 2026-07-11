# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess
import os

class CheckKernelUpdate(ModuleBase):
    id = "check_kernel"
    name = "Kiểm tra cập nhật Kernel & Trạng thái Reboot"
    description = "Kiểm tra xem có bản cập nhật Kernel mới trên kho lưu trữ hay không, hoặc hệ thống có cần khởi động lại để áp dụng Kernel mới hay không."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = []

    def validate(self) -> CheckResult:
        # 1. Kiểm tra xem có cần khởi động lại để áp dụng kernel mới không (đã tải về nhưng chưa reboot)
        try:
            res_reboot = subprocess.run("dnf5 needs-restarting -k", shell=True, capture_output=True, text=True)
            if res_reboot.returncode != 0:
                return CheckResult(False, "⚠️ YÊU CẦU REBOOT", "Hệ thống đã cài đặt Kernel mới nhưng chưa khởi động lại để áp dụng.")
        except Exception:
            pass

        # 2. Kiểm tra xem trên kho có bản cập nhật kernel mới hay không
        try:
            res_update = subprocess.run("dnf5 check-update kernel", shell=True, capture_output=True, text=True)
            # DNF check-update trả về 100 nếu có bản cập nhật mới
            if res_update.returncode == 100:
                lines = [line.strip() for line in res_update.stdout.split('\n') if 'kernel' in line]
                detail = "Có bản Kernel mới sẵn sàng: " + ", ".join(lines[:2])
                return CheckResult(True, "ℹ️ CÓ CẬP NHẬT KERNEL", detail)
        except Exception:
            pass

        return CheckResult(True, "✓ ĐÃ MỚI NHẤT", "Kernel hiện tại đang chạy là mới nhất và không cần khởi động lại.")

    def get_reset_commands(self) -> list[ResetCommand]:
        return []


class SystemUpgrade(ModuleBase):
    id = "system_upgrade"
    name = "Cập nhật hệ thống (DNF5)"
    description = "Làm mới cache dnf5 và nâng cấp tất cả các gói phần mềm hệ thống hiện tại bao gồm cả Kernel lên phiên bản mới nhất."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 upgrade --refresh -y", "Đang chạy nâng cấp toàn bộ hệ thống qua dnf5", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        return CheckResult(True, "✓ SẴN SÀNG", "Sẵn sàng chạy nâng cấp hệ thống qua DNF5")

    def get_reset_commands(self) -> list[ResetCommand]:
        return []


class FlatpakUpgrade(ModuleBase):
    id = "flatpak_upgrade"
    name = "Cập nhật ứng dụng Flatpak"
    description = "Kiểm tra và cập nhật tất cả các ứng dụng và runtime được cài đặt qua Flatpak lên bản mới nhất."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("flatpak update -y", "Đang cập nhật các ứng dụng Flatpak", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        return CheckResult(True, "✓ SẴN SÀNG", "Sẵn sàng chạy cập nhật Flatpak")

    def get_reset_commands(self) -> list[ResetCommand]:
        return []


class DkmsAutoInstall(ModuleBase):
    id = "dkms_autoinstall"
    name = "Biên dịch lại driver DKMS (dkms autoinstall)"
    description = "Tự động biên dịch lại toàn bộ driver đã đăng ký qua DKMS (như driver Nvidia, Linuwu-Sense) cho kernel mới cài đặt để đảm bảo phần cứng nhận diện tốt ngay sau khi khởi động lại."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dkms autoinstall", "Chạy dkms autoinstall biên dịch driver cho các nhân kernel", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        return CheckResult(True, "✓ SẴN SÀNG", "Sẵn sàng chạy dkms autoinstall")

    def get_reset_commands(self) -> list[ResetCommand]:
        return []


class DamxUpdate(ModuleBase):
    id = "damx_update"
    name = "Cập nhật ứng dụng DAMX"
    description = "Tự động tải script remoteSetup.sh mới nhất của PXDiv để cập nhật/cài đặt lại phiên bản DAMX GUI mới nhất."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command(
                "curl -fsSL https://raw.githubusercontent.com/PXDiv/Div-Acer-Manager-Max/refs/heads/main/scripts/remoteSetup.sh -o /tmp/damx-remoteSetup.sh && "
                "chmod +x /tmp/damx-remoteSetup.sh && "
                "bash /tmp/damx-remoteSetup.sh 2>&1 | tee /var/log/damx-install.log",
                "Chạy script update/install chính thức của DAMX",
                is_sudo=True
            )
        ]

    def validate(self) -> CheckResult:
        damx_paths = [
            "/opt/damx/gui/DivAcerManagerMax",
            "/usr/bin/DivAcerManagerMax",
            "/usr/local/bin/DivAcerManagerMax"
        ]
        if any(os.path.exists(p) for p in damx_paths):
            return CheckResult(True, "✓ ĐÃ CÀI ĐẶT", "DAMX GUI đã được cài đặt (Có thể chạy cập nhật bản mới nhất)")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "DAMX chưa được cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        # Reset DAMX (Uninstall DAMX)
        return [
            ResetCommand("systemctl stop damx-daemon.service || true", "Dừng dịch vụ damx-daemon", is_sudo=True),
            ResetCommand("systemctl disable damx-daemon.service || true", "Vô hiệu hóa dịch vụ damx-daemon", is_sudo=True),
            ResetCommand("rm -f /etc/systemd/system/damx-daemon.service", "Xóa file service damx-daemon", is_sudo=True),
            ResetCommand("systemctl daemon-reload", "Tải lại systemd configuration", is_sudo=True),
            ResetCommand("rm -rf /opt/damx /usr/local/bin/damx-launcher /usr/share/applications/damx.desktop /var/log/DAMX_Daemon_Log.log", "Xóa các file ứng dụng DAMX", is_sudo=True)
        ]

# Danh sách xuất bản
MODULES = [
    CheckKernelUpdate,
    SystemUpgrade,
    FlatpakUpgrade,
    DkmsAutoInstall,
    DamxUpdate
]
