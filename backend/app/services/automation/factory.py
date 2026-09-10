import logging
from typing import Dict, Any, Optional

from app.services.automation import JobPortalAdapter

logger = logging.getLogger(__name__)

try:
    from app.services.automation.linkedin import LinkedInAdapter
    from app.services.automation.indeed import IndeedAdapter
    from app.services.automation.generic import GenericAdapter
    PLAYWRIGHT_ADAPTERS_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_ADAPTERS_AVAILABLE = False
    logger.warning("Playwright not installed. Browser automation adapters disabled. Install with: pip install playwright && playwright install")


class AdapterFactory:
    """Factory for creating job portal adapters"""

    _adapters = {}

    if PLAYWRIGHT_ADAPTERS_AVAILABLE:
        _adapters = {
            "linkedin": LinkedInAdapter,
            "indeed": IndeedAdapter,
            "generic": GenericAdapter,
        }

    @classmethod
    def create(cls, portal_name: str, config: Optional[Dict[str, Any]] = None) -> JobPortalAdapter:
        portal_lower = portal_name.lower()

        if not PLAYWRIGHT_ADAPTERS_AVAILABLE:
            raise ValueError(
                "Playwright is not installed. Install with: pip install playwright && playwright install"
            )

        if portal_lower not in cls._adapters:
            supported = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported portal: {portal_name}. Supported portals: {supported}"
            )

        adapter_class = cls._adapters[portal_lower]
        logger.info(f"[AdapterFactory] Creating adapter for: {portal_name}")

        if portal_lower == "generic":
            return adapter_class(config=config)

        return adapter_class()

    @classmethod
    def register(cls, name: str, adapter_class: type) -> None:
        if not issubclass(adapter_class, JobPortalAdapter):
            raise TypeError(f"{adapter_class} must be a subclass of JobPortalAdapter")
        cls._adapters[name.lower()] = adapter_class
        logger.info(f"[AdapterFactory] Registered adapter: {name}")

    @classmethod
    def get_supported_portals(cls) -> list:
        return list(cls._adapters.keys())

    @classmethod
    def is_supported(cls, portal_name: str) -> bool:
        return portal_name.lower() in cls._adapters
