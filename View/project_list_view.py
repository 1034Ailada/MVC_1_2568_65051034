# View/project_list_view.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import pyqtSignal


class ProjectListView(QWidget):
    """
    หน้ารวมโครงการ (View เท่านั้น)
    - แสดงตารางรายการโครงการ
    - ปุ่ม 'ดูสถิติ' → statsRequested
    - ดับเบิลคลิก/ปุ่ม 'ดูรายละเอียด' → openProjectRequested(project_id)
    - render_projects() จะเรียงตาม deadline ใกล้หมดเวลาก่อนเอง
    """

    openProjectRequested = pyqtSignal(str)   # ส่ง project_id ที่เลือก
    statsRequested = pyqtSignal()            # ขอเปิดหน้าสถิติ

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    # ---------------- UI Layout ----------------
    def _build(self):
        v = QVBoxLayout(self)

        header = QLabel("รายการโครงการ (เรียงใกล้หมดเวลาก่อน)")
        header.setStyleSheet("font-size:18px;font-weight:600;")
        v.addWidget(header)

        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels(
            ["ID", "ชื่อโครงการ", "เป้าหมาย", "กำหนดสิ้นสุด", "ยอดระดมปัจจุบัน"]
        )
        self.tbl.setSelectionBehavior(self.tbl.SelectRows)
        self.tbl.setEditTriggers(self.tbl.NoEditTriggers)
        # ดับเบิลคลิกเพื่อเปิดรายละเอียด
        self.tbl.itemDoubleClicked.connect(lambda _: self._emit_open_selected())
        v.addWidget(self.tbl)

        # ปุ่มล่าง: ดูสถิติ / ดูรายละเอียด
        row = QHBoxLayout()
        self.btn_stats = QPushButton("ดูสถิติ")
        self.btn_stats.clicked.connect(lambda: self.statsRequested.emit())
        self.btn_open = QPushButton("ดูรายละเอียด")
        self.btn_open.clicked.connect(self._emit_open_selected)

        row.addWidget(self.btn_stats)
        row.addStretch(1)
        row.addWidget(self.btn_open)
        v.addLayout(row)

    # ---------------- Helpers ----------------
    def _emit_open_selected(self):
        r = self.tbl.currentRow()
        if r < 0:
            QMessageBox.information(self, "ข้อมูลไม่ครบ", "กรุณาเลือกโครงการก่อน")
            return
        pid = self.tbl.item(r, 0).text()
        self.openProjectRequested.emit(pid)

    # ---------------- Render API ----------------
    def render_projects(self, projects):
        """
        projects: iterable ของออบเจ็กต์ที่มีฟิลด์อย่างน้อย:
          - project_id (str)
          - name (str)
          - goal_amount (float|str ตัวเลข)
          - deadline (date|str รูปแบบ YYYY-MM-DD)
          - raised_amount (float|str ตัวเลข)

        View จะเรียงตาม deadline ใกล้หมดเวลาก่อนในเมธอดนี้
        """
        # แปลงและเรียงตาม deadline (หากชนิดไม่ใช่ date ให้ fallback เป็น str เพื่อเรียงได้)
        try:
            sorted_projects = sorted(projects, key=lambda p: getattr(p, "deadline"))
        except Exception:
            sorted_projects = sorted(projects, key=lambda p: str(getattr(p, "deadline")))

        self.tbl.setRowCount(0)
        for p in sorted_projects:
            # อ่านค่าอย่างปลอดภัย
            pid = getattr(p, "project_id", "")
            name = getattr(p, "name", "")
            goal = float(getattr(p, "goal_amount", 0.0))
            deadline = getattr(p, "deadline", "")
            raised = float(getattr(p, "raised_amount", 0.0))

            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(str(pid)))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(name)))
            self.tbl.setItem(r, 2, QTableWidgetItem(f"{goal:.2f}"))
            self.tbl.setItem(r, 3, QTableWidgetItem(str(deadline)))
            self.tbl.setItem(r, 4, QTableWidgetItem(f"{raised:.2f}"))

        self.tbl.resizeColumnsToContents()