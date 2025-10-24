import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Define the root directory of the flowchart project
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
    main_window = MainWindow(root_dir=ROOT_DIR)
    main_window.show()
    sys.exit(app.exec())