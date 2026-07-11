# -*- coding: utf-8 -*-
import os
import datetime
from gi.repository import GLib

class Logger:
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_path = os.path.join(self.log_dir, "setup.log")
        self.gui_callback = None

    def set_gui_callback(self, cb):
        self.gui_callback = cb

    def log(self, message, tag="info"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{tag.upper()}] {message}\n"
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass
        if self.gui_callback:
            # Run inside GLib idle to be safe with GTK threads
            GLib.idle_add(self.gui_callback, log_line, tag)

global_logger = Logger()
