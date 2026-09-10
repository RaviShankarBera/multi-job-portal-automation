import logging
from typing import Dict, Any, Optional

from app.services.automation import JobPortalAdapter
from app.services.automation.linkedin import LinkedInAdapter
from app.services.automation.indeed import IndeedAdapter
from app.services.automation.generic import GenericAdapter

logger = logging.getLogger(__name__)


class AdapterFactory:
    """Factory for creating job portal adapters"""

    _adapters = {
        "linkedin": LinkedInAdapter,
        "indeed": IndeedAdapter,
        "generic": GenericAdapter,
    }

    @classmethod
    def create(cls, portal_name: str, config: Optional[Dict[str, Any]] = None) -> JobPortalAdapter:
        """
        Create an adapter for the specified portal.

        Args:
            portal_name: Name of the portal (linkedin, indeed, generic)
            config: Optional configuration for the adapter

        Returns:
            JobPortalAdapter instance

        Raises:
            ValueError: If portal_name is not supported
        """
        portal_lower = portal_name.lower()

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
        """
        Register a new adapter class.

        Args:
            name: Name to register under
            adapter_class: Class that implements JobPortalAdapter
        """
        if not issubclass(adapter_class, JobPortalAdapter):
            raise TypeError(f"{adapter_class} must be a subclass of JobPortalAdapter")

        cls._adapters[name.lower()] = adapter_class
        logger.info(f"[AdapterFactory] Registered adapter: {name}")

    @classmethod
    def get_supported_portals(cls) -> list:
        """Get list of supported portal names"""
        return list(cls._adapters.keys())

    @classmethod
    def is_supported(cls, portal_name: str) -> bool:
        """Check if a portal is supported"""
        return portal_name.lower() in cls._adapters
