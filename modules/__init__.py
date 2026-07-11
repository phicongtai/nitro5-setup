# -*- coding: utf-8 -*-
import os

from modules.stage1_system import MODULES as STAGE1_MODULES
from modules.stage2_nvidia import MODULES as STAGE2_MODULES
from modules.stage3_codec import MODULES as STAGE3_MODULES
from modules.stage4_thermal import MODULES as STAGE4_MODULES
from modules.stage5_power import MODULES as STAGE5_MODULES
from modules.stage7_developer import MODULES as STAGE7_MODULES
from modules.stage8_cleanup import MODULES as STAGE8_MODULES
from modules.stage10_update import MODULES as STAGE10_MODULES
from modules.stage11_advanced import MODULES as STAGE11_MODULES

# ─────────────────────────────────────────────────────────────────────
# Chi ho tro GNOME (Fedora Workstation)
# ─────────────────────────────────────────────────────────────────────
_CURRENT_DE = "gnome"

from modules.stage6_gnome import MODULES as STAGE6_MODULES
_STAGE6_NAME = "GNOME & Phan mem"
_STAGE6_DESC = (
    "Cai dat GNOME Tweaks, Extensions (AppIndicator, Caffeine, Dash-to-Dock), "
    "Night Light, Flatpak apps va Steam."
)

# Thong tin DE hien tai (co the doc tu ben ngoai)
DETECTED_DE = _CURRENT_DE

STAGES = {
    "stage1": {
        "name": "Hệ thống cơ bản",
        "description": "Cập nhật hệ điều hành và kích hoạt các kho phần mềm chính (RPM Fusion, Flathub). Tối ưu DNF5: deltarpm, fastest mirror, countme=off.",
        "modules": STAGE1_MODULES
    },
    "stage2": {
        "name": "Driver NVIDIA & GPU",
        "description": "Cài đặt Driver NVIDIA độc quyền, CUDA, VA-API, các công cụ tối ưu card đồ họa. Sửa lỗi GDM Wayland và NVIDIA suspend/resume.",
        "modules": STAGE2_MODULES
    },
    "stage3": {
        "name": "Codec & Âm thanh",
        "description": "Cài đặt đầy đủ các codec giải mã đa phương tiện (H.264, H.265, AV1) và cấu hình máy chủ âm thanh PipeWire.",
        "modules": STAGE3_MODULES
    },
    "stage4": {
        "name": "Tối ưu nhiệt độ & Quạt",
        "description": "Cài đặt cảm biến nhiệt độ (lm_sensors), thermald chống quá nhiệt, Linux-NitroSense kiểm soát quạt và RGB bàn phím.",
        "modules": STAGE4_MODULES
    },
    "stage5": {
        "name": "Nguồn & SSD & RAM",
        "description": "Cấu hình TLP Power Management, zRAM zstd, dirty_ratio NVMe, swappiness tối ưu, I/O scheduler và TRIM SSD.",
        "modules": STAGE5_MODULES
    },
    "stage6": {
        "name": _STAGE6_NAME,
        "description": _STAGE6_DESC,
        "modules": STAGE6_MODULES
    },
    "stage7": {
        "name": "Công cụ & Lập trình",
        "description": "Cài đặt Chrome, VS Code, Obsidian, Git+GitHub CLI, C++, Python, Java, Node.js, Rust (rustup) và Podman container runtime.",
        "modules": STAGE7_MODULES
    },
    "stage8": {
        "name": "Dọn dẹp hệ thống",
        "description": "Dọn dẹp các tệp tin tạm, cache DNF5 và các thư viện Flatpak không sử dụng sau khi cài đặt.",
        "modules": STAGE8_MODULES
    },
    "stage10": {
        "name": "Cập nhật Toàn diện (1-Click)",
        "description": "Quét kiểm tra và cập nhật tất cả các phần mềm hệ thống (qua DNF5), ứng dụng Flatpak, và kiểm tra trạng thái cập nhật Kernel mới.",
        "modules": STAGE10_MODULES
    },
    "stage11": {
        "name": "Nâng cao & Tùy chọn",
        "description": "Các thiết lập nâng cao và tùy chọn bổ sung như Btrfs Snapper, mở cổng firewall, và tối ưu hóa Thunderbolt.",
        "modules": STAGE11_MODULES
    },
}
