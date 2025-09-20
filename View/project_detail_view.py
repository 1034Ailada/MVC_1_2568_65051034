from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
)
from PyQt5.QtCore import pyqtSignal


class ProjectDetailView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        v = QVBoxLayout(self)

        self.lbl_title = QLabel("ชื่อโครงการ")
        self.lbl_title.setStyleSheet("font-size:20px;font-weight:700;")
        v.addWidget(self.lbl_title)

        self.lbl_pid = QLabel("รหัสโครงการ: -")
        self.lbl_goal = QLabel("เป้าหมาย: -")
        self.lbl_deadline = QLabel("กำหนดสิ้นสุด: -")
        self.lbl_raised = QLabel("ยอดระดม: -")
        for w in (self.lbl_pid, self.lbl_goal, self.lbl_deadline, self.lbl_raised):
            w.setStyleSheet("font-size:14px;")
            v.addWidget(w)

        v.addWidget(QLabel("ความคืบหน้า (เทียบกับเป้าหมาย):"))
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        v.addWidget(self.progress)

        nav = QHBoxLayout()
        self.btn_back = QPushButton("← กลับหน้ารวมโครงการ")
        self.btn_back.clicked.connect(lambda: self.backRequested.emit())
        nav.addWidget(self.btn_back)
        nav.addStretch(1)
        v.addLayout(nav)

    def render_project(self, project):
        """
        project: ออบเจ็กต์ที่มี (project_id, name, goal_amount, deadline, raised_amount)
        """
        self.lbl_title.setText(project.name)
        self.lbl_pid.setText(f"รหัสโครงการ: {project.project_id}")
        self.lbl_goal.setText(f"เป้าหมาย: {float(project.goal_amount):.2f}")
        self.lbl_deadline.setText(f"กำหนดสิ้นสุด: {project.deadline}")
        self.lbl_raised.setText(f"ยอดระดม: {float(project.raised_amount):.2f}")

        goal = float(project.goal_amount)
        raised = float(project.raised_amount)
        pct = 0 if goal <= 0 else min(int((raised / goal) * 100), 100)
        self.progress.setValue(pct)