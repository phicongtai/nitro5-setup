# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess
import os

class NvidiaDriver(ModuleBase):
    id = "nvidia_driver"
    name = "NVIDIA Proprietary Driver (akmod-nvidia)"
    description = "Cài đặt Driver NVIDIA độc quyền gốc (akmod-nvidia) và CUDA runtime để đạt hiệu năng tối đa cho RTX 3050."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y akmod-nvidia xorg-x11-drv-nvidia-cuda", "Cài đặt akmod-nvidia và CUDA runtime", is_sudo=True),
            Command("akmods --force", "Biên dịch driver nhân (akmods)", is_sudo=True),
            Command("modinfo -F version nvidia", "Kiểm tra phiên bản driver Nvidia đã biên dịch", is_sudo=False),
            Command("grubby --update-kernel=ALL --args='nvidia-drm.modeset=1'", "Kích hoạt nvidia-drm modeset trong GRUB", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q akmod-nvidia", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            res_mod = subprocess.run("lsmod | grep -i nvidia", shell=True, capture_output=True, text=True)
            if res_mod.returncode == 0:
                return CheckResult(True, "✓ OK", "Driver NVIDIA đã load")
            return CheckResult(True, "✓ OK", "Đã cài đặt driver NVIDIA (Cần reboot)")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Không tìm thấy driver")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("grubby --update-kernel=ALL --remove-args='nvidia-drm.modeset=1' || true", "Xóa cấu hình GRUB cho Nvidia modeset", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y akmod-nvidia xorg-x11-drv-nvidia-cuda xorg-x11-drv-nvidia || true", "Gỡ bỏ driver Nvidia và CUDA", is_sudo=True, skip_on_error=True)
        ]


class NvidiaCuda(ModuleBase):
    id = "cuda"
    name = "NVIDIA CUDA Support"
    description = "Cài đặt thư viện tính toán song song CUDA hỗ trợ các tác vụ AI/Deep Learning."
    required_level = "GPU"
    dependencies = ["nvidia_driver"]

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y xorg-x11-drv-nvidia-cuda", "Cài đặt CUDA runtime", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q xorg-x11-drv-nvidia-cuda", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài CUDA")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Không tìm thấy CUDA")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y xorg-x11-drv-nvidia-cuda || true", "Gỡ bỏ gói CUDA", is_sudo=True, skip_on_error=True)
        ]


class NvidiaVaapi(ModuleBase):
    id = "vaapi_nvidia"
    name = "Nvidia VA-API Driver (Hardware Video Decode)"
    description = "Hỗ trợ giải mã video phần cứng trên trình duyệt Firefox và Chrome bằng GPU NVIDIA qua thư viện VA-API."
    required_level = "GPU"
    dependencies = ["nvidia_driver"]

    def __init__(self):
        super().__init__()
        cmd_cleanup = (
            "sed -i '/^LIBVA_DRIVER_NAME=nvidia/d' /etc/environment && "
            "sed -i '/^__GLX_VENDOR_LIBRARY_NAME=nvidia/d' /etc/environment && "
            "sed -i '/^__NV_PRIME_RENDER_OFFLOAD=1/d' /etc/environment && "
            "sed -i '/^MOZ_DISABLE_RDD_SANDBOX=1/d' /etc/environment"
        )
        cmd_env = (
            "grep -q '^NVD_BACKEND=direct' /etc/environment || "
            "echo 'NVD_BACKEND=direct' | tee -a /etc/environment"
        )
        cmd_howto = (
            "echo -e '# Hướng dẫn sử dụng dGPU NVIDIA cho từng ứng dụng (PRIME Offload):\\n"
            "# 1. Với GNOME: Click phải chuột vào icon ứng dụng -> chọn \"Launch using Discrete Graphics\"\\n"
            "# 2. Với Terminal / Command-line: Thêm các biến môi trường trước lệnh chạy:\\n"
            "#    __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia lệnh_chạy\\n"
            "# 3. Ví dụ: __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia vkcube' "
            "| tee /etc/profile.d/nvidia-prime-howto.sh"
        )
        self.commands = [
            Command("dnf5 install -y libva-nvidia-driver libva-utils", "Cài đặt driver VA-API cho Nvidia", is_sudo=True),
            Command(cmd_cleanup, "Dọn dẹp các biến môi trường NVIDIA xung đột trong /etc/environment", is_sudo=True, skip_on_error=True),
            Command(cmd_env, "Cấu hình biến môi trường tăng tốc VA-API Nvidia (/etc/environment)", is_sudo=True),
            Command(cmd_howto, "Tạo tài liệu hướng dẫn chạy PRIME offload (/etc/profile.d/nvidia-prime-howto.sh)", is_sudo=True),
            Command("chmod +x /etc/profile.d/nvidia-prime-howto.sh", "Cấp quyền thực thi file hướng dẫn", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q libva-nvidia-driver", shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt VA-API driver")
        
        env_ok = False
        if os.path.exists("/etc/environment"):
            try:
                with open("/etc/environment", "r") as f:
                    content = f.read()
                if "NVD_BACKEND=direct" in content and "LIBVA_DRIVER_NAME=nvidia" not in content:
                    env_ok = True
            except Exception:
                pass
        
        if env_ok:
            return CheckResult(True, "✓ OK", "Đã cài VA-API Nvidia và cấu hình env tối ưu")
        return CheckResult(False, "✗ SAI CẤU HÌNH", "Thiếu NVD_BACKEND=direct hoặc còn tồn tại biến conflict trong /etc/environment")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y libva-nvidia-driver || true", "Gỡ bỏ driver VA-API cho Nvidia", is_sudo=True, skip_on_error=True),
            ResetCommand("sed -i '/NVD_BACKEND=direct/d' /etc/environment || true", "Xóa biến môi trường NVD_BACKEND từ /etc/environment", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /etc/profile.d/nvidia-prime-howto.sh", "Xóa file hướng dẫn PRIME", is_sudo=True)
        ]


class SwitcherooControl(ModuleBase):
    id = "switcheroo"
    name = "GNOME Switcheroo Control (PRIME Offload)"
    description = "Cho phép click chuột phải vào ứng dụng chọn 'Launch using Discrete Graphics' để chạy game/app qua GPU rời."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y switcheroo-control", "Cài đặt switcheroo-control", is_sudo=True),
            Command("systemctl enable --now switcheroo-control", "Kích hoạt switcheroo-control service", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("systemctl is-active switcheroo-control", shell=True, capture_output=True, text=True)
        if "active" in res.stdout:
            return CheckResult(True, "✓ OK", "Đang chạy - Click phải ứng dụng để chọn GPU")
        return CheckResult(False, "✗ FAILED", "Chưa hoạt động")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now switcheroo-control || true", "Dừng và vô hiệu hóa switcheroo-control", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y switcheroo-control || true", "Gỡ bỏ switcheroo-control", is_sudo=True, skip_on_error=True)
        ]


class EnvyControl(ModuleBase):
    id = "native_optimus_policy"
    name = "EnvyControl (Quản lý chế độ đồ họa Hybrid)"
    description = "Cài đặt EnvyControl và cấu hình GPU chạy ở chế độ Hybrid (Optimus) tối ưu."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y python3-pip", "Cài đặt python3-pip", is_sudo=True),
            Command("pip install envycontrol", "Cài đặt envycontrol qua pip", is_sudo=True),
            Command("envycontrol -s hybrid", "Đặt chế độ đồ họa Hybrid (Optimus)", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which envycontrol || pip show envycontrol", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            res_mode = subprocess.run("envycontrol -q", shell=True, capture_output=True, text=True)
            return CheckResult(True, "✓ OK", f"EnvyControl đã cài đặt (Chế độ: {res_mode.stdout.strip()})")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu envycontrol")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("envycontrol -s integrated || true", "Đặt chế độ đồ họa về Integrated trước khi gỡ", is_sudo=True, skip_on_error=True),
            ResetCommand("pip uninstall -y envycontrol || true", "Gỡ bỏ envycontrol qua pip", is_sudo=True, skip_on_error=True)
        ]


class BrightnessFix(ModuleBase):
    id = "brightness_fix"
    name = "Sửa lỗi độ sáng màn hình (Backlight Fix)"
    description = "Sửa lỗi không tăng giảm được độ sáng màn hình trên Acer Nitro 5 chạy card đồ họa song song."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("echo 'blacklist acer_wmi' | tee /etc/modprobe.d/blacklist-acer-wmi.conf", "Blacklist driver acer_wmi", is_sudo=True),
            Command("grubby --update-kernel=ALL --args='acpi_backlight=native'", "Cấu hình kernel parameter acpi_backlight=native", is_sudo=True),
            Command("dracut -f", "Rebuild initramfs (dracut -f)", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        blacklist_ok = os.path.exists("/etc/modprobe.d/blacklist-acer-wmi.conf")
        cmdline_ok = False
        if os.path.exists("/proc/cmdline"):
            try:
                with open("/proc/cmdline", "r") as f:
                    cmdline = f.read()
                if "acpi_backlight=native" in cmdline:
                    cmdline_ok = True
            except Exception:
                pass
        if blacklist_ok and cmdline_ok:
            return CheckResult(True, "✓ OK", "Đã cấu hình backlight native & blacklist acer_wmi")
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Thiếu cấu hình blacklist hoặc kernel param")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/modprobe.d/blacklist-acer-wmi.conf || true", "Xóa blacklist file của acer_wmi", is_sudo=True, skip_on_error=True),
            ResetCommand("grubby --update-kernel=ALL --remove-args='acpi_backlight=native' || true", "Xóa acpi_backlight=native khỏi kernel args", is_sudo=True, skip_on_error=True),
            ResetCommand("dracut -f", "Rebuild initramfs", is_sudo=True)
        ]


class GamingOverlay(ModuleBase):
    id = "gaming_overlay"
    name = "MangoHud + vkBasalt (Gaming HUD)"
    description = "Hiển thị khung hình (FPS), nhiệt độ CPU/GPU, dung lượng RAM trực tiếp trong game (MangoHud) và bộ lọc đồ họa (vkBasalt)."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y mangohud vkbasalt", "Cài đặt MangoHud và vkBasalt", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q mangohud", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "MangoHud đã cài đặt")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y mangohud vkbasalt || true", "Gỡ bỏ MangoHud và vkBasalt", is_sudo=True, skip_on_error=True)
        ]


class GameMode(ModuleBase):
    id = "gamemode"
    name = "Feral GameMode"
    description = "Tự động cấu hình tối ưu CPU (governor), I/O, GPU khi phát hiện game khởi chạy."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y gamemode", "Cài đặt GameMode package", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("gamemoded --version", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "GameMode đã sẵn sàng")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y gamemode || true", "Gỡ bỏ GameMode", is_sudo=True, skip_on_error=True)
        ]


class NvidiaSuspendFix(ModuleBase):
    id = "nvidia_suspend_fix"
    name = "Sửa lỗi Sleep/Suspend trên NVIDIA"
    description = "Bật tính năng giữ lại bộ nhớ video khi sleep để tránh lỗi màn hình đen sau khi resume."
    required_level = "GPU"
    dependencies = ["nvidia_driver"]

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y xorg-x11-drv-nvidia-power", "Cài đặt gói hỗ trợ quản lý nguồn NVIDIA", is_sudo=True),
            Command("systemctl enable --now nvidia-suspend.service", "Bật dịch vụ nvidia-suspend", is_sudo=True),
            Command("systemctl enable --now nvidia-resume.service", "Bật dịch vụ nvidia-resume", is_sudo=True),
            Command("systemctl enable --now nvidia-hibernate.service", "Bật dịch vụ nvidia-hibernate", is_sudo=True),
            Command("systemctl enable --now nvidia-powerd.service || true", "Bật dịch vụ quản lý điện năng động (nvidia-powerd) nếu được hỗ trợ", is_sudo=True, skip_on_error=True),
            Command("grubby --update-kernel=ALL --args='nvidia.NVreg_PreserveVideoMemoryAllocations=1 nvidia.NVreg_TemporaryFilePath=/var/tmp'", "Cấu hình kernel parameters để giữ bộ nhớ video khi sleep", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        services = ["nvidia-suspend.service", "nvidia-resume.service", "nvidia-hibernate.service"]
        enabled_services = []
        for svc in services:
            res = subprocess.run(f"systemctl is-enabled {svc} 2>/dev/null", shell=True, capture_output=True, text=True)
            if "enabled" in res.stdout:
                enabled_services.append(svc)
                
        cmdline_ok = False
        if os.path.exists("/proc/cmdline"):
            try:
                with open("/proc/cmdline", "r") as f:
                    cmdline = f.read()
                if "nvidia.NVreg_PreserveVideoMemoryAllocations=1" in cmdline:
                    cmdline_ok = True
            except Exception:
                pass
                
        if len(enabled_services) == len(services):
            msg = "Đã bật tất cả dịch vụ nguồn NVIDIA" + (" + kernel param active" if cmdline_ok else " (Cần reboot để áp dụng kernel param)")
            return CheckResult(True, "✓ OK", msg)
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", f"Chỉ bật {len(enabled_services)}/{len(services)} dịch vụ nguồn")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now nvidia-suspend.service nvidia-resume.service nvidia-hibernate.service nvidia-powerd.service || true", "Dừng và vô hiệu hóa các dịch vụ nguồn NVIDIA", is_sudo=True, skip_on_error=True),
            ResetCommand("grubby --update-kernel=ALL --remove-args='nvidia.NVreg_PreserveVideoMemoryAllocations=1 nvidia.NVreg_TemporaryFilePath=/var/tmp' || true", "Xóa các kernel parameters quản lý nguồn NVIDIA", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y xorg-x11-drv-nvidia-power || true", "Gỡ bỏ gói quản lý nguồn NVIDIA", is_sudo=True, skip_on_error=True)
        ]


class NvidiaWaylandEnv(ModuleBase):
    id = "nvidia_wayland_env"
    name = "Cấu hình biến môi trường NVIDIA Wayland (GNOME)"
    description = "Thiết lập G-Sync, VRR cho GNOME Wayland (không ghi đè GBM để đảm bảo tương thích chế độ lai)."
    required_level = "GPU"
    dependencies = ["nvidia_driver"]

    def __init__(self):
        super().__init__()
        env_content = (
            "export __GL_GSYNC_ALLOWED=1\\n"
            "export __GL_VRR_ALLOWED=1\\n"
        )
        self.commands = [
            Command(f"echo -e '{env_content}' | tee /etc/profile.d/gnome-nvidia-wayland.sh", "Tạo file cấu hình NVIDIA Wayland", is_sudo=True),
            Command("chmod +x /etc/profile.d/gnome-nvidia-wayland.sh", "Cấp quyền thực thi cho file config", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        filepath = "/etc/profile.d/gnome-nvidia-wayland.sh"
        if os.path.exists(filepath):
            return CheckResult(True, "✓ OK", "Đã cấu hình biến môi trường")
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa cấu hình")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/profile.d/gnome-nvidia-wayland.sh", "Xóa file cấu hình biến môi trường Wayland", is_sudo=True)
        ]


class NvidiaGdmWayland(ModuleBase):
    id = "nvidia_gdm_wayland"
    name = "Sửa lỗi GDM Wayland trên NVIDIA (Khôi phục Fallback)"
    description = "Khôi phục udev rules cho GDM để cho phép quay lại X11 an toàn nếu driver NVIDIA gặp sự cố."
    required_level = "GPU"
    dependencies = ["nvidia_driver"]

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("rm -f /etc/udev/rules.d/61-gdm.rules", "Khôi phục rule GDM gốc", is_sudo=True),
            Command("grubby --update-kernel=ALL --args='nvidia-drm.modeset=1 nvidia-drm.fbdev=1' 2>/dev/null || true", "Bật NVIDIA DRM modeset & fbdev", is_sudo=True, skip_on_error=True),
            Command("mkdir -p /etc/environment.d && echo -e '__VK_LAYER_NV_optimus=NVIDIA_only' | tee /etc/environment.d/nvidia-wayland.conf", "Cấu hình biến môi trường GDM Wayland", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        rule_path = "/etc/udev/rules.d/61-gdm.rules"
        conf_path = "/etc/environment.d/nvidia-wayland.conf"
        fallback_ok = not os.path.exists(rule_path)
        
        conf_ok = False
        if os.path.exists(conf_path):
            try:
                with open(conf_path, "r") as f:
                    content = f.read()
                if "__VK_LAYER_NV_optimus=NVIDIA_only" in content:
                    conf_ok = True
            except Exception:
                pass
                
        if fallback_ok and conf_ok:
            return CheckResult(True, "✓ OK", "Quy tắc Fallback an toàn đang áp dụng")
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Thiếu file config hoặc cấu hình chưa tối ưu")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/environment.d/nvidia-wayland.conf || true", "Xóa cấu hình biến môi trường GDM Wayland", is_sudo=True, skip_on_error=True),
            ResetCommand("grubby --update-kernel=ALL --remove-args='nvidia-drm.fbdev=1' || true", "Xóa fbdev kernel arg", is_sudo=True, skip_on_error=True)
        ]


class VulkanSupport(ModuleBase):
    id = "vulkan"
    name = "Vulkan API (GPU Rendering)"
    description = "Cài đặt Vulkan API runtime và driver ICD cần thiết để chơi game."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y vulkan-loader vulkan-loader-devel mesa-vulkan-drivers vulkan-tools vulkan-validation-layers", "Cài đặt Vulkan stack", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q vulkan-loader 2>/dev/null", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Vulkan đã cài")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y vulkan-loader vulkan-loader-devel mesa-vulkan-drivers vulkan-tools vulkan-validation-layers || true", "Gỡ bỏ Vulkan stack", is_sudo=True, skip_on_error=True)
        ]


# Danh sách xuất bản
MODULES = [
    NvidiaDriver,
    NvidiaCuda,
    NvidiaVaapi,
    SwitcherooControl,
    EnvyControl,
    BrightnessFix,
    GamingOverlay,
    GameMode,
    NvidiaSuspendFix,
    NvidiaWaylandEnv,
    NvidiaGdmWayland,
    VulkanSupport,
]
