from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
import uuid

Payment = Literal["cash", "card"]
Status = Literal["idle", "playing", "pause"]

@dataclass
class PC:
    id: int
    name: str
    price_per_minute: float = 0.0
    status: Status = "idle"
    last_started_at: Optional[datetime] = None
    total_paid: float = 0.0
    payment_method: Optional[Payment] = None
    order_id: Optional[str] = None
    # accumulated play time across pauses within a session
    _accumulated_minutes: int = 0

@dataclass
class PlayRequest:
    pc_id: int
    hours: int
    minutes: int
    price: float
    payment: Payment

    def validate(self) -> None:
        if self.hours < 0:
            raise ValueError("hours must be >= 0")
        if not (0 <= self.minutes <= 59):
            raise ValueError("minutes must be in [0, 59]")
        if self.hours == 0 and self.minutes == 0:
            raise ValueError("duration must be > 0")
        if self.price <= 0:
            raise ValueError("price must be > 0")
        if self.payment not in ("cash", "card"):
            raise ValueError("payment must be 'cash' or 'card'")

class PCService:
    """In-memory service to manage PCs and sessions.
    This is decoupled from FastAPI/DB for easy unit testing.
    """
    def __init__(self) -> None:
        self._pcs: Dict[int, PC] = {}

    # --- CRUD device ---
    def init_pc(self, name: str) -> PC:
        new_id = (max(self._pcs) + 1) if self._pcs else 1
        pc = PC(id=new_id, name=name)
        self._pcs[new_id] = pc
        return pc

    def list_pcs(self) -> List[PC]:
        return list(self._pcs.values())

    def get_pc(self, pc_id: int) -> PC:
        if pc_id not in self._pcs:
            raise KeyError(f"PC {pc_id} not found")
        return self._pcs[pc_id]

    # --- Playflow ---
    def play(self, req: PlayRequest) -> dict:
        req.validate()
        pc = self.get_pc(req.pc_id)
        if pc.status in ("playing", "pause"):
            raise RuntimeError("PC already in session")

        total_minutes = req.hours * 60 + req.minutes
        pc.status = "playing"
        pc.price_per_minute = req.price / total_minutes
        pc.payment_method = req.payment
        pc.last_started_at = datetime.utcnow()
        pc.order_id = str(uuid.uuid4())
        pc._accumulated_minutes = 0

        finish_at = pc.last_started_at + timedelta(minutes=total_minutes)

        return {
            "order_id": pc.order_id,
            "pc_id": pc.id,
            "status": pc.status,
            "time": {
                "from": int(pc.last_started_at.timestamp()),
                "finish": int(finish_at.timestamp()),
                "total_minutes": total_minutes,
            },
            "price": req.price,
            "payment": req.payment,
        }

    def pause(self, pc_id: int) -> dict:
        pc = self.get_pc(pc_id)
        if pc.status != "playing" or pc.last_started_at is None:
            raise RuntimeError("PC is not playing")
        now = datetime.utcnow()
        elapsed = int((now - pc.last_started_at).total_seconds() // 60)
        pc._accumulated_minutes += max(0, elapsed)
        pc.status = "pause"
        pc.last_started_at = None
        return {"pc_id": pc.id, "status": pc.status, "accumulated_minutes": pc._accumulated_minutes}

    def resume(self, pc_id: int) -> dict:
        pc = self.get_pc(pc_id)
        if pc.status != "pause":
            raise RuntimeError("PC is not paused")
        pc.status = "playing"
        pc.last_started_at = datetime.utcnow()
        return {"pc_id": pc.id, "status": pc.status, "resumed_at": int(pc.last_started_at.timestamp())}

    def stop(self, pc_id: int) -> dict:
        pc = self.get_pc(pc_id)
        if pc.status not in ("playing", "pause") or pc.order_id is None:
            raise RuntimeError("PC has no active session")
        if pc.status == "playing" and pc.last_started_at is not None:
            now = datetime.utcnow()
            elapsed = int((now - pc.last_started_at).total_seconds() // 60)
            pc._accumulated_minutes += max(0, elapsed)

        total_price = round(pc._accumulated_minutes * pc.price_per_minute, 2)

        out = {
            "order_id": pc.order_id,
            "pc_id": pc.id,
            "played_minutes": pc._accumulated_minutes,
            "price": total_price,
            "payment": pc.payment_method,
        }

        # reset
        pc.status = "idle"
        pc.price_per_minute = 0.0
        pc.payment_method = None
        pc.last_started_at = None
        pc.order_id = None
        pc._accumulated_minutes = 0

        return out
