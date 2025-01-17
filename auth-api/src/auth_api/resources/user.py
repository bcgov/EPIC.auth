# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API endpoints for managing an user resource."""

from http import HTTPStatus

from flask import request
from flask_restx import Namespace, Resource

from auth_api.auth import auth
from auth_api.exceptions import BusinessError, ResourceNotFoundError
from auth_api.schemas.response.user_group_response import UserGroupResponseSchema
from auth_api.schemas.user import UserRequestSchema, UserSchema
from auth_api.services.user_service import UserService
from auth_api.utils.util import cors_preflight

from .apihelper import Api as ApiHelper


API = Namespace("users", description="Endpoints for User Management")
"""Custom exception messages
"""

user_request_model = ApiHelper.convert_ma_schema_to_restx_model(
    API, UserRequestSchema(), "User"
)
user_list_model = ApiHelper.convert_ma_schema_to_restx_model(
    API, UserSchema(), "UserListItem"
)
group_list_model = ApiHelper.convert_ma_schema_to_restx_model(
    API, UserGroupResponseSchema(), "UserListItem"
)


@cors_preflight("GET, OPTIONS, POST")
@API.route("", methods=["POST", "GET", "OPTIONS"])
class Users(Resource):
    """Resource for managing users."""

    @staticmethod
    @API.response(code=200, description="Success", model=[user_list_model])
    @ApiHelper.swagger_decorators(API, endpoint_description="Fetch all users")
    @API.response(400, "Bad Request")
    @API.response(404, "Not Found")
    @auth.require
    def get():
        """Fetch all users."""
        users = UserService.get_all_users()
        user_list_schema = UserSchema(many=True)
        return user_list_schema.dump(users), HTTPStatus.OK


@cors_preflight("GET, OPTIONS, PATCH, DELETE")
@API.route("/<user_id>", methods=["PATCH", "GET", "OPTIONS", "DELETE"])
@API.doc(params={"user_id": "The user identifier"})
class User(Resource):
    """Resource for managing a single user."""

    @staticmethod
    @auth.require
    @ApiHelper.swagger_decorators(API, endpoint_description="Fetch a user by id")
    @API.response(code=200, model=user_list_model, description="Success")
    @API.response(404, "Not Found")
    def get(user_id):
        """Fetch a user by id."""
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User with {user_id} not found")
        return UserSchema().dump(user), HTTPStatus.OK

    @staticmethod
    @auth.require
    @ApiHelper.swagger_decorators(API, endpoint_description="Update a user by id")
    @API.expect(user_request_model)
    @API.response(code=200, model=user_list_model, description="Success")
    @API.response(400, "Bad Request")
    @API.response(404, "Not Found")
    def patch(user_id):
        """Update a user by id."""
        user_data = UserRequestSchema().load(API.payload)
        updated_user = UserService.update_user(user_id, user_data)
        if not updated_user:
            raise ResourceNotFoundError(f"User with {user_id} not found")
        return UserSchema().dump(updated_user), HTTPStatus.OK

    @staticmethod
    @auth.require
    @ApiHelper.swagger_decorators(API, endpoint_description="Delete a user by id")
    @API.response(code=200, model=user_list_model, description="Deleted")
    @API.response(404, "Not Found")
    def delete(user_id):
        """Delete a user by id."""
        deleted_user = UserService.delete_user(user_id)
        if not deleted_user:
            raise ResourceNotFoundError(f"User with {user_id} not found")
        return UserSchema().dump(deleted_user), HTTPStatus.OK


@cors_preflight("GET, OPTIONS, PUT")
@API.route("/<user_id>/groups", methods=["GET", "OPTIONS", "PUT"])
@API.doc(params={"user_id": "The user identifier"})
class UserGroups(Resource):
    """Resource for managing user groups."""

    @staticmethod
    @auth.require
    @ApiHelper.swagger_decorators(API, endpoint_description="Fetch groups by user id")
    @API.response(404, "Not Found")
    def get(user_id):
        """Fetch groups for a user by id."""
        groups = UserService.get_groups_by_user_id(user_id)
        if not groups:
            raise ResourceNotFoundError(f"No groups found for user with {user_id}")
        return UserGroupResponseSchema(many=True).dump(groups), HTTPStatus.OK

    @staticmethod
    @auth.require
    def put(user_id):
        """Update the group of the user."""
        response = UserService.update_user_group(user_id, API.payload)
        if response.status_code == 204:
            return "", HTTPStatus.NO_CONTENT
        raise BusinessError("Update failed", 500)


@cors_preflight("OPTIONS, DELETE")
@API.route("/<user_id>/groups/<string:group_name>", methods=["OPTIONS", "DELETE"])
@API.doc(params={"user_id": "The user identifier", "group_name": "Name of the group"})
@API.doc(
    params={
        "del_sub_group_mappings": {
            "description": "Delete all the sub group mappings of the given parent group",
            "type": "boolean",
            "required": False,
        }
    }
)
class UserGroupName(Resource):
    """Resource to manage UserGroup by name."""

    @staticmethod
    @auth.require
    @ApiHelper.swagger_decorators(
        API, endpoint_description="Delete the user-group mapping"
    )
    @API.response(404, "Not Found")
    @API.response(204, "No Content")
    def delete(user_id, group_name):
        """Delete the user group mapping by the group name."""
        del_sub_group_mappings = bool(request.args.get("del_sub_group_mappings", False))
        UserService.delete_user_group(user_id, group_name, del_sub_group_mappings)
        return {}, HTTPStatus.NO_CONTENT


@cors_preflight("GET")
@API.route("/groups", methods=["GET", "OPTIONS"])
class Groups(Resource):
    """Group resource."""

    @staticmethod
    @auth.require
    @ApiHelper.swagger_decorators(
        API, endpoint_description="Fetch all groups in keyclaok"
    )
    @API.response(code=200, model=group_list_model, description="Groups List")
    @API.response(404, "Not Found")
    def get():
        """Get all groups."""
        reponse_schema = UserGroupResponseSchema(many=True)
        return reponse_schema.dump(UserService.get_groups()), HTTPStatus.OK
