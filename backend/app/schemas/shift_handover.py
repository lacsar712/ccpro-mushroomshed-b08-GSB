from marshmallow import Schema, ValidationError, fields, validate, validates, validates_schema


class ShiftHandoverCreateSchema(Schema):
    shed_id = fields.Int(required=True, data_key="shedId")
    phrase = fields.Str(required=True, validate=validate.Length(max=64))
    handed_by = fields.Str(required=True, data_key="handedBy", validate=validate.Length(max=64))
    taken_by = fields.Str(required=True, data_key="takenBy", validate=validate.Length(max=64))

    @validates("phrase")
    def _check_phrase(self, value, **kwargs):
        if not 4 <= len(value.strip()) <= 12:
            raise ValidationError("口令去掉空白后长度须为 4–12 字")

    @validates("handed_by")
    def _check_handed_by(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("handedBy 必填")

    @validates("taken_by")
    def _check_taken_by(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("takenBy 必填")

    @validates_schema
    def _check_distinct_people(self, data, **kwargs):
        handed = (data.get("handed_by") or "").strip()
        taken = (data.get("taken_by") or "").strip()
        if handed and taken and handed == taken:
            raise ValidationError("handedBy 与 takenBy 不得是同一个登录名")


class ShiftHandoverOutSchema(Schema):
    id = fields.Int(dump_only=True)
    shed_id = fields.Int(data_key="shedId")
    work_date = fields.Date(data_key="workDate")
    phrase = fields.Str()
    handed_by = fields.Str(data_key="handedBy")
    taken_by = fields.Str(data_key="takenBy")
    closed_at = fields.DateTime(allow_none=True, data_key="closedAt")
