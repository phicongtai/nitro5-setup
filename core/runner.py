# -*- coding: utf-8 -*-
import subprocess
import threading
from core.logger import global_logger
from gi.repository import GLib

class Runner:
    def __init__(self):
        self.sudo_password = ""
        self.canceled = False
        self.thread = None
        self.run_interactive_cb = None

    def set_sudo_password(self, password):
        self.sudo_password = password

    def cancel(self):
        self.canceled = True

    def run_commands(self, commands, on_progress=None, on_complete=None):
        self.canceled = False
        self.thread = threading.Thread(
            target=self._run_thread,
            args=(commands, on_progress, on_complete),
            daemon=True
        )
        self.thread.start()

    def _run_thread(self, commands, on_progress, on_complete):
        total = len(commands)
        success_count = 0
        
        for idx, cmd in enumerate(commands, 1):
            if self.canceled:
                global_logger.log("Quá trình thiết lập bị hủy bởi người dùng.", "warning")
                break
                
            if on_progress:
                on_progress(idx, total, cmd.description)
                
            # Check if command is interactive
            if hasattr(cmd, 'is_interactive') and cmd.is_interactive:
                if self.run_interactive_cb:
                    event = threading.Event()
                    GLib.idle_add(self.run_interactive_cb, cmd, event)
                    event.wait() # Block background thread until VTE finishes
                    success_count += 1 # Assume interactive commands succeed or user handles them
                    continue
                    
            global_logger.log(f"Đang chạy: {cmd.description}...", "running")
            
            full_cmd = cmd.cmd
            if cmd.is_sudo and self.sudo_password:
                full_cmd = f"echo '{self.sudo_password}' | sudo -S {cmd.cmd}"
                
            try:
                proc = subprocess.Popen(
                    full_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        global_logger.log(line.strip(), "stdout")
                        
                proc.wait()
                
                if proc.returncode == 0:
                    success_count += 1
                    global_logger.log(f"[OK] {cmd.description}", "ok")
                else:
                    global_logger.log(f"[LỖI] {cmd.description} (Mã lỗi: {proc.returncode})", "error")
                    if not cmd.skip_on_error:
                        if on_complete:
                            on_complete(False, success_count, total)
                        return
            except Exception as e:
                global_logger.log(f"Ngoại lệ khi thực thi lệnh: {str(e)}", "error")
                if not cmd.skip_on_error:
                    if on_complete:
                        on_complete(False, success_count, total)
                    return
                    
        if on_complete:
            on_complete(not self.canceled and success_count == total, success_count, total)
