"""OpTech API client for spacing operations."""

import logging

from .commands import CorrectSpacingRecord

logger = logging.getLogger(__name__)


class OpTechClient:
    """Client for interacting with the OpTech API."""

    def send_correction(self, command: CorrectSpacingRecord) -> None:
        """Send a correction command to the OpTech API.

        For now, just log the command details.
        """
        logger.info(
            "Sending correction for partij %s: WZ1=%s, WZ2=%s",
            command.partij_code,
            command.aantal_tafels_na_wdz1,
            command.aantal_tafels_na_wdz2,
        )
