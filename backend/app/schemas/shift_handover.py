import re

from marshmallow import Schema, ValidationError, fields, validates

_WS_RE = re.compile(r"\s+")


def normalize_phrase(value: str) -> str:
    """口令归一化：去掉所有空白字符。"""
    return _WS_RE.sub("", value or "")


class ShiftHandoverCreateSchema(Schema):
    shed_id = fields.Int(required=True, data_key="shedId")
    phrase = fields.Str(required=True)
    handed_by = fields.Str(data_key="handedBy", allow_none=True)
    taken_by = fields.Str(required=True, data_key="takenBy")

    @validates("phrase")
    def _check_phrase(self, value):
        n = len(normalize_phrase(value))
        if not 4 <= n <= 12:
            raise ValidationError("口令去掉空白后长度需为 4 至 12 个字符")


class ShiftHandoverOutSchema(Schema):
    id = fields.Int(dump_only=True)
    shed_id = fields.Int(data_key="shedId")
    work_date = fields.Date(data_key="workDate")
    phrase = fields.Str()
    handed_by = fields.Str(data_key="handedBy")
    taken_by = fields.Str(data_key="takenBy")
    closed_at = fields.DateTime(data_key="closedAt", allow_none=True)
