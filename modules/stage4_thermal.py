# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess
import os

class LmSensors(ModuleBase):
    id = "lm_sensors"
    name = "lm_sensors (Tự động quét cảm biến)"
    description = "Cài đặt gói lm_sensors để theo dõi nhiệt độ phần cứng và tự động quét cảm biến bo mạch chủ."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y lm_sensors", "Cài đặt lm_sensors", is_sudo=True),
            Command("sensors-detect --auto", "Quét tự động các cảm biến nhiệt độ phần cứng", is_sudo=True),
            Command("systemctl enable --now lm_sensors.service || true", "Kích hoạt dịch vụ lm_sensors", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("sensors", shell=True, capture_output=True, text=True)
        if res.returncode == 0 and "coretemp" in res.stdout:
            return CheckResult(True, "✓ OK", "Đã quét và phát hiện CPU core temp")
        elif res.returncode == 0:
            return CheckResult(True, "✓ OK", "lm_sensors hoạt động")
        return CheckResult(False, "✗ FAILED", "Không thể chạy lệnh sensors")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now lm_sensors.service || true", "Dừng và vô hiệu hóa dịch vụ lm_sensors", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y lm_sensors || true", "Gỡ bỏ lm_sensors", is_sudo=True, skip_on_error=True)
        ]


class ThermalD(ModuleBase):
    id = "thermald"
    name = "Intel Thermal Daemon (thermald)"
    description = "Dịch vụ của Intel ngăn ngừa quá nhiệt CPU bằng cách điều phối điện năng, xung nhịp và quạt."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y thermald", "Cài đặt thermald", is_sudo=True),
            Command("systemctl enable --now thermald", "Kích hoạt dịch vụ thermald", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("systemctl is-active thermald", shell=True, capture_output=True, text=True)
        if "active" in res.stdout:
            return CheckResult(True, "✓ OK", "Đang hoạt động")
        return CheckResult(False, "✗ FAILED", "thermald chưa bật")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now thermald || true", "Dừng và vô hiệu hóa dịch vụ thermald", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y thermald || true", "Gỡ bỏ thermald", is_sudo=True, skip_on_error=True)
        ]


class DAMXModule(ModuleBase):
    id = "damx"
    name = "DAMX — Div Acer Manager Max (Fan & Performance cho AN515-58)"
    description = (
        "Cài đặt Div Acer Manager Max (DAMX) — công cụ tối ưu cho Acer Nitro 5 AN515-58. "
        "Sử dụng driver Linuwu-Sense (WMI interface) để điều chỉnh quạt, LED RGB bàn phím, giới hạn pin."
    )
    required_level = "Bắt buộc"
    dependencies = ["build_tools_dkms"]

    def __init__(self):
        super().__init__()
        self.commands = [
            Command(
                "dnf5 install -y git dkms kernel-devel kernel-headers gcc make lm_sensors dwarves elfutils-libelf-devel openssl-devel && "
                "( command -v dotnet &>/dev/null || "
                "  dnf5 install -y dotnet-runtime-9.0 2>/dev/null || "
                "  dnf5 install -y dotnet-runtime-8.0 2>/dev/null || "
                "  { curl -fsSL https://packages.microsoft.com/config/fedora/$(rpm -E %fedora)/prod.repo "
                "    | tee /etc/yum.repos.d/microsoft-prod.repo && "
                "    dnf5 install -y dotnet-runtime-9.0; } "
                ") || echo 'Cài .NET runtime từ packages.microsoft.com thủ công nếu cần'",
                "Cài kernel-devel, dkms, lm_sensors và .NET runtime",
                is_sudo=True,
                skip_on_error=True
            ),
            Command(
                "mkdir -p /etc/modprobe.d && "
                "echo 'blacklist acer_wmi' > /etc/modprobe.d/linuwu-sense.conf && "
                "echo 'options linuwu_sense nitro_v4=1 four_zone_kb=1 enable_all=1' >> /etc/modprobe.d/linuwu-sense.conf && "
                "mkdir -p /etc/modules-load.d && "
                "echo 'linuwu_sense' > /etc/modules-load.d/linuwu-sense.conf && "
                "modprobe -r acer_wmi || true",
                "Cấu hình trước modprobe cho linuwu_sense (tránh lỗi xung đột driver mặc định)",
                is_sudo=True
            ),
            Command(
                "[ ! -d /lib/modules/$(uname -r)/build ] && { "
                "echo -e '\\n>>> LỖI: Kernel mới chưa reboot — vui lòng khởi động lại máy trước!\\n'; exit 1; }; "
                "dkms status 2>/dev/null | grep -qi 'linuwu' && echo 'Linuwu-Sense đã cài sẵn, bỏ qua' || "
                "{ rm -rf /var/tmp/linuwu-sense-build && "
                "  git clone --depth=1 https://github.com/PXDiv/Div-Linuwu-Sense.git /var/tmp/linuwu-sense-build && "
                "  cd /var/tmp/linuwu-sense-build && "
                "  mkdir -p /usr/src/linuwu_sense-1.0 && "
                "  cp -r * /usr/src/linuwu_sense-1.0/ && "
                "  printf 'PACKAGE_NAME=\"linuwu_sense\"\\nPACKAGE_VERSION=\"1.0\"\\nBUILT_MODULE_NAME[0]=\"linuwu_sense\"\\nBUILT_MODULE_LOCATION[0]=\"src\"\\nDEST_MODULE_LOCATION[0]=\"/kernel/drivers/platform/x86\"\\nAUTOINSTALL=\"yes\"\\n' > /usr/src/linuwu_sense-1.0/dkms.conf && "
                "  export MAKEFLAGS=\"-j$(nproc)\" && "
                "  dkms add -m linuwu_sense -v 1.0 && "
                "  dkms build -m linuwu_sense -v 1.0 && "
                "  dkms install -m linuwu_sense -v 1.0 && "
                "  echo '>>> Linuwu-Sense WMI driver đã đăng ký thành công qua DKMS'; }",
                "Biên dịch và cài đặt driver Linuwu-Sense qua DKMS",
                is_sudo=True
            ),
            Command(
                "curl -fsSL https://raw.githubusercontent.com/PXDiv/Div-Acer-Manager-Max/refs/heads/main/scripts/remoteSetup.sh -o /tmp/damx-remoteSetup.sh && chmod +x /tmp/damx-remoteSetup.sh",
                "Tải script remoteSetup.sh của PXDiv",
                is_sudo=True
            ),
            Command(
                "bash /tmp/damx-remoteSetup.sh",
                "Cài DAMX (Div Acer Manager Max) - Vui lòng chọn 1 trong menu",
                is_sudo=True,
                is_interactive=True
            ),
            Command(
                "systemctl stop damx-daemon.service || true && "
                "modprobe -r linuwu_sense || true && "
                "modprobe -r acer_wmi || true && "
                "modprobe linuwu_sense || true && "
                "systemctl start damx-daemon.service || true",
                "Khởi chạy dịch vụ damx-daemon và nạp driver linuwu_sense mới",
                is_sudo=True
            ),
            Command(
                r"""cat > /usr/local/bin/damx-launcher << 'DAMX_LAUNCH_EOF'
#!/bin/bash
if [ -n "$WAYLAND_DISPLAY" ] || [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    export GDK_BACKEND=wayland
fi
export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

DAMX_BIN=""
for p in /opt/damx/gui/DivAcerManagerMax \
          /usr/bin/DivAcerManagerMax \
          /usr/local/bin/DivAcerManagerMax \
          /opt/DivAcerManagerMax/DivAcerManagerMax \
          /opt/damx/DivAcerManagerMax \
          /usr/share/DivAcerManagerMax/DivAcerManagerMax; do
    [ -x "$p" ] && DAMX_BIN="$p" && break
done

if [ -z "$DAMX_BIN" ]; then
    DAMX_BIN=$(find /opt /usr/local /usr -name "DivAcerManagerMax" -type f -executable 2>/dev/null | head -1)
fi

if [ -z "$DAMX_BIN" ]; then
    zenity --error --title="DAMX không tìm thấy" \
      --text="Div Acer Manager Max chưa được cài đặt.\nChạy lại setup stage 4 để cài đặt." 2>/dev/null || \
    echo "DAMX (Div Acer Manager Max) chưa cài. Chạy lại setup stage 4."
    exit 1
fi

exec "$DAMX_BIN" "$@"
DAMX_LAUNCH_EOF
chmod +x /usr/local/bin/damx-launcher""",
                "Tạo launcher GNOME-native cho DAMX",
                is_sudo=True
            ),
            Command(
                "mkdir -p /usr/share/applications && "
                r"""cat > /usr/share/applications/damx.desktop << 'DAMX_DESK_EOF'
[Desktop Entry]
Name=Div Acer Manager Max
GenericName=Fan & Performance Control
Comment=Điều khiển quạt, performance profile và battery limiter cho AN515-58
Exec=/usr/local/bin/damx-launcher
Icon=/opt/damx/gui/iconTransparent.png
Terminal=false
Type=Application
Categories=System;Settings;HardwareSettings;
Keywords=fan;cooling;performance;acer;nitro;nitrosense;damx;battery;
StartupNotify=true
DAMX_DESK_EOF
""" + "chmod 644 /usr/share/applications/damx.desktop && update-desktop-database /usr/share/applications 2>/dev/null || true",
                "Tạo desktop entry GNOME Activities cho DAMX",
                is_sudo=True
            ),
        ]

    def validate(self) -> CheckResult:
        linuwu_ok = subprocess.run(
            "dkms status 2>/dev/null | grep -qi 'linuwu' || lsmod 2>/dev/null | grep -qi 'linuwu'",
            shell=True, capture_output=True
        ).returncode == 0

        damx_paths = [
            "/opt/damx/gui/DivAcerManagerMax",
            "/usr/bin/DivAcerManagerMax",
            "/usr/local/bin/DivAcerManagerMax",
            "/opt/DivAcerManagerMax/DivAcerManagerMax",
            "/opt/damx/DivAcerManagerMax",
        ]
        damx_bin = any(os.path.exists(p) for p in damx_paths)
        if not damx_bin:
            res = subprocess.run("find /opt /usr/local /usr/share -name 'DivAcerManagerMax' -executable 2>/dev/null | head -1",
                                 shell=True, capture_output=True, text=True)
            damx_bin = bool(res.stdout.strip())

        launcher_ok = os.path.exists("/usr/local/bin/damx-launcher")
        desktop_ok = os.path.exists("/usr/share/applications/damx.desktop")

        if damx_bin and launcher_ok and desktop_ok and linuwu_ok:
            return CheckResult(True, "✓ OK", "DAMX đầy đủ: Linuwu-Sense WMI driver ✓ + DAMX GUI ✓")
        if damx_bin and not linuwu_ok:
            return CheckResult(True, "⚠ CẦN REBOOT", "DAMX GUI đã cài — Linuwu-Sense cần reboot để load")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Cần chạy lại stage 4 để cài DAMX + Linuwu-Sense")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl stop damx-daemon.service || true", "Dừng dịch vụ damx-daemon", is_sudo=True, skip_on_error=True),
            ResetCommand("systemctl disable damx-daemon.service || true", "Vô hiệu hóa dịch vụ damx-daemon", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /etc/systemd/system/damx-daemon.service || true", "Xóa file service damx-daemon", is_sudo=True, skip_on_error=True),
            ResetCommand("systemctl daemon-reload", "Tải lại systemd configuration", is_sudo=True),
            ResetCommand("dkms remove linuwu_sense/1.0 --all || true", "Xóa Linuwu-Sense driver khỏi DKMS", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -rf /usr/src/linuwu_sense-1.0 || true", "Xóa mã nguồn Linuwu-Sense trong usr/src", is_sudo=True, skip_on_error=True),
            ResetCommand("modprobe -r linuwu_sense || true", "Unload linuwu_sense kernel module", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /etc/modprobe.d/linuwu-sense.conf /etc/modules-load.d/linuwu-sense.conf || true", "Xóa các cấu hình modprobe của linuwu_sense", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -rf /opt/damx /usr/local/bin/damx-launcher /usr/share/applications/damx.desktop /var/log/DAMX_Daemon_Log.log || true", "Xóa các file ứng dụng DAMX", is_sudo=True, skip_on_error=True)
        ]


class AcerPredatorRGB(ModuleBase):
    id = "acer_predator_rgb"
    name = "Driver RGB bàn phím (acer-predator-module)"
    description = "Biên dịch và cài đặt driver acer-predator-module (facer) cho các dòng Nitro 5 khác AN515-58."
    required_level = "Tùy chọn"
    dependencies = ["build_tools_dkms"]

    def __init__(self):
        super().__init__()
        is_an515_58 = False
        try:
            if os.path.exists("/sys/class/dmi/id/product_name"):
                with open("/sys/class/dmi/id/product_name", "r") as f:
                    if "AN515-58" in f.read():
                        is_an515_58 = True
        except (OSError, IOError):
            pass

        if is_an515_58:
            self.commands = [
                Command("echo 'Dòng máy AN515-58 sử dụng DAMX + Linuwu-Sense cho cả fan và RGB. Bỏ qua facer.'", 
                        "Bỏ qua cài đặt facer trên AN515-58", is_sudo=False)
            ]
        else:
            self.commands = [
                Command("dnf5 install -y rsync", "Cài đặt rsync", is_sudo=True),
                Command("[ ! -d /lib/modules/$(uname -r)/build ] && { echo -e '\\n>>> LỖI CỰC KỲ QUAN TRỌNG: Hãy khởi động lại máy trước!\\n'; exit 1; }; rm -rf /tmp/acer-predator-build && git clone --depth=1 https://github.com/JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module.git /tmp/acer-predator-build && cd /tmp/acer-predator-build && chmod +x ./*.sh && export MAKEFLAGS=\"-j$(nproc)\" && ./install_service.sh && cp facer_rgb.py /usr/local/bin/facer-rgb && chmod +x /usr/local/bin/facer-rgb", "Biên dịch và cài đặt driver RGB bàn phím & CLI", is_sudo=True)
            ]

    def validate(self) -> CheckResult:
        is_an515_58 = False
        try:
            if os.path.exists("/sys/class/dmi/id/product_name"):
                with open("/sys/class/dmi/id/product_name", "r") as f:
                    if "AN515-58" in f.read():
                        is_an515_58 = True
        except (OSError, IOError):
            pass

        if is_an515_58:
            return CheckResult(True, "✓ BỎ QUA", "Sử dụng RGB tích hợp trong DAMX, không cần facer")

        lsmod_res = subprocess.run("lsmod | grep facer", shell=True, capture_output=True, text=True)
        if lsmod_res.returncode == 0:
            return CheckResult(True, "✓ OK", "Driver facer đã được nạp và hoạt động")
        if os.path.exists("/dev/acer-gkbbl-0"):
            return CheckResult(True, "✓ OK", "Thiết bị điều khiển /dev/acer-gkbbl-0 hoạt động")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Driver facer chưa được nạp vào nhân")

    def get_reset_commands(self) -> list[ResetCommand]:
        is_an515_58 = False
        try:
            if os.path.exists("/sys/class/dmi/id/product_name"):
                with open("/sys/class/dmi/id/product_name", "r") as f:
                    if "AN515-58" in f.read():
                        is_an515_58 = True
        except (OSError, IOError):
            pass

        if is_an515_58:
            return []

        return [
            ResetCommand("systemctl disable --now acer-predator-turbo-and-rgb-keyboard || true", "Dừng và vô hiệu hóa service facer", is_sudo=True, skip_on_error=True),
            ResetCommand("dkms remove acer_predator/1.0 --all || true", "Gỡ driver facer khỏi DKMS", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -rf /usr/src/acer_predator-1.0 || true", "Xóa mã nguồn facer", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /usr/local/bin/facer-rgb || true", "Xóa công cụ dòng lệnh facer-rgb", is_sudo=True, skip_on_error=True)
        ]


class STui(ModuleBase):
    id = "s_tui"
    name = "s-tui (Giám sát hiệu năng & nhiệt độ TUI)"
    description = "Giao diện dòng lệnh (TUI) hiển thị biểu đồ nhiệt độ CPU, xung nhịp và công suất tiêu thụ."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y s-tui", "Cài đặt s-tui", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q s-tui", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài đặt")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y s-tui || true", "Gỡ bỏ s-tui", is_sudo=True, skip_on_error=True)
        ]


class CoreTempModule(ModuleBase):
    id = "coretemp"
    name = "Load module coretemp khi khởi động"
    description = "Tự động nạp driver coretemp ở mỗi lần khởi động để thu thập nhiệt độ CPU chính xác."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("mkdir -p /etc/modules-load.d", "Tạo thư mục modules-load.d nếu chưa có", is_sudo=True),
            Command("echo 'coretemp' | tee /etc/modules-load.d/coretemp.conf", "Ghi file cấu hình coretemp.conf", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        path = "/etc/modules-load.d/coretemp.conf"
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
            if "coretemp" in content:
                return CheckResult(True, "✓ OK", "Đã cấu hình load module")
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa cấu hình tự động load")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/modules-load.d/coretemp.conf || true", "Xóa cấu hình load module coretemp", is_sudo=True, skip_on_error=True)
        ]

# Danh sách xuất bản
MODULES = [
    LmSensors,
    ThermalD,
    DAMXModule,
    AcerPredatorRGB,
    STui,
    CoreTempModule
]
