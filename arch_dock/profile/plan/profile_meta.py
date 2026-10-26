"""The .meta file that the georeferencing writes next to a profile image.
"""
import json
import os
from dataclasses import dataclass

AAR_DIRECTIONS = ("original", "horizontal", "absolute height")


@dataclass(frozen=True)
class ProfileMeta:
    """What the plan export needs from the .meta file of a profile image."""

    prof_nr: str
    aar_direction: str
    gcps: list
    transform_params: dict

    @classmethod
    def load(cls, image_path: str) -> "ProfileMeta":
        """Read <image>.meta next to the profile image.

        Raises ValueError with a message meant for the user.
        """
        meta_path = os.path.splitext(image_path)[0] + ".meta"
        if not os.path.isfile(meta_path):
            raise ValueError("Keine .meta Datei zum Profil vorhanden!")

        with open(meta_path) as json_file:  # same default encoding as the writer in georef
            data = json.load(json_file)

        if data.get("aar_direction") not in AAR_DIRECTIONS:
            raise ValueError("AAR direction muss horizontal, absolute height oder original sein!")

        try:
            return cls(
                prof_nr=data["profilnummer"],
                aar_direction=data["aar_direction"],
                gcps=data["gcps"],
                transform_params=data["transform_params"],
            )
        except KeyError as err:
            raise ValueError(f"Eintrag {err} fehlt in {os.path.basename(meta_path)}") from None
