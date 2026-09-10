import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from app.services.automation import JobPortalAdapter

logger = logging.getLogger(__name__)


class GenericAdapter(JobPortalAdapter):
    """
    Generic job portal adapter that works with any website via configurable CSS selectors.
    Useful for smaller job boards that don't have dedicated adapters.
    """

    RATE_LIMIT_DELAY = 2.0  # seconds between requests

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize with optional configuration for CSS selectors.

        config should contain:
        - base_url: Base URL of the job portal
        - selectors: Dict mapping field names to CSS selectors
        - rate_limit: Optional custom rate limit in seconds
        """
        self.config = config or {}
        self.base_url = self.config.get("base_url", "")
        self.selectors = self.config.get("selectors", {})
        self.rate_limit_delay = self.config.get("rate_limit", self.RATE_LIMIT_DELAY)

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._last_request_time: float = 0

    async def _initialize(self) -> None:
        """Initialize browser if not already running"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        if not self.browser:
            self.browser = await self.playwright.chromium.launch(headless=True)
        if not self.context:
            self.context = await self.browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
            )
        if not self.page:
            self.page = await self.context.new_page()

    async def _respect_rate_limit(self) -> None:
        """Enforce rate limiting between requests"""
        elapsed = datetime.now().timestamp() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = datetime.now().timestamp()

    async def _safe_query(self, selector: str) -> Optional[Any]:
        """Safely query an element, returning None if not found"""
        try:
            return await self.page.query_selector(selector)
        except Exception:
            return None

    async def _safe_text(self, selector: str) -> str:
        """Safely get text content from an element"""
        element = await self._safe_query(selector)
        if element:
            text = await element.inner_text()
            return text.strip() if text else ""
        return ""

    async def search_jobs(self, params: Dict[str, Any]) -> List[Dict]:
        """Search for jobs using configurable selectors"""
        await self._initialize()
        await self._respect_rate_limit()

        if not self.base_url:
            raise ValueError("base_url is required in config")

        logger.info(f"[Generic] Searching jobs at {self.base_url} with params: {params}")

        try:
            # Build search URL from config
            search_url = self.selectors.get("search_url_template", self.base_url)
            if params.get("keywords") and "{keywords}" in search_url:
                search_url = search_url.replace("{keywords}", params["keywords"])
            if params.get("location") and "{location}" in search_url:
                search_url = search_url.replace("{location}", params["location"])

            await self.page.goto(search_url, wait_until="networkidle")

            # Extract jobs using configured selectors
            jobs = []
            job_card_selector = self.selectors.get("job_card", ".job-card")
            job_cards = await self.page.query_selector_all(job_card_selector)

            for card in job_cards[: params.get("limit", 25)]:
                try:
                    job = {}
                    # Extract each field using configured selectors
                    for field, selector in self.selectors.items():
                        if field.startswith("job_") and field != "job_card":
                            field_name = field.replace("job_", "")
                            element = await card.query_selector(selector)
                            if element:
                                job[field_name] = (await element.inner_text()).strip()

                    # Try to get URL
                    link_selector = self.selectors.get("job_link", "a")
                    link = await card.query_selector(link_selector)
                    if link:
                        href = await link.get_attribute("href")
                        if href:
                            if href.startswith("http"):
                                job["url"] = href
                            else:
                                job["url"] = f"{self.base_url}{href}"

                    job["source"] = "generic"
                    jobs.append(job)

                except Exception as e:
                    logger.warning(f"[Generic] Error extracting job card: {e}")
                    continue

            logger.info(f"[Generic] Found {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"[Generic] Search failed: {e}")
            raise

    async def open_job(self, job_url: str) -> Dict:
        """Open and extract job details from any job page"""
        await self._initialize()
        await self._respect_rate_limit()

        try:
            await self.page.goto(job_url, wait_until="networkidle")
            return await self.extract_job(self.page)

        except Exception as e:
            logger.error(f"[Generic] Failed to open job: {e}")
            raise

    async def extract_job(self, page) -> Dict:
        """Extract job information using configured selectors"""
        try:
            job = {}
            # Extract each field using configured selectors
            for field, selector in self.selectors.items():
                if field.startswith("detail_"):
                    field_name = field.replace("detail_", "")
                    job[field_name] = await self._safe_text(selector)

            job["source"] = "generic"
            job["url"] = page.url
            job["extracted_at"] = datetime.utcnow().isoformat()

            return job

        except Exception as e:
            logger.error(f"[Generic] Error extracting job: {e}")
            return {}

    async def start_application(self, job_url: str) -> Dict:
        """Start application process"""
        await self._initialize()
        await self._respect_rate_limit()

        try:
            await self.page.goto(job_url, wait_until="networkidle")

            apply_selector = self.selectors.get("apply_button", 'button:has-text("Apply")')
            apply_btn = await self._safe_query(apply_selector)

            if apply_btn:
                await apply_btn.click()
                return {"status": "apply_started", "method": "generic"}

            return {"status": "no_apply_button", "error": "No apply button found"}

        except Exception as e:
            logger.error(f"[Generic] Failed to start application: {e}")
            raise

    async def fill_application(self, application_data: Dict) -> Dict:
        """Fill application form fields using configurable selectors"""
        await self._initialize()

        try:
            filled_fields = []
            for field_name, value in application_data.items():
                if field_name in ["resume_path", "cover_letter_path"]:
                    continue

                # Try multiple selector patterns
                selector_patterns = [
                    self.selectors.get(f"field_{field_name}"),
                    f'input[name="{field_name}"]',
                    f'textarea[name="{field_name}"]',
                    f'input[id="{field_name}"]',
                    f'#{field_name}',
                ]

                for selector in selector_patterns:
                    if not selector:
                        continue
                    element = await self._safe_query(selector)
                    if element:
                        await element.fill(str(value))
                        filled_fields.append(field_name)
                        break

            return {
                "status": "fields_filled",
                "filled_fields": filled_fields,
                "total_fields": len(application_data),
            }

        except Exception as e:
            logger.error(f"[Generic] Failed to fill application: {e}")
            raise

    async def upload_resume(self, file_path: str) -> bool:
        """Upload resume using configured selector"""
        await self._initialize()

        try:
            upload_selector = self.selectors.get(
                "upload_resume", 'input[type="file"]'
            )
            upload_input = await self._safe_query(upload_selector)
            if upload_input:
                await upload_input.set_input_files(file_path)
                return True
            return False

        except Exception as e:
            logger.error(f"[Generic] Failed to upload resume: {e}")
            return False

    async def submit_application(self) -> Dict:
        """Submit application using configured selector"""
        await self._initialize()

        try:
            submit_selector = self.selectors.get(
                "submit_button", 'button[type="submit"]'
            )
            submit_btn = await self._safe_query(submit_selector)
            if submit_btn:
                await submit_btn.click()
                await self.page.wait_for_load_state("networkidle")
                return {"status": "submitted", "timestamp": datetime.utcnow().isoformat()}

            return {"status": "no_submit_button", "error": "Submit button not found"}

        except Exception as e:
            logger.error(f"[Generic] Failed to submit application: {e}")
            raise

    async def capture_confirmation(self) -> Dict:
        """Capture submission confirmation using configured selector"""
        await self._initialize()

        try:
            confirmation_selector = self.selectors.get(
                "confirmation", ".confirmation"
            )
            confirmation = await self._safe_query(confirmation_selector)
            if confirmation:
                text = await confirmation.inner_text()
                return {
                    "status": "confirmed",
                    "message": text.strip(),
                    "timestamp": datetime.utcnow().isoformat(),
                }

            return {"status": "no_confirmation", "message": "No confirmation element found"}

        except Exception as e:
            logger.error(f"[Generic] Error capturing confirmation: {e}")
            return {"status": "error", "error": str(e)}

    async def close(self) -> None:
        """Close browser resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            logger.error(f"[Generic] Error closing resources: {e}")
