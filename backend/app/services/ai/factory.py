import logging
from app.services.ai import AIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """Factory for creating AI provider instances"""

    _providers = {
        "openai": "app.services.ai.openai_provider.OpenAIProvider",
        "mock": "app.services.ai.mock_provider.MockAIProvider",
    }

    @staticmethod
    def create(provider_name: str = None) -> AIProvider:
        if provider_name is None:
            provider_name = settings.AI_PROVIDER

        provider_name = provider_name.lower().strip()

        if provider_name not in AIProviderFactory._providers:
            raise ValueError(
                f"Unknown AI provider: {provider_name}. "
                f"Available providers: {list(AIProviderFactory._providers.keys())}"
            )

        class_path = AIProviderFactory._providers[provider_name]
        module_path, class_name = class_path.rsplit(".", 1)

        try:
            import importlib
            module = importlib.import_module(module_path)
            provider_class = getattr(module, class_name)
            provider = provider_class()
            logger.info(f"Created AI provider: {provider_name}")
            return provider
        except ImportError as e:
            logger.error(f"Failed to import AI provider {provider_name}: {e}")
            raise
        except AttributeError as e:
            logger.error(f"Failed to load AI provider class {class_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create AI provider {provider_name}: {e}")
            raise

    @staticmethod
    def register_provider(name: str, class_path: str):
        AIProviderFactory._providers[name] = class_path

    @staticmethod
    def list_providers():
        return list(AIProviderFactory._providers.keys())
