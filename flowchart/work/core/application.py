from ui.main_window import MainWindow

class Application:
    def __init__(self):
        self.main_window = MainWindow()

    def show(self):
        self.main_window.show()
