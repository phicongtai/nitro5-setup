from abc import ABC, abstractmethod

class Command:
    """Lớp đại diện cho một câu lệnh hệ thống được thực thi."""
    def __init__(self, cmd: str, description: str, is_sudo: bool = True, skip_on_error: bool = False, is_interactive: bool = False):
        self.cmd = cmd
        self.description = description
        self.is_sudo = is_sudo
        self.skip_on_error = skip_on_error
        self.is_interactive = is_interactive

class CheckResult:
    """Lớp chứa kết quả kiểm tra/validation."""
    def __init__(self, success: bool, message: str, detail: str = ""):
        self.success = success      # True nếu OK, False nếu FAILED
        self.message = message      # Tiêu đề kết quả, ví dụ: "✓ OK" hoặc "✗ FAILED"
        self.detail = detail        # Chi tiết thêm, ví dụ: "RTX 3050, 545.xx"

from typing import ClassVar

class ModuleBase(ABC):
    """Lớp cơ sở cho các module thiết lập."""
    id: str = ""
    name: str = ""
    description: str = ""
    required_level: str = "Tùy chọn"  # "Bắt buộc", "Tùy chọn", "GPU"
    tags: ClassVar[list[str]] = []
    dependencies: ClassVar[list[str]] = []      # Danh sách id các module phụ thuộc
    
    def __init__(self):
        self.commands: list[Command] = []

    def get_commands(self) -> list[Command]:
        """Trả về danh sách các câu lệnh cần thực thi cho module này."""
        return self.commands

    @abstractmethod
    def validate(self) -> CheckResult:
        """Kiểm tra xem module đã cài đặt/cấu hình thành công chưa.
        Trả về đối tượng CheckResult.
        """
        pass

    def rollback(self) -> None:
        """Thực hiện hoàn tác nếu quá trình cài đặt lệnh con bị lỗi nửa chừng. (Tùy chọn)"""
        pass

    def get_reset_commands(self) -> list["ResetCommand"]:
        """Trả về danh sách lệnh để reset module về trạng thái mặc định."""
        return []

    def can_reset(self) -> bool:
        """Trả về True nếu module có thể được reset."""
        return len(self.get_reset_commands()) > 0


class ResetCommand:
    """Lớp đại diện cho một câu lệnh hệ thống dùng để hoàn tác/khôi phục cấu hình về mặc định."""
    def __init__(self, cmd: str, description: str, is_sudo: bool = True, skip_on_error: bool = True):
        self.cmd = cmd
        self.description = description
        self.is_sudo = is_sudo
        self.skip_on_error = skip_on_error

