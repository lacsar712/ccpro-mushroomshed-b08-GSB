from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from flask import jsonify
from marshmallow import ValidationError

from app.models.shift_handover import ShiftHandover

# 东八区（UTC+8，无夏令时）：交接班按该时区自然日归日
CN_TZ = timezone(timedelta(hours=8))


def workday_today() -> date:
    """东八区自然日（今天）。"""
    return datetime.now(CN_TZ).date()


def validation_error_response(err: ValidationError):
    messages = []
    for field, msgs in err.messages.items():
        if isinstance(msgs, list):
            for m in msgs:
                messages.append(f"{field}: {m}" if field != "_schema" else str(m))
        else:
            messages.append(f"{field}: {msgs}")
    detail = "; ".join(messages) if messages else "请求参数校验失败"
    return jsonify({"detail": detail}), 400


def get_open_handovers(db) -> List[ShiftHandover]:
    """所有未关闭（closed_at 为空）的交接班口令——棚列表与 open-check 共用此计数来源。"""
    return (
        db.query(ShiftHandover)
        .filter(ShiftHandover.closed_at.is_(None))
        .order_by(ShiftHandover.shed_id, ShiftHandover.id.desc())
        .all()
    )


def open_handover_map(db) -> Dict[int, ShiftHandover]:
    """shed_id -> 该棚未关闭的交接班口令（每棚至多一张）。"""
    result: Dict[int, ShiftHandover] = {}
    for ho in get_open_handovers(db):
        result.setdefault(ho.shed_id, ho)
    return result


def get_open_handover_for_shed(db, shed_id: int) -> Optional[ShiftHandover]:
    """该棚当前未关闭的交接班口令，无则 None。"""
    return (
        db.query(ShiftHandover)
        .filter(ShiftHandover.shed_id == shed_id, ShiftHandover.closed_at.is_(None))
        .order_by(ShiftHandover.id.desc())
        .first()
    )
