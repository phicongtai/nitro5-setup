# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess
import os

class DnfClean(ModuleBase):
    id = "dnf_clean"
    name = "Dọn dẹp gói mồ côi & Cache DNF5"
    description = "Gỡ bỏ các gói phụ thuộc mồ côi (autoremove), dọn cache tải gói của DNF5 và xóa các nhân kernel cũ (chỉ giữ lại 2 bản gần nhất)."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 autoremove -y", "Gỡ bỏ các gói phụ thuộc mồ côi không dùng nữa", is_sudo=True),
            Command("dnf5 clean all", "Xóa sạch bộ nhớ đệm (cache) của DNF5", is_sudo=True),
            Command("rm -rf /var/cache/dnf", "Xóa thư mục cache DNF trên đĩa", is_sudo=True),
            Command("dnf5 remove --oldinstallonly --setopt installonly_limit=2 kernel -y 2>/dev/null || true", "Gỡ bỏ các nhân kernel cũ (giữ lại 2 bản gần nhất)", is_sudo=True, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        return CheckResult(True, "✓ SẴN SÀNG", "Sẵn sàng dọn dẹp cache DNF5 và kernel cũ")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [] # Tác vụ dọn dẹp không thể hoàn tác


class JournalClean(ModuleBase):
    id = "journal_clean"
    name = "Dọn dẹp Nhật ký Hệ thống (Journal logs)"
    description = "Dọn dẹp log hệ thống cũ hơn 2 tuần và giới hạn kích thước log tối đa 100MB để tiết kiệm dung lượng."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("journalctl --vacuum-time=2weeks", "Dọn dẹp nhật ký hệ thống cũ hơn 2 tuần", is_sudo=True),
            Command("journalctl --vacuum-size=100M", "Dọn dẹp nhật ký hệ thống vượt quá 100MB", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        return CheckResult(True, "✓ SẴN SÀNG", "Sẵn sàng dọn dẹp logs hệ thống")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [] # Tác vụ dọn dẹp không thể hoàn tác


class UserCacheClean(ModuleBase):
    id = "temp_clean" # Giữ lại ID cũ để tương thích với config.json
    name = "Dọn dẹp cache của người dùng (~/.cache)"
    description = "Xóa sạch bộ nhớ đệm (cache) trong thư mục cá nhân để giải phóng dung lượng đĩa."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("rm -rf ~/.cache/*", "Xóa toàn bộ các tệp tin tạm trong ~/.cache", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        # Kiểm tra xem ~/.cache có dung lượng lớn không
        try:
            res = subprocess.run("du -sh ~/.cache 2>/dev/null | awk '{print $1}'", shell=True, capture_output=True, text=True)
            size = res.stdout.strip()
            if size:
                return CheckResult(True, "✓ SẴN SÀNG", f"Dung lượng cache hiện tại: {size}")
        except Exception:
            pass
        return CheckResult(True, "✓ SẴN SÀNG", "Sẵn sàng dọn dẹp cache người dùng")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [] # Tác vụ dọn dẹp không thể hoàn tác


class FlatpakClean(ModuleBase):
    id = "flatpak_clean"
    name = "Dọn dẹp thư viện Flatpak thừa"
    description = "Quét và gỡ bỏ các runtime, thư viện Flatpak cũ không còn ứng dụng nào sử dụng."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("flatpak uninstall --unused -y", "Gỡ bỏ các runtime Flatpak thừa không sử dụng", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        return CheckResult(True, "✓ SẴN SÀNG", "Sẵn sàng dọn dẹp Flatpak không sử dụng")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [] # Tác vụ dọn dẹp không thể hoàn tác


class SsdTrim(ModuleBase):
    id = "ssd_trim"
    name = "Chạy tối ưu SSD NVMe (fstrim)"
    description = "Chạy fstrim để thu hồi và tối ưu hóa các khối nhớ trống trên SSD NVMe."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("fstrim -av", "Thực thi lệnh fstrim trên toàn bộ phân vùng hỗ trợ", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        return CheckResult(True, "✓ SẴN SÀNG", "Sẵn sàng chạy tối ưu fstrim")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [] # Tác vụ dọn dẹp không thể hoàn tác


class TempBuildClean(ModuleBase):
    id = "temp_build_clean"
    name = "Dọn dẹp thư mục biên dịch driver tạm"
    description = "Xóa sạch toàn bộ các thư mục tạm được tải về/biên dịch trong quá trình cài đặt driver như linuwu-sense, damx, facer trong /tmp."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("rm -rf /tmp/damx* /var/tmp/linuwu-sense-build /tmp/acer-predator-build || true", "Xóa các thư mục build tạm thời trong /tmp và /var/tmp", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        has_predator = os.path.exists("/tmp/acer-predator-build")
        has_linuwu = os.path.exists("/var/tmp/linuwu-sense-build")
        if not (has_predator or has_linuwu):
            return CheckResult(True, "✓ SẠCH SẼ", "Không phát hiện thư mục biên dịch tạm thời nào cần dọn dẹp")
        return CheckResult(True, "✓ SẴN SÀNG", "Có thư mục tạm cần dọn dẹp trong /tmp hoặc /var/tmp")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [] # Tác vụ dọn dẹp không thể hoàn tác

# Danh sách xuất bản
MODULES = [
    DnfClean,
    JournalClean,
    UserCacheClean,
    FlatpakClean,
    SsdTrim,
    TempBuildClean
]
