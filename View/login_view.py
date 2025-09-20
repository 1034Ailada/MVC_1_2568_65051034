# View/login_view.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import pyqtSignal


class LoginView(QWidget):
    """
    หน้าเข้าสู่ระบบ (View เท่านั้น)
    - ป้อน username / password
    - ปุ่ม 'เข้าสู่ระบบ' ยิงสัญญาณ loginSubmitted(username, password)
    - มีเมธอด show_error(msg) / clear_inputs() ให้ Controller เรียก
    """

    loginSubmitted = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        title = QLabel("เข้าสู่ระบบ")
        title.setStyleSheet("font-size:20px; font-weight:700;")
        v.addWidget(title)

        row_user = QHBoxLayout()
        row_user.addWidget(QLabel("Username:"))
        self.edt_user = QLineEdit()
        row_user.addWidget(self.edt_user)
        v.addLayout(row_user)

        row_pass = QHBoxLayout()
        row_pass.addWidget(QLabel("Password:"))
        self.edt_pass = QLineEdit()
        self.edt_pass.setEchoMode(QLineEdit.Password)
        row_pass.addWidget(self.edt_pass)
        v.addLayout(row_pass)

        self.btn_login = QPushButton("เข้าสู่ระบบ")
        self.btn_login.clicked.connect(self._emit_login)
        v.addWidget(self.btn_login)

        self.lbl_hint = QLabel("ใส่ username/password จาก Database/users.csv")
        self.lbl_hint.setStyleSheet("color:#666; font-size:12px;")
        v.addWidget(self.lbl_hint)

    def _emit_login(self):
        self.loginSubmitted.emit(self.edt_user.text().strip(), self.edt_pass.text())

    def show_error(self, message: str):
        QMessageBox.information(self, "เข้าสู่ระบบไม่สำเร็จ", message)

    def clear_inputs(self):
        self.edt_user.clear()
        self.edt_pass.clear()
        self.edt_user.setFocus()
