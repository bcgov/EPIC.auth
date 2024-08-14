"""Engagement model class.

Manages the engagement
"""

from marshmallow import EXCLUDE, Schema, fields
from auth_api.models import User
from .user_group_response import UserGroupResponseSchema


class UserSchema(Schema):
    """User schema."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Exclude unknown fields in the deserialized output."""

        unknown = EXCLUDE

    id = fields.Str(data_key='id')
    firstName = fields.Str(data_key='first_name')
    middle_name = fields.Str(data_key='description')
    lastName = fields.Str(data_key='last_name')
    email = fields.Str(data_key='email_address')
    username = fields.Str(data_key='username')
    group = fields.Nested(UserGroupResponseSchema)


class UserRequestSchema(Schema):
    """User Request Schema"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Exclude unknown fields in the deserialized output."""

        unknown = EXCLUDE
    
    first_name = fields.Str(data_key='first_name')
    middle_name = fields.Str(data_key='description')
    last_name = fields.Str(data_key='last_name')
    email_address = fields.Str(data_key='email_address')
    contact_number = fields.Str(data_key='contact_number')
    username = fields.Str(data_key='username')
