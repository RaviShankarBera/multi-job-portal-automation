import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.automation import JobPortalAdapter
from app.services.automation.factory import AdapterFactory
from app.services.automation.linkedin import LinkedInAdapter
from app.services.automation.indeed import IndeedAdapter
from app.services.automation.generic import GenericAdapter


class TestAdapterFactory:
    def test_create_linkedin_adapter(self):
        """Test creating LinkedIn adapter"""
        adapter = AdapterFactory.create("linkedin")
        assert isinstance(adapter, LinkedInAdapter)

    def test_create_indeed_adapter(self):
        """Test creating Indeed adapter"""
        adapter = AdapterFactory.create("indeed")
        assert isinstance(adapter, IndeedAdapter)

    def test_create_generic_adapter(self):
        """Test creating Generic adapter"""
        config = {
            "base_url": "https://example.com",
            "selectors": {
                "job_card": ".job-item",
                "job_title": ".job-title",
            },
        }
        adapter = AdapterFactory.create("generic", config=config)
        assert isinstance(adapter, GenericAdapter)

    def test_create_unsupported_adapter(self):
        """Test that unsupported portal raises error"""
        with pytest.raises(ValueError, match="Unsupported portal"):
            AdapterFactory.create("unsupported_portal")

    def test_get_supported_portals(self):
        """Test getting list of supported portals"""
        portals = AdapterFactory.get_supported_portals()
        assert "linkedin" in portals
        assert "indeed" in portals
        assert "generic" in portals

    def test_is_supported(self):
        """Test checking if portal is supported"""
        assert AdapterFactory.is_supported("linkedin") is True
        assert AdapterFactory.is_supported("unsupported") is False

    def test_register_custom_adapter(self):
        """Test registering a custom adapter"""
        class CustomAdapter(JobPortalAdapter):
            async def search_jobs(self, params):
                return []

            async def open_job(self, job_url):
                return {}

            async def extract_job(self, page):
                return {}

            async def start_application(self, job_url):
                return {}

            async def fill_application(self, application_data):
                return {}

            async def upload_resume(self, file_path):
                return True

            async def submit_application(self):
                return {}

            async def capture_confirmation(self):
                return {}

            async def close(self):
                pass

        AdapterFactory.register("custom", CustomAdapter)
        assert "custom" in AdapterFactory.get_supported_portals()
        adapter = AdapterFactory.create("custom")
        assert isinstance(adapter, CustomAdapter)

    def test_register_invalid_adapter(self):
        """Test that registering non-adapter class raises error"""
        class NotAnAdapter:
            pass

        with pytest.raises(TypeError):
            AdapterFactory.register("invalid", NotAnAdapter)


class TestGenericAdapter:
    @pytest.fixture
    def config(self):
        return {
            "base_url": "https://example.com/jobs",
            "selectors": {
                "search_url_template": "https://example.com/jobs?q={keywords}&l={location}",
                "job_card": ".job-listing",
                "job_title": ".job-title a",
                "job_company": ".company-name",
                "job_location": ".job-location",
                "job_link": ".job-title a",
                "apply_button": ".apply-btn",
                "upload_resume": 'input[type="file"]',
                "submit_button": 'button[type="submit"]',
                "confirmation": ".success-message",
            },
            "rate_limit": 1.0,
        }

    @pytest.fixture
    def adapter(self, config):
        return GenericAdapter(config)

    def test_init_with_config(self, adapter, config):
        """Test adapter initialization with config"""
        assert adapter.base_url == config["base_url"]
        assert adapter.selectors == config["selectors"]
        assert adapter.rate_limit_delay == 1.0

    def test_init_without_config(self):
        """Test adapter initialization without config"""
        adapter = GenericAdapter()
        assert adapter.base_url == ""
        assert adapter.selectors == {}

    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test closing browser resources"""
        # Should not raise even without initialized browser
        await adapter.close()

    @pytest.mark.asyncio
    async def test_initialize(self, adapter):
        """Test browser initialization"""
        with patch("app.services.automation.generic.async_playwright") as mock_pw:
            mock_pw_instance = AsyncMock()
            mock_pw.return_value.start = AsyncMock(return_value=mock_pw_instance)

            mock_browser = AsyncMock()
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)

            await adapter._initialize()

            assert adapter.playwright is not None
            assert adapter.browser is not None
            assert adapter.context is not None
            assert adapter.page is not None


class TestLinkedInAdapter:
    @pytest.fixture
    def adapter(self):
        return LinkedInAdapter()

    def test_init(self, adapter):
        """Test LinkedIn adapter initialization"""
        assert adapter.BASE_URL == "https://www.linkedin.com"
        assert adapter.RATE_LIMIT_DELAY == 2.0

    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test closing browser resources"""
        await adapter.close()

    @pytest.mark.asyncio
    async def test_check_robots_txt(self, adapter):
        """Test robots.txt check"""
        result = await adapter._check_robots_txt()
        assert result is True


class TestIndeedAdapter:
    @pytest.fixture
    def adapter(self):
        return IndeedAdapter()

    def test_init(self, adapter):
        """Test Indeed adapter initialization"""
        assert adapter.BASE_URL == "https://www.indeed.com"
        assert adapter.RATE_LIMIT_DELAY == 3.0

    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test closing browser resources"""
        await adapter.close()

    @pytest.mark.asyncio
    async def test_check_robots_txt(self, adapter):
        """Test robots.txt check"""
        result = await adapter._check_robots_txt()
        assert result is True


class TestAdapterInterface:
    """Test that all adapters implement the required interface"""

    @pytest.mark.asyncio
    async def test_linkedin_has_all_methods(self):
        """Test LinkedIn adapter has all required methods"""
        adapter = LinkedInAdapter()
        assert hasattr(adapter, "search_jobs")
        assert hasattr(adapter, "open_job")
        assert hasattr(adapter, "extract_job")
        assert hasattr(adapter, "start_application")
        assert hasattr(adapter, "fill_application")
        assert hasattr(adapter, "upload_resume")
        assert hasattr(adapter, "submit_application")
        assert hasattr(adapter, "capture_confirmation")
        assert hasattr(adapter, "close")

    @pytest.mark.asyncio
    async def test_indeed_has_all_methods(self):
        """Test Indeed adapter has all required methods"""
        adapter = IndeedAdapter()
        assert hasattr(adapter, "search_jobs")
        assert hasattr(adapter, "open_job")
        assert hasattr(adapter, "extract_job")
        assert hasattr(adapter, "start_application")
        assert hasattr(adapter, "fill_application")
        assert hasattr(adapter, "upload_resume")
        assert hasattr(adapter, "submit_application")
        assert hasattr(adapter, "capture_confirmation")
        assert hasattr(adapter, "close")

    @pytest.mark.asyncio
    async def test_generic_has_all_methods(self):
        """Test Generic adapter has all required methods"""
        adapter = GenericAdapter()
        assert hasattr(adapter, "search_jobs")
        assert hasattr(adapter, "open_job")
        assert hasattr(adapter, "extract_job")
        assert hasattr(adapter, "start_application")
        assert hasattr(adapter, "fill_application")
        assert hasattr(adapter, "upload_resume")
        assert hasattr(adapter, "submit_application")
        assert hasattr(adapter, "capture_confirmation")
        assert hasattr(adapter, "close")
