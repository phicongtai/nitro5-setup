# Nitro5-Setup-GUI

Công cụ GUI tự động hoá setup Fedora Workstation 44 (Wayland) cho Acer Nitro 5 AN515-58.
Ứng dụng được thiết kế chạy dưới dạng script Python qua terminal (KHÔNG cài đặt như app hệ thống).

## Yêu cầu hệ thống
- Fedora Workstation 44 (Khuyến nghị dùng phiên Wayland)
- Python 3.12+
- Các gói hệ thống bắt buộc: `vte291-gtk4`, `python3-devel`, `cairo-devel`, `gobject-introspection-devel`

Bạn có thể cài đặt các thư viện hệ thống trước bằng lệnh:
```bash
sudo dnf install -y gcc vte291-gtk4 python3-devel cairo-devel pkg-config gobject-introspection-devel
```

## Cách chạy ứng dụng

Đây là cách duy nhất để khởi chạy ứng dụng (không có icon trong menu ứng dụng):

```bash
cd nitro5-setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Kiến trúc
- Ứng dụng chạy GUI bằng quyền user thường (GTK4 + Libadwaita).
- Các lệnh hệ thống yêu cầu quyền root sẽ được gửi qua IPC đến một helper chạy ngầm qua `pkexec`. Helper này chỉ xin quyền root **một lần duy nhất**.
- Các lệnh tương tác sẽ được mở trực tiếp trong `Vte.Terminal`.
