# 📘 Hướng Dẫn Sử Dụng & Danh Sách Công Cụ Cài Đặt
### Bộ công cụ tối ưu hóa Acer Nitro 5 AN515-58 trên Fedora Workstation 44 (Intel Core i5-12500H + RTX 3050 + 16GB RAM)

Tài liệu này hướng dẫn cách khởi chạy bộ công cụ thiết lập, cách kiểm tra thủ công các thay đổi để xác thực hệ thống, cách sử dụng các phần mềm điều khiển quạt, LED RGB bàn phím, giới hạn sạc pin, tính năng khôi phục cài đặt gốc (Reset) và danh sách chi tiết các công cụ/môi trường phát triển đã được cài đặt.

---

## 🚀 1. Cách Khởi Chạy Bộ Công Cụ Tối Ưu (Setup Utility)

Để cấu hình hệ thống, cài đặt driver hoặc cài đặt thêm môi trường lập trình mới, bạn chỉ cần mở Terminal và chạy lệnh sau:

```bash
cd <đường_dẫn_đến_thư_mục_nitro5-setup>
bash install.sh
```

### Quy Trình Bảo Mật Mật Khẩu (Secure Keyring Pipeline):
*   Ứng dụng sử dụng thư viện **GNOME Keyring** thông qua `python3-keyring` để lưu trữ mật khẩu quản trị (`sudo`) tạm thời khi bắt đầu chạy GUI.
*   Mật khẩu của bạn được mã hóa an toàn ở cấp độ hệ thống thay vì lưu dạng văn bản thuần (plain-text) trong bộ nhớ ứng dụng.
*   Token sudo sẽ tự động được thu hồi và **xóa sạch hoàn toàn** khỏi keyring hệ thống khi tắt GUI bình thường, khi nhấn đóng cửa sổ hoặc khi ứng dụng nhận được tín hiệu ngắt đột ngột (`SIGINT` / Ctrl+C, `SIGTERM`).

---

## ❄️ 2. Điều Khiển Quạt & Hiệu Năng Với DAMX

Ứng dụng **DAMX** (Dynamic Acer Management X) được cài để thay thế NitroSense trên Windows, hỗ trợ tốt nhất cho Intel i5-12500H + RTX 3050 trên AN515-58.

### Cách khởi chạy:
*   **Cách 1 (Giao diện đồ họa)**: Nhấn phím **Windows (Super)** -> Gõ tìm kiếm **"DAMX"** hoặc **"Acer Fan"** -> Click vào icon ứng dụng để mở.
*   **Cách 2 (Dòng lệnh)**: Khởi chạy trực tiếp từ Terminal bằng lệnh:
    ```bash
    damx-launcher
    ```

### Tính năng chính:
*   Sử dụng driver **Linuwu-Sense WMI** (giao tiếp trực tiếp cổng WMI ACPI kernel thay thế cho module `acer_wmi` mặc định hay bị lỗi).
*   Theo dõi tốc độ quạt CPU và GPU theo thời gian thực.
*   Chọn chế độ quạt: **Quiet**, **Normal**, **Performance**, **Turbo** (Max).
*   Fan Curve tùy chỉnh — kiểm soát tốc độ quạt theo nhiệt độ CPU/GPU.
*   Chọn Performance Profile tương tự NitroSense trên Windows (Eco, Silent, Balanced, Performance, Turbo).
*   Hỗ trợ Wayland native (chạy native trên giao thức Wayland không thông qua lớp dịch XWayland).

---

## 🌈 3. Điều Khiển Đèn Nền RGB Bàn Phím

*   **Đối với Acer Nitro 5 AN515-58**: Driver **Linuwu-Sense** tích hợp sẵn trong ứng dụng DAMX đã bao gồm tính năng điều chỉnh LED RGB bàn phím 4 vùng. Do đó, hệ thống sẽ tự động bỏ qua driver `facer-rgb` độc lập để tránh xung đột xung khắc phần cứng. Bạn chỉ cần chỉnh LED trực tiếp trên giao diện của DAMX.
*   **Đối với các dòng Nitro 5 khác**: Hệ thống sẽ tự động cài đặt driver hạt nhân `facer` (`acer-predator-module`). Bạn có thể thay đổi hiệu ứng LED trực tiếp qua giao diện dòng lệnh bằng công cụ **`facer-rgb`** (yêu cầu `sudo`).

### Các lệnh điều khiển LED phổ biến (Chỉ dùng cho các dòng khác AN515-58):

*   **Chế độ Static (Màu tĩnh cho từng vùng)**:
    ```bash
    sudo facer-rgb -m 0 -z 1 -b 100 -cR 255 -cG 0 -cB 0
    ```
    *(Thay đổi `-z` từ 1 đến 4 để chỉnh các vùng khác, chỉnh `-cR`, `-cG`, `-cB` từ 0 đến 255 để phối màu).*
*   **Chế độ Neon (Đổi màu tuần hoàn)**:
    ```bash
    sudo facer-rgb -m 2 -s 3 -b 100
    ```
*   **Chế độ Wave (Sóng màu chuyển động)**:
    ```bash
    sudo facer-rgb -m 3 -s 2 -b 100
    ```

---

## 🔋 4. Giới Hạn Sạc Pin (Battery Charge Limit Customizer)

Để bảo vệ tuổi thọ pin khi bạn cắm sạc liên tục để làm việc hoặc chơi game, bộ công cụ tích hợp thanh trượt giới hạn sạc trực tiếp trong GUI ở Stage 5.

### Cách sử dụng:
1.  Chuyển sang **Stage 5 (Nguồn & SSD & RAM)** trên giao diện Setup Utility.
2.  Kéo thanh trượt **Giới hạn sạc Pin** đến mức mong muốn (Ví dụ: 80% là mức khuyên dùng tối ưu).
3.  Nhấn nút **Áp dụng**. GUI sẽ gọi lệnh ghi trực tiếp giá trị vào sysfs của kernel (`/sys/class/power_supply/BAT0/charge_control_limit_max` hoặc BAT1/WMI).
4.  Khi sạc đạt mức giới hạn, hệ thống sẽ tự động ngắt nhận điện vào pin và chuyển sang dùng nguồn AC trực tiếp, giúp pin không bị chai phồng.

---

## 📈 5. Giám Sát Nhiệt Độ Hệ Thống Với `s-tui`

Bộ công cụ đã cài đặt **`s-tui`** - trình giám sát hiệu năng TUI siêu nhẹ và trực quan. Để mở biểu đồ giám sát CPU, nhiệt độ và công suất tiêu thụ của máy, bạn chỉ cần chạy lệnh:

```bash
s-tui
```

---

## ↩️ 6. Tính Năng Reset Khôi Phục Mặc Định (Rollback)

GUI Setup Utility được tích hợp nút **↩ Reset** ở góc phải của từng thẻ dịch vụ/công cụ.
*   **Mục đích**: Cho phép bạn hoàn tác, gỡ bỏ cài đặt hoặc khôi phục lại cấu hình gốc của hệ thống của từng module riêng lẻ một cách an toàn mà không cần cài đặt lại từ đầu.
*   **Cách sử dụng**: Bấm nút **↩ Reset** trên module muốn hoàn tác -> Hộp thoại xác nhận xuất hiện -> Đồng ý để ứng dụng chạy các lệnh gỡ cài đặt tương ứng.

---

## 🔍 7. Hướng Dẫn Xác Thực Hệ Thống Thủ Công (Diagnostics & Verification)

Sau khi hoàn thành cài đặt, bạn có thể kiểm chứng xem các cấu hình tối ưu đã hoạt động thực tế trên máy hay chưa qua các lệnh kiểm tra sau:

### 7.1. Xác thực Kernel Parameters (GRUB)
Chạy lệnh kiểm tra tham số boot của nhân:
```bash
cat /proc/cmdline
```
**Yêu cầu kết quả phải chứa các tham số:**
*   `mem_sleep_default=deep` (Ép dùng Deep Sleep S3 thay thế cho s2idle hao pin).
*   `pci=noaer` (Vô hiệu hóa spam log cảnh báo lỗi bus PCIe).
*   `pcie_aspm=force` (Ép kích hoạt liên kết tiết kiệm điện PCIe ASPM - điều kiện cần để GPU đi vào trạng thái ngủ sâu).

### 7.2. Xác thực Trạng Trái Ngủ Sâu của GPU NVIDIA (RTD3)
Khi máy không cắm sạc và không chạy ứng dụng 3D nặng, GPU rời NVIDIA phải tự động chuyển sang chế độ ngủ sâu (`D3cold`) để tiết kiệm pin.
Chạy lệnh kiểm tra trạng thái nguồn của dGPU:
```bash
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status
```
*   **Kết quả đúng**: `suspended` (NVIDIA dGPU đang ngủ).
*   **Kết quả sai**: `active` (NVIDIA dGPU vẫn đang thức, đang ngốn pin).

### 7.3. Xác thực Dịch Vụ TLP Power Profiles
Kiểm tra xem dịch vụ TLP đã chạy ổn định và cấu hình đúng profile chưa:
```bash
tlp-stat -s
```
*   **Kết quả**: `State = enabled` cùng với thông tin cấu hình AC/BAT tối ưu từ `/etc/tlp.conf`.

### 7.4. Xác thực Cấu Hình Electron Wayland Native
Kiểm tra xem biến môi trường ép Electron chạy native Wayland đã hoạt động chưa:
```bash
printenv ELECTRON_OZONE_PLATFORM_HINT
```
*   **Kết quả**: `auto` (Đã cấu hình thành công).

---

## 📋 8. Danh Sách Các Công Cụ & Môi Trường Đã Cài Đặt

Dưới đây là danh sách phân loại chi tiết các công cụ được cài đặt và tối ưu hóa theo 10 giai đoạn trong GUI:

| Giai Đoạn | Tên Mục | Loại / Cách Cài | Mô Tả & Tính Năng |
| :--- | :--- | :--- | :--- |
| **Giai đoạn 1** | Tối ưu hóa DNF | File `/etc/dnf/dnf.conf` & `dnf5.conf` | Tự động chọn mirror phản hồi nhanh nhất gần VN (`fastestmirror=True`) và bật tải song song 10 gói cùng lúc (`max_parallel_downloads=10`). |
| | Chẩn đoán ban đầu | DNF5 (`inxi`) | Tạo thông tin phần cứng ban đầu đối chiếu khi có sự cố. |
| | Nâng cấp hệ thống | DNF5 | Cập nhật tất cả các gói lên bản mới nhất của Fedora. |
| | RPM Fusion Repo | RPM Fusion (Free & Non-Free) | Cài đặt các kho chứa driver độc quyền và phần mềm bản quyền. |
| | Flathub | Flatpak | Thêm kho ứng dụng Flatpak lớn nhất thế giới. |
| | Firmware Updates | CLI (`fwupdmgr`) | Cập nhật firmware thiết bị qua LVFS. |
| | DKMS & Build-Tools | DNF5 (`kernel-devel`, `dkms`) | Biên dịch tự động các driver bên ngoài khi nâng cấp kernel. |
| | Tinh chỉnh Native AN515-58 | Grubby config & Profile script | Kích hoạt Deep Sleep S3, chặn cảnh báo rác PCIe AER, ép PCIe ASPM và tự động boost 100% âm lượng Headset Mic. |
| **Giai đoạn 2** | Driver NVIDIA | DNF5 (`akmod-nvidia`) | Bộ driver độc quyền chính thức từ NVIDIA tối ưu nhất cho RTX 3050, tương thích chuẩn với Wayland và RTD3. |
| | NVIDIA CUDA Support | DNF5 | Thư viện tính toán song song CUDA để hỗ trợ các tác vụ AI, Deep Learning. |
| | Nvidia VA-API Driver | DNF5 & `/etc/environment` | Hỗ trợ giải mã video phần cứng trên trình duyệt Firefox/Chrome qua GPU NVIDIA. |
| | Switcheroo Control | Systemd Service | Dịch vụ điều phối đồ họa thông minh giữa CPU Intel và GPU NVIDIA. |
| | EnvyControl | Pip & CLI | Chuyển đổi và quản lý chế độ hoạt động đồ họa (Hybrid/Optimus/Integrated). |
| | Sửa lỗi độ sáng | Grubby config | Sửa lỗi thanh trượt độ sáng GNOME trên GPU Optimus bằng kernel parameter `acpi_backlight=native`. |
| | Gamemode & MangoHud | DNF5 | Thư viện tối ưu hóa CPU/GPU khi chơi game và HUD hiển thị FPS/nhiệt độ thực tế. |
| | Sửa lỗi Suspend NVIDIA | DNF5 & kernel parameter | Bật tính năng giữ lại bộ nhớ video khi sleep (`nvidia.NVreg_PreserveVideoMemoryAllocations=1`) tránh lỗi màn hình đen. |
| | NVIDIA Wayland/GDM | Udev & profile environment | Khôi phục fallback GDM an toàn về X11 nếu driver gặp sự cố. |
| **Giai đoạn 3** | Codec Đa Phương Tiện | DNF5 | Cài đặt đầy đủ bộ giải mã video chuẩn từ RPM Fusion (FFmpeg bản đầy đủ, GStreamer). |
| | Thư viện Intel Media | DNF5 (`libva-intel-media-driver`) | Tăng tốc phần cứng giải mã video trên iGPU Intel. |
| | PipeWire | DNF5 & Systemd | Máy chủ âm thanh thế hệ mới độ trễ cực thấp. |
| | Bluetooth & aptX | DNF5 & WirePlumber | Cài đặt dịch vụ bluetooth, aptX codec cho PipeWire. |
| **Giai đoạn 4** | Cảm biến lm_sensors | DNF5 | Quét và nhận diện các cảm biến nhiệt độ phần cứng. |
| | Intel Thermald | DNF5 & Systemd | Dịch vụ ngầm chống quá nhiệt CPU Intel. |
| | DAMX GUI & Driver | Git + DKMS + .NET | Công cụ GUI & driver Linuwu-Sense WMI điều khiển quạt, LED RGB bàn phím và Performance Profile thay NitroSense. |
| | s-tui | DNF5 | Giám sát đồ thị nhiệt độ và công suất CPU. |
| | CoreTemp Module | Systemd configuration | Tự động load module `coretemp` khi khởi động để thu thập nhiệt độ CPU. |
| **Giai đoạn 5** | TLP Power Management | DNF5 & Systemd | Trình quản lý nguồn thay thế tuned/PPD, tối ưu hóa pin tối đa. |
| | Battery Charge Limit | GUI Slider (sysfs kernel) | Thanh trượt tùy chỉnh giới hạn sạc từ 50% đến 100% bảo vệ pin. |
| | Swappiness Config | `/etc/sysctl.d` | Giảm swappiness xuống `10` nếu RAM > 16GB để giảm ghi SSD; tăng lên `100` nếu RAM <= 16GB để ưu tiên zRAM. |
| | SSD Mount & Scheduler | Udev rules & `/etc/fstab` | Tối ưu hóa Btrfs fstab và I/O scheduler chuyển sang `none` đối với SSD NVMe. |
| | SSD Fstrim | Systemd Timer | Tự động dọn dẹp khối trống SSD hàng tuần. |
| | Usb Autosuspend Fix | Udev rules | Vô hiệu hóa tự động ngắt nguồn USB cho chuột và thiết bị HID/input. |
| | zRAM zstd | DNF5 & generator | Cấu hình zRAM swap bằng 1/2 dung lượng RAM vật lý sử dụng thuật toán nén zstd tối ưu nhất. |
| | Ananicy-CPP | DNF5 COPR | Tự động điều phối độ ưu tiên CPU (nice values) cho các ứng dụng desktop giúp giảm giật lag UI. |
| | Dirty Ratio Config | `/etc/sysctl.d` | Tối ưu dirty_ratio=20 cho SSD NVMe Gen 4. |
| **Giai đoạn 6** | GNOME Tweaks & App | DNF5 | Cài đặt công cụ tinh chỉnh giao diện nâng cao và extensions. |
| | Fractional Scaling | Gsettings | Mở khóa mức scale hiển thị lẻ 125% và 150%. |
| | Keyboard Shortcuts | Gsettings | Đặt Ctrl+Alt+T mở Terminal, Super+L khóa màn hình để tối ưu trải nghiệm. |
| | Các ứng dụng Flatpak | Flatpak | Cài đặt VLC, Flatseal, Discord, LocalSend, EasyEffects và Extension Manager. |
| | EasyEffects Presets | Git download | Cài đặt các profile lọc âm thanh JackHack96 mang lại hiệu ứng âm thanh vòm 3D DTS:X Ultra giả lập cho loa laptop. |
| | Electron Wayland Native| `/etc/profile.d` | Buộc các app Electron (VS Code, Discord, Obsidian...) chạy native trên Wayland tránh mờ/giật lag. |
| | Steam Gaming | DNF5 | Trình quản lý game Steam kích hoạt sẵn Proton chơi game Windows. |
| | Spotify & SpotX | Flatpak + Curl | Cài đặt Spotify qua Flatpak và áp dụng patch SpotX-Bash để loại bỏ quảng cáo. |
| **Giai đoạn 7** | Google Chrome | DNF5 (Native RPM) | Trình duyệt Google Chrome bản chính thức ổn định. |
| | VS Code | DNF5 (Native RPM Repo) | Trình soạn thảo VS Code chính thức từ Microsoft. |
| | Obsidian | Flatpak | Ứng dụng ghi chú Markdown. |
| | Môi trường C/C++ | DNF5 | gcc, g++, cmake, make, gdb, ninja-build, clang. |
| | Môi trường Python 3 | DNF5 | python3-pip, python3-devel, python3-virtualenv. |
| | Môi trường Java | DNF5 | OpenJDK Development Kit và Maven. |
| | Môi trường .NET | DNF5 | .NET SDK 8.0/9.0 để viết C#. |
| | Môi trường Node.js | DNF5 | nodejs, npm phát triển web. |
| | Môi trường Rust | DNF5 & rustup | rustup stable toolchain & cargo. |
| | Podman Rootless | DNF5 & systemd | Podman rootless, compose và socket API tương thích Docker. |
| **Giai đoạn 8** | Dọn dẹp DNF5 Cache | DNF5 | Dọn dẹp cache DNF5, autoremove và xóa kernel cũ. |
| | Dọn dẹp Logs | CLI | Giới hạn dung lượng log hệ thống tối đa 100MB và cũ hơn 2 tuần. |
| | Dọn dẹp User Cache | CLI | Xóa sạch bộ nhớ đệm trong ~/.cache của người dùng. |
| | Dọn dẹp Flatpak | Flatpak | Dọn các runtime Flatpak thừa không sử dụng. |
| | SSD Trim | CLI | Chạy lệnh fstrim tối ưu hóa và dọn khối trống SSD thủ công. |
| | Dọn dẹp Build temp | CLI | Xóa bỏ các thư mục source build tạm trong /tmp. |
| **Giai đoạn 10** | Cập nhật Toàn diện | DNF5 + Flatpak + DKMS | Cập nhật hệ thống (DNF5), ứng dụng Flatpak, tự động biên dịch lại driver DKMS (dkms autoinstall). |
| **Giai đoạn 11** | Btrfs Snapshot | Snapper & grub-btrfs | Cấu hình tạo snapshot tự động trước khi dnf update và cho phép boot vào snapshot từ menu boot GRUB. |
| | Mở port dev | Firewall | Mở cổng tường lửa 3000, 5000, 8000 cho dev server. |
| | Ethernet EEE Fix | dispatcher script | Tắt Energy Efficient Ethernet cho Killer E2600 tránh rớt mạng. |
| | Webcam setup | DNF5 | Cài đặt v4l-utils và Cheese để sẵn sàng camera. |
| | Thunderbolt Policy | Systemd & conf | Thiết lập Bolt daemon tự động kết nối (auto-authorize) cho Thunderbolt 4. |
