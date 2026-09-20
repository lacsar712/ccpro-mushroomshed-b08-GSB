from marshmallow import Schema, fields, validate

from app.schemas.shift_handover import ShiftHandoverOutSchema


class ShedCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    location = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    notes = fields.Str(allow_none=True)


class ShedOutSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    location = fields.Str()
    notes = fields.Str(allow_none=True)
    open_handover = fields.Nested(
        ShiftHandoverOutSchema, data_key="openHandover", allow_none=True, dump_only=True
    )
