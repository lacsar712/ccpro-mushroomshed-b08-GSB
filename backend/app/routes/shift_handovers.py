from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.shed import Shed
from app.models.shift_handover import ShiftHandover
from app.models.user import User
from app.schemas.shift_handover import ShiftHandoverCreateSchema, ShiftHandoverOutSchema
from app.utils import open_handover_counts, validation_error_response, work_date_today

bp = Blueprint("shift_handovers", __name__, url_prefix="/api/shift-handovers")

create_schema = ShiftHandoverCreateSchema()
out_schema = ShiftHandoverOutSchema()
out_many = ShiftHandoverOutSchema(many=True)


@bp.get("")
@jwt_required()
def list_shift_handovers():
    db = SessionLocal()
    try:
        shed_id = request.args.get("shedId", type=int)
        only_open = request.args.get("open") in ("1", "true")
        q = db.query(ShiftHandover)
        if shed_id is not None:
            q = q.filter(ShiftHandover.shed_id == shed_id)
        if only_open:
            q = q.filter(ShiftHandover.closed_at.is_(None))
        rows = q.order_by(ShiftHandover.id.desc()).all()
        return jsonify(out_many.dump(rows))
    finally:
        db.close()


@bp.get("/open-check")
@jwt_required()
def open_check():
    db = SessionLocal()
    try:
        counts = open_handover_counts(db)
        return jsonify({"total": sum(counts.values())})
    finally:
        db.close()


@bp.post("")
@jwt_required()
def create_shift_handover():
    db = SessionLocal()
    try:
        try:
            data = create_schema.load(request.get_json(silent=True) or {})
        except ValidationError as err:
            return validation_error_response(err)
        shed = db.query(Shed).filter(Shed.id == data["shed_id"]).first()
        if not shed:
            return jsonify({"detail": "菇房不存在"}), 400
        today = work_date_today()
        existing = (
            db.query(ShiftHandover)
            .filter(ShiftHandover.shed_id == shed.id, ShiftHandover.work_date == today)
            .first()
        )
        if existing:
            return (
                jsonify({"detail": "该菇房当日已存在交接班口令", "existingId": existing.id}),
                409,
            )
        item = ShiftHandover(
            shed_id=shed.id,
            work_date=today,
            phrase=data["phrase"].strip(),
            handed_by=data["handed_by"].strip(),
            taken_by=data["taken_by"].strip(),
            closed_at=None,
        )
        db.add(item)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = (
                db.query(ShiftHandover)
                .filter(ShiftHandover.shed_id == shed.id, ShiftHandover.work_date == today)
                .first()
            )
            return (
                jsonify(
                    {
                        "detail": "该菇房当日已存在交接班口令",
                        "existingId": existing.id if existing else None,
                    }
                ),
                409,
            )
        db.refresh(item)
        return jsonify(out_schema.dump(item)), 201
    finally:
        db.close()


@bp.post("/<int:handover_id>/close")
@jwt_required()
def close_shift_handover(handover_id: int):
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
            return jsonify({"detail": "交接班已关闭"}), 400
        item.closed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return jsonify(out_schema.dump(item))
    finally:
        db.close()
