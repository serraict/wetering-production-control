from os import getenv
from fastapi import Request
from nicegui import context


def get_current_user():
    """Get the current authenticated user information from Authelia headers.

    Returns:
        dict: User information with keys 'name', 'roles', 'email', and 'profile_page'
    """
    user_info = {"name": "Guest", "roles": [], "email": "", "profile_page": ""}

    try:
        request: Request = context.client.request
        user_name = request.headers.get("remote-name") or request.headers.get("remote-user")
        if user_name:
            user_info["name"] = user_name

        email = request.headers.get("remote-email")
        if email:
            user_info["email"] = email

        groups = request.headers.get("remote-groups")
        if groups:
            user_info["roles"] = [group.strip() for group in groups.split(",")]

        # Check for profile page URL from environment variable
        profile_url = getenv("PROFILE_PAGE_URL")
        if profile_url:
            user_info["profile_page"] = profile_url

    except Exception as e:
        print(f"Error getting user info: {e}")

    return user_info
