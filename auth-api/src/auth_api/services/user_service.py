"""Service for user management."""
from auth_api.models.user import User as UserModel
from .keycloak import KeycloakService
from flask import g


class UserService:
    """User management service."""

    @classmethod
    def get_user_by_id(cls, user_id):
        """Get user by id."""
        app_name = g.app_name
        user = KeycloakService.get_user_by_id(user_id)

        user_groups = KeycloakService.get_user_groups(user.get('id'))

        app_groups = [group for group in user_groups if
                      app_name.lower() in group.get("path", "").lower()] if app_name else user_groups

        # Add groups to user data
        user["groups"] = app_groups
        return user

    @classmethod
    def get_all_users(cls):
        """Get all users, optionally filtered by app name."""
        users = KeycloakService.get_users()
        app_name = g.app_name
        groups = sorted(UserService.get_groups(), key=UserService._get_level)

        app_groups = [group for group in groups if
                      app_name.lower() in group.get("path", "").lower()] if app_name else groups

        # Create a dictionary to map group IDs to members
        group_members = {}
        for group in app_groups:
            members = KeycloakService.get_group_members(group["id"])
            member_ids = {member["id"] for member in members}
            group_members[group["id"]] = member_ids

        # Map users to their groups
        for user in users:
            user["groups"] = [group for group in app_groups if user["id"] in group_members.get(group["id"], set())]

        # Return only users with at least one group if filtered by app_name
        return [user for user in users if user["group"]] if app_name else users

    @classmethod
    def _get_level(cls, group):
        """Gets the level from the group, defaulting to 0 if not valid."""
        # Safely retrieve the level attribute and default to 0 if not valid
        level_str = group.get("attributes", {}).get("level", [0])[0]
        try:
            return int(level_str)
        except (ValueError, TypeError):
            return 0

    @classmethod
    def update_user_group(cls, user_id, user_data):
        """Update users group."""
        app_name = g.app_name
        group_name = user_data.get('group_name')
        path = f"/{app_name}/{group_name}" if app_name else group_name
        all_groups = cls.get_groups()
        group = next(
            (group for group in all_groups if group['name'] == group_name and group['path'] == path),
            None
        )
        result = KeycloakService.update_user_group(
            user_id, group["id"]
        )
        return result

    @classmethod
    def get_groups(cls):
        """Get groups that has "level" attribute set up"""
        groups = KeycloakService.get_groups()
        all_groups = []

        for group in groups:
            all_groups.append(group)
            if group.get("subGroups"):
                all_groups.extend(group["subGroups"])

        return all_groups

    @classmethod
    def get_groups_by_user_id(cls, user_id):
        """Get groups for a specific user by their ID."""
        groups = KeycloakService.get_user_groups(user_id)
        return groups

    @classmethod
    def create_user(cls, user_data):
        """Create user."""
        created_user = UserModel.create_user(user_data)
        return created_user

    @classmethod
    def update_user(cls, user_id, user_data):
        """Update user."""
        updated_user = UserModel.update_user(user_id, user_data)
        return updated_user

    @classmethod
    def delete_user(cls, user_id):
        """Update user."""
        user = UserModel.find_by_id(user_id)
        if not user:
            return None

        user.delete()
        return user
