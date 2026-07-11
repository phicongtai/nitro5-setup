# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess
import os

class GoogleChrome(ModuleBase):
    id = "google_chrome"
    name = "Trình duyệt Google Chrome"
    description = "Cài đặt trình duyệt web Google Chrome stable chính thức từ kho lưu trữ của Google."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 config-manager setopt google-chrome.enabled=1 || dnf5 config-manager --set-enabled google-chrome || true", "Kích hoạt repo Google Chrome", is_sudo=True),
            Command("dnf5 install -y google-chrome-stable", "Cài đặt Google Chrome", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which google-chrome-stable", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài đặt Google Chrome")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt Google Chrome")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y google-chrome-stable || true", "Gỡ bỏ Google Chrome", is_sudo=True, skip_on_error=True)
        ]


class VSCode(ModuleBase):
    id = "vscode"
    name = "Visual Studio Code"
    description = "Cài đặt trình soạn thảo mã nguồn VS Code chính thức (RPM) từ Microsoft."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("rpm --import https://packages.microsoft.com/keys/microsoft.asc", "Nhập khóa ký GPG Microsoft", is_sudo=True),
            Command("sh -c 'echo -e \"[code]\\nname=Visual Studio Code\\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\\nenabled=1\\ngpgcheck=1\\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc\" > /etc/yum.repos.d/vscode.repo'", "Thêm kho phần mềm VS Code (Microsoft)", is_sudo=True),
            Command("dnf5 install -y code", "Cài đặt VS Code (code)", is_sudo=True),
            Command("[ -f /usr/share/applications/code.desktop ] && sed -i 's|Exec=/usr/share/code/code|Exec=/usr/share/code/code --enable-features=UseOzonePlatform --ozone-platform=wayland --enable-wayland-ime --wayland-text-input-version=3|' /usr/share/applications/code.desktop || true", "Cấu hình VS Code Wayland native & IME support", is_sudo=True, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which code", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài đặt VS Code")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt VS Code")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y code || true", "Gỡ bỏ VS Code", is_sudo=True, skip_on_error=True),
            ResetCommand("rm -f /etc/yum.repos.d/vscode.repo || true", "Xóa file repo VS Code", is_sudo=True, skip_on_error=True)
        ]


class Obsidian(ModuleBase):
    id = "obsidian"
    name = "Ghi chú Obsidian"
    description = "Cài đặt ứng dụng ghi chú Obsidian Markdown (Flatpak từ Flathub)."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("flatpak install -y flathub md.obsidian.Obsidian", "Cài đặt Obsidian từ Flathub", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("flatpak list --columns=application", shell=True, capture_output=True, text=True)
        if "md.obsidian.Obsidian" in res.stdout:
            return CheckResult(True, "✓ OK", "Đã cài đặt Obsidian Flatpak")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt Obsidian")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("flatpak uninstall -y md.obsidian.Obsidian || true", "Gỡ bỏ Obsidian Flatpak", is_sudo=False, skip_on_error=True)
        ]


class CppEnv(ModuleBase):
    id = "cpp_env"
    name = "Môi trường C/C++ (Gcc, G++, CMake, Ninja)"
    description = "Cài đặt gcc, g++, gdb, cmake, ninja-build, clang và make để hỗ trợ biên dịch phát triển phần mềm C/C++."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 group install -y \"Development Tools\" \"C Development Tools and Libraries\"", "Cài đặt Development Tools cho C/C++", is_sudo=True),
            Command("dnf5 install -y gcc gcc-c++ gdb cmake make ninja-build clang clang-tools-extra", "Cài đặt các công cụ compiler, build và debug C/C++ bổ sung", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which g++ && which cmake && which make && which ninja && which clang", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cấu hình môi trường C/C++ đầy đủ")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu các công cụ lập trình C/C++")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y gdb cmake ninja-build clang clang-tools-extra || true", "Gỡ các công cụ build nâng cao C/C++", is_sudo=True, skip_on_error=True)
        ]


class PythonEnv(ModuleBase):
    id = "python_env"
    name = "Môi trường Python 3"
    description = "Cài đặt các thư viện bổ sung python3-pip, python3-devel, python3-virtualenv phục vụ phát triển ứng dụng Python."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y python3 python3-pip python3-devel python3-virtualenv", "Cài đặt python3, pip, python-devel và virtualenv", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("python3 -c 'import venv'", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Môi trường Python 3 sẵn sàng")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu các gói python-devel hoặc virtualenv")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y python3-virtualenv || true", "Gỡ bỏ virtualenv", is_sudo=True, skip_on_error=True)
        ]


class JavaEnv(ModuleBase):
    id = "java_env"
    name = "Môi trường Java (OpenJDK & Maven)"
    description = "Cài đặt OpenJDK 21 và Maven phục vụ phát triển ứng dụng Java."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y java-21-openjdk java-21-openjdk-devel maven", "Cài đặt OpenJDK 21 và Maven", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res_java = subprocess.run("which javac", shell=True, capture_output=True, text=True)
        res_maven = subprocess.run("which mvn", shell=True, capture_output=True, text=True)
        if res_java.returncode == 0 and res_maven.returncode == 0:
            return CheckResult(True, "✓ OK", "JDK 21 và Maven đã sẵn sàng")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu JDK hoặc Maven")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y java-21-openjdk java-21-openjdk-devel maven || true", "Gỡ bỏ Java JDK 21 và Maven", is_sudo=True, skip_on_error=True)
        ]


class DotnetEnv(ModuleBase):
    id = "dotnet_env"
    name = "Môi trường C# .NET SDK"
    description = "Cài đặt .NET SDK 8.0 phục vụ phát triển phần mềm C#/.NET."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y dotnet-sdk-8.0", "Cài đặt .NET SDK 8.0", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which dotnet", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", ".NET SDK đã sẵn sàng")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu .NET SDK")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y dotnet-sdk-8.0 || true", "Gỡ bỏ .NET SDK 8.0", is_sudo=True, skip_on_error=True)
        ]


class NodejsEnv(ModuleBase):
    id = "nodejs_env"
    name = "Môi trường Node.js & NPM"
    description = "Cài đặt Node.js và trình quản lý gói NPM để phát triển ứng dụng JS/React."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y nodejs npm", "Cài đặt Node.js và NPM", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which node && which npm", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Node.js và NPM đã sẵn sàng")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt Node.js/NPM")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y nodejs npm || true", "Gỡ bỏ Node.js và NPM", is_sudo=True, skip_on_error=True)
        ]


class GitConfig(ModuleBase):
    id = "git_config"
    name = "Git & Cấu hình cơ bản"
    description = "Cài đặt git và thiết lập các cấu hình global cơ bản."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y git", "Cài đặt git", is_sudo=True),
            Command(
                "git config --global core.autocrlf input && "
                "git config --global init.defaultBranch main && "
                "git config --global pull.rebase false",
                "Cấu hình git global: autocrlf=input, defaultBranch=main",
                is_sudo=False,
                skip_on_error=True
            ),
            Command("git config --global user.name \"Acer Nitro 5 User\" && git config --global user.email \"user@nitro5.local\"", "Thiết lập thông tin git user placeholder (Tùy chỉnh lại sau)", is_sudo=False, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which git", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            ver = subprocess.run("git --version", shell=True, capture_output=True, text=True)
            return CheckResult(True, "✓ OK", f"git sẵn sàng ({ver.stdout.strip()})")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu git")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("git config --global --remove-section core || true", "Xóa cấu hình core git", is_sudo=False, skip_on_error=True),
            ResetCommand("git config --global --remove-section init || true", "Xóa cấu hình init git", is_sudo=False, skip_on_error=True),
            ResetCommand("git config --global --remove-section user || true", "Xóa thông tin user git", is_sudo=False, skip_on_error=True),
            ResetCommand("dnf5 remove -y git || true", "Gỡ bỏ git", is_sudo=True, skip_on_error=True)
        ]


class DockerPodman(ModuleBase):
    id = "podman_docker"
    name = "Podman (Docker-compatible)"
    description = "Cài đặt Podman, podman-compose, podman-docker và cấu hình rootless socket."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y podman podman-compose podman-docker buildah skopeo", "Cài đặt Podman stack", is_sudo=True),
            Command("loginctl enable-linger ${SUDO_USER:-$USER} 2>/dev/null || true", "Bật lingering cho rootless Podman", is_sudo=True, skip_on_error=True),
            Command("systemctl --user enable --now podman.socket 2>/dev/null || true", "Bật socket Docker API cho rootless Podman", is_sudo=False, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which podman", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            ver = subprocess.run("podman --version", shell=True, capture_output=True, text=True)
            return CheckResult(True, "✓ OK", f"Podman sẵn sàng ({ver.stdout.strip()})")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Podman chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("systemctl --user disable --now podman.socket || true", "Tắt user service podman.socket", is_sudo=False, skip_on_error=True),
            ResetCommand("loginctl disable-linger ${SUDO_USER:-$USER} || true", "Tắt lingering", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y podman podman-compose podman-docker buildah skopeo || true", "Gỡ bỏ Podman stack", is_sudo=True, skip_on_error=True)
        ]


class RustEnv(ModuleBase):
    id = "rust_env"
    name = "Môi trường Rust (rustup + cargo)"
    description = "Cài đặt Rust toolchain (stable) qua rustup và thiết lập PATH."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y rustup rust-analyzer || dnf5 install -y rustup", "Cài đặt rustup và rust-analyzer qua DNF5", is_sudo=True),
            Command("rustup toolchain install stable --no-self-update 2>/dev/null || true", "Cài đặt Rust stable toolchain", is_sudo=False, skip_on_error=True),
            Command("rustup default stable 2>/dev/null || true", "Đặt stable làm mặc định", is_sudo=False, skip_on_error=True),
            Command("echo 'export PATH=$HOME/.cargo/bin:$PATH' | tee /etc/profile.d/cargo-path.sh && chmod +x /etc/profile.d/cargo-path.sh", "Thêm ~/.cargo/bin vào PATH toàn hệ thống", is_sudo=True, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("which rustup || which cargo", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            ver = subprocess.run("rustup show active-toolchain 2>/dev/null || cargo --version 2>/dev/null", shell=True, capture_output=True, text=True)
            return CheckResult(True, "✓ OK", f"Rust sẵn sàng ({ver.stdout.strip()[:40]})")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "rustup/cargo chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("rm -f /etc/profile.d/cargo-path.sh || true", "Xóa PATH cấu hình cho Cargo", is_sudo=True, skip_on_error=True),
            ResetCommand("rustup self uninstall -y || true", "Gỡ bỏ Rust toolchain cài qua rustup", is_sudo=False, skip_on_error=True),
            ResetCommand("dnf5 remove -y rustup rust-analyzer || true", "Gỡ bỏ gói rustup và rust-analyzer cài qua DNF5", is_sudo=True, skip_on_error=True)
        ]

# Danh sách xuất bản
MODULES = [
    GoogleChrome,
    VSCode,
    Obsidian,
    GitConfig,
    CppEnv,
    PythonEnv,
    JavaEnv,
    DotnetEnv,
    NodejsEnv,
    RustEnv,
    DockerPodman,
]
