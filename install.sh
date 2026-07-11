#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# ============================================================
#  Acer Nitro 5 AN515-58 — Fedora Workstation Setup Utility
#  Bootstrap script: kiem tra moi truong, cai dependency, launch GUI
# ============================================================

# Mau sac thong bao
RED='\e[1;31m'
GREEN='\e[1;32m'
YELLOW='\e[1;33m'
BLUE='\e[1;34m'
CYAN='\e[1;36m'
NC='\e[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ACER NITRO 5 AN515-58 — FEDORA WORKSTATION SETUP  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"

# 1. Kiểm tra Hệ điều hành (Fedora 41+)
if [ -f /etc/os-release ]; then
    source /etc/os-release
    if [ "$ID" != "fedora" ]; then
        echo -e "${RED}[LỖI] Hệ điều hành không được hỗ trợ ($NAME). Chỉ hỗ trợ Fedora Workstation!${NC}"
        exit 1
    fi
    
    # Kiểm tra phiên bản Fedora 41+ để dùng dnf5
    if (( ${VERSION_ID} < 41 )); then
        echo -e "${RED}[LỖI] Phiên bản Fedora của bạn là $VERSION_ID. Script yêu cầu Fedora 41+ sử dụng dnf5 mặc định!${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Phát hiện Fedora $VERSION_ID${NC}"
else
    echo -e "${RED}[LỖI] Không thể đọc tệp tin /etc/os-release để nhận diện hệ điều hành. Thất bại!${NC}"
    exit 1
fi

# 1b. Bỏ qua phát hiện Desktop Environment — chỉ hỗ trợ GNOME Workstation
DETECTED_DE="GNOME"
echo -e "${GREEN}[OK] Chế độ GNOME Workstation (Fedora Workstation) được kích hoạt.${NC}"
# Xuất biến môi trường để Python có thể đọc được
export XDG_CURRENT_DESKTOP="GNOME"

# 1c. Kiểm tra hệ thống tập tin của thư mục hiện tại (tránh fuseblk/NTFS gây lỗi build/ngắt kết nối)
FS_TYPE=$(df -T . 2>/dev/null | awk 'NR==2 {print $2}')
if [[ "$FS_TYPE" == "fuseblk" || "$FS_TYPE" == "ntfs" || "$FS_TYPE" == "vfat" || "$FS_TYPE" == "msdos" ]]; then
    echo -e "${YELLOW}[CẢNH BÁO] Bộ cài đang chạy trên phân vùng định dạng $FS_TYPE (NTFS/FAT) của Windows.${NC}"
    echo -e "${YELLOW}Biên dịch driver, cài đặt Wine hoặc nâng cấp hệ thống trực tiếp trên phân vùng NTFS rất dễ gặp lỗi mất kết nối (Transport endpoint is not connected) hoặc lỗi phân quyền Linux.${NC}"
    echo -e "${BLUE}Khuyến nghị sao chép thư mục cài đặt vào phân vùng Linux nội bộ (thư mục Home) để cài đặt ổn định.${NC}"
    read -p "Bạn có muốn tự động copy bộ cài này sang ~/nitro5-setup và chạy lại từ đó không? (Y/n): " copy_choice
    copy_choice=${copy_choice:-Y}
    if [[ "$copy_choice" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}[ACTION] Đang sao chép thư mục cài đặt sang ~/nitro5-setup...${NC}"
        mkdir -p ~/nitro5-setup
        if command -v rsync &>/dev/null; then
            rsync -a --exclude='.git' ./ ~/nitro5-setup/
        else
            cp -r ./ ~/nitro5-setup/
        fi
        echo -e "${GREEN}[OK] Sao chép hoàn tất!${NC}"
        echo -e "${CYAN}Vui lòng chạy lệnh sau để tiếp tục thiết lập an toàn:${NC}"
        echo -e "${BLUE}cd ~/nitro5-setup && bash install.sh${NC}"
        exit 0
    fi
fi

# 2. Kiểm tra Dòng máy (Acer Nitro 5 AN515-58)
PRODUCT_NAME=$(cat /sys/class/dmi/id/product_name 2>/dev/null | xargs)
if [[ "$PRODUCT_NAME" != *"AN515-58"* ]]; then
    echo -e "${RED}[CẢNH BÁO] Hệ thống phát hiện bạn không chạy trên Acer Nitro 5 AN515-58 (Phần cứng: '$PRODUCT_NAME').${NC}"
    echo -e "${YELLOW}Một số cấu hình chuyên sâu (như điều khiển quạt NitroSense, TLP tối ưu phần cứng) có thể gây lỗi hoặc không hoạt động.${NC}"
    read -p "Bạn có muốn bỏ qua cảnh báo và tiếp tục chạy ứng dụng thử nghiệm không? (y/N): " choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Đã hủy bỏ thiết lập.${NC}"
        exit 0
    fi
    echo -e "${YELLOW}[BYPASS] Tiếp tục thử nghiệm trên thiết bị: $PRODUCT_NAME${NC}"
else
    echo -e "${GREEN}[OK] Phát hiện dòng máy tương thích: Acer Nitro 5 AN515-58${NC}"
fi

# 2b. Hien thi thong tin phan cung truoc khi chay
echo -e "${CYAN}[INFO] Thong tin phan cung:${NC}"
CPU_NAME=$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d':' -f2 | xargs || echo 'Khong ro')
RAM_TOTAL=$(free -h | awk '/^Mem:/{print $2}' 2>/dev/null || echo '?')
GPU_NAME=$(lspci 2>/dev/null | grep -i 'vga\|3d\|display' | head -3 | sed 's/.*: //' | head -1 || echo 'Khong ro')
KERNEL_VER=$(uname -r)
echo -e "  CPU    : ${GREEN}${CPU_NAME}${NC}"
echo -e "  RAM    : ${GREEN}${RAM_TOTAL}B${NC}"
echo -e "  GPU    : ${GREEN}${GPU_NAME}${NC}"
echo -e "  Kernel : ${GREEN}${KERNEL_VER}${NC}"
echo -e "  DE     : ${GREEN}${DETECTED_DE}${NC}"
echo

# 2c. Kiem tra Python 3.10+
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo '0.0')
PY_MAJOR=$(echo $PY_VERSION | cut -d'.' -f1)
PY_MINOR=$(echo $PY_VERSION | cut -d'.' -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo -e "${RED}[LOI] Python ${PY_VERSION} khong du yeu cau. Can Python 3.10+ (Fedora 36+).${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Python ${PY_VERSION} - Du yeu cau (>= 3.10)${NC}"

# 3. Yeu cau quyen Sudo mot lan
echo -e "${BLUE}[SUDO] Vui lòng nhập mật khẩu root để cấp quyền thực hiện các thiết lập hệ thống:${NC}"
if ! sudo -v; then
    echo -e "${RED}[LỖI] Cấp quyền sudo thất bại!${NC}"
    exit 1
fi

# Tạo tiến trình ngầm giữ phiên sudo (sudo timestamp keep-alive)
# Cứ mỗi 60 giây chạy 'sudo -v', tự động thoát khi tiến trình cha ($$) kết thúc
(
    while true; do
        sudo -n true
        sleep 60
        kill -0 "$$" || exit
    done 2>/dev/null
) &
SUDO_KEEP_ALIVE_PID=$!

# Đảm bảo dọn dẹp tiến trình ngầm khi thoát
trap 'kill $SUDO_KEEP_ALIVE_PID 2>/dev/null' EXIT SIGINT SIGTERM

# 4. Cài đặt các gói Dependency qua dnf5 hoặc dnf fallback
# Tự động nhận diện dnf5 hoặc dnf truyền thống
if command -v dnf5 &>/dev/null; then
    DNF_CMD="dnf5"
else
    DNF_CMD="dnf"
fi

echo -e "${BLUE}[$DNF_CMD] Dang kiem tra va cai dat cac thu vien Python GTK4 va Libadwaita...${NC}"
if ! sudo $DNF_CMD install -y python3-pip python3-gobject gtk4 libadwaita; then
    echo -e "${YELLOW}[CANH BAO] Khong the cai gop nhom. Thu cai rieng le...${NC}"
    sudo $DNF_CMD install -y python3-gobject-base 2>/dev/null || sudo $DNF_CMD install -y python3-pip || true
    sudo $DNF_CMD install -y python3-gobject || true
    sudo $DNF_CMD install -y gtk4 || true
    sudo $DNF_CMD install -y libadwaita || true
    
    python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" &>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}[LOI] Thu vien PyGObject/GTK4 khong the nap. Kiem tra ket noi mang!${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}[OK] Da cai dat day du cac thu vien GUI.${NC}"

# 4b. Kiểm tra phiên bản Libadwaita (yêu cầu >= 1.4 cho các widget mới)
ADW_VER=$(python3 -c "import gi; gi.require_version('Adw', '1'); from gi.repository import Adw; print(Adw.VERSION_S)" 2>/dev/null || echo "0.0")
ADW_MAJOR=$(echo $ADW_VER | cut -d'.' -f1)
ADW_MINOR=$(echo $ADW_VER | cut -d'.' -f2)
if [ "$ADW_MAJOR" -lt 1 ] || ([ "$ADW_MAJOR" -eq 1 ] && [ "$ADW_MINOR" -lt 4 ]); then
    echo -e "${YELLOW}[CẢNH BÁO] Phiên bản Libadwaita hiện tại là $ADW_VER. Ứng dụng yêu cầu Libadwaita >= 1.4 để kích hoạt các widget native cao cấp (như AlertDialog, OverlaySplitView). Một số thành phần có thể tự động hạ cấp giao diện hoặc không hiển thị tối ưu.${NC}"
else
    echo -e "${GREEN}[OK] Phiên bản Libadwaita: $ADW_VER (Đủ điều kiện >= 1.4)${NC}"
fi

# 5. Khởi chạy GUI Python
echo -e "${GREEN}[LAUNCH] Đang khởi chạy ứng dụng GUI...${NC}"
python3 main.py

exit 0
