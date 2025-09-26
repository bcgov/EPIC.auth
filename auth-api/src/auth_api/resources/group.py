# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API endpoint for retrieving a group by name."""

from http import HTTPStatus

from flask import request
from flask_restx import Namespace, Resource

from auth_api.auth import auth
from auth_api.schemas.response.user_group_response import UserGroupResponseSchema
from auth_api.utils.util import cors_preflight

from .apihelper import Api as ApiHelper
from ..services.group_service import GroupService

API = Namespace("groups", description="Endpoint for Group Management")

group_response_model = ApiHelper.convert_ma_schema_to_restx_model(
    API, UserGroupResponseSchema(), "Group"
)


@cors_preflight("GET, OPTIONS")
@API.route("/<group_name>", methods=["GET", "OPTIONS"])
class Groups(Resource):
    """Resource for fetching a group by name."""

    @staticmethod
    @API.response(code=200, description="Group Found", model=group_response_model)
    @ApiHelper.swagger_decorators(API, endpoint_description="Get group by name")
    @API.response(400, "Bad Request")
    @API.response(404, "Group Not Found")
    @auth.require
    def get(group_name):
        """Get group by name."""
        include_sub_groups = request.args.get("include_sub_groups", "true").lower() == "true"
        request_data = {"group_name": group_name, "include_sub_groups": include_sub_groups}
        result = GroupService.get_group(request_data)
        return result, HTTPStatus.OK
