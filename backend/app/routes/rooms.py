from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.room import Room
from app.models.shed import Shed
from app.schemas.room import RoomCreateSchema, RoomOutSchema, RoomStatusUpdateSchema
from app.utils import get_open_handover_for_shed, validation_error_response

bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")

create_schema = RoomCreateSchema()
status_schema = RoomStatusUpdateSchema()
out_schema = RoomOutSchema()
out_many = RoomOutSchema(many=True)


def fruiting_blocked_response(shed_id: int, db):
    """该棚存在未关闭交接班口令时，禁止把 Room status 写成 fruiting。"""
    open_ho = get_open_handover_for_shed(db, shed_id)
    if open_ho:
        return jsonify(
            {
                "detail": "该菇房存在未关闭的交接班口令，关闭后才可写入 fruiting 状态",
                "handoverId": open_ho.id,
            }
        ), 409
    return None


@bp.get("")
@jwt_required()
def list_rooms():
    db = SessionLocal()
    try:
        shed_id = request.args.get("shedId", type=int)
        q = db.query(Room)
        if shed_id is not None:
            q = q.filter(Room.shed_id == shed_id)
        rows = q.order_by(Room.id).all()
        return jsonify(out_many.dump(rows))
    finally:
        db.close()


@bp.post("")
@jwt_required()
def create_room():
    db = SessionLocal()
    try:
        try:
            data = create_schema.load(request.get_json(silent=True) or {})
        except ValidationError as err:
            return validation_error_response(err)
        shed = db.query(Shed).filter(Shed.id == data["shed_id"]).first()
        if not shed:
            return jsonify({"detail": "菇房不存在"}), 400
        if data["status"] == "fruiting":
            blocked = fruiting_blocked_response(shed.id, db)
            if blocked:
                return blocked
        item = Room(
            shed_id=data["shed_id"],
            room_code=data["room_code"],
            species=data["species"],
            capacity_bags=data["capacity_bags"],
            status=data["status"],
        )
        db.add(item)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return jsonify({"detail": "同菇房内出菇室编号已存在"}), 400
        db.refresh(item)
        return jsonify(out_schema.dump(item)), 201
    finally:
        db.close()


@bp.patch("/<int:room_id>")
@jwt_required()
def update_room_status(room_id: int):
    db = SessionLocal()
    try:
        item = db.query(Room).filter(Room.id == room_id).first()
        if not item:
            return jsonify({"detail": "出菇室不存在"}), 404
        try:
            data = status_schema.load(request.get_json(silent=True) or {})
        except ValidationError as err:
            return validation_error_response(err)
        if data["status"] == "fruiting" and item.status != "fruiting":
            blocked = fruiting_blocked_response(item.shed_id, db)
            if blocked:
                return blocked
        item.status = data["status"]
        db.commit()
        db.refresh(item)
        return jsonify(out_schema.dump(item))
    finally:
        db.close()


@bp.delete("/<int:room_id>")
@jwt_required()
def delete_room(room_id: int):
    db = SessionLocal()
    try:
        item = db.query(Room).filter(Room.id == room_id).first()
        if not item:
            return jsonify({"detail": "出菇室不存在"}), 404
        db.delete(item)
        db.commit()
        return "", 204
    finally:
        db.close()
