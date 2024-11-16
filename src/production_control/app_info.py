"""Application metadata information."""

from importlib.metadata import metadata, version
from pydantic import BaseModel, HttpUrl


class ApplicationInfo(BaseModel):
    """Application metadata information."""

    name: str
    version: str
    description: str
    author_email: str
    project_url: HttpUrl


def get_application_info() -> ApplicationInfo:
    """Get application metadata information."""
    pkg_metadata = metadata("production_control")
    app_version = version("production_control")

    return ApplicationInfo(
        name=pkg_metadata["Name"],
        version=app_version,
        description=pkg_metadata["Summary"],
        author_email=pkg_metadata["Author-email"],
        project_url=pkg_metadata["Project-URL"].split(",")[1].strip(),
    )
