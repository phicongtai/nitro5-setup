# -*- coding: utf-8 -*-
from modules.base import ModuleBase, Command, CheckResult, ResetCommand
import subprocess

class FullFFmpeg(ModuleBase):
    id = "ffmpeg"
    name = "FFmpeg đầy đủ (RPM Fusion)"
    description = "Tráo đổi thư viện ffmpeg-free mặc định bằng bản ffmpeg đầy đủ từ RPM Fusion chứa codec độc quyền (H264, H265/HEVC, AAC) và NVENC."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 swap -y ffmpeg-free ffmpeg --allowerasing", "Tráo đổi ffmpeg-free bằng bản ffmpeg đầy đủ từ RPM Fusion", is_sudo=True),
            Command("dnf5 install -y x264 x265 libavcodec-freeworld libde265 libaom aom dav1d libvpx", "Cài đặt các thư viện video codec lẻ", is_sudo=True),
            Command("dnf5 install -y xorg-x11-drv-nvidia-cuda nv-codec-headers || dnf5 install -y nv-codec-headers", "Cài đặt CUDA và NVENC headers cho mã hóa phần cứng Nvidia", is_sudo=True, skip_on_error=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("ffmpeg -version", shell=True, capture_output=True, text=True)
        if "Configuration:" in res.stdout and "rpmfusion" in res.stdout:
            return CheckResult(True, "✓ OK", "Bản đầy đủ RPM Fusion + NVENC Support")
        return CheckResult(False, "✗ FAILED", "Vẫn dùng bản ffmpeg-free giới hạn")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 swap -y ffmpeg ffmpeg-free --allowerasing || true", "Khôi phục lại ffmpeg-free mặc định", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y x264 x265 libavcodec-freeworld libde265 libaom aom dav1d libvpx nv-codec-headers || true", "Gỡ bỏ các gói codec lẻ và NVENC headers", is_sudo=True, skip_on_error=True)
        ]


class GStreamerPlugins(ModuleBase):
    id = "gstreamer"
    name = "GStreamer Plugins & Media Tools"
    description = "Cài đặt đầy đủ các plugin GStreamer để xem video/nghe nhạc, codec ảnh (AVIF, HEIF, WebP) và các công cụ chỉnh sửa đa phương tiện."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y gstreamer1-plugins-base gstreamer1-plugins-good gstreamer1-plugins-good-extras gstreamer1-plugins-bad-free gstreamer1-plugins-bad-freeworld gstreamer1-plugins-ugly gstreamer1-libav gstreamer1-plugin-openh264 gstreamer1-vaapi", "Cài đặt các plugin GStreamer", is_sudo=True),
            Command("dnf5 install -y libheif libheif-tools libwebp-tools libavif libavif-tools", "Cài đặt các công cụ xử lý ảnh HEIF/AVIF/WebP", is_sudo=True),
            Command("dnf5 install -y handbrake handbrake-gui mkvtoolnix mkvtoolnix-gui mediainfo mediainfo-gui", "Cài đặt các ứng dụng chỉnh sửa video (Handbrake, MKVToolNix, MediaInfo)", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q gstreamer1-plugins-ugly gstreamer1-libav handbrake mkvtoolnix", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đầy đủ plugin và công cụ media")
        return CheckResult(False, "✗ FAILED", "Thiếu plugin hoặc công cụ chỉnh sửa")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y gstreamer1-plugins-ugly gstreamer1-plugins-bad-freeworld gstreamer1-libav handbrake handbrake-gui mkvtoolnix mkvtoolnix-gui mediainfo mediainfo-gui libheif-tools libavif-tools || true", "Gỡ bỏ các plugin GStreamer ngoài và công cụ media", is_sudo=True, skip_on_error=True)
        ]


class IntelMediaDriver(ModuleBase):
    id = "intel_media"
    name = "Intel Media Driver (Intel VA-API iGPU)"
    description = "Driver tăng tốc mã hóa/giải mã phần cứng (VA-API) cho card đồ họa tích hợp Intel."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y intel-media-driver libva libva-utils", "Cài đặt intel-media-driver cho iGPU và driver dự phòng", is_sudo=True),
            Command("vainfo", "Kiểm tra thông tin tăng tốc đồ họa iGPU", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q intel-media-driver", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài driver Intel Media")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Thiếu driver")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y intel-media-driver || true", "Gỡ bỏ Intel Media Driver", is_sudo=True, skip_on_error=True)
        ]


class PipeWireAudio(ModuleBase):
    id = "pipewire"
    name = "PipeWire Âm thanh đầy đủ"
    description = "Đảm bảo cài đặt đầy đủ các wrapper cho PipeWire bao gồm PulseAudio, ALSA và JACK để tương thích âm thanh tối đa."
    required_level = "Bắt buộc"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y pipewire-alsa pipewire-pulseaudio pipewire-jack-audio-connection-kit wireplumber", "Cài đặt đầy đủ các gói Pipewire audio", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("pactl info | grep -i 'pipewire'", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "PipeWire làm máy chủ âm thanh")
        return CheckResult(False, "✗ FAILED", "Chưa chuyển đổi hoặc thiếu service")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [] # Tránh gỡ bỏ Pipewire vì là service âm thanh cốt lõi của Fedora


class MozillaOpenH264(ModuleBase):
    id = "openh264"
    name = "Mozilla OpenH264 (Firefox hardware decode)"
    description = "Cài đặt thư viện openh264 từ Cisco dành riêng cho Firefox để hỗ trợ giải mã video WebRTC và H.264 hiệu quả."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y mozilla-openh264", "Cài đặt mozilla-openh264", is_sudo=True)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("rpm -q mozilla-openh264", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return CheckResult(True, "✓ OK", "Đã cài OpenH264")
        return CheckResult(False, "✗ CHƯA CÀI ĐẶT", "Chưa cài đặt")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("dnf5 remove -y mozilla-openh264 || true", "Gỡ bỏ mozilla-openh264", is_sudo=True, skip_on_error=True)
        ]


class BluetoothService(ModuleBase):
    id = "bluetooth"
    name = "Bluetooth Tools & Service & Codecs"
    description = "Cài đặt công cụ Bluetooth, kích hoạt dịch vụ bluetooth.service, cài đặt aptX codec cho PipeWire và cấu hình tự động chuyển đổi profile tai nghe Bluetooth."
    required_level = "Tùy chọn"

    def __init__(self):
        super().__init__()
        self.commands = [
            Command("dnf5 install -y bluez bluez-tools pipewire-codec-aptx || dnf5 install -y bluez bluez-tools", "Cài đặt các gói Bluetooth và aptX codec cho PipeWire", is_sudo=True),
            Command("systemctl enable --now bluetooth", "Kích hoạt bluetooth.service", is_sudo=True),
            Command("wpctl settings --save bluetooth.autoswitch-to-headset-profile true || true", "Cấu hình tự động chuyển đổi profile tai nghe Bluetooth khi gọi/nghe", is_sudo=False)
        ]

    def validate(self) -> CheckResult:
        res = subprocess.run("systemctl is-active bluetooth 2>/dev/null", shell=True, capture_output=True, text=True)
        if "active" in res.stdout:
            res_aptx = subprocess.run("rpm -q pipewire-codec-aptx 2>/dev/null", shell=True, capture_output=True, text=True)
            has_aptx = res_aptx.returncode == 0
            msg = "Bluetooth active" + (" + aptX codec" if has_aptx else " (Thiếu aptX codec)")
            return CheckResult(True, "✓ OK", msg)
        return CheckResult(False, "✗ FAILED", "Bluetooth service chưa bật")

    def get_reset_commands(self) -> list[ResetCommand]:
        return [
            ResetCommand("wpctl settings --save bluetooth.autoswitch-to-headset-profile false || true", "Tắt cấu hình tự động chuyển profile tai nghe", is_sudo=False, skip_on_error=True),
            ResetCommand("systemctl disable --now bluetooth || true", "Dừng và vô hiệu hóa dịch vụ bluetooth", is_sudo=True, skip_on_error=True),
            ResetCommand("dnf5 remove -y pipewire-codec-aptx bluez-tools || true", "Gỡ bỏ aptX codec và bluez-tools", is_sudo=True, skip_on_error=True)
        ]

# Danh sách xuất bản
MODULES = [
    FullFFmpeg,
    GStreamerPlugins,
    IntelMediaDriver,
    PipeWireAudio,
    MozillaOpenH264,
    BluetoothService
]
