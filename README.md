# 🚀 Nitro5-Setup-GUI — Bộ Công Cụ Tối Ưu Hóa Acer Nitro 5 AN515-58 trên Fedora Workstation

[![Fedora Workstation](https://img.shields.io/badge/Fedora%20Workstation-41%2B%20%2F%2044-51A2DA?style=for-the-badge&logo=fedora&logoColor=white)](https://fedoraproject.org/)
[![Hardware Support](https://img.shields.io/badge/Hardware-Acer%20Nitro%205%20AN515--58-8A2BE2?style=for-the-badge)](https://www.acer.com/)
[![GUI Framework](https://img.shields.io/badge/GUI-GTK4%20%2B%20Libadwaita-4E9A06?style=for-the-badge&logo=gnome&logoColor=white)](https://gnome.pages.gitlab.gnome.org/libadwaita/)
[![Python](https://img.shields.io/badge/Python-3.10%2B%20%2F%203.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

**Nitro5-Setup-GUI** là công cụ đồ họa (GUI) tự động hóa toàn diện được thiết kế đặc biệt cho dòng laptop **Acer Nitro 5 AN515-58** (Intel Core i5-12500H / i7-12700H + NVIDIA RTX 3050/3060 + 16GB/32GB RAM) chạy hệ điều hành **Fedora Workstation 41+ / 44 (Wayland native)**.

Ứng dụng giúp bạn biến một hệ thống Fedora mới cài đặt thành một trạm làm việc (Workstation) và cỗ máy giải trí hoàn hảo: từ việc tự động tinh chỉnh kernel, tối ưu hóa pin & nhiệt độ, quản lý quạt & LED RGB bàn phím, cài đặt đầy đủ driver NVIDIA chuẩn Wayland, cho đến thiết lập toàn bộ môi trường lập trình hiện đại chỉ với vài cú nhấp chuột.

---

## ✨ Các Tính Năng Nổi Bật

```
+-----------------------------------------------------------------------------------+
|                           NITRO5-SETUP-GUI ARCHITECTURE                           |
+-----------------------------------------------------------------------------------+
|  [⚡ Stage 0: 1-Click Core Setup] ---> Tự động chạy tuần tự 27 module cốt lõi   |
|  [🏆 Stage 9: Native Score 100]  ---> Quét 16 tiêu chí đánh giá tương thích       |
|  [❄️ DAMX / Linuwu-Sense WMI]    ---> Điều khiển quạt & LED RGB 4 vùng Wayland    |
|  [🔋 Battery Charge Limit]       ---> Giới hạn sạc pin 50-100% trực tiếp trên GUI |
|  [↩️ Per-Module Reset/Rollback]  ---> Hoàn tác/gỡ bỏ từng module độc lập an toàn  |
+-----------------------------------------------------------------------------------+
```

* ⚡ **Cài Đặt Lõi Siêu Tốc 1-Click (Stage 0 - Core Setup)**: Tự động phân tích và chạy tuần tự **27 module bắt buộc** theo đúng thứ tự phụ thuộc phần cứng/phần mềm. Sau khi hoàn tất, hệ thống được cấu hình tối ưu toàn diện.
* 🏆 **Hệ Thống Chấm Điểm Tương Thích Native 100/100 (Stage 9 - Native Score)**: Quét thời gian thực và đánh giá mức độ tương thích của hệ thống theo **16 tiêu chí phần cứng/phần mềm** (Driver NVIDIA, chế độ EnvyControl Hybrid, Switcheroo, Intel thermald, cảm biến lm_sensors, driver Linuwu-Sense WMI, TLP Power, zRAM zstd, fstrim, NVMe Scheduler none, Deep Sleep S3, PCIe AER suppress, Kernel >= 6.8, PipeWire, FFmpeg Full Codec, Fcitx5 Tiếng Việt).
* ❄️ **Quản Lý Quạt & LED RGB Bàn Phím (DAMX - Dynamic Acer Management X)**: Tích hợp driver kernel **Linuwu-Sense WMI** giao tiếp trực tiếp qua cổng ACPI/WMI, thay thế hoàn toàn NitroSense trên Windows. Hỗ trợ chọn chế độ quạt (*Quiet, Normal, Performance, Turbo*), tùy chỉnh Fan Curve và điều khiển LED RGB 4 vùng native trên Wayland.
* 🔋 **Bảo Vệ Pin & Giới Hạn Sạc (Battery Charge Limit Customizer)**: Tích hợp thanh trượt điều chỉnh giới hạn sạc pin (50% – 100%) trực tiếp trên giao diện GUI. Kết hợp cùng dịch vụ **TLP Power Management** giúp kéo dài tuổi thọ pin và ngăn ngừa chai phồng khi cắm sạc liên tục.
* ↩️ **Hoàn Tác & Khôi Phục Từng Module (Modular Rollback)**: Mỗi module đều được tích hợp nút **↩ Reset** độc lập, cho phép bạn gỡ bỏ cài đặt hoặc khôi phục cấu hình gốc của từng thành phần mà không làm ảnh hưởng đến các phần khác của hệ thống.
* 🛡️ **Quản Lý Quyền Sudo Thông Minh & An Toàn**: Chỉ yêu cầu mật khẩu `sudo` một lần duy nhất khi khởi chạy qua script bootstrap, tự động duy trì phiên làm việc ngầm và dọn dẹp sạch sẽ ngay khi đóng ứng dụng.

---

## 💻 Yêu Cầu Hệ Thống

| Thành Phần | Yêu Cầu Tối Thiểu | Khuyến Nghị |
| :--- | :--- | :--- |
| **Hệ điều hành** | Fedora Workstation 41+ | **Fedora Workstation 44 (GNOME / Wayland)** |
| **Dòng máy** | Acer Nitro 5 AN515-58 | Acer Nitro 5 AN515-58 (i5-12500H + RTX 3050) |
| **Python** | Python 3.10+ | Python 3.12+ |
| **Trình quản lý gói** | `dnf5` (hoặc `dnf`) | `dnf5` |
| **Thư viện GUI** | `python3-gobject`, `gtk4`, `libadwaita` | Libadwaita >= 1.4 (hiển thị đầy đủ widget native) |

> [!NOTE]
> Bộ cài `install.sh` sẽ tự động kiểm tra hệ điều hành, dòng máy, định dạng hệ thống tập tin (tự động phát hiện và cảnh báo nếu đang chạy trên phân vùng NTFS/FAT của Windows) và tự động cài đặt các thư viện GUI cần thiết (`gtk4`, `libadwaita`, `python3-pip`).

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh

Đây là phương thức chuẩn và an toàn nhất để khởi chạy ứng dụng GUI:

### Bước 1: Mở Terminal và truy cập vào thư mục mã nguồn
```bash
cd nitro5-setup
```

### Bước 2: Khởi chạy bộ công cụ bằng script tự động
```bash
bash install.sh
```

> [!TIP]
> **Cơ chế tự động thông minh của `install.sh`**:
> 1. Kiểm tra môi trường Fedora Workstation & phiên bản Python.
> 2. Phát hiện nếu thư mục đang nằm trên phân vùng NTFS/vFAT của Windows -> Tự động gợi ý sao chép sang `~/nitro5-setup` trên phân vùng ext4/btrfs Linux để tránh lỗi phân quyền khi biên dịch driver DKMS.
> 3. Xin quyền `sudo` một lần duy nhất và khởi chạy giao diện GTK4 + Libadwaita.

---

## 🖥️ Cấu Trúc Giao Diện GUI (5 Thẻ Chức Năng)

Giao diện ứng dụng được chia thành 5 thẻ chính trong điều hướng:

1. **📦 Cài đặt (Setup Stages)**: Danh sách 11 Giai đoạn tối ưu hóa hệ thống từ cơ bản đến nâng cao, cho phép bạn chọn cài đặt nhanh 1-Click hoặc từng giai đoạn cụ thể.
2. **🩺 Kiểm tra Hệ thống (System Health)**: Chẩn đoán tình trạng phần cứng, kiểm tra thông số CPU, RAM, GPU NVIDIA, trạng thái Wayland/X11 và dịch vụ nguồn.
3. **⚙️ Trạng thái Modules (Module Status & Rollback)**: Quản lý chi tiết từng module, hiển thị trạng thái đã cài đặt hay chưa, kèm nút **↩ Reset** để hoàn tác cấu hình từng module.
4. **🏆 Đánh giá Native (Native Score 100/100)**: Chấm điểm độ tương thích phần cứng/phần mềm của máy theo thang điểm 100 với 16 tiêu chí chi tiết.
5. **📜 Nhật ký (Full Log)**: Xem trực tiếp toàn bộ lệnh hệ thống đang thực hiện theo thời gian thực.

---

## 📋 Hướng Dẫn Sử Dụng Chi Tiết

Để tìm hiểu sâu hơn về cách sử dụng từng tính năng, hướng dẫn kiểm chứng thủ công, bảng điểm tương thích Native 100/100 và giải đáp thắc mắc thường gặp, vui lòng tham khảo tài liệu chi tiết:

👉 **[Xem Tài Liệu Hướng Dẫn Sử Dụng Chi Tiết (HUONG_DAN.md)](file:///run/media/pctai/0AAA0F280AAA0F28/project/My%20Project/nitro5-setup/HUONG_DAN.md)**

---

## 📄 Bản Quyền & Đóng Góp

* **Dự án**: Nitro5-Setup-GUI cho Fedora Workstation
* **Mục đích**: Tối ưu hóa hiệu năng, pin, nhiệt độ và trải nghiệm người dùng trên Acer Nitro 5 AN515-58.
