# Controller/project_controller.py
from PyQt5.QtCore import QObject
from Model.basic_model import BasicFundingModel
from Model.stretch_model import StretchGoalFundingModel

from dataclasses import dataclass
from pathlib import Path
import csv


class ProjectController(QObject):
    """
    Controller เดียว ใช้ได้ 2 โหมด:
      - mode="basic"   → ไม่มี Stretch Goal
      - mode="stretch" → มี Stretch Goals
    รวมระบบ Login แบบง่าย (อ่านจาก Database/users.csv)
    """
    def __init__(self, main_window, mode: str = "basic"):
        super().__init__()
        self._win = main_window
        self._mode = "stretch" if mode.lower() == "stretch" else "basic"

        # เลือกโมเดลจากโหมด
        self._model = StretchGoalFundingModel() if self._mode == "stretch" else BasicFundingModel()

        # paths
        self._db_dir = Path("Database")
        self._project_csv = self._db_dir / "project.csv"
        self._pledges_csv = self._db_dir / "pledges.csv"
        self._users_csv = self._db_dir / "users.csv"

        # session
        self._current_user = None  # dict: {user_id, username, display_name}

        # signals (model → controller)
        self._model.dataChanged.connect(self.refresh_list)
        self._model.errorOccurred.connect(self._handle_error)

        # signals (view → controller)
        self._win.login_view.loginSubmitted.connect(self._on_login_submitted)               # << login
        self._win.project_list_view.openProjectRequested.connect(self._on_open_project)
        self._win.project_list_view.statsRequested.connect(self.show_statistics)
        self._win.project_detail_view.backRequested.connect(self._on_back)
        self._win.statistics_view.backRequested.connect(self._on_back)

        # เริ่มต้นอยู่หน้า Login (index 0)
        self._win._stack.setCurrentIndex(0)

    # ---------------- Authentication ----------------
    def _on_login_submitted(self, username: str, password: str):
        user = self._find_user(username)
        if not user or user.get("password", "") != password:
            self._win.login_view.show_error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            return
        # success
        self._current_user = {
            "user_id": user["user_id"],
            "username": user["username"],
            "display_name": user.get("display_name", user["username"]),
        }
        self._win.login_view.clear_inputs()
        # ไปหน้ารวมโครงการ
        self.refresh_list()

    def _find_user(self, username: str):
        if not self._users_csv.exists():
            return None
        with self._users_csv.open("r", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("username", "") == username:
                    return r
        return None

    def _require_login(self) -> bool:
        if self._current_user is None:
            # ถ้าหลุดเซสชัน ให้เด้งกลับหน้า Login
            self._win._stack.setCurrentIndex(0)
            return False
        return True

    # ---------------- Actions ----------------
    def refresh_list(self):
        # ต้องล็อกอินก่อนจึงให้เข้าหน้าหลัก
        if not self._require_login():
            return
        projects = self._model.list_projects()
        self._win.project_list_view.render_projects(projects)
        self._win._stack.setCurrentIndex(1)  # list = index 1

    def _on_open_project(self, project_id: str):
        if not self._require_login():
            return
        proj = self._model.get_project(project_id)
        if not proj:
            return
        self._win.project_detail_view.render_project(proj)
        self._win._stack.setCurrentIndex(2)  # detail = index 2

    def _on_back(self):
        if not self._require_login():
            return
        self._win._stack.setCurrentIndex(1)  # back to list

    def _handle_error(self, message: str):
        # TODO: ถ้าต้องการ popup: ใช้ QMessageBox.information(self._win, "ผิดพลาด", message)
        print("Error:", message)

    # ---------------- Statistics ----------------
    @dataclass
    class _ProjectRow:
        project_id: str
        name: str
        goal_amount: float
        raised_amount: float
        funded: bool
        success_count: int
        rejected_count: int
        unlocked_goals: list  # รายการ SG ที่ปลดล็อก (list[str]) — โหมด basic ให้ []

    def show_statistics(self):
        if not self._require_login():
            return

        # อ่าน projects
        projects = []
        total_rejected = 0
        if self._project_csv.exists():
            with self._project_csv.open("r", newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    goal = float(r["goal_amount"])
                    raised = float(r["raised_amount"])
                    rejected = int(r.get("rejected_count", "0"))
                    total_rejected += rejected
                    projects.append({
                        "project_id": r["project_id"],
                        "name": r["name"],
                        "goal_amount": goal,
                        "raised_amount": raised,
                        "rejected_count": rejected,
                        "funded": (raised >= goal),
                    })

        # นับ pledges สำเร็จต่อโครงการ
        per_project_success = {p["project_id"]: 0 for p in projects}
        total_success = 0
        if self._pledges_csv.exists():
            with self._pledges_csv.open("r", newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    pid = r["project_id"]
                    per_project_success[pid] = per_project_success.get(pid, 0) + 1
                    total_success += 1

        # (เฉพาะ stretch) ดึงรายการ SG ที่ปลดล็อกจากโมเดล
        unlocked_map = {p["project_id"]: [] for p in projects}
        if isinstance(self._model, StretchGoalFundingModel):
            for p in projects:
                sgs = self._model.unlocked_goals(p["project_id"])  # DTO list
                labels = []
                for sg in sgs:
                    label = getattr(sg, "description", None) or getattr(sg, "sg_id", "")
                    if label:
                        labels.append(str(label))
                unlocked_map[p["project_id"]] = labels

        # จัด row ส่งให้ view
        per_project_rows = []
        for p in projects:
            per_project_rows.append(self._ProjectRow(
                project_id=p["project_id"],
                name=p["name"],
                goal_amount=p["goal_amount"],
                raised_amount=p["raised_amount"],
                funded=p["funded"],
                success_count=per_project_success.get(p["project_id"], 0),
                rejected_count=p["rejected_count"],
                unlocked_goals=unlocked_map.get(p["project_id"], []),
            ))

        # summary รวม + ป้ายโหมด
        summary = {
            "total_projects": len(projects),
            "total_success_pledges": total_success,
            "total_rejected": total_rejected,
            "mode_label": "Stretch" if isinstance(self._model, StretchGoalFundingModel) else "Basic",
        }

        self._win.statistics_view.render(summary, per_project_rows)
        self._win._stack.setCurrentIndex(3)  # statistics = index 3
