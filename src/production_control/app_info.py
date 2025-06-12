"""Application metadata information."""

import os
from importlib.metadata import metadata, version
from pydantic import BaseModel, HttpUrl
from typing import Optional


class ApplicationInfo(BaseModel):
    """Application metadata information."""

    name: str
    version: str
    description: str
    author_email: str
    project_url: HttpUrl
    qr_code_base_url: Optional[str] = None


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
        qr_code_base_url=os.getenv("QR_CODE_BASE_URL"),
    )
