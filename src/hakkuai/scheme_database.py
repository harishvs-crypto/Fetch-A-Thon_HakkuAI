"""
Scheme database module for HakkuAI.
Loads, indexes, and queries verified welfare schemes from local storage.
Accurately distinguishes state-specific schemes from national schemes and
identifies when local rules are incomplete or unverified.
"""

import json
from pathlib import Path
from hakkuai.config import settings
from hakkuai.logging_config import logger
from hakkuai.schemas import Scheme, VerificationStatus

# Normalized state names mapping for robust matching
STATE_ALIASES = {
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "karnataka": "Karnataka",
    "ka": "Karnataka",
    "karnatak": "Karnataka",
    "kerala": "Kerala",
    "andhra pradesh": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    "telangana": "Telangana",
    "ts": "Telangana",
    "maharashtra": "Maharashtra",
    "delhi": "Delhi",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "bihar": "Bihar",
    "west bengal": "West Bengal",
    "wb": "West Bengal",
    "rajasthan": "Rajasthan",
    "gujarat": "Gujarat",
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "haryana": "Haryana",
    "assam": "Assam",
    "jharkhand": "Jharkhand",
    "chhattisgarh": "Chhattisgarh",
    "uttarakhand": "Uttarakhand",
    "himachal pradesh": "Himachal Pradesh",
    "goa": "Goa",
    "tripura": "Tripura",
    "meghalaya": "Meghalaya",
    "manipur": "Manipur",
    "nagaland": "Nagaland",
    "sikkim": "Sikkim",
    "arunachal pradesh": "Arunachal Pradesh",
    "mizoram": "Mizoram",
}

class SchemeDatabase:
    """Manages the local repository of verified government welfare schemes."""

    def __init__(self, data_path: Path | str | None = None):
        self.data_path = Path(data_path) if data_path else settings.SCHEMES_FILE
        self._schemes: dict[str, Scheme] = {}
        self.load_schemes()

    def load_schemes(self) -> None:
        """Loads and validates schemes from JSON file."""
        if not self.data_path.exists():
            logger.error(f"Schemes data file not found at: {self.data_path}")
            self._schemes = {}
            return

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._schemes = {}
            for item in data:
                scheme = Scheme(**item)
                self._schemes[scheme.scheme_id] = scheme
            logger.info(f"Loaded {len(self._schemes)} verified welfare schemes from {self.data_path}")
        except Exception as e:
            logger.error(f"Failed to load schemes from {self.data_path}: {e}")
            self._schemes = {}

    def get_all_schemes(self) -> list[Scheme]:
        """Returns all schemes in database."""
        return list(self._schemes.values())

    def get_scheme_by_id(self, scheme_id: str) -> Scheme | None:
        """Retrieves a specific scheme by its ID."""
        return self._schemes.get(scheme_id)

    @staticmethod
    def normalize_state(state_input: str | None) -> str | None:
        """Normalizes state name to standard title case or alias."""
        if not state_input:
            return None
        cleaned = state_input.strip().lower()
        return STATE_ALIASES.get(cleaned, state_input.strip().title())

    def has_state_specific_coverage(self, state_name: str | None) -> bool:
        """
        Checks whether the database contains state-specific schemes
        for the given state.
        """
        norm_state = self.normalize_state(state_name)
        if not norm_state:
            return False
        for s in self._schemes.values():
            if s.state_or_national.lower() == norm_state.lower():
                return True
        return False

    def query_schemes(
        self,
        state: str | None = None,
        include_national: bool = True
    ) -> list[Scheme]:
        """
        Finds schemes applicable to the specified state plus national schemes.
        Guarantees that state-specific schemes from OTHER states are NOT returned.
        """
        results: list[Scheme] = []
        norm_state = self.normalize_state(state)

        for s in self._schemes.values():
            # If national scheme and requested
            if s.state_or_national.lower() == "national":
                if include_national:
                    results.append(s)
            # If state matches worker's state
            elif norm_state and s.state_or_national.lower() == norm_state.lower():
                results.append(s)
            # Schemes from other specific states are strictly omitted

        return results

# Default singleton instance
scheme_db = SchemeDatabase()
