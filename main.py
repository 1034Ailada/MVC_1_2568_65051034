# main.py
from PyQt5.QtWidgets import QApplication, QMessageBox
import sys
from View.app import MainWindow
from Controller.project_controller import ProjectController

def main():
    app = QApplication(sys.argv)

    # กล่องถามโหมดตอนเริ่ม
    choice = QMessageBox.question(
        None, "เลือกโหมด",
        "คุณต้องการรันโครงการแบบ Stretch Goals หรือไม่?",
        QMessageBox.Yes | QMessageBox.No
    )
    mode = "stretch" if choice == QMessageBox.Yes else "basic"

    main_window = MainWindow()
    controller = ProjectController(main_window, mode=mode)
    main_window.set_controller(controller)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()