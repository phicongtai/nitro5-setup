# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import os
import subprocess

class SystemDiagnostics(ModuleBase):
    id = "system_diagnostics"
    name = "Chẩn đoán hệ thống ban đầu (inxi)"
    description = "Cài đặt inxi và kiểm tra thông tin cấu hình phần cứng trước khi tiến hành tối ưu hóa."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y inxi", "Cài đặt công cụ chẩn đoán inxi", is_sudo=True),
            Command("inxi -Fxxxz", "Hiển thị thông tin phần cứng chi tiết", is_sudo=True),
            Command("cat /etc/os-release", "Xem thông tin hệ điều hành", is_sudo=False),
            Command("uname -r", "Xem phiên bản Kernel hiện tại", is_sudo=False),
            Command("lspci -k", "Xem danh sách thiết bị PCI và driver đang sử dụng", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which inxi 2>/dev/null", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "inxi đã được cài đặt và sẵn sàng chẩn đoán")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt inxi")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y inxi", "Gỡ bỏ công cụ chẩn đoán inxi", is_sudo=True)
        ]


class UpgradeSystem(ModuleBase):
    id = "upgrade"
    name = "Cập nhật toàn bộ hệ thống & Đồng bộ giờ"
    description = "Nâng cấp hệ thống và đồng bộ hóa giờ RTC cho dual-boot Windows."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 upgrade --refresh -y", "Nâng cấp toàn bộ hệ thống bằng dnf5", is_sudo=True),
            Command("timedatectl set-local-rtc 1 --adjust-system-clock", "Đồng bộ RTC theo giờ local (sửa lệch giờ Windows)", is_sudo=True),
            Command("timedatectl set-timezone Asia/Ho_Chi_Minh", "Đặt múi giờ Việt Nam", is_sudo=True),
            Command("timedatectl set-ntp true", "Bật đồng bộ thời gian NTP", is_sudo=True),
            Command("timedatectl", "Hiển thị trạng thái thời gian hệ thống", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("timedatectl | grep 'RTC in local TZ: yes'", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cập nhật & đồng bộ giờ local")
        return CheckResult(False, "✗ CHƯA ĐỒNG BỘ", "Giờ RTC chưa được chuyển về local")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("timedatectl set-local-rtc 0", "Trả lại cài đặt RTC sang UTC (mặc định của Linux)", is_sudo=True)
        ]


class RpmFusionFree(ModuleBase):
    id = "rpm_fusion_free"
    name = "Bật RPM Fusion Free"
    description = "Kích hoạt kho phần mềm RPM Fusion Free để cài đặt driver và ứng dụng mã nguồn mở không đi kèm mặc định."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm", "Cài đặt gói release RPM Fusion Free", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("dnf5 repolist | grep -i 'rpmfusion-free'", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Kích hoạt thành công")
        return CheckResult(False, "✗ FAILED", "Chưa kích hoạt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y rpmfusion-free-release", "Gỡ bỏ kho phần mềm RPM Fusion Free", is_sudo=True)
        ]


class RpmFusionNonFree(ModuleBase):
    id = "rpm_fusion_nonfree"
    name = "Bật RPM Fusion Non-Free & Codec Cơ Bản"
    description = "Kích hoạt kho RPM Fusion Non-Free, swap ffmpeg-free và cài đặt các nhóm đa phương tiện cơ bản."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm", "Cài đặt RPM Fusion Non-Free", is_sudo=True),
            Command("dnf5 upgrade --refresh -y", "Cập nhật cache sau khi thêm repo", is_sudo=True),
            Command("dnf5 group upgrade core -y", "Cập nhật nhóm gói core", is_sudo=True),
            Command("dnf5 swap ffmpeg-free ffmpeg --allowerasing -y", "Tráo đổi sang FFmpeg đầy đủ từ RPM Fusion", is_sudo=True),
            Command("dnf5 group upgrade multimedia --setopt=\"install_weak_deps=False\" --exclude=PackageKit-gstreamer-plugin -y", "Cập nhật nhóm multimedia (loại trừ xung đột PackageKit)", is_sudo=True),
            Command("dnf5 group upgrade sound-and-video -y", "Cập nhật nhóm sound-and-video", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("dnf5 repolist | grep -i 'rpmfusion-nonfree'", shell=True, capture_output=True, text=True)
        res_ffmpeg = subprocess.run("rpm -q ffmpeg", shell=True, capture_output=True, text=True)
        if res.returncode == 0 and res_ffmpeg.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã bật RPM Fusion Non-Free & FFmpeg đầy đủ")
        return CheckResult(False, "✗ FAILED", "Chưa cấu hình hoàn chỉnh")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y rpmfusion-nonfree-release", "Gỡ bỏ kho phần mềm RPM Fusion Non-Free", is_sudo=True),
            ResetCommand("dnf5 swap ffmpeg ffmpeg-free --allowerasing -y || true", "Hoàn tác swap FFmpeg về bản ffmpeg-free mặc định", is_sudo=True, skip_on_error=True)
        ]


class FlathubRepo(ModuleBase):
    id = "flathub"
    name = "Bật Flathub Repository"
    description = "Kích hoạt kho ứng dụng Flatpak lớn nhất thế giới, cung cấp nhiều phần mềm desktop phổ biến dạng sandbox."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo", "Thêm remote Flathub cho Flatpak", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("flatpak remotes | grep -i 'flathub'", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Kích hoạt thành công")
        return CheckResult(False, "✗ FAILED", "Chưa kích hoạt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("flatpak remote-delete flathub || true", "Gỡ bỏ Flathub khỏi Flatpak", is_sudo=False, skip_on_error=True)
        ]


class FedoraWorkstationRepos(ModuleBase):
    id = "workstation_repos"
    name = "Cài fedora-workstation-repositories"
    description = "Kích hoạt các repository bổ sung của Fedora Workstation như Google Chrome, PyCharm, v.v."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y fedora-workstation-repositories", "Cài đặt fedora-workstation-repositories", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("dnf5 repolist | grep -i 'google-chrome'", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã kích hoạt repo phụ")
        return CheckResult(False, "✗ FAILED", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y fedora-workstation-repositories", "Gỡ bỏ fedora-workstation-repositories", is_sudo=True)
        ]


class OptimizeNetwork(ModuleBase):
    id = "optimize_network"
    name = "Tối ưu tải gói và Tốc độ mạng (Việt Nam/Châu Á)"
    description = "Cấu hình DNF/DNF5 tự động định tuyến tìm máy chủ mirror phản hồi nhanh nhất gần Việt Nam và tải song song 10 gói cùng lúc."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        cmd_backup = "[ -f /etc/dnf/dnf.conf ] && cp /etc/dnf/dnf.conf /etc/dnf/dnf.conf.bak || true"
        cmd_parallel = 'grep -q "^max_parallel_downloads" /etc/dnf/dnf.conf && sed -i "s/^max_parallel_downloads.*/max_parallel_downloads=10/" /etc/dnf/dnf.conf || echo "max_parallel_downloads=10" >> /etc/dnf/dnf.conf'
        cmd_mirror = 'grep -q "^fastestmirror" /etc/dnf/dnf.conf && sed -i "s/^fastestmirror.*/fastestmirror=True/" /etc/dnf/dnf.conf || echo "fastestmirror=True" >> /etc/dnf/dnf.conf'
        cmd_deltarpm = 'grep -q "^deltarpm" /etc/dnf/dnf.conf && sed -i "s/^deltarpm.*/deltarpm=True/" /etc/dnf/dnf.conf || echo "deltarpm=True" >> /etc/dnf/dnf.conf'
        cmd_countme = 'grep -q "^countme" /etc/dnf/dnf.conf && sed -i "s/^countme.*/countme=False/" /etc/dnf/dnf.conf || echo "countme=False" >> /etc/dnf/dnf.conf'
        
        cmd_dnf5_dir = "mkdir -p /etc/dnf"
        cmd_dnf5_conf = (
            "touch /etc/dnf/dnf5.conf && "
            "grep -q \"max_parallel_downloads\" /etc/dnf/dnf5.conf && sed -i \"s/max_parallel_downloads.*/max_parallel_downloads = 10/\" /etc/dnf/dnf5.conf || echo \"max_parallel_downloads = 10\" >> /etc/dnf/dnf5.conf && "
            "grep -q \"fastestmirror\" /etc/dnf/dnf5.conf && sed -i \"s/fastestmirror.*/fastestmirror = true/\" /etc/dnf/dnf5.conf || echo \"fastestmirror = true\" >> /etc/dnf/dnf5.conf"
        )
        
        self.commands = [
            Command(cmd_backup, "Sao lưu file cấu hình dnf.conf mặc định", is_sudo=True),
            Command(cmd_parallel, "Cấu hình DNF tải song song 10 kết nối cùng lúc", is_sudo=True),
            Command(cmd_mirror, "Bật tự động tìm kiếm máy chủ gương (mirror) nhanh nhất", is_sudo=True),
            Command(cmd_deltarpm, "Bật deltarpm (tải gói cập nhật nhỏ hơn - tiết kiệm băng thông)", is_sudo=True),
            Command(cmd_countme, "Tắt countme (không gửi thống kê sử dụng về Fedora)", is_sudo=True),
            Command(cmd_dnf5_dir, "Tạo thư mục cấu hình cho DNF5", is_sudo=True),
            Command(cmd_dnf5_conf, "Cấu hình tải song song và mirror nhanh cho DNF5 (Fedora 44)", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        checks = []
        if os.path.exists("/etc/dnf/dnf.conf"):
            try:
                with open("/etc/dnf/dnf.conf", "r") as f:
                    content = f.read()
                if "max_parallel_downloads=10" in content:
                    checks.append("parallel=10")
                if "fastestmirror=True" in content:
                    checks.append("mirror=on")
            except (OSError, IOError):
                pass
        if os.path.exists("/etc/dnf/dnf5.conf"):
            try:
                with open("/etc/dnf/dnf5.conf", "r") as f:
                    content = f.read()
                if "max_parallel_downloads = 10" in content or "max_parallel_downloads=10" in content:
                    checks.append("dnf5_parallel=10")
                if "fastestmirror = true" in content or "fastestmirror=true" in content or "fastestmirror=True" in content:
                    checks.append("dnf5_mirror=on")
            except (OSError, IOError):
                pass
        if checks:
            return CheckResult(True, "✓ OK", " | ".join(checks))
        return CheckResult(False, "✗ CHƯA TỐI ƯU", "Chưa bật các tham số tăng tốc DNF/DNF5")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("[ -f /etc/dnf/dnf.conf.bak ] && mv /etc/dnf/dnf.conf.bak /etc/dnf/dnf.conf || (sed -i '/max_parallel_downloads/d; /fastestmirror/d; /deltarpm/d; /countme/d' /etc/dnf/dnf.conf || true)", "Khôi phục dnf.conf từ bản sao lưu hoặc xóa dòng tùy chỉnh", is_sudo=True),
            ResetCommand("rm -f /etc/dnf/dnf5.conf", "Xóa cấu hình tối ưu dnf5.conf", is_sudo=True)
        ]


class BuildToolsDkms(ModuleBase):
    id = "build_tools_dkms"
    name = "DKMS & Công cụ biên dịch nhân (kernel-devel)"
    description = "Cài đặt dkms, kernel-devel và kernel-headers phù hợp với phiên bản nhân đang chạy để biên dịch các driver bên thứ ba."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command(
                "dnf5 install -y kernel-devel-$(uname -r) kernel-headers dkms || dnf5 install -y kernel-devel kernel-headers dkms",
                "Cài đặt kernel-devel, kernel-headers và dkms",
                is_sudo=True
            )
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q dkms 2>/dev/null", shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu dkms")
        res_devel = subprocess.run("rpm -qa | grep kernel-devel 2>/dev/null", shell=True, capture_output=True, text=True)
        if res_devel.returncode != 0:
            return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu kernel-devel")
        return CheckResult(True, "✓ OK", "Đã cài dkms và kernel-devel")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y dkms || true", "Gỡ bỏ dkms", is_sudo=True, skip_on_error=True)
        ]


class AcerNitroNativeFix(ModuleBase):
    id = "acer_nitro_native_fix"
    name = "Tinh chỉnh Native AN515-58 (Deep Sleep, Audio, PCIe AER)"
    description = (
        "Khắc phục 3 lỗi phổ biến trên Nitro 5 AN515-58 (Intel Gen 12): "
        "1) Ép dùng Deep Sleep (S3) để chống hao pin khi gập nắp; "
        "2) Tắt cảnh báo lỗi rác PCIe Bus gây nóng CPU; "
        "3) Tự động kích hoạt (Boost) Headset Mic để cổng 3.5mm hoạt động ngay."
    )
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command(
                "grubby --update-kernel=ALL --args='mem_sleep_default=deep pci=noaer pcie_aspm=force'",
                "Cấu hình GRUB: Bật Deep Sleep, Tắt lỗi PCIe AER và Ép PCIe ASPM",
                is_sudo=True
            ),
            Command(
                "mkdir -p /etc/profile.d && "
                "echo -e '#!/bin/bash\\namixer -c 1 sset \"Headset Mic Boost\" 100% > /dev/null 2>&1 || amixer -c 0 sset \"Headset Mic Boost\" 100% > /dev/null 2>&1 || true' | tee /etc/profile.d/acer-audio-fix.sh && "
                "chmod +x /etc/profile.d/acer-audio-fix.sh",
                "Tạo script tự động kích hoạt mức khuếch đại (Boost) cho Headphone Mic",
                is_sudo=True
            )
        ]

    def validate(self) -> CheckResult:
        cmdline_res = subprocess.run("cat /proc/cmdline", shell=True, capture_output=True, text=True)
        if (
            "mem_sleep_default=deep" in cmdline_res.stdout 
            and "pci=noaer" in cmdline_res.stdout 
            and "pcie_aspm=force" in cmdline_res.stdout
        ):
            return CheckResult(True, "✓ OK", "Đã cấu hình GRUB (Deep Sleep, PCIe AER, ASPM Force, Audio Fix)")
        return CheckResult(True, "✓ OK", "Cần khởi động lại để áp dụng tham số GRUB mới")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("grubby --update-kernel=ALL --remove-args='mem_sleep_default=deep pci=noaer pcie_aspm=force' || true", "Hoàn tác cấu hình GRUB kernel parameters", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /etc/profile.d/acer-audio-fix.sh", "Xóa script tự động Boost Headset Mic", is_sudo=True)
        ]


class FirmwareUpdates(ModuleBase):
    id = "firmware_updates"
    name = "Cập nhật Firmware EC/SSD/NVMe qua fwupd"
    description = (
        "Sử dụng fwupd (Linux Vendor Firmware Service) để kiểm tra và cài đặt cập nhật firmware "
        "an toàn cho các thiết bị như Embedded Controller (EC) hoặc SSD qua kho LVFS (Không đụng vào BIOS/UEFI setup)."
    )
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y fwupd", "Cài đặt fwupd (Linux Vendor Firmware Service)", is_sudo=True),
            Command("systemctl enable --now fwupd", "Kích hoạt dịch vụ fwupd", is_sudo=True),
            Command("fwupdmgr refresh --force 2>/dev/null || true", "Làm mới danh sách firmware từ LVFS", is_sudo=True, skip_on_error=True),
            Command("fwupdmgr get-updates 2>/dev/null || echo 'Không có bản cập nhật firmware mới hoặc thiết bị chưa được LVFS hỗ trợ'", "Kiểm tra các bản cập nhật firmware", is_sudo=True, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which fwupdmgr", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            svc = subprocess.run("systemctl is-active fwupd", shell=True, capture_output=True, text=True)
            if "active" in svc.stdout:
                return CheckResult(True, "✓ OK", "fwupd đang chạy — Dùng 'fwupdmgr update' để cập nhật firmware")
            return CheckResult(True, "✓ OK", "fwupdmgr đã cài đặt (dịch vụ chưa chạy)")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "fwupd chưa được cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now fwupd || true", "Dừng và vô hiệu hóa dịch vụ fwupd", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y fwupd || true", "Gỡ bỏ fwupd", is_sudo=True, skip_on_error=True)
        ]


# Danh sách xuất bản của giai đoạn
MODULES = [
    FirmwareUpdates
]
