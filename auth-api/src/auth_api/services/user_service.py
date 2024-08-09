"""Service for user management."""
from auth_api.models.user import User as UserModel
from .keycloak import KeycloakService


class UserService:
    """User management service."""

    @classmethod
    def get_user_by_id(cls, _user_id):
        """Get user by id."""
        db_user = UserModel.find_by_id(_user_id)
        return db_user

    @classmethod
    def get_all_users(cls):
        """Get all users."""
        return KeycloakService.get_users()

    @classmethod
    def update_user_group(cls, user_id, user_data):
        """Update users group."""
        app_name = user_data.get('app_name')
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
