"""Service for user management."""


from auth_api.exceptions import ResourceNotFoundError
from .keycloak import KeycloakService


class GroupService:
    """User management service."""

    @classmethod
    def get_group(cls, group_data):
        """Get user by username."""
        group_name = group_data.get("group_name")
        groups = KeycloakService.get_groups(brief_representation=False)
        parent_group = next(
            (group for group in groups if group.get("name", "").lower() == group_name.lower()), None
        )
        if not parent_group:
            raise ResourceNotFoundError(f"Group with name '{group_name}' not found.")

        include_sub_groups = group_data.get("include_sub_groups", False)
        if include_sub_groups:
            child_groups = KeycloakService.get_sub_groups(parent_group.get("id"))
            parent_group["subGroups"] = child_groups
        return parent_group

