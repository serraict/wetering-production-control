"""OpTech API client for spacing operations."""

import logging
import os

import httpx
from pydantic import BaseModel

from .commands import CorrectSpacingRecord

logger = logging.getLogger(__name__)


class OpTechError(Exception):
    """Base exception for OpTech API errors."""

    pass


class OpTechConnectionError(OpTechError):
    """Raised when connection to OpTech API fails."""

    pass


class OpTechResponseError(OpTechError):
    """Raised when OpTech API returns an error response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"OpTech API error {status_code}: {detail}")


class CorrectionResponse(BaseModel):
    """Response from the OpTech API for a correction."""

    success: bool
    message: str


class OpTechClient:
    """Client for interacting with the OpTech API."""

    def __init__(self) -> None:
        """Initialize the OpTech API client.

        Raises:
            ValueError: If VINEAPP_OPTECH_API_URL environment variable is not set
        """
        self.base_url = os.getenv("VINEAPP_OPTECH_API_URL")
        if not self.base_url:
            raise ValueError("VINEAPP_OPTECH_API_URL environment variable not set")

    def send_correction(self, command: CorrectSpacingRecord) -> CorrectionResponse:
        """Send a correction command to the OpTech API.

        Args:
            command: The correction command to send

        Returns:
            CorrectionResponse with success status and message

        Raises:
            OpTechConnectionError: If connection to API fails
            OpTechResponseError: If API returns an error response
        """
        logger.info(
            "Sending correction for partij %s: WZ1=%s, WZ2=%s",
            command.partij_code,
            command.aantal_tafels_na_wdz1,
            command.aantal_tafels_na_wdz2,
        )

        url = f"{self.base_url}/api/partij/{command.partij_code}/wijderzet"
        payload = {
            "aantal_wz1": command.aantal_tafels_na_wdz1,
            "aantal_wz2": command.aantal_tafels_na_wdz2,
        }

        try:
            with httpx.Client() as client:
                response = client.put(url, json=payload)

                if response.status_code != 200:
                    try:
                        detail = response.json().get("detail", "Unknown error")
                    except Exception:
                        detail = response.text or "Unknown error"
                    raise OpTechResponseError(response.status_code, detail)

                return CorrectionResponse(
                    success=True,
                    message=f"Successfully updated spacing data for partij {command.partij_code}",
                )

        except httpx.RequestError as e:
            raise OpTechConnectionError(f"Failed to connect to OpTech API: {str(e)}")
