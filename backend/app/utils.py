from datetime import datetime, timedelta, timezone
from typing import Dict

from flask import jsonify
from marshmallow import ValidationError
from sqlalchemy import func

from app.models.shift_handover import ShiftHandover

# 东八区自然日：交接班按 UTC+8 的日历日归日，不设三班分钟表，也不按潮次切班
CN_TZ = timezone(timedelta(hours=8))


def work_date_today():
    """当前时刻按东八区归属的自然日。"""
    return datetime.now(CN_TZ).date()


def open_handover_counts(db) -> Dict[int, int]:
    """每个菇房未关闭（closed_at 为空）的交接班数量。

    GET /api/sheds 的 openHandover 与 GET /api/shift-handovers/open-check
    的 total 共用此计数，保证两处口径一致。
    """
    rows = (
        db.query(ShiftHandover.shed_id, func.count(ShiftHandover.id))
        .filter(ShiftHandover.closed_at.is_(None))
        .group_by(ShiftHandover.shed_id)
        .all()
    )
    return {shed_id: count for shed_id, count in rows}


def shed_has_open_handover(db, shed_id: int) -> bool:
    return (
        db.query(ShiftHandover.id)
        .filter(ShiftHandover.shed_id == shed_id, ShiftHandover.closed_at.is_(None))
        .first()
        is not None
    )


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
