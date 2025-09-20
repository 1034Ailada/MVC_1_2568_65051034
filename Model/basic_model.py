# Model/basic_model.py
from __future__ import annotations
from typing import List, Optional
from datetime import date, datetime
import csv
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal

# --- โครงสร้างข้อมูลแบบเบา ๆ สำหรับ View/Controller ใช้ ---
class ProjectDTO:
    def __init__(self, project_id: str, name: str, goal_amount: float, deadline: date, raised_amount: float, rejected_count: int):
        self.project_id = project_id
        self.name = name
        self.goal_amount = goal_amount
        self.deadline = deadline
        self.raised_amount = raised_amount
        self.rejected_count = rejected_count


class BasicFundingModel(QObject):
    dataChanged = pyqtSignal()
    errorOccurred = pyqtSignal(str)

    def __init__(self, db_dir: Path = Path("Database")):
        super().__init__()
        self.db_dir = db_dir
        self._ensure_headers()

    # ---------------- CSV helpers ----------------
    def _p(self, name: str) -> Path: return self.db_dir / name

    def _ensure_headers(self):
        # project.csv
        pf = self._p("project.csv")
        if not pf.exists():
            with pf.open("w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=["project_id","name","goal_amount","deadline","raised_amount","rejected_count"]).writeheader()
        # reward_tiers.csv
        tf = self._p("reward_tiers.csv")
        if not tf.exists():
            with tf.open("w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=["project_id","tier_id","title","minimum_amount","quota_left"]).writeheader()
        # pledges.csv
        plf = self._p("pledges.csv")
        if not plf.exists():
            with plf.open("w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=["pledge_id","user_id","project_id","amount","created_at","reward_tier_id"]).writeheader()

    # ---------------- Validation ----------------
    @staticmethod
    def _validate_project_id(project_id: str):
        if len(project_id) != 8 or not project_id.isdigit() or project_id[0] == "0":
            raise ValueError("รหัสโครงการต้องเป็นตัวเลข 8 หลัก และตัวแรกห้ามเป็น 0")

    @staticmethod
    def _validate_goal(goal_amount: float):
        if goal_amount <= 0:
            raise ValueError("เป้าหมายยอดระดมทุนหลักต้องมากกว่า 0")

    @staticmethod
    def _validate_deadline_future(deadline: date):
        if deadline <= date.today():
            raise ValueError("วันสิ้นสุดต้องอยู่ในอนาคต")

    # ---------------- CRUD/ops ----------------
    def create_project(self, project_id: str, name: str, goal_amount: float, deadline: date):
        try:
            self._validate_project_id(project_id)
            self._validate_goal(goal_amount)
            self._validate_deadline_future(deadline)
            if self.get_project(project_id) is not None:
                raise ValueError("มีรหัสโครงการนี้อยู่แล้ว")

            with self._p("project.csv").open("a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["project_id","name","goal_amount","deadline","raised_amount","rejected_count"])
                w.writerow({
                    "project_id": project_id,
                    "name": name.strip(),
                    "goal_amount": f"{float(goal_amount):.2f}",
                    "deadline": deadline.isoformat(),
                    "raised_amount": f"{0.0:.2f}",
                    "rejected_count": "0",
                })
            self.dataChanged.emit()
        except Exception as e:
            self.errorOccurred.emit(str(e))

    def add_pledge(self, pledge_id: str, user_id: str, project_id: str, amount: float, when: Optional[datetime] = None, reward_tier_id: Optional[str] = None):
        try:
            proj = self.get_project(project_id)
            if proj is None:
                raise ValueError("ไม่พบโครงการ")

            now_dt = when or datetime.now()
            if now_dt.date() > proj.deadline:
                raise ValueError("โครงการนี้หมดเขตระดมทุนแล้ว")
            if amount <= 0:
                raise ValueError("จำนวนเงินต้องมากกว่า 0")

            tier = None
            if reward_tier_id:
                tier = self._get_tier(project_id, reward_tier_id)
                if tier is None:
                    raise ValueError("ไม่พบ Reward Tier ที่เลือก")
                if float(amount) < float(tier["minimum_amount"]):
                    raise ValueError("จำนวนเงินไม่ถึงขั้นต่ำของรางวัลนี้")
                if int(tier["quota_left"]) <= 0:
                    raise ValueError("รางวัลนี้เต็มแล้ว")

            # บันทึก pledge
            with self._p("pledges.csv").open("a", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=["pledge_id","user_id","project_id","amount","created_at","reward_tier_id"]).writerow({
                    "pledge_id": pledge_id,
                    "user_id": user_id,
                    "project_id": project_id,
                    "amount": f"{float(amount):.2f}",
                    "created_at": now_dt.isoformat(timespec="seconds"),
                    "reward_tier_id": reward_tier_id or "",
                })

            # อัปเดตยอดรวม
            self._update_project_amount(project_id, proj.raised_amount + float(amount))

            # ลดโควตา
            if tier is not None:
                self._update_tier_quota(project_id, reward_tier_id, int(tier["quota_left"]) - 1)

            self.dataChanged.emit()

        except Exception as e:
            # เพิ่ม rejected_count
            self._bump_rejected(project_id)
            self.errorOccurred.emit(str(e))

    # ---------------- Queries ----------------
    def list_projects(self) -> List[ProjectDTO]:
        out: List[ProjectDTO] = []
        with self._p("project.csv").open("r", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                out.append(ProjectDTO(
                    project_id=r["project_id"],
                    name=r["name"],
                    goal_amount=float(r["goal_amount"]),
                    deadline=date.fromisoformat(r["deadline"]),
                    raised_amount=float(r["raised_amount"]),
                    rejected_count=int(r.get("rejected_count", "0")),
                ))
        return out

    def get_project(self, project_id: str) -> Optional[ProjectDTO]:
        for p in self.list_projects():
            if p.project_id == project_id:
                return p
        return None

    def is_funded(self, project_id: str) -> bool:
        p = self.get_project(project_id)
        if p is None:
            raise ValueError("ไม่พบโครงการ")
        return p.raised_amount >= p.goal_amount

    # ---------------- Internal CSV ops ----------------
    def _read_all(self, filename: str) -> list[dict]:
        with self._p(filename).open("r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _write_all(self, filename: str, rows: list[dict], headers: list[str]):
        with self._p(filename).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            w.writerows(rows)

    def _update_project_amount(self, project_id: str, new_amount: float):
        rows = self._read_all("project.csv")
        for i, r in enumerate(rows):
            if r["project_id"] == project_id:
                rows[i]["raised_amount"] = f"{float(new_amount):.2f}"
                # คงค่า rejected_count เดิม
        self._write_all("project.csv", rows, ["project_id","name","goal_amount","deadline","raised_amount","rejected_count"])

    def _bump_rejected(self, project_id: str):
        rows = self._read_all("project.csv")
        for i, r in enumerate(rows):
            if r["project_id"] == project_id:
                rc = int(r.get("rejected_count","0")) + 1
                rows[i]["rejected_count"] = str(rc)
        self._write_all("project.csv", rows, ["project_id","name","goal_amount","deadline","raised_amount","rejected_count"])

    def _get_tier(self, project_id: str, tier_id: str) -> Optional[dict]:
        for r in self._read_all("reward_tiers.csv"):
            if r["project_id"] == project_id and r["tier_id"] == tier_id:
                return r
        return None

    def _update_tier_quota(self, project_id: str, tier_id: str, new_quota: int):
        rows = self._read_all("reward_tiers.csv")
        for i, r in enumerate(rows):
            if r["project_id"] == project_id and r["tier_id"] == tier_id:
                rows[i]["quota_left"] = str(int(new_quota))
        self._write_all("reward_tiers.csv", rows, ["project_id","tier_id","title","minimum_amount","quota_left"])