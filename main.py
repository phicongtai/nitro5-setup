# -*- coding: utf-8 -*-
import sys
import os

# Thiết lập đường dẫn project
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from gui.app import SetupApp

if __name__ == "__main__":
    app = SetupApp()
    sys.exit(app.run(sys.argv))
