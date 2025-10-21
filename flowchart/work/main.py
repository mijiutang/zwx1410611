import sys
from PyQt5.QtWidgets import QApplication
from core.application import Application

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = Application()
    main_app.show()
    sys.exit(app.exec_())
