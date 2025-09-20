# View/statistics_view.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar
)
from PyQt5.QtCore import pyqtSignal, Qt


class StatisticsView(QWidget):
    backRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("สถิติภาพรวมการระดมทุน")
        title.setStyleSheet("font-size:20px; font-weight:700;")
        root.addWidget(title)

        # โหมด (Basic / Stretch)
        self.lbl_mode = QLabel("โหมด: -")
        self.lbl_mode.setStyleSheet("font-size:12px; color:#555;")
        root.addWidget(self.lbl_mode)

        # Summary row
        self.lbl_total_projects = QLabel("โครงการทั้งหมด: 0")
        self.lbl_success = QLabel("สำเร็จ (pledges): 0")
        self.lbl_rejected = QLabel("ถูกปฏิเสธ: 0")
        self.lbl_success_rate = QLabel("อัตราสำเร็จ: 0.00%")

        summary_row = QHBoxLayout()
        for w in (self.lbl_total_projects, self.lbl_success, self.lbl_rejected, self.lbl_success_rate):
            w.setStyleSheet("font-size:14px;")
            summary_row.addWidget(w)
        summary_row.addStretch(1)
        root.addLayout(summary_row)

        # Table: per-project (+ คอลัมน์ Unlocked SG)
        self.tbl = QTableWidget(0, 10)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "ชื่อโครงการ", "เป้าหมาย", "ยอดระดม", "สำเร็จ?",
            "#สำเร็จ", "#ปฏิเสธ", "%Progress", "Progress", "Unlocked SG"
        ])
        self.tbl.setEditTriggers(self.tbl.NoEditTriggers)
        self.tbl.setSelectionBehavior(self.tbl.SelectRows)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.setColumnWidth(8, 180)   # progress bar
        self.tbl.setColumnWidth(9, 260)   # unlocked sg
        root.addWidget(self.tbl)

        # Footer / Nav
        nav = QHBoxLayout()
        self.btn_back = QPushButton("← กลับ")
        self.btn_back.clicked.connect(lambda: self.backRequested.emit())
        nav.addWidget(self.btn_back)
        nav.addStretch(1)
        root.addLayout(nav)

    # ---------------- Render API ----------------
    def render_summary(self, *, total_projects: int, total_success_pledges: int, total_rejected: int, mode_label: str = "-"):
        total_attempts = max(total_success_pledges + total_rejected, 1)
        rate = (total_success_pledges / total_attempts) * 100.0
        self.lbl_total_projects.setText(f"โครงการทั้งหมด: {total_projects}")
        self.lbl_success.setText(f"สำเร็จ (pledges): {total_success_pledges}")
        self.lbl_rejected.setText(f"ถูกปฏิเสธ: {total_rejected}")
        self.lbl_success_rate.setText(f"อัตราสำเร็จ: {rate:.2f}%")
        self.lbl_mode.setText(f"โหมด: {mode_label}")

    def render_project_rows(self, projects):
        self.tbl.setRowCount(0)

        for p in projects:
            goal = float(getattr(p, "goal_amount", 0.0))
            raised = float(getattr(p, "raised_amount", 0.0))
            pct = 0 if goal <= 0 else min(int((raised / goal) * 100), 100)

            r = self.tbl.rowCount()
            self.tbl.insertRow(r)

            self.tbl.setItem(r, 0, QTableWidgetItem(str(getattr(p, "project_id", ""))))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(getattr(p, "name", ""))))
            self.tbl.setItem(r, 2, QTableWidgetItem(f"{goal:.2f}"))
            self.tbl.setItem(r, 3, QTableWidgetItem(f"{raised:.2f}"))
            self.tbl.setItem(r, 4, QTableWidgetItem("✅" if bool(getattr(p, "funded", False)) else "—"))
            self.tbl.setItem(r, 5, QTableWidgetItem(str(int(getattr(p, "success_count", 0)))))
            self.tbl.setItem(r, 6, QTableWidgetItem(str(int(getattr(p, "rejected_count", 0)))))
            self.tbl.setItem(r, 7, QTableWidgetItem(f"{pct:d}%"))

            # ProgressBar ในคอลัมน์ 8
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(100)
            bar.setValue(pct)
            bar.setAlignment(Qt.AlignCenter)
            self.tbl.setCellWidget(r, 8, bar)

            # คอลัมน์ 9: Unlocked SG
            unlocked = getattr(p, "unlocked_goals", None) or []
            txt = " , ".join([str(x) for x in unlocked]) if unlocked else "—"
            self.tbl.setItem(r, 9, QTableWidgetItem(txt))

        self.tbl.resizeColumnsToContents()

    def render(self, summary, per_project):

        self.render_summary(
            total_projects=int(summary["total_projects"]),
            total_success_pledges=int(summary["total_success_pledges"]),
            total_rejected=int(summary["total_rejected"]),
            mode_label=str(summary.get("mode_label", "-")),
        )
        self.render_project_rows(per_project)