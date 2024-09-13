# Copyright © 2019 Province of British Columbia
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
"""Keycloak admin functions"""
import requests
from flask import current_app
from auth_api.utils.enums import HttpMethod


class KeycloakService:
    """Keycloak services"""

    @staticmethod
    def get_groups(brief_representation: bool = False):
        """Get all the groups"""
        response = KeycloakService._request_keycloak(f'groups?briefRepresentation={brief_representation}')
        return response.json()

    @staticmethod
    def get_user():
        """Get users"""
        response = KeycloakService._request_keycloak('users?max=2000')
        return response.json()

    @classmethod
    def get_user_groups_by_id(cls, user_id):
        """Get groups of a specific user by their ID."""
        response = KeycloakService._request_keycloak(f'users/{user_id}/groups')
        return response.json()

    @staticmethod
    def get_user_by_id(username):
        """Get users"""
        response = KeycloakService._request_keycloak(f'users?username={username}')
        users = response.json()

        if not users:
            raise ValueError(f"User with username '{username}' not found.")

        # Assuming usernames are unique, return the first user found
        return users[0]

    @staticmethod
    def get_users():
        """Get users"""
        response = KeycloakService._request_keycloak('users?max=2000')
        return response.json()

    @staticmethod
    def get_members_for_groups(groups):
        """Get all groups with their members."""

        # For each group, get its members
        for group in groups:
            group_id = group['id']
            members_response = KeycloakService._request_keycloak(f'groups/{group_id}/members')
            group['members'] = members_response.json()

        return groups

    @staticmethod
    def get_members_for_group(group_id):
        """Get the members of a group"""
        response = KeycloakService._request_keycloak(f'groups/{group_id}/members')
        return response.json()

    @staticmethod
    def get_group_members(group_id):
        """Get the members of a group"""
        response = KeycloakService._request_keycloak(f'groups/{group_id}/members')
        return response.json()

    @staticmethod
    def get_group_id_by_name(group_name):
        """Get the group ID by its name"""
        groups = KeycloakService.get_groups(brief_representation=True)
        for group in groups:
            if group['name'] == group_name:
                return group['id']
        raise ValueError(f"Group with name '{group_name}' not found.")

    @staticmethod
    def update_user_group(user_id, group_id):
        """Update the group of user"""
        kc_user_id = KeycloakService.get_user_by_id(user_id)['id']
        return KeycloakService._request_keycloak(f'users/{kc_user_id}/groups/{group_id}', HttpMethod.PUT)

    @staticmethod
    def delete_user_group(user_id, group_id):
        """Delete user-group mapping"""
        kc_user_id = KeycloakService.get_user_by_id(user_id)['id']
        return KeycloakService._request_keycloak(f'users/{kc_user_id}/groups/{group_id}', HttpMethod.DELETE)

    @staticmethod
    def _request_keycloak(relative_url, http_method: HttpMethod = HttpMethod.GET, data=None):
        """Common method to request keycloak"""
        base_url = current_app.config.get('KEYCLOAK_BASE_URL')
        realm = current_app.config.get('KEYCLOAK_REALM_NAME')
        timeout = int(current_app.config.get('CONNECT_TIMEOUT', 60))
        admin_token = KeycloakService._get_admin_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {admin_token}'
        }

        url = f'{base_url}/auth/admin/realms/{realm}/{relative_url}'
        if http_method == HttpMethod.GET:
            response = requests.get(url, headers=headers, timeout=timeout)
        if http_method == HttpMethod.PUT:
            response = requests.put(url, headers=headers, data=data, timeout=timeout)
        if http_method == HttpMethod.DELETE:
            response = requests.delete(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response

    @staticmethod
    def get_user_groups(user_id):
        """Get groups directly associated with a specific user by their ID."""
        response = KeycloakService._request_keycloak(f'users/{user_id}/groups')
        return response.json()

    @staticmethod
    def get_sub_groups(group_id):
        """Return the subgroups of given group"""
        response = KeycloakService._request_keycloak(f"groups/{group_id}/children")
        return response.json()

    @staticmethod
    def _get_admin_token():
        """Create an admin token."""
        config = current_app.config
        base_url = config.get('KEYCLOAK_BASE_URL')
        realm = config.get('KEYCLOAK_REALM_NAME')
        admin_client_id = config.get(
            'KEYCLOAK_ADMIN_CLIENT')
        admin_secret = config.get('KEYCLOAK_ADMIN_SECRET')
        timeout = int(config.get('CONNECT_TIMEOUT', 60))
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        token_url = f'{base_url}/auth/realms/{realm}/protocol/openid-connect/token'

        response = requests.post(token_url,
                                 data=f'client_id={admin_client_id}&grant_type=client_credentials'
                                      f'&client_secret={admin_secret}', headers=headers,
                                 timeout=timeout)
        return response.json().get('access_token')