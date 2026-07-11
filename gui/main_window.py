# -*- coding: utf-8 -*-
import os
import json
import shutil
import gi
try:
    gi.require_version('Vte', '3.91')
    from gi.repository import Vte
    HAS_VTE = True
except (ValueError, ImportError):
    try:
        gi.require_version('Vte', '2.91')
        from gi.repository import Vte
        HAS_VTE = True
    except (ValueError, ImportError):
        HAS_VTE = False
import html
import threading

try:
    import keyring
except ImportError:
    class DummyKeyring:
        def __init__(self):
            self.passwords = {}
        def set_password(self, service, username, password):
            self.passwords[(service, username)] = password
        def get_password(self, service, username):
            return self.passwords.get((service, username))
        def delete_password(self, service, username):
            self.passwords.pop((service, username), None)
    keyring = DummyKeyring()
from gi.repository import Gtk, Gdk, GLib, Gio, GObject
from core.logger import global_logger
from core.runner import Runner
from core.checker import check_all
from modules import STAGES
from modules.base import Command

# Tải libadwaita nếu có
try:
    from gi.repository import Adw
    HAS_ADW = True
except ImportError:
    HAS_ADW = False

# Nạp CSS định dạng các badge và terminal view
def apply_css():
    css_provider = Gtk.CssProvider()
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        css_provider.load_from_path(css_path)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
    else:
        print(f"Warning: CSS file not found at {css_path}")

class MainWindow:
    def __init__(self, app, has_adw=False):
        self.app = app
        self.has_adw = has_adw
        self.runner = Runner()
        self.runner.run_interactive_cb = self.run_interactive
        self._sudo_keep_alive_event = threading.Event()
        
        # Load preset cấu hình
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        self.config_data = self.load_config()

        # Tạo Window
        if self.has_adw:
            self.window = Adw.ApplicationWindow(application=app)
        else:
            self.window = Gtk.ApplicationWindow(application=app)
            
        self.window.set_title("Acer Nitro 5 Setup Utility · Fedora Workstation")
        self.window.set_default_size(960, 680)
        
        apply_css()

        # Thiết lập logger callback để in trực tiếp lên GUI
        global_logger.set_gui_callback(self.append_log_to_gui)

        # Trạng thái hiện tại
        self.current_stage_key = "stage1"
        self.stage_keys = list(STAGES.keys())
        self.checkbox_widgets = {} # Lưu widget để đọc trạng thái check
        self._scroll_mark = None  # Mark tái sử dụng để scroll log — tránh memory leak

        # Biến instance cho trang Trạng thái module
        self._failed_modules = []
        self._mod_status_card_refs = {}
        self._dependency_cache = {}
        self._total_module_count = 0

        # Xây dựng bố cục giao diện
        self.build_ui()
        
        # Thiết lập phím tắt
        self.setup_shortcuts()
        
        # Load danh sách checkbox cho stage đầu tiên
        self.load_stage(self.current_stage_key)
        
        # Hỏi mật khẩu sudo sau khi giao diện đã render xong
        GLib.idle_add(self.ask_sudo_password)
        
        # Kiểm tra Secure Boot lúc khởi chạy
        self.check_secure_boot_on_startup()

    def present(self):
        """Hiển thị cửa sổ ứng dụng."""
        self.window.present()

    def setup_shortcuts(self):
        """Thiết lập các phím tắt cho ứng dụng."""
        shortcut_controller = Gtk.ShortcutController()
        
        # Ctrl+Q -> Thoát
        shortcut_quit = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>q"),
            Gtk.CallbackAction.new(lambda w, a: self.app.quit() or True)
        )
        shortcut_controller.add_shortcut(shortcut_quit)
        
        # Ctrl+R -> Chạy giai đoạn
        shortcut_run = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>r"),
            Gtk.CallbackAction.new(lambda w, a: self.on_run_stage_clicked(None) or True)
        )
        shortcut_controller.add_shortcut(shortcut_run)
        
        self.window.add_controller(shortcut_controller)

    def show_toast(self, message: str):
        if self.has_adw:
            toast = Adw.Toast.new(message)
            toast.set_timeout(3)
            self.toast_overlay.add_toast(toast)
        else:
            self.show_dialog("Thông báo", message)

    def ask_sudo_password(self):
        """Hiển thị Dialog nhập mật khẩu Sudo và xác thực."""
        # Entry nhập mật khẩu bảo mật
        entry = Gtk.Entry()
        entry.set_visibility(False) # Ẩn mật khẩu dạng password dots
        entry.set_placeholder_text("Mật khẩu sudo")
        entry.set_activates_default(True)

        lbl_error = Gtk.Label()
        lbl_error.add_css_class("checker-failed")

        def on_verify_result(success: bool, password: str, dlg):
            """Callback chạy trên GTK main thread sau khi verify xong."""
            if success:
                # Lưu mật khẩu an toàn trong Keyring và báo cho Runner
                keyring.set_password("nitro5-setup", "sudo", password)
                self.runner.set_sudo_password(password)

                # Bắt đầu thread giữ cache sudo sống sử dụng -S
                def keep_sudo_alive():
                    import subprocess
                    while not self._sudo_keep_alive_event.is_set():
                        self._sudo_keep_alive_event.wait(50)
                        if self._sudo_keep_alive_event.is_set():
                            break
                        pwd = keyring.get_password("nitro5-setup", "sudo") or ""
                        if not pwd:
                            break
                        try:
                            proc = subprocess.Popen(
                                "sudo -S -v",
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            proc.communicate(input=f"{pwd}\n", timeout=10)
                        except Exception:
                            pass
                
                threading.Thread(target=keep_sudo_alive, daemon=True).start()
                
                if self.has_adw:
                    dlg.close()
                else:
                    dlg.destroy()
                global_logger.log("Xác thực Sudo thành công và giữ cache hoạt động.", "ok")
            else:
                dlg.set_sensitive(True)
                lbl_error.set_text("Mật khẩu không đúng! Vui lòng thử lại.")
            return False

        def do_verify(password, dlg):
            lbl_error.set_markup("<span color='#3498db'>Đang xác thực...</span>")
            dlg.set_sensitive(False)
            
            import subprocess
            def verify_in_thread():
                try:
                    # Dùng sudo -S -v để tạo cache sudo ban đầu
                    proc = subprocess.Popen(
                        "sudo -S -v",
                        shell=True,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    proc.communicate(input=f"{password}\n", timeout=5)
                    success = proc.returncode == 0
                except Exception:
                    success = False
                GLib.idle_add(on_verify_result, success, password, dlg)

            import threading as _threading
            _threading.Thread(target=verify_in_thread, daemon=True).start()

        if self.has_adw:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            box.append(entry)
            box.append(lbl_error)

            dialog = Adw.AlertDialog(
                heading="Xác thực quyền hệ thống (Sudo)",
                body="Ứng dụng cần quyền quản trị để cài đặt driver và tối ưu hệ thống.\nVui lòng nhập mật khẩu sudo của bạn:"
            )
            dialog.set_extra_child(box)
            dialog.add_response("cancel", "Thoát")
            dialog.add_response("ok", "Xác nhận")
            dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("ok")

            def on_adw_response(dlg, response_id):
                if response_id == "ok":
                    do_verify(entry.get_text(), dlg)
                else:
                    dlg.close()
                    self.app.quit()

            dialog.connect("response", on_adw_response)
            dialog.present(self.window)
        else:
            # Fallback cho Gtk.Dialog truyền thống
            dialog = Gtk.Dialog(title="Xác thực quyền hệ thống (Sudo)")
            dialog.set_transient_for(self.window)
            dialog.set_modal(True)
            dialog.set_default_size(360, 180)
            
            content = dialog.get_content_area()
            content.set_margin_top(15)
            content.set_margin_bottom(15)
            content.set_margin_start(15)
            content.set_margin_end(15)
            content.set_spacing(10)

            lbl = Gtk.Label(label="Ứng dụng cần quyền quản trị để cài đặt driver và tối ưu hệ thống.\nVui lòng nhập mật khẩu sudo của bạn:")
            lbl.set_wrap(True)
            content.append(lbl)
            content.append(entry)
            content.append(lbl_error)

            dialog.add_button("Thoát", Gtk.ResponseType.CANCEL)
            dialog.add_button("Xác nhận", Gtk.ResponseType.OK)
            dialog.set_default_response(Gtk.ResponseType.OK)

            def on_gtk_response(dlg, response_id):
                if response_id == Gtk.ResponseType.OK:
                    do_verify(entry.get_text(), dlg)
                else:
                    dlg.destroy()
                    self.app.quit()

            dialog.connect("response", on_gtk_response)
            dialog.present()
        return False

    def cleanup(self):
        """Dọn dẹp tài nguyên và các thread ngầm khi tắt ứng dụng."""
        if hasattr(self, "_sudo_keep_alive_event"):
            self._sudo_keep_alive_event.set()
        try:
            keyring.delete_password("nitro5-setup", "sudo")
        except Exception:
            pass

    def load_config(self) -> dict:
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            # FIX: Thong bao nguoi dung khi config bi corrupt thay vi silent fail
            print(f"Loi load config.json: {e}")
            GLib.idle_add(
                self.show_dialog,
                "Canh bao cau hinh",
                f"File config.json bi loi hoac khong doc duoc:\n{e}\n\nHe thong se su dung cau hinh mac dinh."
            )
        return {}

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            global_logger.log(f"Không thể lưu config.json: {str(e)}", "warning")

    def build_ui(self):
        # HeaderBar / Toolbar trên cùng
        if self.has_adw:
            header = Adw.HeaderBar()
        else:
            header = Gtk.HeaderBar()
            self.window.set_titlebar(header)

        # Thêm các nút chức năng trên HeaderBar
        btn_open_log = Gtk.Button(label="Mở thư mục log")
        btn_open_log.connect("clicked", self.on_open_log_dir)
        header.pack_start(btn_open_log)

        btn_export_log = Gtk.Button(label="Xuất file log")
        btn_export_log.connect("clicked", self.on_export_log)
        header.pack_end(btn_export_log)

        # Container chứa Toast
        if self.has_adw:
            self.toast_overlay = Adw.ToastOverlay()
            self.toast_overlay.set_vexpand(True)
            self.toast_overlay.set_hexpand(True)

        # Thiết kế responsive với Adw.OverlaySplitView
        if self.has_adw:
            split_view = Adw.OverlaySplitView()
            split_view.set_show_sidebar(True)
            split_view.set_sidebar_position(Gtk.PackType.START)
            split_view.set_min_sidebar_width(260)
            split_view.set_max_sidebar_width(300)
            
            # Nút toggle sidebar trên HeaderBar
            btn_sidebar = Gtk.ToggleButton()
            btn_sidebar.set_icon_name("sidebar-show-symbolic")
            btn_sidebar.set_tooltip_text("Ẩn/Hiện danh mục")
            btn_sidebar.set_active(True)
            btn_sidebar.connect("toggled", lambda b: split_view.set_show_sidebar(b.get_active()))
            header.pack_start(btn_sidebar)
            
            self.toast_overlay.set_child(split_view)

            # Với Adw.ApplicationWindow, chúng ta không thể gọi set_titlebar().
            # Thay vào đó, đặt HeaderBar và ToastOverlay/SplitView vào trong một Box dọc làm root child.
            main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            main_container.append(header)
            main_container.append(self.toast_overlay)
            self.window.set_content(main_container)
        else:
            main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            self.window.set_child(main_box)

        # --- SIDEBAR TRÁI ---
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sidebar_box.set_size_request(240, -1)
        sidebar_box.set_margin_start(10)
        sidebar_box.set_margin_end(10)
        sidebar_box.set_margin_top(15)
        sidebar_box.set_margin_bottom(15)

        # Header Giai đoạn
        lbl_giai_doan = Gtk.Label(label="GIAI ĐOẠN")
        lbl_giai_doan.add_css_class("sidebar-header")
        lbl_giai_doan.set_halign(Gtk.Align.START)
        sidebar_box.append(lbl_giai_doan)

        # ListBox các giai đoạn
        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_list.connect("row-selected", self.on_sidebar_row_selected)
        sidebar_box.append(self.sidebar_list)

        # Nạp các Giai đoạn vào ListBox
        self.sidebar_rows = {}
        for key, value in STAGES.items():
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row_box.set_margin_start(10)
            row_box.set_margin_end(10)
            row_box.set_margin_top(8)
            row_box.set_margin_bottom(8)
            
            lbl_name = Gtk.Label(label=value["name"])
            lbl_name.set_halign(Gtk.Align.START)
            row_box.append(lbl_name)
            
            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            self.sidebar_list.append(row)
            self.sidebar_rows[row] = key

        # Dải phân cách
        sidebar_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Header Kết quả
        lbl_ket_qua = Gtk.Label(label="KẾT QUẢ")
        lbl_ket_qua.add_css_class("sidebar-header")
        lbl_ket_qua.set_halign(Gtk.Align.START)
        sidebar_box.append(lbl_ket_qua)

        # ListBox kết quả
        self.sidebar_results_list = Gtk.ListBox()
        self.sidebar_results_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_results_list.connect("row-selected", self.on_sidebar_row_selected)
        sidebar_box.append(self.sidebar_results_list)

        # Hàng "Kiểm tra hệ thống"
        row_check_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_check_box.set_margin_start(10)
        row_check_box.set_margin_end(10)
        row_check_box.set_margin_top(8)
        row_check_box.set_margin_bottom(8)
        row_check_box.append(Gtk.Label(label="Kiểm tra hệ thống"))
        self.row_check = Gtk.ListBoxRow()
        self.row_check.set_child(row_check_box)
        self.sidebar_results_list.append(self.row_check)
        self.sidebar_rows[self.row_check] = "system_check"

        # Hàng "Trạng thái module"
        row_mod_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_mod_box.set_margin_start(10)
        row_mod_box.set_margin_end(10)
        row_mod_box.set_margin_top(8)
        row_mod_box.set_margin_bottom(8)
        row_mod_box.append(Gtk.Label(label="Trạng thái module"))
        self.row_mod_status = Gtk.ListBoxRow()
        self.row_mod_status.set_child(row_mod_box)
        self.sidebar_results_list.append(self.row_mod_status)
        self.sidebar_rows[self.row_mod_status] = "module_status"

        # Hàng "Xem file log"
        row_view_log_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_view_log_box.set_margin_start(10)
        row_view_log_box.set_margin_end(10)
        row_view_log_box.set_margin_top(8)
        row_view_log_box.set_margin_bottom(8)
        row_view_log_box.append(Gtk.Label(label="Xem log"))
        self.row_view_log = Gtk.ListBoxRow()
        self.row_view_log.set_child(row_view_log_box)
        self.sidebar_results_list.append(self.row_view_log)
        self.sidebar_rows[self.row_view_log] = "view_log"

        # Bọc sidebar trong ScrolledWindow
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_child(sidebar_box)

        if self.has_adw:
            split_view.set_sidebar(sidebar_scroll)
        else:
            main_box.append(sidebar_scroll)
            main_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        # --- PANEL PHẢI (CONTENT AREA) ---
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content_box.set_hexpand(True)
        self.content_box.set_vexpand(True)
        
        if self.has_adw:
            split_view.set_content(self.content_box)
        else:
            main_box.append(self.content_box)

        # Banner cảnh báo
        self.banner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.banner_box.add_css_class("module-card-warning")
        self.banner_box.set_margin_start(20)
        self.banner_box.set_margin_end(20)
        self.banner_box.set_margin_top(10)
        self.banner_box.set_visible(False)
        
        lbl_banner = Gtk.Label()
        lbl_banner.set_markup("<b>⚠️ Cảnh báo Secure Boot:</b> Secure Boot đang bật. Nếu bạn cài đặt Driver độc quyền NVIDIA, vui lòng đăng ký khóa MOK khi khởi động lại máy để driver có thể hoạt động.")
        lbl_banner.set_wrap(True)
        lbl_banner.set_hexpand(True)
        lbl_banner.set_halign(Gtk.Align.START)
        self.banner_box.append(lbl_banner)
        
        btn_banner_info = Gtk.Button(label="Hướng dẫn MOK")
        btn_banner_info.connect("clicked", lambda b: self.show_secure_boot_dialog())
        self.banner_box.append(btn_banner_info)
        
        self.content_box.append(self.banner_box)

        # Khung chứa Stack động
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        self.content_box.append(self.stack)

        # 1. Trang Thiết lập chung (sử dụng lại cho 6 giai đoạn)
        self.setup_page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.setup_page_box.set_margin_start(20)
        self.setup_page_box.set_margin_end(20)
        self.setup_page_box.set_margin_top(20)
        self.setup_page_box.set_margin_bottom(10)
        
        # Tiêu đề & mô tả giai đoạn
        self.lbl_stage_title = Gtk.Label()
        self.lbl_stage_title.add_css_class("main-header")
        self.lbl_stage_title.set_halign(Gtk.Align.START)
        self.setup_page_box.append(self.lbl_stage_title)

        self.lbl_stage_desc = Gtk.Label()
        self.lbl_stage_desc.set_halign(Gtk.Align.START)
        self.lbl_stage_desc.set_wrap(True)
        self.setup_page_box.append(self.lbl_stage_desc)

        # ListBox chứa danh sách Checkbox items
        self.items_list_box = Gtk.ListBox()
        self.items_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        
        # Bọc ListBox trong ScrolledWindow để cuộn nếu quá dài
        scroll_items = Gtk.ScrolledWindow()
        scroll_items.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_items.set_min_content_height(180)
        scroll_items.set_max_content_height(250)
        scroll_items.set_child(self.items_list_box)
        self.setup_page_box.append(scroll_items)

        # Phần Log trực tiếp
        lbl_log_title = Gtk.Label(label="LOG TRỰC TIẾP")
        lbl_log_title.set_halign(Gtk.Align.START)
        lbl_log_title.set_margin_top(10)
        self.setup_page_box.append(lbl_log_title)

        self.log_stack = Gtk.Stack()
        self.log_stack.set_vexpand(True)

        self.log_scroll = Gtk.ScrolledWindow()
        self.log_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.log_scroll.set_min_content_height(160)
        self.log_scroll.add_css_class("terminal-box")

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_view.add_css_class("terminal-text")
        self.log_scroll.set_child(self.log_view)
        self.log_stack.add_named(self.log_scroll, "text")

        if HAS_VTE:
            self.terminal = Vte.Terminal()
            self.terminal.set_size_request(-1, 160)
            term_scroll = Gtk.ScrolledWindow()
            term_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            term_scroll.set_min_content_height(160)
            term_scroll.set_child(self.terminal)
            self.log_stack.add_named(term_scroll, "vte")
        else:
            self.terminal = None
            lbl_no_vte = Gtk.Label(label="VTE not available. Interactive mode runs in background.")
            self.log_stack.add_named(lbl_no_vte, "vte")

        self.setup_page_box.append(self.log_stack)

        # Tạo Text Buffer tags cho màu sắc terminal log
        self.log_buffer = self.log_view.get_buffer()
        self.log_buffer.create_tag("ok", foreground="#2ecc71")
        self.log_buffer.create_tag("running", foreground="#3498db")
        self.log_buffer.create_tag("warning", foreground="#f1c40f")
        self.log_buffer.create_tag("error", foreground="#ef2929", weight=700) # Đậm cho lỗi
        self.log_buffer.create_tag("stdout", foreground="#d3d7cf")
        self.log_buffer.create_tag("info", foreground="#888a85")

        # Bọc trang setup trong Adw.Clamp
        if self.has_adw:
            clamp_setup = Adw.Clamp()
            clamp_setup.set_maximum_size(860)
            clamp_setup.set_child(self.setup_page_box)
            self.stack.add_named(clamp_setup, "setup_stage")
        else:
            self.stack.add_named(self.setup_page_box, "setup_stage")

        # 2. Trang Kiểm tra hệ thống
        self.check_page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.check_page_box.set_margin_start(20)
        self.check_page_box.set_margin_end(20)
        self.check_page_box.set_margin_top(20)
        self.check_page_box.set_margin_bottom(10)

        lbl_check_title = Gtk.Label(label="Kết quả kiểm tra cấu hình")
        lbl_check_title.add_css_class("main-header")
        lbl_check_title.set_halign(Gtk.Align.START)
        self.check_page_box.append(lbl_check_title)

        lbl_check_desc = Gtk.Label(label="Hệ thống tự động quét và phân tích trạng thái hoạt động của driver, nhiệt độ và các daemon tối ưu.")
        lbl_check_desc.set_halign(Gtk.Align.START)
        self.check_page_box.append(lbl_check_desc)

        # Nút quét lại
        self.btn_refresh_check = Gtk.Button(label="Quét & Kiểm tra lại")
        self.btn_refresh_check.set_halign(Gtk.Align.START)
        self.btn_refresh_check.connect("clicked", lambda x: self.run_system_check())
        self.check_page_box.append(self.btn_refresh_check)

        # Grid / Table kết quả
        self.check_grid = Gtk.Grid()
        self.check_grid.set_column_spacing(20)
        self.check_grid.set_row_spacing(10)
        self.check_grid.set_margin_top(10)

        scroll_grid = Gtk.ScrolledWindow()
        scroll_grid.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_grid.set_vexpand(True)
        scroll_grid.set_child(self.check_grid)
        self.check_page_box.append(scroll_grid)

        # Bọc trang check trong Adw.Clamp
        if self.has_adw:
            clamp_check = Adw.Clamp()
            clamp_check.set_maximum_size(860)
            clamp_check.set_child(self.check_page_box)
            self.stack.add_named(clamp_check, "system_check")
        else:
            self.stack.add_named(self.check_page_box, "system_check")

        # 2.5 Trang Trạng thái module
        self.mod_status_page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.mod_status_page_box.set_margin_start(20)
        self.mod_status_page_box.set_margin_end(20)
        self.mod_status_page_box.set_margin_top(20)
        self.mod_status_page_box.set_margin_bottom(10)

        lbl_mod_status_title = Gtk.Label(label="📋 Trạng thái cài đặt toàn bộ module")
        lbl_mod_status_title.add_css_class("main-header")
        lbl_mod_status_title.set_halign(Gtk.Align.START)
        self.mod_status_page_box.append(lbl_mod_status_title)

        lbl_mod_status_desc = Gtk.Label(label="Kiểm tra xem từng module đã được cấu hình hoặc tối ưu thành công trên hệ thống hay chưa.")
        lbl_mod_status_desc.set_halign(Gtk.Align.START)
        self.mod_status_page_box.append(lbl_mod_status_desc)

        # Vùng chứa nút bấm kiểm tra và kết quả tóm tắt
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        ctrl_box.set_valign(Gtk.Align.CENTER)
        
        self.btn_check_modules = Gtk.Button(label="🔍 Kiểm tra tất cả")
        self.btn_check_modules.add_css_class("suggested-action")
        self.btn_check_modules.connect("clicked", self.run_module_validate_check)
        ctrl_box.append(self.btn_check_modules)

        self.lbl_mod_check_summary = Gtk.Label(label="")
        self.lbl_mod_check_summary.set_halign(Gtk.Align.START)
        self.lbl_mod_check_summary.add_css_class("check-summary-label")
        ctrl_box.append(self.lbl_mod_check_summary)
        
        self.mod_status_page_box.append(ctrl_box)

        # Hộp chứa danh sách card các module
        self.mod_status_cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        scroll_cards = Gtk.ScrolledWindow()
        scroll_cards.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_cards.set_vexpand(True)
        scroll_cards.set_child(self.mod_status_cards_box)
        self.mod_status_page_box.append(scroll_cards)

        # Nút "Cài & Tối ưu ngay" cho các module chưa cài
        self.btn_fix_failed = Gtk.Button(label="🚀 Cài & Tối ưu ngay")
        self.btn_fix_failed.add_css_class("btn-fix-all")
        self.btn_fix_failed.set_halign(Gtk.Align.START)
        self.btn_fix_failed.set_visible(False)
        self.btn_fix_failed.connect("clicked", self.on_fix_failed_modules_clicked)
        self.mod_status_page_box.append(self.btn_fix_failed)

        # Đăng ký vào Gtk.Stack
        if self.has_adw:
            clamp_mod = Adw.Clamp()
            clamp_mod.set_maximum_size(860)
            clamp_mod.set_child(self.mod_status_page_box)
            self.stack.add_named(clamp_mod, "module_status")
        else:
            self.stack.add_named(self.mod_status_page_box, "module_status")

        # 3. Trang Xem file log
        self.view_log_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.view_log_page.set_margin_start(20)
        self.view_log_page.set_margin_end(20)
        self.view_log_page.set_margin_top(20)
        self.view_log_page.set_margin_bottom(10)

        lbl_view_log_title = Gtk.Label(label="Nội dung file log hoàn chỉnh")
        lbl_view_log_title.add_css_class("main-header")
        lbl_view_log_title.set_halign(Gtk.Align.START)
        self.view_log_page.append(lbl_view_log_title)

        scroll_view_log = Gtk.ScrolledWindow()
        scroll_view_log.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll_view_log.set_vexpand(True)
        scroll_view_log.add_css_class("terminal-box")

        self.full_log_text = Gtk.TextView()
        self.full_log_text.set_editable(False)
        self.full_log_text.set_wrap_mode(Gtk.WrapMode.NONE)
        self.full_log_text.add_css_class("terminal-text")
        scroll_view_log.set_child(self.full_log_text)
        self.view_log_page.append(scroll_view_log)

        self.stack.add_named(self.view_log_page, "view_log")

        # --- PROGRESS BAR AREA ---
        self.progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.progress_box.set_margin_start(20)
        self.progress_box.set_margin_end(20)
        self.progress_box.set_margin_top(10)
        self.content_box.append(self.progress_box)

        # ProgressBar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_box.append(self.progress_bar)

        # Label tiến trình
        self.lbl_progress = Gtk.Label(label="Sẵn sàng thiết lập")
        self.lbl_progress.set_halign(Gtk.Align.START)
        self.lbl_progress.set_margin_bottom(10)
        self.progress_box.append(self.lbl_progress)

        # Dải phân cách trước footer
        self.content_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # --- FOOTER CONTROLS ---
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        footer_box.set_margin_start(20)
        footer_box.set_margin_end(20)
        footer_box.set_margin_top(12)
        footer_box.set_margin_bottom(12)
        self.content_box.append(footer_box)

        # Nút Dừng lại (Đỏ)
        self.btn_stop = Gtk.Button(label="Dừng lại")
        self.btn_stop.set_sensitive(False)
        self.btn_stop.connect("clicked", self.on_stop_clicked)
        if self.has_adw:
            self.btn_stop.add_css_class("destructive-action")
        footer_box.append(self.btn_stop)

        # Khung trống căn lề phải cho các nút khác
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        footer_box.append(spacer)

        # Nút Quay lại
        self.btn_back = Gtk.Button(label=" Quay lại")
        self.btn_back.connect("clicked", self.on_back_clicked)
        footer_box.append(self.btn_back)

        # Nút Chạy giai đoạn này (Màu nhấn)
        self.btn_run_stage = Gtk.Button(label="Chạy giai đoạn này")
        self.btn_run_stage.connect("clicked", self.on_run_stage_clicked)
        if self.has_adw:
            self.btn_run_stage.add_css_class("suggested-action")
        footer_box.append(self.btn_run_stage)

        # Nút Cài đặt tất cả đã chọn
        self.btn_run_all = Gtk.Button(label="Cài đặt tất cả đã chọn")
        self.btn_run_all.connect("clicked", self.on_run_all_clicked)
        if self.has_adw:
            self.btn_run_all.add_css_class("suggested-action")
        footer_box.append(self.btn_run_all)

        # Nút Tiếp tục
        self.btn_next = Gtk.Button(label="Tiếp tục →")
        self.btn_next.connect("clicked", self.on_next_clicked)
        footer_box.append(self.btn_next)

    # --- ĐIỀU PHỐI SIDEBAR & CHUYỂN GIAI ĐOẠN ---
    def on_sidebar_row_selected(self, listbox, row):
        if not row:
            return
            
        # Bỏ chọn bên ListBox kia để tránh hiển thị nhiều dòng cùng chọn
        if listbox == self.sidebar_list:
            self.sidebar_results_list.select_row(None)
        else:
            self.sidebar_list.select_row(None)

        key = self.sidebar_rows.get(row)
        if not key:
            return

        if key == "system_check":
            self.stack.set_visible_child_name("system_check")
            self.progress_box.set_visible(False)
            self.btn_run_stage.set_visible(False)
            self.btn_run_all.set_visible(False)
            self.run_system_check()
        elif key == "module_status":
            self.stack.set_visible_child_name("module_status")
            self.progress_box.set_visible(False)
            self.btn_run_stage.set_visible(False)
            self.btn_run_all.set_visible(False)
            self.load_module_status_page()
        elif key == "view_log":
            self.stack.set_visible_child_name("view_log")
            self.progress_box.set_visible(False)
            self.btn_run_stage.set_visible(False)
            self.btn_run_all.set_visible(False)
            self.load_full_log_file()
        else:
            self.stack.set_visible_child_name("setup_stage")
            self.progress_box.set_visible(True)
            self.btn_run_stage.set_visible(True)
            self.btn_run_all.set_visible(True)
            self.current_stage_key = key
            self.load_stage(key)

    def is_dependency_satisfied(self, dep_id: str) -> bool:
        """Kiểm tra xem module phụ thuộc (dep_id) đã được chọn/cấu hình thành công chưa (sử dụng cache RAM)."""
        if dep_id in self._dependency_cache:
            return self._dependency_cache[dep_id]

        satisfied = False
        if dep_id in ("nvidia_driver_open", "nvidia_driver_proprietary"):
            dep_id = "nvidia_driver"

        # Duyệt config_data để tìm trạng thái chọn của dep_id
        for stage_key, stage_info in STAGES.items():
            for m_cls in stage_info["modules"]:
                if m_cls.id == dep_id:
                    satisfied = self.config_data.get(stage_key, {}).get(dep_id, True)
                    break
            if satisfied:
                break

        self._dependency_cache[dep_id] = satisfied
        return satisfied

    def load_stage(self, stage_key):
        """Cập nhật giao diện tương ứng với giai đoạn được chọn."""
        stage_info = STAGES[stage_key]
        self.lbl_stage_title.set_text(stage_info["name"])
        self.lbl_stage_desc.set_text(stage_info["description"])

        # Xóa các checkbox cũ
        while True:
            row = self.items_list_box.get_row_at_index(0)
            if not row:
                break
            self.items_list_box.remove(row)

        self.checkbox_widgets.clear()

        # Nạp danh sách Checkbox items của Giai đoạn
        for module_cls in stage_info["modules"]:
            module = module_cls()
            
            # Cấu trúc box cho mỗi dòng checkbox
            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            item_box.set_margin_start(10)
            item_box.set_margin_end(10)
            item_box.set_margin_top(6)
            item_box.set_margin_bottom(6)

            # Checkbox widget
            chk = Gtk.CheckButton()
            # Đọc trạng thái lưu trong config.json
            is_checked = self.config_data.get(stage_key, {}).get(module.id, True)
            chk.set_active(is_checked)
            # Sự kiện cập nhật config.json khi click
            chk.connect("toggled", self.on_checkbox_toggled, stage_key, module.id)
            item_box.append(chk)
            self.checkbox_widgets[module.id] = (chk, module_cls)

            # Nhãn thông tin (Tên + Mô tả)
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lbl_name = Gtk.Label(label=module.name)
            lbl_name.set_halign(Gtk.Align.START)
            lbl_name.set_markup(f"<b>{html.escape(module.name)}</b>")
            info_box.append(lbl_name)

            lbl_desc = Gtk.Label(label=module.description)
            lbl_desc.set_halign(Gtk.Align.START)
            lbl_desc.set_wrap(True)
            lbl_desc.set_max_width_chars(60)
            lbl_desc.add_css_class("dim-label")
            info_box.append(lbl_desc)

            # Kiểm tra phụ thuộc (Dependencies)
            deps_satisfied = True
            unsatisfied_deps = []
            if hasattr(module, "dependencies") and module.dependencies:
                for dep in module.dependencies:
                    if not self.is_dependency_satisfied(dep):
                        deps_satisfied = False
                        dep_name = dep
                        for sd in STAGES.values():
                            for mc in sd["modules"]:
                                if mc.id == dep:
                                    dep_name = mc.name
                                    break
                        unsatisfied_deps.append(dep_name)

            if not deps_satisfied:
                chk.set_active(False)
                chk.set_sensitive(False)
                chk.set_tooltip_text(f"Bị khóa do thiếu phụ thuộc: {', '.join(unsatisfied_deps)}")
                
                lbl_dep_warn = Gtk.Label()
                lbl_dep_warn.set_markup(f"<span foreground='#e74c3c'>⚠️ Cần cài trước: {', '.join(unsatisfied_deps)}</span>")
                lbl_dep_warn.set_halign(Gtk.Align.START)
                lbl_dep_warn.add_css_class("dim-label")
                lbl_dep_warn.set_margin_top(4)
                info_box.append(lbl_dep_warn)

            # Thêm DropDown chọn chế độ cho BrightnessFix
            if module.id == "brightness_fix" and deps_satisfied:
                combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                combo_box.set_margin_top(4)
                
                lbl_opt = Gtk.Label(label="Tham số:")
                lbl_opt.add_css_class("dim-label")
                combo_box.append(lbl_opt)
                
                strings = Gtk.StringList.new([
                    "native (Khuyên dùng)",
                    "vendor",
                    "video",
                    "Khôi phục mặc định (Undo)"
                ])
                combo_brightness = Gtk.DropDown(model=strings)
                
                saved_mode = self.config_data.get("stage2", {}).get("brightness_fix_mode", "native")
                mapping_rev = {"native": 0, "vendor": 1, "video": 2, "undo": 3}
                combo_brightness.set_selected(mapping_rev.get(saved_mode, 0))
                    
                combo_brightness.connect("notify::selected", self.on_brightness_mode_changed)
                combo_box.append(combo_brightness)
                info_box.append(combo_box)

            item_box.append(info_box)

            # Khoảng trống đẩy badge về góc phải
            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            item_box.append(spacer)

            # Badge màu sắc trạng thái yêu cầu
            badge_label = Gtk.Label(label=module.required_level.lower())
            badge_label.set_margin_end(10)
            if module.required_level == "Bắt buộc":
                badge_label.add_css_class("badge-required")
            elif module.required_level == "GPU":
                badge_label.add_css_class("badge-gpu")
            else:
                badge_label.add_css_class("badge-optional")
            item_box.append(badge_label)

            # Nút Reset nếu module hỗ trợ
            if module.can_reset():
                btn_reset = Gtk.Button(label="↩ Reset")
                btn_reset.set_margin_end(10)
                btn_reset.connect("clicked", self.on_reset_clicked, stage_key, module)
                item_box.append(btn_reset)

            row = Gtk.ListBoxRow()
            row.set_child(item_box)
            self.items_list_box.append(row)

        # Thêm slider giới hạn sạc pin cho Stage 5
        if stage_key == "stage5":
            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            item_box.set_margin_start(10)
            item_box.set_margin_end(10)
            item_box.set_margin_top(10)
            item_box.set_margin_bottom(10)

            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            lbl_name = Gtk.Label()
            lbl_name.set_markup("<b>🔋 Giới hạn sạc Pin (Battery Charge Limit)</b>")
            lbl_name.set_halign(Gtk.Align.START)
            info_box.append(lbl_name)

            lbl_desc = Gtk.Label(label="Giới hạn sạc để bảo vệ tuổi thọ pin (khuyên dùng 80% nếu cắm sạc liên tục).")
            lbl_desc.set_halign(Gtk.Align.START)
            lbl_desc.set_wrap(True)
            lbl_desc.set_max_width_chars(50)
            lbl_desc.add_css_class("dim-label")
            info_box.append(lbl_desc)
            item_box.append(info_box)

            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            item_box.append(spacer)

            control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            control_box.set_valign(Gtk.Align.CENTER)

            current_limit = 80
            for path in [
                "/sys/class/power_supply/BAT0/charge_control_limit_max",
                "/sys/class/power_supply/BAT1/charge_control_limit_max",
                "/sys/bus/wmi/devices/61B1D55A-284C-437B-9293-4B968B4268F9/battery_limit"
            ]:
                if os.path.exists(path):
                    try:
                        with open(path, "r") as f:
                            current_limit = int(f.read().strip())
                            break
                    except Exception:
                        pass

            lbl_val = Gtk.Label(label=f"{current_limit}%")
            lbl_val.set_width_chars(5)

            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 50.0, 100.0, 5.0)
            scale.set_value(float(current_limit))
            scale.set_draw_value(False)
            scale.set_size_request(120, -1)
            
            def on_scale_changed(slider):
                val = int(slider.get_value())
                lbl_val.set_text(f"{val}%")

            scale.connect("value-changed", on_scale_changed)
            control_box.append(scale)
            control_box.append(lbl_val)

            btn_apply = Gtk.Button(label="Áp dụng")
            btn_apply.add_css_class("suggested-action")
            
            def on_btn_apply_clicked(btn, slider):
                val = int(slider.get_value())
                cmd_str = (
                    f"for path in "
                    f"/sys/class/power_supply/BAT0/charge_control_limit_max "
                    f"/sys/class/power_supply/BAT1/charge_control_limit_max "
                    f"/sys/bus/wmi/devices/61B1D55A-284C-437B-9293-4B968B4268F9/battery_limit; do "
                    f"[ -f \"$path\" ] && echo {val} | tee \"$path\" >/dev/null; "
                    f"done || true"
                )
                
                cmd_obj = Command(cmd_str, f"Thiết lập giới hạn sạc pin về {val}%", is_sudo=True)
                
                self.show_toast(f"Đang thiết lập giới hạn sạc về {val}%...")
                
                def on_cmd_complete(is_success, sc, t):
                    if is_success:
                        GLib.idle_add(self.show_toast, f"Đã áp dụng giới hạn sạc {val}% thành công!")
                    else:
                        GLib.idle_add(self.show_toast, "Không thể thiết lập giới hạn sạc (Thử lại).")

                self.runner.run_commands([cmd_obj], on_complete=on_cmd_complete)

            btn_apply.connect("clicked", on_btn_apply_clicked, scale)
            control_box.append(btn_apply)
            item_box.append(control_box)

            row = Gtk.ListBoxRow()
            row.set_child(item_box)
            self.items_list_box.append(row)

        # Cập nhật trạng thái các nút phân trang
        idx = self.stage_keys.index(stage_key)
        self.btn_back.set_sensitive(idx > 0)
        self.btn_next.set_sensitive(idx < len(self.stage_keys) - 1)

    def on_checkbox_toggled(self, chk, stage_key, module_id):
        if stage_key not in self.config_data:
            self.config_data[stage_key] = {}
        self.config_data[stage_key][module_id] = chk.get_active()
        self.save_config()

    def on_reset_clicked(self, btn, stage_key, module):
        title = "Xác nhận Reset"
        message = f"Bạn có muốn gỡ bỏ / hoàn tác thiết lập của module '{module.name}' về mặc định không?"
        
        def do_reset():
            reset_cmds = module.get_reset_commands()
            if not reset_cmds:
                self.show_dialog("Không thể reset", "Module này không hỗ trợ hoàn tác tự động hoặc không có gì để reset.")
                return
            
            self.set_ui_sensitive(False)
            self.btn_stop.set_sensitive(True)
            self.progress_bar.set_fraction(0.0)
            self.lbl_progress.set_text(f"Đang hoàn tác {module.name}...")
            
            global_logger.log(f"=== BẮT ĐẦU HOÀN TÁC (RESET) MODULE: {module.name} ===", "info")
            
            self.runner.run_commands(
                commands=reset_cmds,
                on_progress=self.on_runner_progress,
                on_complete=lambda ok, succ, tot: GLib.idle_add(self.on_reset_complete, ok, succ, tot, stage_key, module)
            )

        if HAS_ADW:
            dialog = Adw.MessageDialog(
                transient_for=self.window,
                heading=title,
                body=message
            )
            dialog.add_response("cancel", "Hủy")
            dialog.add_response("ok", "Đồng ý")
            dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            
            def on_adw_response(dlg, response_id):
                dlg.close()
                if response_id == "ok":
                    do_reset()
            dialog.connect("response", on_adw_response)
            dialog.present()
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                modal=True,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=title
            )
            dialog.props.secondary_text = message
            def on_gtk_response(dlg, response_id):
                dlg.destroy()
                if response_id == Gtk.ResponseType.YES:
                    do_reset()
            dialog.connect("response", on_gtk_response)
            dialog.present()

    def on_reset_complete(self, is_success, success_count, total, stage_key, module):
        self.set_ui_sensitive(True)
        self.btn_stop.set_sensitive(False)
        self.progress_bar.set_fraction(1.0)
        
        if is_success:
            global_logger.log(f"[XONG] Đã hoàn tác thành công cấu hình module '{module.name}'", "ok")
            self.show_dialog("Hoàn tất", f"Đã khôi phục mặc định thành công cho '{module.name}'.")
        else:
            global_logger.log(f"[LỖI] Hoàn tác thất bại cho module '{module.name}'", "error")
            self.show_dialog("Lỗi", f"Hoàn tác thất bại cho '{module.name}' (Mã lỗi: {success_count}/{total} lệnh thành công).")
            
        self.load_stage(stage_key)

    def on_brightness_mode_changed(self, combo, pspec):
        selected_idx = combo.get_selected()
        mapping = {0: "native", 1: "vendor", 2: "video", 3: "undo"}
        active_id = mapping.get(selected_idx, "native")
        if "stage2" not in self.config_data:
            self.config_data["stage2"] = {}
        self.config_data["stage2"]["brightness_fix_mode"] = active_id
        self.save_config()

    # --- XỬ LÝ LOG REALTIME & TERMINAL VIEW ---
    def append_log_to_gui(self, log_line: str, tag: str):
        """Ham callback chay an toan tren Main Thread cua GTK."""
        iter_end = self.log_buffer.get_end_iter()
        self.log_buffer.insert_with_tags_by_name(iter_end, log_line, tag)
        
        # FIX: Tai su dung mot mark co dinh thay vi tao moi moi lan (tranh memory leak)
        iter_end2 = self.log_buffer.get_end_iter()
        if self._scroll_mark is None:
            self._scroll_mark = self.log_buffer.create_mark("scroll_end", iter_end2, False)
        else:
            self.log_buffer.move_mark(self._scroll_mark, iter_end2)
        self.log_view.scroll_to_mark(self._scroll_mark, 0.05, True, 0.0, 1.0)
        return False

    def run_interactive(self, cmd, event):
        GLib.idle_add(self._run_interactive_ui, cmd, event)

    def _run_interactive_ui(self, cmd, event):
        if not HAS_VTE or not self.terminal:
            global_logger.log(f"VTE không khả dụng. Chạy ngầm: {cmd.cmd}", "warning")
            import subprocess
            try:
                proc = subprocess.Popen(cmd.cmd, shell=True)
                proc.wait()
            except Exception as e:
                global_logger.log(f"Lỗi chạy lệnh: {e}", "error")
            event.set()
            return False

        self.log_stack.set_visible_child_name("vte")
        
        def on_child_exited(term, status):
            self.terminal.disconnect(handler_id)
            self.log_stack.set_visible_child_name("text")
            event.set()

        handler_id = self.terminal.connect("child-exited", on_child_exited)
        
        try:
            self.terminal.spawn_async(
                Vte.PtyFlags.DEFAULT,
                None,
                ["/bin/bash", "-c", cmd.cmd],
                None,
                GLib.SpawnFlags.DEFAULT,
                None, None,
                -1,
                None,
                None
            )
        except Exception as e:
            global_logger.log(f"Lỗi khởi động VTE: {str(e)}", "error")
            self.terminal.disconnect(handler_id)
            self.log_stack.set_visible_child_name("text")
            event.set()
            
        return False

    def filter_modules_async(self, selected_modules, is_all_stages, on_filtered_cb):
        """Lọc các module đã cài đặt bất đồng bộ trên một worker thread để tránh đơ GUI."""
        self.btn_run_stage.set_sensitive(False)
        self.btn_run_all.set_sensitive(False)
        self.progress_bar.set_fraction(0.0)
        self.lbl_progress.set_text("Đang kiểm tra trạng thái các mục trên hệ thống...")
        
        def run_filter():
            runnable_modules = []
            already_installed = []
            for m in selected_modules:
                try:
                    check_res = m.validate()
                    if check_res.success:
                        already_installed.append(m)
                    else:
                        runnable_modules.append(m)
                except Exception:
                    runnable_modules.append(m)
            
            GLib.idle_add(lambda: self.on_modules_filtered(runnable_modules, already_installed, is_all_stages, on_filtered_cb))
            
        threading.Thread(target=run_filter, daemon=True).start()

    def on_modules_filtered(self, runnable_modules, already_installed, is_all_stages, on_filtered_cb):
        self.btn_run_stage.set_sensitive(True)
        self.btn_run_all.set_sensitive(True)
        self.lbl_progress.set_text("Đã kiểm tra xong.")
        on_filtered_cb(runnable_modules, already_installed, is_all_stages)

    # --- THỰC THI SETUP GIAI ĐOẠN ---
    def on_run_stage_clicked(self, btn):
        # 1. Thu thập danh sách các module được tick chọn
        selected_modules = []
        for module_id, (chk, module_cls) in self.checkbox_widgets.items():
            if chk.get_active():
                selected_modules.append(module_cls())

        if not selected_modules:
            self.show_toast("Vui lòng chọn ít nhất một mục để cài đặt.")
            return

        def handle_filtered(runnable_modules, already_installed, is_all_stages):
            all_commands = []
            if not runnable_modules and already_installed:
                # Hỏi người dùng có muốn cài đè/cài lại không
                def on_reinstall_response(dlg, response_id):
                    if response_id == "yes" or response_id == Gtk.ResponseType.YES:
                        self.proceed_execution(selected_modules, all_commands, is_all_stages=False)
                    if self.has_adw:
                        dlg.close()
                    else:
                        dlg.destroy()
                
                title = "Xác nhận cài đặt lại"
                msg = "Tất cả các mục bạn chọn đều đã được cấu hình/cài đặt thành công trên hệ thống.\nBạn có muốn tiến hành cài đặt lại các mục này không?"
                if self.has_adw:
                    dlg = Adw.AlertDialog(heading=title, body=msg)
                    dlg.add_response("no", "Bỏ qua")
                    dlg.add_response("yes", "Cài đặt lại")
                    dlg.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)
                    dlg.connect("response", on_reinstall_response)
                    dlg.present(self.window)
                else:
                    dlg = Gtk.MessageDialog(
                        transient_for=self.window,
                        modal=True,
                        message_type=Gtk.MessageType.QUESTION,
                        buttons=Gtk.ButtonsType.YES_NO,
                        text=title
                    )
                    dlg.props.secondary_text = msg
                    dlg.connect("response", on_reinstall_response)
                    dlg.present()
                return
            
            # Nếu có module đã cài và một số chưa cài, in skip log
            for m in already_installed:
                global_logger.log(f"[BỎ QUA] {m.name} đã được thiết lập thành công trước đó.", "ok")
                
            self.proceed_execution(runnable_modules, all_commands, is_all_stages=False)

        self.filter_modules_async(selected_modules, is_all_stages=False, on_filtered_cb=handle_filtered)

    def on_run_all_clicked(self, btn):
        selected_modules = []
        for stage_key in self.stage_keys:
            stage_info = STAGES.get(stage_key)
            if not stage_info:
                continue
                
            for module_cls in stage_info["modules"]:
                module = module_cls()
                is_checked = self.config_data.get(stage_key, {}).get(module.id, True)
                if is_checked:
                    selected_modules.append(module)

        if not selected_modules:
            self.show_toast("Không tìm thấy mục nào được chọn để cài đặt ở tất cả các giai đoạn.")
            return

        def handle_filtered(runnable_modules, already_installed, is_all_stages):
            all_commands = []
            if not runnable_modules and already_installed:
                # Hỏi người dùng có muốn cài đè/cài lại không
                def on_reinstall_response(dlg, response_id):
                    if response_id == "yes" or response_id == Gtk.ResponseType.YES:
                        self.proceed_execution(selected_modules, all_commands, is_all_stages=True)
                    if self.has_adw:
                        dlg.close()
                    else:
                        dlg.destroy()
                
                title = "Xác nhận cài đặt lại"
                msg = "Tất cả các mục bạn chọn đều đã được cấu hình/cài đặt thành công trên hệ thống.\nBạn có muốn tiến hành cài đặt lại tất cả các mục này không?"
                if self.has_adw:
                    dlg = Adw.AlertDialog(heading=title, body=msg)
                    dlg.add_response("no", "Bỏ qua")
                    dlg.add_response("yes", "Cài đặt lại")
                    dlg.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)
                    dlg.connect("response", on_reinstall_response)
                    dlg.present(self.window)
                else:
                    dlg = Gtk.MessageDialog(
                        transient_for=self.window,
                        modal=True,
                        message_type=Gtk.MessageType.QUESTION,
                        buttons=Gtk.ButtonsType.YES_NO,
                        text=title
                    )
                    dlg.props.secondary_text = msg
                    dlg.connect("response", on_reinstall_response)
                    dlg.present()
                return

            for m in already_installed:
                global_logger.log(f"[BỎ QUA] {m.name} đã được thiết lập thành công trước đó.", "ok")

            self.proceed_execution(runnable_modules, all_commands, is_all_stages=True)

        self.filter_modules_async(selected_modules, is_all_stages=True, on_filtered_cb=handle_filtered)

    def proceed_execution(self, runnable_modules, all_commands, is_all_stages=False):
        # Thiết lập grubby động cho BrightnessFix
        for m in runnable_modules:
            if m.id == "brightness_fix":
                mode = self.config_data.get("stage2", {}).get("brightness_fix_mode", "native")
                remove_cmd = "grubby --update-kernel=ALL --remove-args='acpi_backlight=native acpi_backlight=vendor acpi_backlight=video acpi_backlight=none'"
                if mode == "undo":
                    m.commands = [
                        Command(remove_cmd, "Khôi phục cấu hình độ sáng mặc định", is_sudo=True)
                    ]
                else:
                    m.commands = [
                        Command(f"{remove_cmd} && grubby --update-kernel=ALL --args='acpi_backlight={mode}'", f"Thiết lập tham số độ sáng acpi_backlight={mode}", is_sudo=True)
                    ]

        self.start_execution(runnable_modules, all_commands, is_all_stages)

    def start_execution(self, selected_modules, all_commands, is_all_stages=False):
        # Thu thập toàn bộ command
        for m in selected_modules:
            all_commands.extend(m.commands)

        if not all_commands:
            self.show_dialog("Không có câu lệnh", "Không tìm thấy câu lệnh nào cần thực hiện.")
            return

        # Vô hiệu hóa giao diện khi đang chạy
        self.set_ui_sensitive(False)
        self.btn_stop.set_sensitive(True)

        # Xác định số stage có trong selected_modules
        represented_stages = set()
        for module in selected_modules:
            for s_key, s_info in STAGES.items():
                if any(m_cls.id == module.id for m_cls in s_info["modules"]):
                    represented_stages.add(s_key)
                    break

        is_multi_stage = is_all_stages or len(represented_stages) > 1

        if is_multi_stage:
            global_logger.log("=== BẮT ĐẦU CHẠY THIẾT LẬP HÀNG LOẠT (TỰ ĐỘNG SỬA LỖI / NHIỀU GIAI ĐOẠN) ===", "info")
        else:
            global_logger.log(f"=== BẮT ĐẦU CHẠY GIAI ĐOẠN: {STAGES[self.current_stage_key]['name']} ===", "info")

        # Khởi chạy ngầm thông qua Runner
        self.runner.run_commands(
            commands=all_commands,
            on_progress=self.on_runner_progress,
            on_complete=lambda ok, succ, tot: GLib.idle_add(self.on_runner_complete, ok, succ, tot, selected_modules, is_all_stages)
        )

    def on_runner_progress(self, step, total, desc):
        GLib.idle_add(self.update_progress_ui, step, total, desc)

    def update_progress_ui(self, step, total, desc):
        fraction = float(step) / float(total)
        self.progress_bar.set_fraction(fraction)
        self.lbl_progress.set_text(f"Đang cài đặt · Bước {step}/{total} · {desc} ({int(fraction*100)}%)")
        return False

    def on_runner_complete(self, is_success, success_count, total, selected_modules, is_all_stages=False):
        # Khôi phục trạng thái giao diện
        self._dependency_cache.clear()
        self.set_ui_sensitive(True)
        self.btn_stop.set_sensitive(False)
        
        self.progress_bar.set_fraction(1.0)

        # Xác định số stage có trong selected_modules
        represented_stages = set()
        for module in selected_modules:
            for s_key, s_info in STAGES.items():
                if any(m_cls.id == module.id for m_cls in s_info["modules"]):
                    represented_stages.add(s_key)
                    break

        is_multi_stage = is_all_stages or len(represented_stages) > 1
        
        if is_success:
            self.lbl_progress.set_text(f"Hoàn thành xuất sắc: {success_count}/{total} bước cài đặt.")
            reboot_ids = {"nvidia_driver", "acer_nitro_native_fix", "brightness_fix", "nvidia_suspend_fix", "damx"}
            needs_reboot = any(m.id in reboot_ids for m in selected_modules)
            
            if is_multi_stage:
                global_logger.log("=== THIẾT LẬP TOÀN BỘ CÁC MỤC THÀNH CÔNG ===", "ok")
                if needs_reboot:
                    self.show_reboot_dialog()
                else:
                    self.show_dialog("Hoàn tất", "Tất cả các mục được chọn đã được thiết lập thành công!")
            else:
                global_logger.log("=== THIẾT LẬP GIAI ĐOẠN THÀNH CÔNG ===", "ok")
                if needs_reboot:
                    self.show_reboot_dialog()
                else:
                    self.show_dialog("Hoàn tất", "Giai đoạn này đã được thiết lập thành công!")
        else:
            self.lbl_progress.set_text(f"Hoàn thành {success_count}/{total} bước. Một số mục thất bại.")
            if is_multi_stage:
                global_logger.log("=== THIẾT LẬP TOÀN BỘ CÓ LỖI XẢY RA ===", "error")
            else:
                global_logger.log("=== THIẾT LẬP GIAI ĐOẠN CÓ LỖI XẢY RA ===", "error")
            
            # Kiểm tra cụ thể xem NVIDIA Driver cài lỗi (do Secure Boot chưa tắt/MOK)
            has_nvidia = any(m.id == "nvidia_driver" for m in selected_modules)
            if has_nvidia:
                # Chạy validate nhanh để phát hiện Secure Boot MOK
                nvidia_mod = None
                for m in selected_modules:
                    if m.id == "nvidia_driver":
                        nvidia_mod = m
                        break
                if nvidia_mod:
                    check_res = nvidia_mod.validate()
                    if "SECURE BOOT MOK" in check_res.message:
                        self.show_secure_boot_dialog()
                        return

            self.show_dialog(
                "Có lỗi xảy ra", 
                "Quá trình cài đặt hoàn tất nhưng có lỗi xảy ra ở một số câu lệnh.\nVui lòng kiểm tra tab 'Xem log' để biết chi tiết."
            )
        return False

    def on_stop_clicked(self, btn):
        self.runner.cancel()
        self.btn_stop.set_sensitive(False)

    def set_ui_sensitive(self, sensitive: bool):
        self.sidebar_list.set_sensitive(sensitive)
        self.sidebar_results_list.set_sensitive(sensitive)
        self.items_list_box.set_sensitive(sensitive)
        self.btn_run_stage.set_sensitive(sensitive)
        self.btn_run_all.set_sensitive(sensitive)
        self.btn_back.set_sensitive(sensitive)
        self.btn_next.set_sensitive(sensitive)

    # --- ĐIỀU PHỐI FOOTER DỊCH CHUYỂN TRANG ---
    def on_back_clicked(self, btn):
        idx = self.stage_keys.index(self.current_stage_key)
        if idx > 0:
            next_key = self.stage_keys[idx - 1]
            # Kích hoạt dòng tương ứng trên sidebar
            row = self.sidebar_list.get_row_at_index(idx - 1)
            self.sidebar_list.select_row(row)

    def on_next_clicked(self, btn):
        idx = self.stage_keys.index(self.current_stage_key)
        if idx < len(self.stage_keys) - 1:
            next_key = self.stage_keys[idx + 1]
            row = self.sidebar_list.get_row_at_index(idx + 1)
            self.sidebar_list.select_row(row)

    # --- TRANG KIỂM TRA HỆ THỐNG (SYSTEM CHECKER) ---
    def run_system_check(self):
        self.btn_refresh_check.set_sensitive(False)
        self.btn_refresh_check.set_label("🔍 Đang quét hệ thống...")

        child = self.check_grid.get_first_child()
        while child:
            next_sibling = child.get_next_sibling()
            self.check_grid.remove(child)
            child = next_sibling

        lbl_status_msg = Gtk.Label()
        lbl_status_msg.set_markup("<i>Đang phân tích cấu hình phần cứng và driver... Vui lòng đợi trong giây lát.</i>")
        lbl_status_msg.set_halign(Gtk.Align.START)
        self.check_grid.attach(lbl_status_msg, 0, 0, 3, 1)

        def check_thread():
            report = check_all()
            GLib.idle_add(self._update_system_check_ui, report)

        import threading
        threading.Thread(target=check_thread, daemon=True).start()

    def _update_system_check_ui(self, report):
        self.btn_refresh_check.set_sensitive(True)
        self.btn_refresh_check.set_label("Quét & Kiểm tra lại")

        child = self.check_grid.get_first_child()
        while child:
            next_sibling = child.get_next_sibling()
            self.check_grid.remove(child)
            child = next_sibling

        # Thêm header bảng
        headers = ["Chức năng hệ thống", "Trạng thái", "Chi tiết cấu hình"]
        for col_idx, text in enumerate(headers):
            lbl = Gtk.Label()
            lbl.set_markup(f"<b>{text}</b>")
            lbl.set_halign(Gtk.Align.START)
            lbl.set_margin_bottom(10)
            self.check_grid.attach(lbl, col_idx, 0, 1, 1)

        for row_idx, r in enumerate(report, start=1):
            # Cột 1: Tên chức năng
            lbl_feat = Gtk.Label(label=r["feature"])
            lbl_feat.set_halign(Gtk.Align.START)
            self.check_grid.attach(lbl_feat, 0, row_idx, 1, 1)

            # Cột 2: Trạng thái
            lbl_status = Gtk.Label(label=r["status"])
            lbl_status.set_halign(Gtk.Align.START)
            if "✓ OK" in r["status"]:
                lbl_status.add_css_class("checker-ok")
            elif "✗ FAILED" in r["status"]:
                lbl_status.add_css_class("checker-failed")
            else:
                lbl_status.add_css_class("checker-warning")
            self.check_grid.attach(lbl_status, 1, row_idx, 1, 1)

            # Cột 3: Chi tiết cấu hình
            lbl_detail = Gtk.Label(label=r["detail"])
            lbl_detail.set_halign(Gtk.Align.START)
            lbl_detail.set_wrap(True)
            self.check_grid.attach(lbl_detail, 2, row_idx, 1, 1)
        return False

    # --- TRANG XEM FILE LOG HOÀN CHỈNH ---
    def load_full_log_file(self):
        try:
            if os.path.exists(global_logger.log_path):
                import collections
                with open(global_logger.log_path, "r", encoding="utf-8") as f:
                    lines = collections.deque(f, maxlen=5000)
                content = "".join(lines)
                self.full_log_text.get_buffer().set_text(content)
            else:
                self.full_log_text.get_buffer().set_text("Chưa tạo file log.")
        except Exception as e:
            self.full_log_text.get_buffer().set_text(f"Không thể đọc file log: {str(e)}")

    # --- DIALOG & MESSAGES ---
    def show_dialog(self, title: str, message: str):
        if HAS_ADW:
            dialog = Adw.MessageDialog(
                transient_for=self.window,
                heading=title,
                body=message
            )
            dialog.add_response("ok", "OK")
            dialog.set_default_response("ok")
            dialog.connect("response", lambda d, r: d.close())
            dialog.present()
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=title
            )
            dialog.props.secondary_text = message
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.present()

    def show_secure_boot_dialog(self):
        """Dialog hướng dẫn Secure Boot MOK khi cài driver Nvidia lỗi."""
        lbl_body = Gtk.Label()
        lbl_body.set_wrap(True)
        lbl_body.set_markup(
            "Driver độc quyền NVIDIA yêu cầu chữ ký nhân (kernel modules signature).\n"
            "Để card đồ họa hoạt động, bạn cần đăng ký khóa chữ ký MOK.\n\n"
            "<b>Các bước thực hiện:</b>\n"
            "1. <b>Khởi động lại máy</b>.\n"
            "2. Khi màn hình xanh <b>'Perform MOK management'</b> hiện lên, bấm phím bất kỳ.\n"
            "3. Chọn <b>Enroll MOK</b> -> Chọn <b>Continue</b>.\n"
            "4. Chọn <b>Yes</b> để xác nhận enroll key.\n"
            "5. Nhập <b>mật khẩu MOK</b> được sinh ra bởi hệ thống (thường bạn đã nhập lúc cài driver hoặc mật khẩu rỗng).\n"
            "6. Chọn <b>Reboot</b> để hoàn tất.\n\n"
            "<i>Nếu không làm bước này, Driver Nvidia sẽ bị chặn và hệ thống sẽ dùng card Onboard Intel.</i>"
        )

        if self.has_adw:
            dialog = Adw.AlertDialog(
                heading="Phát hiện Secure Boot đang kích hoạt!",
                body="Driver độc quyền NVIDIA yêu cầu chữ ký nhân (kernel modules signature)."
            )
            dialog.set_extra_child(lbl_body)
            dialog.add_response("ok", "Đã hiểu")
            dialog.set_default_response("ok")
            dialog.connect("response", lambda d, r: d.close())
            dialog.present(self.window)
        else:
            dialog = Gtk.Dialog(title="Hướng dẫn Secure Boot MOK Enrollment")
            dialog.set_transient_for(self.window)
            dialog.set_modal(True)
            dialog.set_default_size(500, 350)

            content = dialog.get_content_area()
            content.set_margin_top(15)
            content.set_margin_bottom(15)
            content.set_margin_start(15)
            content.set_margin_end(15)
            content.set_spacing(10)

            lbl_title = Gtk.Label()
            lbl_title.set_markup("<b><span size='large' color='#e74c3c'>Phát hiện Secure Boot đang kích hoạt!</span></b>")
            content.append(lbl_title)
            content.append(lbl_body)

            dialog.add_button("Đã hiểu", Gtk.ResponseType.OK)
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.present()

    def show_reboot_dialog(self):
        title = "Yêu cầu khởi động lại"
        msg = "Hệ thống đã thiết lập các thay đổi quan trạng (Driver/GRUB/Kernel).\nBạn có muốn khởi động lại máy ngay bây giờ để áp dụng các thay đổi không?"

        def do_reboot():
            cmd = Command("shutdown -r now", "Khởi động lại hệ thống", is_sudo=True)
            self.runner.run_commands(
                [cmd],
                on_complete=lambda ok, s, t: None if ok else GLib.idle_add(
                    self.show_toast, "Không thể khởi động lại tự động. Vui lòng reboot thủ công."
                )
            )

        if self.has_adw:
            dialog = Adw.AlertDialog(
                heading=title,
                body=msg
            )
            dialog.add_response("cancel", "Để sau")
            dialog.add_response("reboot", "Khởi động lại ngay")
            dialog.set_response_appearance("reboot", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("reboot")

            def on_response(dlg, response_id):
                if response_id == "reboot":
                    do_reboot()
                dlg.close()

            dialog.connect("response", on_response)
            dialog.present(self.window)
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                modal=True,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=title
            )
            dialog.props.secondary_text = msg

            def on_response(dlg, response_id):
                if response_id == Gtk.ResponseType.YES:
                    do_reboot()
                dlg.destroy()

            dialog.connect("response", on_response)
            dialog.present()

    def check_secure_boot_on_startup(self):
        def run_check():
            try:
                import subprocess
                res = subprocess.run("mokutil --sb-state", shell=True, capture_output=True, text=True)
                if res.returncode == 0 and "enabled" in res.stdout.lower():
                    GLib.idle_add(lambda: self.banner_box.set_visible(True))
            except Exception:
                pass
        import threading
        threading.Thread(target=run_check, daemon=True).start()

    # --- EVENTS HEADERBAR ---
    def on_open_log_dir(self, btn):
        """Mở thư mục chứa file log trong File Manager."""
        try:
            Gio.AppInfo.launch_default_for_uri(
                Gio.File.new_for_path(global_logger.log_dir).get_uri(),
                None
            )
        except Exception as e:
            self.show_dialog("Không thể mở thư mục", str(e))

    def on_export_log(self, btn):
        """Mở hộp thoại lưu file để xuất log."""
        file_chooser = Gtk.FileDialog()
        file_chooser.set_initial_name("setup_report.log")
        
        # Tạo bộ lọc file
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filter_log = Gtk.FileFilter()
        filter_log.set_name("Log Files (*.log)")
        filter_log.add_pattern("*.log")
        filters.append(filter_log)
        file_chooser.set_filters(filters)

        def save_callback(dialog, result):
            try:
                dest_file = file_chooser.save_finish(result)
                if dest_file:
                    dest_path = dest_file.get_path()
                    shutil.copy2(global_logger.log_path, dest_path)
                    global_logger.log(f"Đã xuất log thành công ra: {dest_path}", "ok")
                    # Chạy trên main thread để báo cáo
                    GLib.idle_add(lambda: self.show_toast(f"Đã xuất log thành công ra: {dest_path}"))
            except Exception as e:
                GLib.idle_add(lambda: self.show_dialog("Lỗi xuất log", str(e)))

        file_chooser.save(self.window, None, save_callback)

    # --- TRANG TRẠNG THÁI MODULE (MODULE STATUS CHECKS) ---
    def load_module_status_page(self):
        """Xây dựng và nạp các card trạng thái cho từng module."""
        # Xóa các card cũ
        child = self.mod_status_cards_box.get_first_child()
        while child:
            next_sibling = child.get_next_sibling()
            self.mod_status_cards_box.remove(child)
            child = next_sibling

        self._mod_status_card_refs.clear()
        self._failed_modules.clear()
        self.btn_fix_failed.set_visible(False)
        self.lbl_mod_check_summary.set_text("Nhấn 'Kiểm tra tất cả' để bắt đầu.")

        self._total_module_count = 0

        # Duyệt qua các stage
        for stage_key, stage_info in STAGES.items():
            # Label tiêu đề stage
            stage_lbl = Gtk.Label()
            stage_lbl.set_markup(f"<b><span size='large' color='#7f8c8d'>─── {html.escape(stage_info['name'].upper())} ───</span></b>")
            stage_lbl.set_halign(Gtk.Align.START)
            stage_lbl.set_margin_top(15)
            stage_lbl.set_margin_bottom(5)
            self.mod_status_cards_box.append(stage_lbl)

            # Box dọc chứa các card của stage này
            stage_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            self.mod_status_cards_box.append(stage_box)

            for module_cls in stage_info["modules"]:
                self._total_module_count += 1
                module = module_cls()

                # Tạo container cho Card
                card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                card_box.add_css_class("module-card-checking")
                
                # Row 1: Header của card
                header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                
                lbl_icon = Gtk.Label(label="⏳")
                lbl_icon.set_margin_end(5)
                header_row.append(lbl_icon)

                lbl_name = Gtk.Label()
                lbl_name.set_markup(f"<b>{html.escape(module.name)}</b>")
                lbl_name.set_halign(Gtk.Align.START)
                header_row.append(lbl_name)

                # Spacer đẩy level badge về góc phải
                spacer = Gtk.Box()
                spacer.set_hexpand(True)
                header_row.append(spacer)

                badge = Gtk.Label(label=module.required_level.lower())
                if module.required_level == "Bắt buộc":
                    badge.add_css_class("badge-required")
                elif module.required_level == "GPU":
                    badge.add_css_class("badge-gpu")
                else:
                    badge.add_css_class("badge-optional")
                header_row.append(badge)

                card_box.append(header_row)

                # Row 2: Status & details
                status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                
                lbl_status = Gtk.Label()
                lbl_status.set_markup("<span color='#7f8c8d'>Chờ kiểm tra...</span>")
                lbl_status.set_halign(Gtk.Align.START)
                status_row.append(lbl_status)

                lbl_detail = Gtk.Label(label="")
                lbl_detail.set_halign(Gtk.Align.START)
                lbl_detail.add_css_class("dim-label")
                status_row.append(lbl_detail)

                card_box.append(status_row)

                # Thêm card vào stage box
                stage_box.append(card_box)

                # Lưu reference để cập nhật kết quả sau này
                self._mod_status_card_refs[module.id] = (card_box, lbl_status, lbl_detail, lbl_icon)

    def run_module_validate_check(self, btn):
        """Khởi chạy quét trạng thái validate các module bất đồng bộ."""
        self.btn_check_modules.set_sensitive(False)
        self.btn_check_modules.set_label("⏳ Đang quét...")
        self.btn_fix_failed.set_visible(False)
        self._failed_modules.clear()

        # Đặt lại icon ⏳ cho tất cả card
        for ref in self._mod_status_card_refs.values():
            card_box, lbl_status, lbl_detail, lbl_icon = ref
            lbl_icon.set_text("⏳")
            lbl_status.set_markup("<span color='#7f8c8d'>Đang kiểm tra...</span>")
            lbl_detail.set_text("")
            for cls in ["module-card-ok", "module-card-failed", "module-card-warning"]:
                card_box.remove_css_class(cls)
            card_box.add_css_class("module-card-checking")

        def check_thread():
            import time
            for stage_info in STAGES.values():
                for module_cls in stage_info["modules"]:
                    module = module_cls()
                    try:
                        # Thêm delay rất nhỏ để thấy hiệu ứng quét realtime sinh động
                        time.sleep(0.1)
                        result = module.validate()
                    except Exception as e:
                        from modules.base import CheckResult
                        result = CheckResult(False, "✗ LỖI", str(e))
                    GLib.idle_add(self._update_module_card, module.id, result)
            GLib.idle_add(self._on_module_check_complete)

        import threading
        threading.Thread(target=check_thread, daemon=True).start()

    def _update_module_card(self, module_id, result):
        """Cập nhật giao diện của một card cụ thể dựa trên kết quả validate."""
        ref = self._mod_status_card_refs.get(module_id)
        if not ref:
            return False
        card_box, lbl_status, lbl_detail, lbl_icon = ref

        card_box.remove_css_class("module-card-checking")

        if result.success:
            card_box.add_css_class("module-card-ok")
            lbl_icon.set_text("🟢")
            lbl_status.set_markup(f"<span color='#2ecc71'><b>{html.escape(result.message)}</b></span>")
        elif "⚠" in result.message or "WARNING" in result.message:
            card_box.add_css_class("module-card-warning")
            lbl_icon.set_text("🟡")
            lbl_status.set_markup(f"<span color='#f1c40f'><b>{html.escape(result.message)}</b></span>")
        else:
            card_box.add_css_class("module-card-failed")
            lbl_icon.set_text("🔴")
            lbl_status.set_markup(f"<span color='#e74c3c'><b>{html.escape(result.message)}</b></span>")
            if module_id not in self._failed_modules:
                self._failed_modules.append(module_id)

        lbl_detail.set_markup(f"<i>{html.escape(result.detail or '')}</i>")
        return False

    def _on_module_check_complete(self):
        """Callback khi quá trình quét hoàn tất."""
        self.btn_check_modules.set_sensitive(True)
        self.btn_check_modules.set_label("🔍 Kiểm tra lại")

        failed_count = len(self._failed_modules)
        passed_count = self._total_module_count - failed_count

        if failed_count == 0:
            self.lbl_mod_check_summary.set_markup(
                f"<span class='check-summary-ok'>✅ Tất cả {passed_count} module đều tối ưu!</span>"
            )
            self.btn_fix_failed.set_visible(False)
        else:
            self.lbl_mod_check_summary.set_markup(
                f"<span color='#2ecc71'><b>✓ {passed_count} đạt</b></span>  ·  "
                f"<span color='#e74c3c'><b>✗ {failed_count} chưa đạt</b></span>"
            )
            self.btn_fix_failed.set_label(f"🚀 Cài & Tối ưu ngay ({failed_count} mục chưa đạt)")
            self.btn_fix_failed.set_visible(True)
        return False

    def on_fix_failed_modules_clicked(self, btn):
        """Hiển thị dialog lựa chọn module trước khi cài đặt."""
        # 1. Thu thập các lớp module (module class) thất bại
        all_failed_module_cls = []
        for stage_info in STAGES.values():
            for module_cls in stage_info["modules"]:
                if module_cls.id in self._failed_modules:
                    all_failed_module_cls.append(module_cls)

        if not all_failed_module_cls:
            self.show_toast("Không có mục nào chưa đạt cần cài đặt.")
            return

        # 2. Phân loại mandatory (Bắt buộc / GPU) và optional (Tùy chọn)
        mandatory = [mc for mc in all_failed_module_cls
                     if mc.required_level in ("Bắt buộc", "GPU")]
        optional  = [mc for mc in all_failed_module_cls
                     if mc.required_level == "Tùy chọn"]

        # 3. Xây dựng content widget và dictionary lưu các checkbox tùy chọn
        content_widget, optional_checkbox_map = self._build_fix_dialog_content(
            mandatory, optional
        )

        # 4. Hàm thực thi cài đặt khi người dùng nhấn xác nhận
        def do_run():
            selected = list(mandatory)  # Các mục bắt buộc luôn được thêm vào
            for mc, chk in optional_checkbox_map.items():
                if chk.get_active():
                    selected.append(mc)
            
            if not selected:
                self.show_toast("Bạn chưa chọn mục nào để cài đặt.")
                return

            # Chuyển sang trang setup_stage để theo dõi log
            self.stack.set_visible_child_name("setup_stage")
            self.progress_box.set_visible(True)
            self.btn_run_stage.set_visible(True)
            self.btn_run_all.set_visible(True)

            modules_to_run = [mc() for mc in selected]
            self.proceed_execution(modules_to_run, [], is_all_stages=False)

        # 5. Khởi chạy Dialog dựa trên Libadwaita hoặc Gtk.Dialog fallback
        if self.has_adw:
            dialog = Adw.AlertDialog(
                heading="Chọn mục muốn cài đặt & tối ưu",
                body="Các mục Bắt buộc/GPU không thể bỏ qua. Các mục Tùy chọn có thể chọn hoặc bỏ."
            )
            dialog.set_extra_child(content_widget)
            dialog.add_response("cancel", "Hủy")
            dialog.add_response("ok", "Xác nhận & Cài đặt")
            dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("ok")

            def on_adw_response(dlg, response_id):
                if response_id == "ok":
                    do_run()
                dlg.close()

            dialog.connect("response", on_adw_response)
            dialog.present(self.window)
        else:
            dialog = Gtk.Dialog(title="Chọn mục muốn cài đặt & tối ưu")
            dialog.set_transient_for(self.window)
            dialog.set_modal(True)
            dialog.set_default_size(520, 460)

            content = dialog.get_content_area()
            content.set_margin_top(15)
            content.set_margin_bottom(15)
            content.set_margin_start(15)
            content.set_margin_end(15)
            content.set_spacing(12)

            lbl_desc = Gtk.Label(
                label="Các mục Bắt buộc/GPU không thể bỏ qua.\nCác mục Tùy chọn có thể chọn hoặc bỏ tick."
            )
            lbl_desc.set_wrap(True)
            lbl_desc.set_halign(Gtk.Align.START)
            content.append(lbl_desc)
            content.append(content_widget)

            dialog.add_button("Hủy", Gtk.ResponseType.CANCEL)
            dialog.add_button("Xác nhận & Cài đặt", Gtk.ResponseType.OK)
            dialog.set_default_response(Gtk.ResponseType.OK)

            def on_gtk_response(dlg, response_id):
                if response_id == Gtk.ResponseType.OK:
                    do_run()
                dlg.destroy()

            dialog.connect("response", on_gtk_response)
            dialog.present()

    def _build_fix_dialog_content(self, mandatory, optional):
        """
        Xây dựng widget hiển thị danh sách module cho dialog lựa chọn.
        Trả về: (scrolled_window, optional_checkbox_map)
        """
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_size_request(480, -1)

        optional_checkbox_map = {}  # Lưu checkbox của các module tùy chọn

        def _make_module_row(module_cls, is_locked: bool):
            """Tạo giao diện một hàng hiển thị module thông tin."""
            module = module_cls()
            row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            row_box.set_margin_top(6)
            row_box.set_margin_bottom(6)
            row_box.set_margin_start(10)
            row_box.set_margin_end(10)

            top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            # Checkbox trạng thái chọn cài đặt
            chk = Gtk.CheckButton()
            chk.set_active(True)
            if is_locked:
                chk.set_sensitive(False)
                chk.set_tooltip_text("Mục bắt buộc đối với hệ thống, không thể bỏ qua")
            top_row.append(chk)

            # Label icon biểu tượng khóa nếu bị locked
            lbl_lock = Gtk.Label(label="🔒" if is_locked else "  ")
            lbl_lock.set_margin_end(3)
            top_row.append(lbl_lock)

            # Tên module
            lbl_name = Gtk.Label()
            lbl_name.set_markup(f"<b>{html.escape(module.name)}</b>")
            lbl_name.set_halign(Gtk.Align.START)
            lbl_name.set_hexpand(True)
            top_row.append(lbl_name)

            # Badge hiển thị loại yêu cầu
            badge = Gtk.Label(label=module.required_level.lower())
            if module.required_level == "Bắt buộc":
                badge.add_css_class("badge-required")
            elif module.required_level == "GPU":
                badge.add_css_class("badge-gpu")
            else:
                badge.add_css_class("badge-optional")
            top_row.append(badge)

            row_box.append(top_row)

            # Mô tả tóm tắt module
            lbl_desc = Gtk.Label(label=module.description)
            lbl_desc.set_halign(Gtk.Align.START)
            lbl_desc.set_wrap(True)
            lbl_desc.set_max_width_chars(50)
            lbl_desc.add_css_class("dim-label")
            lbl_desc.set_margin_start(40)  # Thụt lề thẳng hàng với text bên trên
            row_box.append(lbl_desc)

            return row_box, chk

        # --- Section 1: Nhóm Bắt buộc / GPU ---
        if mandatory:
            lbl_mandatory = Gtk.Label()
            lbl_mandatory.set_markup(
                "<b><span color='#e74c3c'>🔒 BẮT BUỘC / GPU (Không thể bỏ qua)</span></b>"
            )
            lbl_mandatory.set_halign(Gtk.Align.START)
            content_box.append(lbl_mandatory)

            mandatory_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            mandatory_list.add_css_class("module-card-failed")  # Khung viền đỏ nhạt cảnh báo

            for idx, mc in enumerate(mandatory):
                row_widget, _ = _make_module_row(mc, is_locked=True)
                mandatory_list.append(row_widget)
                if idx < len(mandatory) - 1:
                    mandatory_list.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

            content_box.append(mandatory_list)

        # --- Section 2: Nhóm Tùy chọn ---
        if optional:
            lbl_optional = Gtk.Label()
            lbl_optional.set_markup(
                "<b><span color='#3498db'>☑️ TÙY CHỌN (Có thể chọn hoặc bỏ tick)</span></b>"
            )
            lbl_optional.set_halign(Gtk.Align.START)
            lbl_optional.set_margin_top(8)
            content_box.append(lbl_optional)

            optional_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            optional_list.add_css_class("module-card-checking")  # Khung viền xanh dương nhạt

            for idx, mc in enumerate(optional):
                row_widget, chk = _make_module_row(mc, is_locked=False)
                optional_list.append(row_widget)
                optional_checkbox_map[mc] = chk
                if idx < len(optional) - 1:
                    optional_list.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

            content_box.append(optional_list)

        # --- Phần chân thông tin tóm tắt số lượng ---
        summary_text = f"ℹ️ Phát hiện {len(mandatory)} mục bắt buộc"
        if optional:
            summary_text += f" và {len(optional)} mục tùy chọn."
        lbl_summary = Gtk.Label(label=summary_text)
        lbl_summary.set_halign(Gtk.Align.START)
        lbl_summary.add_css_class("dim-label")
        lbl_summary.set_margin_top(4)
        content_box.append(lbl_summary)

        # Bọc danh sách bằng ScrolledWindow để cuộn nếu vượt quá kích thước màn hình
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(120)
        scroll.set_max_content_height(350)
        scroll.set_child(content_box)

        return scroll, optional_checkbox_map


