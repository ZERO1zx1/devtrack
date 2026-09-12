"""Platform roles and their permissions.

These roles describe trust and administrative authority. Developer seniority
belongs to the future onboarding profile and must never grant moderation rights.
"""

ROLES = ("owner", "co_owner", "admin", "moderator", "member")

ROLE_PERMISSIONS = {
    "owner": frozenset(
        {
            "transfer_ownership",
            "manage_platform",
            "manage_roles",
            "manage_members",
            "manage_projects",
            "moderate_content",
            "view_private_analytics",
        }
    ),
    "co_owner": frozenset(
        {
            "manage_platform",
            "manage_roles",
            "manage_members",
            "manage_projects",
            "moderate_content",
            "view_private_analytics",
        }
    ),
    "admin": frozenset(
        {
            "manage_roles",
            "manage_members",
            "manage_projects",
            "moderate_content",
            "view_private_analytics",
        }
    ),
    "moderator": frozenset({"moderate_content"}),
    "member": frozenset(),
}


def validate_role(role):
    if role not in ROLE_PERMISSIONS:
        raise ValueError(f"Unknown system role: {role}")
    return role


def has_permission(role, permission):
    """Return False for unknown roles; authorization fails closed."""
    return permission in ROLE_PERMISSIONS.get(role, ())


def can_assign_role(actor_role, target_role):
    """Return whether an actor may assign ``target_role``.

    Ownership can only be transferred by the current owner. Admins may assign
    moderator/member roles; co-owners may additionally assign admins.
    """
    if actor_role == "owner":
        return target_role in ROLES
    if actor_role == "co_owner":
        return target_role in {"admin", "moderator", "member"}
    if actor_role == "admin":
        return target_role in {"moderator", "member"}
    return False
