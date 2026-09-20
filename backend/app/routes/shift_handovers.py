from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.shed import Shed
from app.models.shift_handover import ShiftHandover
from app.models.user import User
from app.schemas.shift_handover import (
    ShiftHandoverCreateSchema,
    ShiftHandoverOutSchema,
    normalize_phrase,
)
from app.utils import (
    get_open_handover_for_shed,
    get_open_handovers,
    validation_error_response,
    workday_today,
)

bp = Blueprint("shift_handovers", __name__, url_prefix="/api/shift-handovers")

create_schema = ShiftHandoverCreateSchema()
out_schema = ShiftHandoverOutSchema()


@bp.post("")
@jwt_required()
def open_handover():
    """开交接：admin / fruiter 均可。同棚同日仅一张，再开 409 并带回已有 id。"""
    db = SessionLocal()
    try:
        try:
            data = create_schema.load(request.get_json(silent=True) or {})
        except ValidationError as err:
            return validation_error_response(err)

        shed = db.query(Shed).filter(Shed.id == data["shed_id"]).first()
        if not shed:
            return jsonify({"detail": "菇房不存在"}), 400

        username = get_jwt_identity()
        handed_by = (data.get("handed_by") or "").strip() or username
        taken_by = (data.get("taken_by") or "").strip()
        if not taken_by:
            return jsonify({"detail": "接班人登录名必填"}), 400
        if handed_by == taken_by:
            return jsonify({"detail": "交班人与接班人不得是同一个登录名"}), 400

        open_existing = get_open_handover_for_shed(db, shed.id)
        if open_existing:
            return jsonify(
                {
                    "detail": "该菇房存在未关闭的交接班口令，请先关闭",
                    "existingId": open_existing.id,
                }
            ), 409

        item = ShiftHandover(
            shed_id=shed.id,
            work_date=workday_today(),
            phrase=normalize_phrase(data["phrase"]),
            handed_by=handed_by,
            taken_by=taken_by,
            closed_at=None,
        )
        db.add(item)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            dup = (
                db.query(ShiftHandover)
                .filter(
                    ShiftHandover.shed_id == shed.id,
                    ShiftHandover.work_date == workday_today(),
                )
                .first()
            )
            return jsonify(
                {
                    "detail": "同棚同日仅一张交接班口令，今日已存在",
                    "existingId": dup.id if dup else None,
                }
            ), 409
        db.refresh(item)
        return jsonify(out_schema.dump(item)), 201
    finally:
        db.close()


@bp.post("/<int:handover_id>/close")
@jwt_required()
def close_handover(handover_id: int):
    """关交接：仅 admin，其他人 403。关闭后该棚 Room 才放行 fruiting。"""
    db = SessionLocal()
    try:
        username = get_jwt_identity()
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return jsonify({"detail": "无效或过期的令牌"}), 401
        if user.role != "admin":
            return jsonify({"detail": "仅场长（admin）可关闭交接班"}), 403

        item = db.query(ShiftHandover).filter(ShiftHandover.id == handover_id).first()
        if not item:
            return jsonify({"detail": "交接班记录不存在"}), 404
        if item.closed_at is not None:
            return jsonify({"detail": "交接班已关闭", "existingId": item.id}), 409

        item.closed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return jsonify(out_schema.dump(item))
    finally:
        db.close()


@bp.get("/open-check")
@jwt_required()
def open_check():
    """未关闭交接班总数；与 GET /api/sheds 每行 openHandover 共用同一计数来源。"""
    db = SessionLocal()
    try:
        return jsonify({"total": len(get_open_handovers(db))})
    finally:
        db.close()
