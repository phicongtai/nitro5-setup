# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess
import os

class GnomeTweaks(ModuleBase):
    id = "gnome_tweaks"
    name = "GNOME Tweaks"
    description = "Công cụ tinh chỉnh GNOME nâng cao (giao diện, font chữ, hành vi cửa sổ)."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y gnome-tweaks", "Cài đặt gnome-tweaks", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q gnome-tweaks", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài đặt")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y gnome-tweaks || true", "Gỡ bỏ gnome-tweaks", is_sudo=True, skip_on_error=True)
        ]


class GnomeExtensions(ModuleBase):
    id = "gnome_extensions"
    name = "GNOME Extensions App"
    description = "Ứng dụng quản lý các phần mở rộng (extensions) của GNOME shell."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y gnome-extensions-app", "Cài đặt gnome-extensions-app", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q gnome-extensions-app", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài đặt")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y gnome-extensions-app || true", "Gỡ bỏ gnome-extensions-app", is_sudo=True, skip_on_error=True)
        ]


class FractionalScaling(ModuleBase):
    id = "fractional_scaling"
    name = "Bật GNOME Fractional Scaling (125%, 150%)"
    description = "Kích hoạt tính năng scale màn hình lẻ của GNOME, mở khóa các mức scale 125% và 150%."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("gsettings set org.gnome.mutter experimental-features \"['scale-monitor-framebuffer']\"", "Bật tính năng scale monitor framebuffer thử nghiệm", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("gsettings get org.gnome.mutter experimental-features", shell=True, capture_output=True, text=True)
        if "scale-monitor-framebuffer" in res.stdout:
            return CheckResult(True, "✓ OK", "Đã kích hoạt tính năng scale lẻ")
        return CheckResult(False, "✗ CHƯA KÍCH HOẠT", "Chưa bật tính năng")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("gsettings reset org.gnome.mutter experimental-features || true", "Khôi phục cấu hình scale mặc định", is_sudo=False, skip_on_error=True)
        ]


class SystemMonitors(ModuleBase):
    id = "system_monitors"
    name = "Htop, Btop & Fastfetch"
    description = "Cài đặt các ứng dụng giám sát tài nguyên qua terminal đẹp mắt và fastfetch."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y htop btop fastfetch", "Cài đặt htop, btop và fastfetch", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which btop && which fastfetch", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài đặt các công cụ")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đủ công cụ")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y htop btop fastfetch || true", "Gỡ bỏ htop, btop và fastfetch", is_sudo=True, skip_on_error=True)
        ]


class TimeshiftBackup(ModuleBase):
    id = "timeshift"
    name = "Timeshift (Sao lưu & Khôi phục hệ thống)"
    description = "Công cụ tạo snapshot hệ thống (giống Restore Point của Windows)."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y timeshift", "Cài đặt Timeshift", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q timeshift", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài đặt Timeshift")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y timeshift || true", "Gỡ bỏ Timeshift", is_sudo=True, skip_on_error=True)
        ]


class FlatpakApps(ModuleBase):
    id = "flatpak_apps"
    name = "Các ứng dụng Flatpak phổ biến"
    description = "Tự động cài đặt VLC, Flatseal, Discord, LocalSend, EasyEffects và Extension Manager từ Flathub."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("flatpak install -y flathub org.videolan.VLC com.github.tchx84.Flatseal com.discordapp.Discord org.localsend.localsend_app com.github.wwmm.easyeffects com.mattjakeman.ExtensionManager", "Cài đặt VLC, Flatseal, Discord, LocalSend, EasyEffects và Extension Manager", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("flatpak list --columns=application", shell=True, capture_output=True, text=True)
        installed = []
        apps = ["org.videolan.VLC", "com.github.tchx84.Flatseal", "com.discordapp.Discord", "org.localsend.localsend_app", "com.github.wwmm.easyeffects", "com.mattjakeman.ExtensionManager"]
        for app in apps:
            if app in res.stdout:
                installed.append(app.split(".")[-1])
        if len(installed) == len(apps):
            return CheckResult(True, "✓ OK", f"Đã cài đủ {len(apps)} apps")
        elif len(installed) > 0:
            return CheckResult(True, "✓ OK", f"Đã cài: {', '.join(installed)}")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài ứng dụng nào")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("flatpak uninstall -y org.videolan.VLC com.github.tchx84.Flatseal com.discordapp.Discord org.localsend.localsend_app com.github.wwmm.easyeffects com.mattjakeman.ExtensionManager || true", "Gỡ bỏ các ứng dụng Flatpak", is_sudo=False, skip_on_error=True)
        ]


class SteamGaming(ModuleBase):
    id = "steam"
    name = "Steam (RPM Fusion) + Proton Support"
    description = "Cài đặt Steam từ RPM Fusion Non-Free hỗ trợ chơi game Windows mượt mà."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y steam", "Cài đặt Steam", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q steam", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài đặt Steam")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y steam || true", "Gỡ bỏ Steam", is_sudo=True, skip_on_error=True)
        ]


class Fcitx5Lotus(ModuleBase):
    id = "fcitx5_lotus"
    name = "Bộ gõ tiếng Việt Lotus (Fcitx5)"
    description = "Cài đặt bộ gõ tiếng Việt Lotus, thiết lập tự động khởi chạy, tắt ibus và cấu hình biến môi trường."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        cmd_install = (
            "RELEASEVER=$(grep '^VERSION_ID=' /etc/os-release | cut -d'=' -f2) && "
            "rpm --import https://fcitx5-lotus.pages.dev/pubkey.gpg && "
            "dnf5 config-manager addrepo --from-repofile=https://fcitx5-lotus.pages.dev/rpm/fedora/fcitx5-lotus-$RELEASEVER.repo && "
            "dnf5 install -y fcitx5-lotus fcitx5 fcitx5-gtk4 fcitx5-qt"
        )
        cmd_config = (
            "systemctl enable --now fcitx5-lotus-server@${SUDO_USER:-$USER}.service || (systemd-sysusers && systemctl enable --now fcitx5-lotus-server@${SUDO_USER:-$USER}.service) && "
            "killall ibus-daemon || true && "
            "ibus exit || true && "
            "grep -q 'export XMODIFIERS=@im=fcitx' /home/${SUDO_USER:-$USER}/.bash_profile || "
            "echo -e 'export XMODIFIERS=@im=fcitx\\nexport QT_IM_MODULE=fcitx\\nexport QT_IM_MODULES=\"wayland;fcitx\"\\nexport GLFW_IM_MODULE=ibus' >> /home/${SUDO_USER:-$USER}/.bash_profile && "
            "chown ${SUDO_USER:-$USER}:$(id -gn ${SUDO_USER:-$USER}) /home/${SUDO_USER:-$USER}/.bash_profile && "
            "mkdir -p /home/${SUDO_USER:-$USER}/.config/autostart && "
            "cp /usr/share/applications/org.fcitx.Fcitx5.desktop /home/${SUDO_USER:-$USER}/.config/autostart/ 2>/dev/null || "
            "echo -e '[Desktop Entry]\\nType=Application\\nExec=fcitx5\\nHidden=false\\nX-GNOME-Autostart-enabled=true\\nName=Fcitx5' > /home/${SUDO_USER:-$USER}/.config/autostart/fcitx5.desktop && "
            "chown -R ${SUDO_USER:-$USER}:$(id -gn ${SUDO_USER:-$USER}) /home/${SUDO_USER:-$USER}/.config/autostart && "
            "[ -f /usr/share/applications/code.desktop ] && sed -i 's|Exec=/usr/share/code/code|Exec=/usr/share/code/code --enable-features=UseOzonePlatform --ozone-platform=wayland --enable-wayland-ime --wayland-text-input-version=3|' /usr/share/applications/code.desktop || true"
        )
        
        self.commands = [
            Command(cmd_install, "Thêm repo và cài đặt fcitx5-lotus cùng các thư viện liên quan", is_sudo=True),
            Command(cmd_config, "Cấu hình tự khởi chạy fcitx5, tắt ibus và thiết lập biến môi trường", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q fcitx5-lotus", shell=True, capture_output=True, text=True)
        service_active = subprocess.run("systemctl is-active fcitx5-lotus-server@${USER:-$SUDO_USER}.service 2>/dev/null", shell=True, capture_output=True, text=True)
        is_active = "active" in service_active.stdout
        
        if res.returncode == 0 and is_active:
            return CheckResult(True, "✓ OK", "Lotus đã cài đặt và dịch vụ đang hoạt động")
        elif res.returncode == 0:
            return CheckResult(True, "✓ OK", "Lotus đã cài đặt (dịch vụ chưa chạy)")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt Lotus")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl disable --now fcitx5-lotus-server@${SUDO_USER:-$USER}.service || true", "Dừng và vô hiệu hóa fcitx5-lotus-server", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y fcitx5-lotus fcitx5 fcitx5-gtk4 fcitx5-qt || true", "Gỡ bỏ fcitx5-lotus", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /etc/yum.repos.d/fcitx5-lotus*.repo || true", "Xóa file repo fcitx5-lotus", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /home/${SUDO_USER:-$USER}/.config/autostart/org.fcitx.Fcitx5.desktop /home/${SUDO_USER:-$USER}/.config/autostart/fcitx5.desktop || true", "Xóa fcitx5 khỏi autostart", is_sudo=True, skip_on_error=True),
            ResetCommand("sed -i '/XMODIFIERS/d; /QT_IM_MODULE/d; /GLFW_IM_MODULE/d' /home/${SUDO_USER:-$USER}/.bash_profile || true", "Khôi phục file .bash_profile", is_sudo=True, skip_on_error=True),
            ResetCommand("[ -f /usr/share/applications/code.desktop ] && sed -i 's|--enable-features=UseOzonePlatform --ozone-platform=wayland --enable-wayland-ime --wayland-text-input-version=3||' /usr/share/applications/code.desktop || true", "Hoàn tác chỉnh sửa desktop file của VS Code", is_sudo=True, skip_on_error=True)
        ]


class GnomeShellExtensions(ModuleBase):
    id = "gnome_shell_extensions"
    name = "GNOME Shell Extensions (AppIndicator, Caffeine, Dash-to-Dock)"
    description = "Cài đặt và kích hoạt các extension GNOME thiết yếu: AppIndicator, Caffeine, Dash-to-Dock."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y gnome-shell-extension-appindicator gnome-shell-extension-caffeine gnome-shell-extension-dash-to-dock", "Cài đặt các GNOME shell extensions từ repo Fedora", is_sudo=True),
            Command(
                "gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com 2>/dev/null || true && "
                "gnome-extensions enable caffeine@patapon.info 2>/dev/null || true && "
                "gnome-extensions enable dash-to-dock@micxgx.gmail.com 2>/dev/null || true",
                "Kích hoạt các GNOME extensions đã cài",
                is_sudo=False,
                skip_on_error=True
            )
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -qa 2>/dev/null | grep -E 'appindicator|caffeine|dash-to-dock'", shell=True, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            count = len(res.stdout.strip().split('\n'))
            return CheckResult(True, "✓ OK", f"Đã cài {count} GNOME extension")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài extension nào")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand(
                "gnome-extensions disable appindicatorsupport@rgcjonas.gmail.com 2>/dev/null || true && "
                "gnome-extensions disable caffeine@patapon.info 2>/dev/null || true && "
                "gnome-extensions disable dash-to-dock@micxgx.gmail.com 2>/dev/null || true",
                "Vô hiệu hóa các GNOME extensions",
                is_sudo=False,
                skip_on_error=True
            ),
            ResetCommand("dnf5 remove -y gnome-shell-extension-appindicator gnome-shell-extension-caffeine gnome-shell-extension-dash-to-dock || true", "Gỡ bỏ các GNOME extensions", is_sudo=True, skip_on_error=True)
        ]


class GnomeKeyboardShortcuts(ModuleBase):
    id = "gnome_shortcuts"
    name = "Phím tắt GNOME tối ưu (Terminal Ctrl+Alt+T)"
    description = "Thiết lập Ctrl+Alt+T mở Terminal, Super+L khóa màn hình để tối ưu trải nghiệm."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command(
                "gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "
                "\"['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']\" && "
                "gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"
                "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ "
                "name 'Open Terminal' && "
                "gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"
                "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ "
                "command 'gnome-terminal' && "
                "gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"
                "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ "
                "binding '<Control><Alt>t'",
                "Đặt phím tắt Ctrl+Alt+T mở GNOME Terminal",
                is_sudo=False,
                skip_on_error=True
            ),
            Command(
                "gsettings set org.gnome.settings-daemon.plugins.media-keys screensaver \"['<Super>l']\"",
                "Đặt Super+L khóa màn hình",
                is_sudo=False,
                skip_on_error=True
            )
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings", shell=True, capture_output=True, text=True)
        if "custom0" in res.stdout:
            return CheckResult(True, "✓ OK", "Phím tắt đã thiết lập (Ctrl+Alt+T, Super+L)")
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa thiết lập phím tắt tùy chỉnh")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("gsettings reset org.gnome.settings-daemon.plugins.media-keys custom-keybindings || true", "Khôi phục phím tắt custom về mặc định", is_sudo=False, skip_on_error=True),
            ResetCommand("gsettings reset org.gnome.settings-daemon.plugins.media-keys screensaver || true", "Khôi phục phím tắt khóa màn hình về mặc định", is_sudo=False, skip_on_error=True)
        ]


class EasyEffectsPresets(ModuleBase):
    id = "easyeffects_presets"
    name = "EasyEffects Presets (DTS:X Ultra Alternative)"
    description = "Cài đặt bộ lọc âm thanh vòm JackHack96 mang lại hiệu ứng âm thanh 3D DTS:X Ultra laptop."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        cmd_install = (
            "USER_HOME=$(getent passwd ${SUDO_USER:-$USER} | cut -d: -f6) && "
            "rm -rf /tmp/EasyEffects-Presets && "
            "git clone --depth=1 https://github.com/JackHack96/EasyEffects-Presets.git /tmp/EasyEffects-Presets && "
            "mkdir -p \"$USER_HOME/.var/app/com.github.wwmm.easyeffects/data/easyeffects/irs\" && "
            "mkdir -p \"$USER_HOME/.var/app/com.github.wwmm.easyeffects/data/easyeffects/output\" && "
            "cp -r /tmp/EasyEffects-Presets/irs/* \"$USER_HOME/.var/app/com.github.wwmm.easyeffects/data/easyeffects/irs/\" 2>/dev/null || true && "
            "cp -r /tmp/EasyEffects-Presets/*.json \"$USER_HOME/.var/app/com.github.wwmm.easyeffects/data/easyeffects/output/\" 2>/dev/null || true && "
            "chown -R ${SUDO_USER:-$USER}:${SUDO_USER:-$USER} \"$USER_HOME/.var/app/com.github.wwmm.easyeffects\" 2>/dev/null || true"
        )
        self.commands = [
            Command(cmd_install, "Tải và cài đặt Presets giả lập âm thanh vòm cho EasyEffects", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        sudo_user = os.environ.get("SUDO_USER")
        home = os.path.expanduser(f"~{sudo_user}") if sudo_user else os.path.expanduser("~")
        preset_dir = os.path.join(home, ".var/app/com.github.wwmm.easyeffects/data/easyeffects/output")
        if os.path.exists(preset_dir) and os.listdir(preset_dir):
            return CheckResult(True, "✓ OK", "Đã cài đặt các Presets âm thanh vòm")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Không tìm thấy thư mục cấu hình của EasyEffects Flatpak")

    def get_reset_commands(self) -> list[ResetCommand]:
        sudo_user = os.environ.get("SUDO_USER")
        home = os.path.expanduser(f"~{sudo_user}") if sudo_user else os.path.expanduser("~")
        preset_dir = os.path.join(home, ".var/app/com.github.wwmm.easyeffects/data/easyeffects")
        return [
            ResetCommand(f"rm -rf {preset_dir}/irs/* {preset_dir}/output/* || true", "Xóa sạch các EasyEffects Presets và IRS files đã cài", is_sudo=True, skip_on_error=True)
        ]


class ElectronWaylandNative(ModuleBase):
    id = "electron_wayland_native"
    name = "Cấu hình Electron chạy Native trên Wayland"
    description = "Thêm biến môi trường để buộc các ứng dụng Electron chạy native trên Wayland tránh mờ/giật lag."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("echo 'export ELECTRON_OZONE_PLATFORM_HINT=auto' | tee /etc/profile.d/electron-wayland.sh && chmod +x /etc/profile.d/electron-wayland.sh", "Tạo file cấu hình môi trường toàn cục cho Electron Wayland Native", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        filepath = "/etc/profile.d/electron-wayland.sh"
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                if "ELECTRON_OZONE_PLATFORM_HINT=auto" in content:
                    return CheckResult(True, "✓ OK", "Đã cấu hình Electron Wayland Native")
            except Exception:
                pass
        return CheckResult(False, "✗ CHƯA CẤU HÌNH", "Chưa cấu hình")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/profile.d/electron-wayland.sh || true", "Xóa file cấu hình môi trường Electron Wayland Native", is_sudo=True, skip_on_error=True)
        ]


class SpotifySpotX(ModuleBase):
    id = "spotify_spotx"
    name = "Spotify & SpotX (Mở khóa Premium, Không quảng cáo)"
    description = "Cài đặt Spotify qua Flatpak và áp dụng patch SpotX-Bash để loại bỏ quảng cáo."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("flatpak install -y flathub com.spotify.Client", "Cài đặt Spotify từ Flathub", is_sudo=False),
            Command("bash <(curl -sSL https://spotx-official.github.io/run.sh) -i", "Chạy script SpotX-Bash tương tác để patch Spotify (Không quảng cáo)", is_sudo=False, is_interactive=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("flatpak list --columns=application", shell=True, capture_output=True, text=True)
        if "com.spotify.Client" in res.stdout:
            return CheckResult(True, "✓ OK", "Spotify đã được cài đặt (SpotX-Bash chạy cùng lúc)")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Spotify chưa được cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("flatpak uninstall -y com.spotify.Client || true", "Gỡ bỏ Spotify Flatpak", is_sudo=False, skip_on_error=True)
        ]

# Danh sách xuất bản
MODULES = [
    GnomeTweaks,
    GnomeExtensions,
    GnomeShellExtensions,
    FractionalScaling,
    GnomeKeyboardShortcuts,
    SystemMonitors,
    TimeshiftBackup,
    FlatpakApps,
    SteamGaming,
    EasyEffectsPresets,
    ElectronWaylandNative,
    SpotifySpotX,
]
