# 📘 Hướng Dẫn Sử Dụng Chi Tiết & Danh Sách Công Cụ Cài Đặt
### Bộ công cụ tối ưu hóa Acer Nitro 5 AN515-58 trên Fedora Workstation 41+ / 44 (Intel Core i5-12500H + NVIDIA RTX 3050 + 16GB RAM + Wayland Native)

Tài liệu này cung cấp hướng dẫn toàn diện về cách khởi chạy ứng dụng, cách sử dụng các tính năng điều khiển phần cứng chuyên sâu (quạt DAMX, đèn nền RGB bàn phím, giới hạn sạc pin), giải thích hệ thống chấm điểm tương thích **Native Score 100/100**, hướng dẫn kiểm chứng thủ công các thiết lập kernel và bảng danh sách chi tiết toàn bộ các module trong 11 giai đoạn cài đặt.

---

## 📑 Mục Lục

1. [Giới Thiệu & Cơ Chế Hoạt Động](#1-giới-thiệu--cơ-chế-hoạt-động)
2. [Cách Khởi Chạy & Cơ Chế Bảo Mật Sudo](#2-cách-khởi-chạy--cơ-chế-bảo-mật-sudo)
3. [Cài Đặt Siêu Tốc 1-Click (Stage 0 - Core Setup)](#3-cài-đặt-siêu-tốc-1-click-stage-0---core-setup)
4. [Hệ Thống Chấm Điểm Tương Thích Native 100/100 (Stage 9)](#4-hệ-thống-chấm-điểm-tương-thích-native-100100-stage-9)
5. [Điều Khiển Quạt & Hiệu Năng Với DAMX (Linuwu-Sense WMI)](#5-điều-khiển-quạt--hiệu-năng-với-damx-linuwu-sense-wmi)
6. [Điều Khiển Đèn Nền RGB Bàn Phím](#6-điều-khiển-đèn-nền-rgb-bàn-phím)
7. [Giới Hạn Sạc Pin (Battery Charge Limit Customizer)](#7-giới-hạn-sạc-pin-battery-charge-limit-customizer)
8. [Giám Sát Nhiệt Độ & Trạng Thái Hệ Thống (`s-tui` & `sensors`)](#8-giám-sát-nhiệt-độ--trạng-thái-hệ-thống-s-tui--sensors)
9. [Tính Năng Khôi Phục & Hoàn Tác Từng Module (Modular Rollback)](#9-tính-năng-khôi-phục--hoàn-tác-từng-module-modular-rollback)
10. [Hướng Dẫn Kiểm Chứng & Xác Thực Hệ Thống Thủ Công](#10-hướng-dẫn-kiểm-chứng--xác-thực-hệ-thống-thủ-công)
11. [Danh Sách Chi Tiết Toàn Bộ 11 Giai Đoạn & Modules Cài Đặt](#11-danh-sách-chi-tiết-toàn-bộ-11-giai-đoạn--modules-cài-đặt)
12. [Câu Hỏi Thường Gặp (FAQ) & Xử Lý Sự Cố (Troubleshooting)](#12-câu-hỏi-thường-gặp-faq--xử-lý-sự-cố-troubleshooting)

---

## 🚀 1. Giới Thiệu & Cơ Chế Hoạt Động

Dòng laptop gaming **Acer Nitro 5 AN515-58** sử dụng cấu trúc phần cứng lai phức tạp giữa CPU Intel thế hệ 12 (P-core + E-core) và card đồ họa rời NVIDIA GeForce RTX 3050/3060. Khi cài đặt Linux nói chung và Fedora Workstation nói riêng, người dùng thường gặp phải các thách thức:
* Hệ thống quản lý quạt mặc định không phản hồi theo nhiệt độ thực tế, thiếu phần mềm NitroSense như trên Windows.
* Máy hao pin nhanh do GPU NVIDIA không tự động chuyển sang chế độ ngủ sâu (`D3cold` / RTD3) khi không chạy tác vụ nặng.
* Trình quản lý nguồn mặc định chưa được tối ưu hóa cho NVMe Gen 4 và bộ nhớ zRAM.

**Nitro5-Setup-GUI** giải quyết toàn bộ các vấn đề trên bằng cách tích hợp các driver hạt nhân chuyên dụng (**Linuwu-Sense WMI**), cấu hình tự động GRUB kernel parameters, dịch vụ điều phối nguồn **TLP**, cùng giao diện đồ họa trực quan viết bằng **GTK4 + Libadwaita**.

---

## 🔐 2. Cách Khởi Chạy & Cơ Chế Bảo Mật Sudo

Để khởi chạy giao diện cài đặt và tối ưu hóa hệ thống, bạn chỉ cần mở Terminal và chạy lệnh sau:

```bash
cd <đường_dẫn_đến_thư_mục_nitro5-setup>
bash install.sh
```

### Quy Trình Xử Lý Thông Minh Của `install.sh`:
1. **Kiểm tra Hệ điều hành**: Xác nhận hệ điều hành là **Fedora Workstation 41+** (sử dụng trình quản lý gói `dnf5` tốc độ cao).
2. **Kiểm tra Phân vùng lưu trữ**: Nếu phát hiện thư mục mã nguồn đang nằm trên phân vùng định dạng Windows (`NTFS`, `vFAT`, `fuseblk`), script sẽ tự động cảnh báo và gợi ý sao chép toàn bộ bộ cài sang thư mục `~/nitro5-setup` trên hệ thống Linux để tránh lỗi mất kết nối I/O hoặc lỗi phân quyền khi biên dịch driver DKMS.
3. **Cơ chế Bảo mật Sudo Keep-Alive**:
   * Khi khởi chạy, script sẽ yêu cầu bạn nhập mật khẩu `sudo` **một lần duy nhất**.
   * Script tạo một tiến trình nền duy trì phiên làm việc (`sudo -n true` định kỳ 60 giây), giúp giao diện GUI thực hiện các lệnh quản trị mà không làm gián đoạn trải nghiệm hay đòi mật khẩu liên tục.
   * Ngay khi bạn đóng cửa sổ ứng dụng hoặc ngắt tiến trình (`Ctrl+C`), phiên làm việc ngầm lập tức được dọn dẹp an toàn.

---

## ⚡ 3. Cài Đặt Siêu Tốc 1-Click (Stage 0 - Core Setup)

Nếu bạn vừa cài mới Fedora Workstation và muốn tối ưu toàn bộ hệ thống nhanh nhất mà không cần chọn từng mục, hãy sử dụng tính năng **Cài đặt Lõi 1-Click (Stage 0)**.

### Cách thực hiện:
1. Mở GUI và chọn thẻ **📦 Cài đặt (Setup Stages)**.
2. Tại mục đầu tiên **⚡ Cài đặt Lõi (1-Click)**, bấm nút **Thực hiện ngay**.
3. Hệ thống sẽ tự động chạy tuần tự **27 module cốt lõi** theo đúng thứ tự tối ưu:
   * Chẩn đoán hệ thống & tối ưu hóa mạng DNF5 (`fastestmirror`, `max_parallel_downloads`).
   * Nâng cấp hệ điều hành & kích hoạt kho RPM Fusion (Free/Non-Free), Flathub.
   * Cài đặt Driver độc quyền NVIDIA, CUDA, VA-API và dịch vụ Switcheroo Control / EnvyControl.
   * Cài đặt trọn bộ Codec Đa phương tiện FFmpeg Full, GStreamer và máy chủ âm thanh PipeWire.
   * Cài đặt cảm biến `lm_sensors`, `thermald`, và driver điều khiển quạt **DAMX (Linuwu-Sense WMI)**.
   * Cấu hình nguồn **TLP Power Management**, zRAM zstd, tối ưu I/O NVMe và lịch TRIM SSD.
   * Kích hoạt bộ gõ Tiếng Việt **Fcitx5 Lotus**.
4. Sau khi hoàn tất toàn bộ 27 module, ứng dụng sẽ nhắc bạn khởi động lại máy để kích hoạt đầy đủ các driver kernel mới.

---

## 🏆 4. Hệ Thống Chấm Điểm Tương Thích Native 100/100 (Stage 9)

Thẻ **🏆 Đánh giá Native** (Stage 9) là công cụ kiểm tra sức khỏe và độ tương thích sâu của phần cứng Acer Nitro 5 AN515-58 trên Fedora Workstation theo thang điểm 100.

Bấm nút **🔄 Chấm điểm hệ thống** để chạy quét thời gian thực qua **16 tiêu chí** được chia thành 5 nhóm chuyên sâu:

| Nhóm Tiêu Chí | Tiêu Chí Đánh Giá | Điểm | Điều Kiện Đạt Điểm Tối Đa |
| :--- | :--- | :---: | :--- |
| **NVIDIA & GPU** *(Tối đa 25 điểm)* | **NVIDIA Driver Loaded** | 10 | Module hạt nhân `nvidia` đã được nạp thành công (`lsmod | grep nvidia`). |
| | **EnvyControl Hybrid Mode** | 8 | Chế độ đồ họa đang được cấu hình ở mức `hybrid` tối ưu hiệu năng & pin. |
| | **Switcheroo Control Service** | 7 | Dịch vụ `switcheroo-control` đang chạy để tự động chuyển lệnh render GPU. |
| **Nhiệt độ & Quạt** *(Tối đa 20 điểm)* | **Intel Thermal Daemon** | 8 | Dịch vụ `thermald` đang hoạt động để chống giảm xung đột ngột (thermal throttling). |
| | **Hardware Temperature Sensors** | 7 | Lệnh `sensors` nhận diện thành công cảm biến nhiệt độ `coretemp` / CPU / GPU. |
| | **Linuwu-Sense WMI Driver** | 5 | Driver hạt nhân `linuwu_sense` đã nạp, cho phép kiểm soát quạt & LED RGB. |
| **Nguồn & SSD & RAM** *(Tối đa 25 điểm)* | **TLP Power Management** | 8 | Dịch vụ `tlp.service` đang chạy ngầm, quản lý năng lượng AC/BAT tự động. |
| | **zRAM Virtual Memory Swap** | 7 | Bộ nhớ swap ảo `zram0` đã kích hoạt với thuật toán nén `zstd`. |
| | **fstrim SSD Timer** | 5 | Lịch trình `fstrim.timer` đã bật để tự động thu hồi khối trống SSD hàng tuần. |
| | **NVMe I/O Scheduler (none)** | 5 | Lập lịch I/O của ổ NVMe được đặt là `[none]` để giảm độ trễ tối đa cho SSD PCIe. |
| **Nhân Kernel & GRUB** *(Tối đa 15 điểm)* | **Kernel Deep Sleep (S3)** | 5 | Tham số GRUB `mem_sleep_default=deep` đã kích hoạt giúp tiết kiệm pin khi sleep. |
| | **PCIe AER Warning Suppress** | 5 | Tham số `pci=noaer` đã kích hoạt để chặn spam log lỗi bus PCIe. |
| | **Kernel Version Core Support** | 5 | Phiên bản Linux Kernel đang chạy đạt `>= 6.8`. |
| **Đa phương tiện / Bộ gõ** *(Tối đa 10 điểm)* | **PipeWire Audio Server** | 5 | Máy chủ âm thanh độ trễ thấp PipeWire đang hoạt động ổn định. |
| | **RPM Fusion FFmpeg Codec** | 5 | Bộ giải mã FFmpeg đã chuyển sang bản đầy đủ từ kho RPM Fusion. |
| **Bộ gõ Tiếng Việt** *(Tối đa 5 điểm)* | **Fcitx5 Input Framework** | 5 | Trình gõ Tiếng Việt Fcitx5 đang hoạt động nền. |

> [!TIP]
> **Thang xếp hạng sao**:
> * **90 – 100 điểm (⭐⭐⭐⭐⭐ Xuất sắc)**: Hệ thống đã hoàn toàn native, hoạt động tối ưu 100% hiệu năng và tiết kiệm pin.
> * **75 – 89 điểm (⭐⭐⭐⭐ Tốt)**: Máy chạy ổn định, chỉ thiếu một vài thiết lập tùy chọn nhỏ.
> * **Dưới 75 điểm**: Bạn nên chạy **Cài đặt Lõi 1-Click (Stage 0)** để tự động bổ sung các cấu hình còn thiếu.

---

## ❄️ 5. Điều Khiển Quạt & Hiệu Năng Với DAMX (Linuwu-Sense WMI)

Ứng dụng **DAMX (Dynamic Acer Management X)** được cài đặt để thay thế hoàn toàn phần mềm NitroSense trên Windows, tương thích trực tiếp với giao thức hiển thị Wayland trên Fedora.

### Cách mở giao diện DAMX:
* **Cách 1**: Nhấn phím **Super (Windows)** -> Tìm kiếm **"DAMX"** hoặc **"Acer Fan"** -> Nhấp vào biểu tượng để mở.
* **Cách 2**: Chạy lệnh trực tiếp từ Terminal:
  ```bash
  damx-launcher
  ```

### Các tính năng chính của DAMX:
* **Hiển thị thông số thời gian thực**: Theo dõi tốc độ quạt (RPM) và nhiệt độ CPU / GPU chính xác theo thời gian thực.
* **Chế độ quạt cố định**: Chuyển đổi nhanh giữa các chế độ **Quiet** (Yên tĩnh), **Normal** (Cân bằng), **Performance** (Hiệu năng cao), **Turbo** (Tối đa 100% công suất quạt).
* **Fan Curve tùy chỉnh**: Thiết lập biểu đồ đường cong tốc độ quạt theo từng mức nhiệt độ cụ thể.
* **Chế độ hiệu năng (Performance Profile)**: Chuyển đổi profile năng lượng ACPI của máy (Eco, Silent, Balanced, Performance, Turbo).

---

## 🌈 6. Điều Khiển Đèn Nền RGB Bàn Phím

* **Với Acer Nitro 5 AN515-58**: Driver **Linuwu-Sense WMI** tích hợp trong DAMX hỗ trợ điều chỉnh trực tiếp LED RGB bàn phím 4 vùng. Bạn có thể thay đổi màu sắc, độ sáng và chế độ hiệu ứng ngay trong giao diện đồ họa của DAMX mà không cần cài thêm công cụ bên ngoài.
* **Với các dòng Nitro 5 khác**: Hệ thống tự động cài đặt công cụ dòng lệnh **`facer-rgb`**. Bạn có thể tùy chỉnh qua Terminal:

```bash
# Đặt màu tĩnh (Static) cho vùng 1 (Màu đỏ sáng 100%)
sudo facer-rgb -m 0 -z 1 -b 100 -cR 255 -cG 0 -cB 0

# Chế độ chuyển màu Neon tuần hoàn
sudo facer-rgb -m 2 -s 3 -b 100

# Chế độ hiệu ứng sóng chuyển động (Wave)
sudo facer-rgb -m 3 -s 2 -b 100
```

---

## 🔋 7. Giới Hạn Sạc Pin (Battery Charge Limit Customizer)

Để bảo vệ pin lithium-ion không bị chai phồng khi cắm sạc liên tục để làm việc hoặc chơi game, bộ công cụ tích hợp sẵn tính năng giới hạn mức sạc tối đa.

### Cách thiết lập trên GUI:
1. Chuyển sang thẻ **📦 Cài đặt (Setup Stages)** -> Chọn **Stage 5 (Nguồn & SSD & RAM)**.
2. Tìm thanh trượt **Giới hạn sạc Pin (Battery Charge Limit)**.
3. Kéo thanh trượt tới mức mong muốn (khuyến nghị **80%** cho nhu cầu cắm sạc thường xuyên).
4. Nhấn nút **Áp dụng**. Hệ thống ghi trực tiếp mức giới hạn vào sysfs hạt nhân (`/sys/class/power_supply/BAT0/charge_control_limit_max`). Khi pin sạc tới mức đã chọn, máy sẽ tự động ngắt dòng sạc vào pin và dùng điện trực tiếp từ adapter.

---

## 📈 8. Giám Sát Nhiệt Độ & Trạng Thái Hệ Thống (`s-tui` & `sensors`)

Bộ công cụ cung cấp sẵn các tiện ích giám sát hiệu năng trực quan ngay trong Terminal:

* **Trình giám sát đồ họa TUI (`s-tui`)**:
  ```bash
  s-tui
  ```
  Hiển thị biểu đồ tần số xung nhịp CPU, nhiệt độ từng nhân, mức tiêu thụ điện năng (Watts) và hỗ trợ chạy bài test tải nặng (Stress test) để kiểm tra hiệu quả tản nhiệt.

* **Kiểm tra nhanh cảm biến nhiệt độ (`sensors`)**:
  ```bash
  sensors
  ```

---

## ↩️ 9. Tính Năng Khôi Phục & Hoàn Tác Từng Module (Modular Rollback)

Một trong những ưu điểm cốt lõi của **Nitro5-Setup-GUI** là khả năng quản lý độc lập từng module trong thẻ **⚙️ Trạng thái Modules**:

* **Kiểm tra trạng thái**: Bạn có thể dễ dàng xem module nào đã được cài đặt thành công (`Đã cài đặt`), module nào chưa chạy (`Chưa cài đặt`).
* **Nút Khôi phục (↩ Reset)**: Bên cạnh mỗi module có một nút **Reset**. Khi bấm vào, ứng dụng sẽ chạy các lệnh gỡ cài đặt, khôi phục lại tệp cấu hình gốc của hệ thống tương ứng với riêng module đó một cách an toàn mà không làm xáo trộn các module khác.

---

## 🔍 10. Hướng Dẫn Kiểm Chứng & Xác Thực Hệ Thống Thủ Công

Sau khi cài đặt, bạn có thể tự mình chạy các lệnh sau trong Terminal để xác thực hệ thống đã thực sự tối ưu hay chưa:

### 10.1. Kiểm tra tham số boot GRUB Kernel
```bash
cat /proc/cmdline
```
**Yêu cầu kết quả chứa**:
* `mem_sleep_default=deep` — Kích hoạt trạng thái ngủ sâu S3 Deep Sleep.
* `pci=noaer` — Vô hiệu hóa log báo lỗi bus PCIe AER.
* `pcie_aspm=force` — Ép kích hoạt tính năng quản lý nguồn liên kết PCIe ASPM.

### 10.2. Kiểm tra trạng thái ngủ sâu của GPU NVIDIA (RTD3)
Khi rút sạc hoặc khi không mở ứng dụng đồ họa nặng, GPU rời NVIDIA phải tự động chuyển sang trạng thái nghỉ:
```bash
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status
```
* **Kết quả đúng**: `suspended` (NVIDIA dGPU đang ở trạng thái D3cold tiết kiệm pin).
* **Kết quả sai**: `active` (GPU vẫn đang chạy, cần kiểm tra lại dịch vụ Switcheroo/EnvyControl).

### 10.3. Kiểm tra dịch vụ quản lý nguồn TLP
```bash
tlp-stat -s
```
* **Kết quả yêu cầu**: `State = enabled` và đang áp dụng đúng cấu hình AC/BAT.

### 10.4. Kiểm tra ép biến môi trường Wayland Native cho Electron
```bash
printenv ELECTRON_OZONE_PLATFORM_HINT
```
* **Kết quả yêu cầu**: `auto` (Các ứng dụng như VS Code, Discord, Obsidian sẽ tự động chạy native trên Wayland mượt mà).

---

## 📋 11. Danh Sách Chi Tiết Toàn Bộ 11 Giai Đoạn & Modules Cài Đặt

Dưới đây là bảng tổng hợp toàn bộ các module được chia theo 11 giai đoạn trong ứng dụng GUI:

| Giai Đoạn | Tên Module | Loại / Cách Cài | Mô Tả & Tính Năng |
| :--- | :--- | :--- | :--- |
| **Stage 0** | **Cài đặt Lõi 1-Click** | Siêu tốc tự động | Thực thi tuần tự 27 module cốt lõi quan trọng nhất của hệ thống chỉ với 1 cú nhấp chuột. |
| **Stage 1**<br>*(Hệ thống)* | **Tối ưu hóa DNF5** | `/etc/dnf/dnf.conf` | Chọn mirror nhanh nhất (`fastestmirror=True`) và bật tải song song 10 gói (`max_parallel_downloads=10`). |
| | **Chẩn đoán ban đầu** | CLI (`inxi`, `lspci`) | Quét thông số phần cứng, CPU, RAM, GPU, Kernel để đối chiếu. |
| | **Nâng cấp hệ thống** | DNF5 | Cập nhật toàn bộ hệ điều hành Fedora lên bản mới nhất. |
| | **RPM Fusion Repo** | RPM Fusion | Thêm kho phần mềm Free & Non-Free cho Fedora. |
| | **Flathub Repo** | Flatpak | Thêm kho ứng dụng Flatpak lớn nhất thế giới. |
| | **Firmware Updates** | `fwupdmgr` | Cập nhật BIOS & firmware thiết bị qua dịch vụ LVFS. |
| | **DKMS & Build-Tools** | DNF5 (`dkms`, `gcc`) | Cài đặt công cụ biên dịch tự động driver khi nâng cấp kernel. |
| | **Tinh chỉnh AN515-58** | Grubby script | Cấu hình Deep Sleep S3, tắt cảnh báo rác PCIe AER, ép PCIe ASPM và tự động tăng 100% âm lượng Headset Mic. |
| **Stage 2**<br>*(NVIDIA & GPU)* | **Driver NVIDIA** | `akmod-nvidia` | Cài đặt driver độc quyền chính thức tối ưu cho RTX 3050, tương thích Wayland và RTD3. |
| | **NVIDIA CUDA Support** | DNF5 | Cài đặt bộ thư viện CUDA hỗ trợ AI, Deep Learning và render đồ họa. |
| | **NVIDIA VA-API Driver** | DNF5 | Hỗ trợ giải mã video phần cứng trên trình duyệt Firefox/Chrome qua GPU NVIDIA. |
| | **Switcheroo Control** | Systemd Service | Dịch vụ tự động chuyển đổi đồ họa thông minh giữa iGPU Intel và dGPU NVIDIA. |
| | **EnvyControl** | CLI / Pip | Quản lý và chuyển đổi chế độ đồ họa (Hybrid / Optimus / Integrated). |
| | **Sửa lỗi độ sáng** | Grubby (`acpi_backlight`) | Sửa lỗi thanh trượt độ sáng màn hình GNOME trên GPU Optimus (`acpi_backlight=native`). |
| | **Gamemode & MangoHud** | DNF5 | Tối ưu tài nguyên CPU/GPU khi chơi game và HUD hiển thị FPS/nhiệt độ thực tế. |
| | **Sửa lỗi Suspend NVIDIA**| Kernel parameter | Bật giữ lại bộ nhớ video khi sleep (`NVreg_PreserveVideoMemoryAllocations=1`) tránh lỗi màn đen. |
| | **NVIDIA Wayland/GDM** | Udev rules | Bảo đảm GDM hoạt động mượt mà trên Wayland và có cơ chế fallback an toàn. |
| **Stage 3**<br>*(Codec & Audio)*| **Full FFmpeg Codec** | RPM Fusion | Thay thế bản FFmpeg giới hạn bằng bản đầy đủ hỗ trợ H.264/H.265/HEVC/AV1. |
| | **Intel Media Driver** | DNF5 | Tăng tốc phần cứng giải mã video trên iGPU Intel (`libva-intel-media-driver`). |
| | **PipeWire Audio** | Systemd | Cấu hình máy chủ âm thanh thế hệ mới độ trễ thấp PipeWire & WirePlumber. |
| | **Bluetooth & aptX** | DNF5 | Cài đặt codec âm thanh chất lượng cao aptX/LDAC cho tai nghe Bluetooth. |
| **Stage 4**<br>*(Nhiệt độ & Quạt)*| **Cảm biến lm_sensors** | DNF5 | Quét và cấu hình nhận dạng cảm biến nhiệt độ phần cứng. |
| | **Intel Thermald** | Systemd Service | Dịch vụ ngăn chặn quá nhiệt và ổn định xung nhịp CPU Intel. |
| | **DAMX GUI & Driver** | Git + DKMS | Cài đặt driver Linuwu-Sense WMI & GUI DAMX điều khiển quạt, LED RGB 4 vùng và Profile. |
| | **s-tui Monitor** | DNF5 | Trình giám sát đồ thị tần số và nhiệt độ CPU trong Terminal. |
| | **CoreTemp Module** | Systemd conf | Tự động nạp module `coretemp` khi khởi động máy. |
| **Stage 5**<br>*(Nguồn & SSD)* | **TLP Power Management**| DNF5 & Systemd | Quản lý năng lượng thông minh thay thế PPD, tối ưu thời lượng pin tối đa. |
| | **Battery Charge Limit** | GUI Slider | Thanh trượt giới hạn sạc pin từ 50% - 100% bảo vệ tuổi thọ pin. |
| | **Swappiness Config** | `/etc/sysctl.d` | Tối ưu hóa swappiness=10 (với RAM > 16GB) giảm ghi SSD hoặc swappiness=100 (RAM <= 16GB) ưu tiên zRAM. |
| | **SSD Mount & Scheduler**| `/etc/fstab` & Udev | Tối ưu hóa tùy chọn mount Btrfs và chuyển I/O scheduler sang `[none]` cho SSD NVMe. |
| | **SSD Fstrim Timer** | Systemd Timer | Tự động TRIM dọn dẹp khối trống SSD hàng tuần. |
| | **USB Autosuspend Fix** | Udev rules | Vô hiệu hóa ngắt nguồn tự động đối với chuột và thiết bị HID USB. |
| | **zRAM zstd** | Generator | Tạo bộ nhớ ảo zRAM bằng 1/2 RAM vật lý với thuật toán nén `zstd` tốc độ cao. |
| | **Ananicy-CPP** | COPR Repo | Tự động điều phối độ ưu tiên CPU cho các ứng dụng desktop giúp giao diện luôn mượt mà. |
| | **Dirty Ratio Config** | `/etc/sysctl.d` | Tối ưu tham số `dirty_ratio=20` cho SSD NVMe Gen 4. |
| **Stage 6**<br>*(GNOME & App)* | **GNOME Tweaks & Ext** | DNF5 | Cài đặt công cụ tinh chỉnh GNOME và các tiện ích mở rộng hữu ích. |
| | **Fractional Scaling** | Gsettings | Mở khóa tỷ lệ hiển thị lẻ 125% và 150% cho màn hình độ phân giải cao. |
| | **Keyboard Shortcuts** | Gsettings | Thiết lập phím tắt `Ctrl+Alt+T` mở Terminal, `Super+L` khóa màn hình chuẩn tiện lợi. |
| | **Ứng dụng Flatpak** | Flatpak | Cài đặt VLC, Flatseal, Discord, LocalSend, EasyEffects và Extension Manager. |
| | **EasyEffects Presets** | Audio Profiles | Bộ lọc âm thanh vòm 3D DTS:X Ultra giả lập cho loa laptop. |
| | **Electron Wayland Native**| `/etc/profile.d` | Ép các ứng dụng Electron (VS Code, Discord, Obsidian...) chạy native Wayland chống mờ chữ. |
| | **Steam Gaming** | DNF5 | Cài đặt nền tảng game Steam & Proton tối ưu chơi game Windows trên Linux. |
| | **Bộ gõ Fcitx5 Lotus** | DNF5 | Bộ gõ Tiếng Việt hiện đại, hoạt động native trên Wayland không bị lỗi gạch chân. |
| **Stage 7**<br>*(Lập trình)* | **Google Chrome** | RPM Repository | Trình duyệt Google Chrome chính thức. |
| | **VS Code** | Microsoft Repo | Trình soạn thảo Visual Studio Code chính thức. |
| | **Obsidian** | Flatpak | Ứng dụng ghi chú kiến thức Markdown. |
| | **Môi trường C/C++** | DNF5 | `gcc`, `g++`, `cmake`, `make`, `gdb`, `ninja-build`, `clang`. |
| | **Môi trường Python 3** | DNF5 | `python3-pip`, `python3-devel`, `python3-virtualenv`. |
| | **Môi trường Java** | DNF5 | OpenJDK Development Kit và Maven. |
| | **Môi trường .NET SDK** | DNF5 | .NET SDK 8.0/9.0 cho phát triển C#. |
| | **Môi trường Node.js** | DNF5 | `nodejs`, `npm` phát triển web. |
| | **Môi trường Rust** | `rustup` | Toolchain Rust stable & Cargo. |
| | **Podman Rootless** | DNF5 | Container runtime tương thích Docker chạy không cần quyền root. |
| **Stage 8**<br>*(Dọn dẹp)* | **Dọn dẹp DNF5 Cache** | DNF5 | Xóa bộ nhớ đệm DNF5, gói mồ côi và kernel cũ không dùng. |
| | **Dọn dẹp Logs** | CLI | Giới hạn dung lượng log hệ thống journald tối đa 100MB. |
| | **Dọn dẹp User Cache** | CLI | Xóa sạch thư mục tạm `~/.cache` của người dùng. |
| | **Dọn dẹp Flatpak** | Flatpak | Gỡ bỏ các runtime Flatpak thừa không còn ứng dụng nào phụ thuộc. |
| | **SSD Trim thủ công** | CLI | Chạy lệnh `fstrim -v /` thu hồi ngay các khối trống SSD. |
| **Stage 9**<br>*(Chấm điểm)* | **Native Score 100/100** | Hệ thống quét | Đánh giá độ tương thích phần cứng/phần mềm với 16 tiêu chí chi tiết. |
| **Stage 10**<br>*(Cập nhật)* | **Cập nhật Toàn diện** | 1-Click Update | Quét cập nhật DNF5, Flatpak, và tự động biên dịch lại driver DKMS (`dkms autoinstall`). |
| **Stage 11**<br>*(Nâng cao)* | **Btrfs Snapshot** | Snapper & GRUB | Cấu hình tạo snapshot tự động trước khi update và cho phép boot vào snapshot từ menu GRUB. |
| | **Mở cổng Firewall Dev** | `firewalld` | Mở cổng tường lửa 3000, 5000, 8000 phục vụ lập trình web server nội bộ. |
| | **Ethernet EEE Fix** | Dispatcher script | Tắt Energy Efficient Ethernet cho card mạng Killer E2600 tránh hiện tượng rớt mạng. |
| | **Webcam & V4L2 Setup** | DNF5 | Cài đặt `v4l-utils` và `cheese` để quản lý camera. |
| | **Thunderbolt Policy** | Systemd conf | Tự động xác thực (`auto-authorize`) cho các thiết bị cắm cổng Thunderbolt 4. |

---

## ❓ 12. Câu Hỏi Thường Gặp (FAQ) & Xử Lý Sự Cố (Troubleshooting)

### Q1: Khi chạy `install.sh` báo cảnh báo phân vùng NTFS/vFAT của Windows?
**Trả lời**: Hệ thống tập tin NTFS của Windows không hỗ trợ đầy đủ các quyền sở hữu tệp tin POSIX (`chmod`, `chown`) và symlink của Linux. Nếu bạn biên dịch driver hạt nhân (DKMS) hoặc chạy pip/venv trực tiếp trên ổ NTFS sẽ dễ gặp lỗi `Transport endpoint is not connected` hoặc lỗi phân quyền.
* **Cách giải quyết**: Khi `install.sh` hỏi *"Bạn có muốn tự động copy bộ cài sang `~/nitro5-setup` không?"*, hãy chọn **Y (Yes)**. Script sẽ tự sao chép sang thư mục Home trên ổ Linux và hướng dẫn bạn chạy từ đó.

### Q2: Làm thế nào nếu sau khi cài driver NVIDIA màn hình đăng nhập GDM bị đen hoặc không vào được Wayland?
**Trả lời**: Bộ công cụ đã tích hợp sẵn quy tắc udev và biến môi trường bảo đảm GDM hoạt động với NVIDIA Wayland. Nếu gặp sự cố:
1. Chuyển sang TTY bằng tổ hợp phím `Ctrl + Alt + F3`.
2. Đăng nhập tài khoản của bạn và chạy lệnh kiểm tra module nvidia:
   ```bash
   modinfo -F version nvidia
   ```
3. Nếu cần chuyển GDM về chế độ X11 truyền thống an toàn, chỉnh sửa tệp `/etc/gdm/custom.conf` và bỏ ghi chú dòng `WaylandEnable=false`, sau đó khởi động lại máy (`sudo reboot`).

### Q3: Tôi muốn khôi phục lại cấu hình gốc trước khi chạy Nitro5-Setup thì làm thế nào?
**Trả lời**: Bạn có 2 phương án khôi phục:
* **Khôi phục từng phần (Khuyên dùng)**: Mở ứng dụng GUI -> Vào thẻ **⚙️ Trạng thái Modules** -> Bấm nút **↩ Reset** ở module bạn muốn gỡ cấu hình.
* **Khôi phục toàn bộ hệ thống qua Btrfs Snapshot (Nếu đã bật ở Stage 11)**: Khởi động lại máy -> Tại menu GRUB chọn **Fedora Linux snapshots** -> Chọn điểm khôi phục trước thời điểm cài đặt để quay trở lại chính xác trạng thái hệ thống lúc đó.

---
*Tài liệu được cập nhật cho phiên bản Nitro5-Setup-GUI chạy trên Fedora Workstation 41+ / 44 (Wayland Native).*
