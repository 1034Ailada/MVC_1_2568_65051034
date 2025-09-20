# View/app.py
from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from View.project_list_view import ProjectListView
from View.project_detail_view import ProjectDetailView
from View.statistics_view import StatisticsView
from View.login_view import LoginView   # << เพิ่มบรรทัดนี้

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crowdfunding App")
        self.resize(960, 600)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # --- Views ---
        self.login_view = LoginView()                # << หน้า Login
        self.project_list_view = ProjectListView()
        self.project_detail_view = ProjectDetailView()
        self.statistics_view = StatisticsView()

        # --- Add to stack ---
        self._stack.addWidget(self.login_view)       # index 0
        self._stack.addWidget(self.project_list_view)  # index 1
        self._stack.addWidget(self.project_detail_view) # index 2
        self._stack.addWidget(self.statistics_view)    # index 3

        self._stack.setCurrentIndex(0)  # เริ่มที่หน้า Login

    def set_controller(self, controller):
        self.controller = controller