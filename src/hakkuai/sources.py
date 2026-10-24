"""
Government source handling and verification module for HakkuAI.
Manages official URLs, domain integrity, and source verification metadata.
"""

from urllib.parse import urlparse
from pydantic import BaseModel
from hakkuai.logging_config import logger

# Official trusted domains for Indian government portals
TRUSTED_GOV_DOMAINS = [
    "gov.in",
    "nic.in",
    "tn.gov.in",
    "karnataka.gov.in",
    "labour.gov.in",
    "eshram.gov.in",
    "pmjay.gov.in",
    "financialservices.gov.in",
    "indiacode.nic.in"
]

class SourceMetadata(BaseModel):
    title: str
    official_url: str
    issuing_authority: str
    state_or_central: str
    verified_date: str
    is_official_domain: bool
    live_lookup_performed: bool = False
    verification_notes: str

class SourceManager:
    """Manages official sources and ensures domain authenticity."""
    
    @staticmethod
    def is_official_gov_domain(url: str) -> bool:
        """Verifies if the URL domain is an official government domain."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            hostname = hostname.lower().strip()
            for domain in TRUSTED_GOV_DOMAINS:
                if hostname == domain or hostname.endswith("." + domain):
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {e}")
            return False

    @staticmethod
    def get_source_badge(url: str, is_live: bool = False) -> str:
        """Returns human-readable verification label for citations."""
        is_gov = SourceManager.is_official_gov_domain(url)
        gov_label = "Official Government Source (.gov.in / .nic.in)" if is_gov else "External Authority / Reference"
        lookup_label = "Live Verification" if is_live else "Local Verified Registry (Offline Verified)"
        return f"[{gov_label} | {lookup_label}]"

    @staticmethod
    def format_citation(title: str, url: str, authority: str, verified_date: str) -> str:
        """Creates a standardized citation string."""
        gov_tag = " [Official Gov Portal]" if SourceManager.is_official_gov_domain(url) else ""
        return (
            f"• **Source**: {title} ({authority}){gov_tag}\n"
            f"  Link: {url}\n"
            f"  Record Verification Date: {verified_date} (Local Knowledge Base; live lookup was not performed)"
        )
