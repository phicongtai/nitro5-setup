# -*- coding: utf-8 -*-
import sys
import gi
try:
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw
    HAS_ADW = True
except (ValueError, ImportError):
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk
    HAS_ADW = False

class SetupApp:
    """GTK4 / Libadwaita Application entry point."""
    def __init__(self):
        if HAS_ADW:
            self.app = Adw.Application(
                application_id="com.acer_nitro5.FedoraSetup",
                flags=gi.repository.Gio.ApplicationFlags.FLAGS_NONE
            )
            self.app.connect("activate", self.on_activate_adw)
        else:
            self.app = Gtk.Application(
                application_id="com.acer_nitro5.FedoraSetup",
                flags=gi.repository.Gio.ApplicationFlags.FLAGS_NONE
            )
            self.app.connect("activate", self.on_activate_gtk)
        
        self.app.connect("shutdown", self.on_shutdown)

    def on_shutdown(self, app):
        try:
            if hasattr(self, "win") and self.win:
                self.win.cleanup()
        except Exception:
            pass
        try:
            import keyring
            keyring.delete_password("nitro5-setup", "sudo")
        except Exception:
            pass

    def on_activate_adw(self, app):
        # Kích hoạt chế độ Dark Mode mặc định để mang lại giao diện gaming premium
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        
        from gui.main_window import MainWindow
        self.win = MainWindow(app, has_adw=True)
        self.win.window.present()

    def on_activate_gtk(self, app):
        from gui.main_window import MainWindow
        self.win = MainWindow(app, has_adw=False)
        self.win.window.present()

    def run(self, args):
        return self.app.run(args)
