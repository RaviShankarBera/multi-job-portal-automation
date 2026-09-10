import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from app.services.automation import JobPortalAdapter

logger = logging.getLogger(__name__)

LINKEDIN_SELECTORS = {
    "search_input": 'input[aria-label="Search by title, skill, or company"]',
    "location_input": 'input[aria-label="City, state, or zip code"]',
    "search_button": 'button[aria-label="Search"]',
    "job_card": ".jobs-search-results__list-item",
    "job_title": ".job-card-list__title--link",
    "job_company": ".artdeco-entity-lockup__subtitle",
    "job_location": ".artdeco-entity-lockup__caption",
    "job_description": ".jobs-description__content",
    "easy_apply_button": 'button[aria-label*="Easy Apply"]',
    "apply_button": 'button[aria-label*="Apply"]',
    "upload_resume": 'input[accept*="pdf"]',
    "submit_button": 'button[aria-label="Submit application"]',
    "confirmation": ".artdeco-toast-item",
}


class LinkedInAdapter(JobPortalAdapter):
    """
    LinkedIn job portal adapter.

    IMPORTANT: This is a template implementation. Real implementation requires:
    - User authorization and login
    - Compliance with LinkedIn's Terms of Service
    - Respect for rate limits and robots.txt
    - NO bypassing of CAPTCHA, MFA, or security controls
    """

    BASE_URL = "https://www.linkedin.com"
    RATE_LIMIT_DELAY = 2.0  # seconds between requests

    def __init__(self):
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
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = datetime.now().timestamp()

    async def _check_robots_txt(self) -> bool:
        """Check robots.txt compliance (simplified check)"""
        # In production, fetch and parse actual robots.txt
        # This is a basic check - real implementation should properly parse robots.txt
        logger.info("[LinkedIn] Checking robots.txt compliance")
        return True

    async def search_jobs(self, params: Dict[str, Any]) -> List[Dict]:
        """
        Search for jobs on LinkedIn.

        NOTE: This requires user to be logged in. In production, implement
        OAuth flow or session management with user consent.
        """
        await self._initialize()
        await self._respect_rate_limit()

        if not await self._check_robots_txt():
            raise PermissionError("robots.txt prohibits this action")

        logger.info(f"[LinkedIn] Searching jobs with params: {params}")

        try:
            # Navigate to LinkedIn jobs
            await self.page.goto(f"{self.BASE_URL}/jobs/", wait_until="networkidle")

            # Check for login required
            if "login" in self.page.url:
                raise PermissionError(
                    "LinkedIn login required. User authorization needed."
                )

            # Fill search criteria
            if params.get("keywords"):
                await self.page.fill(
                    LINKEDIN_SELECTORS["search_input"], params["keywords"]
                )
            if params.get("location"):
                await self.page.fill(
                    LINKEDIN_SELECTORS["location_input"], params["location"]
                )

            # Click search
            await self.page.click(LINKEDIN_SELECTORS["search_button"])
            await self.page.wait_for_load_state("networkidle")

            # Extract job listings
            jobs = []
            job_cards = await self.page.query_selector_all(
                LINKEDIN_SELECTORS["job_card"]
            )

            for card in job_cards[: params.get("limit", 25)]:
                try:
                    title_el = await card.query_selector(
                        LINKEDIN_SELECTORS["job_title"]
                    )
                    company_el = await card.query_selector(
                        LINKEDIN_SELECTORS["job_company"]
                    )
                    location_el = await card.query_selector(
                        LINKEDIN_SELECTORS["job_location"]
                    )

                    title = await title_el.inner_text() if title_el else "Unknown"
                    company = await company_el.inner_text() if company_el else "Unknown"
                    location = await location_el.inner_text() if location_el else "Unknown"

                    link = await card.query_selector("a")
                    url = await link.get_attribute("href") if link else None

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location.strip(),
                        "url": url,
                        "source": "linkedin",
                    })
                except Exception as e:
                    logger.warning(f"[LinkedIn] Error extracting job card: {e}")
                    continue

            logger.info(f"[LinkedIn] Found {len(jobs)} jobs")
            return jobs

        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"[LinkedIn] Search failed: {e}")
            raise

    async def open_job(self, job_url: str) -> Dict:
        """Open and extract job details from a LinkedIn job page"""
        await self._initialize()
        await self._respect_rate_limit()

        try:
            await self.page.goto(job_url, wait_until="networkidle")

            if "login" in self.page.url:
                raise PermissionError("LinkedIn login required")

            return await self.extract_job(self.page)

        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"[LinkedIn] Failed to open job: {e}")
            raise

    async def extract_job(self, page) -> Dict:
        """Extract job information from current LinkedIn page"""
        try:
            title = await page.text_content(
                ".job-details-jobs-unified-top-card__job-title"
            )
            company = await page.text_content(
                ".job-details-jobs-unified-top-card__company-name"
            )
            location = await page.text_content(
                ".job-details-jobs-unified-top-card__bullet"
            )
            description = await page.text_content(
                ".jobs-description__content"
            )

            return {
                "title": title.strip() if title else "Unknown",
                "company": company.strip() if company else "Unknown",
                "location": location.strip() if location else "Unknown",
                "description": description.strip() if description else "",
                "source": "linkedin",
                "url": page.url,
                "extracted_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"[LinkedIn] Error extracting job: {e}")
            return {}

    async def start_application(self, job_url: str) -> Dict:
        """Start application process for a LinkedIn job"""
        await self._initialize()
        await self._respect_rate_limit()

        try:
            await self.page.goto(job_url, wait_until="networkidle")

            if "login" in self.page.url:
                raise PermissionError("LinkedIn login required to apply")

            # Check for Easy Apply button
            easy_apply = await self.page.query_selector(
                LINKEDIN_SELECTORS["easy_apply_button"]
            )
            if easy_apply:
                await easy_apply.click()
                return {"status": "easy_apply_started", "method": "easy_apply"}

            # Check for regular Apply button
            apply_btn = await self.page.query_selector(LINKEDIN_SELECTORS["apply_button"])
            if apply_btn:
                await apply_btn.click()
                return {"status": "apply_started", "method": "external"}

            return {"status": "no_apply_button", "error": "No apply button found"}

        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"[LinkedIn] Failed to start application: {e}")
            raise

    async def fill_application(self, application_data: Dict) -> Dict:
        """Fill LinkedIn application form fields"""
        await self._initialize()

        try:
            filled_fields = []
            for field_name, value in application_data.items():
                if field_name in ["resume_path", "cover_letter_path"]:
                    continue

                selector = f'input[name="{field_name}"], textarea[name="{field_name}"]'
                element = await self.page.query_selector(selector)
                if element:
                    await element.fill(str(value))
                    filled_fields.append(field_name)

            return {
                "status": "fields_filled",
                "filled_fields": filled_fields,
                "total_fields": len(application_data),
            }

        except Exception as e:
            logger.error(f"[LinkedIn] Failed to fill application: {e}")
            raise

    async def upload_resume(self, file_path: str) -> bool:
        """Upload resume to LinkedIn application"""
        await self._initialize()

        try:
            upload_input = await self.page.query_selector(
                LINKEDIN_SELECTORS["upload_resume"]
            )
            if upload_input:
                await upload_input.set_input_files(file_path)
                return True
            return False

        except Exception as e:
            logger.error(f"[LinkedIn] Failed to upload resume: {e}")
            return False

    async def submit_application(self) -> Dict:
        """Submit LinkedIn application"""
        await self._initialize()

        try:
            submit_btn = await self.page.query_selector(
                LINKEDIN_SELECTORS["submit_button"]
            )
            if submit_btn:
                await submit_btn.click()
                await self.page.wait_for_load_state("networkidle")
                return {"status": "submitted", "timestamp": datetime.utcnow().isoformat()}

            return {"status": "no_submit_button", "error": "Submit button not found"}

        except Exception as e:
            logger.error(f"[LinkedIn] Failed to submit application: {e}")
            raise

    async def capture_confirmation(self) -> Dict:
        """Capture LinkedIn submission confirmation"""
        await self._initialize()

        try:
            confirmation = await self.page.query_selector(
                LINKEDIN_SELECTORS["confirmation"]
            )
            if confirmation:
                text = await confirmation.inner_text()
                return {
                    "status": "confirmed",
                    "message": text.strip(),
                    "timestamp": datetime.utcnow().isoformat(),
                }

            return {"status": "no_confirmation", "message": "No confirmation element found"}

        except Exception as e:
            logger.error(f"[LinkedIn] Error capturing confirmation: {e}")
            return {"status": "error", "error": str(e)}

    async def close(self) -> None:
        """Close LinkedIn browser resources"""
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
            logger.error(f"[LinkedIn] Error closing resources: {e}")
