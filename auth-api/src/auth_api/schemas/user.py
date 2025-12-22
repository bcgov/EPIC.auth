"""Engagement model class.

Manages the engagement.
"""

from marshmallow import EXCLUDE, Schema, fields, pre_dump

from .user_group_response import UserGroupResponseSchema


class UserSchema(Schema):
    """User schema."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Exclude unknown fields in the deserialized output."""

        unknown = EXCLUDE

    id = fields.Str(data_key="id")
    first_name = fields.Str()
    middle_name = fields.Str()
    last_name = fields.Str(data_key="last_name")
    email = fields.Str(data_key="email_address")
    username = fields.Str(data_key="username")
    groups = fields.List(fields.Nested(UserGroupResponseSchema))
    enabled = fields.Bool(data_key="enabled")
    attributes = fields.Dict(data_key="attributes")

    @pre_dump
    def convert_keys(self, data, **kwargs):
        """Convert keys to match the desired output format."""
        # Map incoming keys to output keys
        if "firstName" in data:
            data["first_name"] = data.pop("firstName")
        if "lastName" in data:
            data["last_name"] = data.pop("lastName")
        return data


class UserUpdateRequestSchema(Schema):
    """User Update Request Schema."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Exclude unknown fields in the deserialized output."""

        unknown = EXCLUDE

    first_name = fields.Str(data_key="firstName", required=False)
    last_name = fields.Str(data_key="lastName", required=False)
    enabled = fields.Bool(data_key="enabled", required=False)
