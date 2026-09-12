"""Role hierarchy and persistence tests."""

import pytest

from app.models import role as role_model
from app.models import user as user_model


@pytest.mark.unit
def test_role_permissions_fail_closed():
    assert role_model.has_permission("owner", "transfer_ownership")
    assert role_model.has_permission("moderator", "moderate_content")
    assert not role_model.has_permission("member", "moderate_content")
    assert not role_model.has_permission("invented", "manage_platform")


@pytest.mark.unit
def test_role_assignment_hierarchy():
    assert role_model.can_assign_role("owner", "co_owner")
    assert role_model.can_assign_role("co_owner", "admin")
    assert role_model.can_assign_role("admin", "moderator")
    assert not role_model.can_assign_role("admin", "co_owner")
    assert not role_model.can_assign_role("moderator", "member")


@pytest.mark.unit
def test_update_system_role_validates_and_persists(app):
    with app.app_context():
        user_id = user_model.create_user(
            "role_user", "role@example.com", user_model.hash_password("secret123")
        )
        assert user_model.update_system_role(user_id, "moderator") == 1
        assert user_model.get_user_by_id(user_id)["system_role"] == "moderator"
        with pytest.raises(ValueError):
            user_model.update_system_role(user_id, "superuser")
