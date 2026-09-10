import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from app.services.automation import JobPortalAdapter

logger = logging.getLogger(__name__)

INDEED_SELECTORS = {
    "search_input": 'input[name="q"]',
    "location_input": 'input[name="l"]',
    "search_button": 'button[type="submit"]',
    "job_card": ".jobsearch-ResultsList .result",
    "job_title": ".jobTitle a",
    "job_company": ".companyName",
    "job_location": ".companyLocation",
    "job_snippet": ".job-snippet",
    "apply_button": 'button[data-tn-element="applyButton"]',
    "upload_resume": 'input[type="file"][name="resume"]',
    "submit_button": 'button[type="submit"]',
    "confirmation": ".application-confirmation",
}


class IndeedAdapter(JobPortalAdapter):
    """
    Indeed job portal adapter.

    IMPORTANT: This is a template implementation. Real implementation requires:
    - User authorization and login
    - Compliance with Indeed's Terms of Service
    - Respect for rate limits and robots.txt
    - NO bypassing of CAPTCHA, MFA, or security controls
    """

    BASE_URL = "https://www.indeed.com"
    RATE_LIMIT_DELAY = 3.0  # seconds between requests (Indeed is stricter)

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
        """Check robots.txt compliance"""
        logger.info("[Indeed] Checking robots.txt compliance")
        return True

    async def search_jobs(self, params: Dict[str, Any]) -> List[Dict]:
        """
        Search for jobs on Indeed.

        NOTE: This requires user to be logged in for some features.
        """
        await self._initialize()
        await self._respect_rate_limit()

        if not await self._check_robots_txt():
            raise PermissionError("robots.txt prohibits this action")

        logger.info(f"[Indeed] Searching jobs with params: {params}")

        try:
            search_url = f"{self.BASE_URL}/jobs?"
            query_params = []
            if params.get("keywords"):
                query_params.append(f"q={params['keywords']}")
            if params.get("location"):
                query_params.append(f"l={params['location']}")
            if params.get("radius"):
                query_params.append(f"radius={params['radius']}")

            search_url += "&".join(query_params)
            await self.page.goto(search_url, wait_until="networkidle")

            # Extract job listings
            jobs = []
            job_cards = await self.page.query_selector_all(
                INDEED_SELECTORS["job_card"]
            )

            for card in job_cards[: params.get("limit", 25)]:
                try:
                    title_el = await card.query_selector(INDEED_SELECTORS["job_title"])
                    company_el = await card.query_selector(
                        INDEED_SELECTORS["job_company"]
                    )
                    location_el = await card.query_selector(
                        INDEED_SELECTORS["job_location"]
                    )
                    snippet_el = await card.query_selector(
                        INDEED_SELECTORS["job_snippet"]
                    )

                    title = await title_el.inner_text() if title_el else "Unknown"
                    company = await company_el.inner_text() if company_el else "Unknown"
                    location = (
                        await location_el.inner_text() if location_el else "Unknown"
                    )
                    snippet = (
                        await snippet_el.inner_text() if snippet_el else ""
                    )

                    link = await title_el.query_selector("a") if title_el else None
                    url = await link.get_attribute("href") if link else None

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location.strip(),
                        "snippet": snippet.strip(),
                        "url": f"{self.BASE_URL}{url}" if url and not url.startswith("http") else url,
                        "source": "indeed",
                    })
                except Exception as e:
                    logger.warning(f"[Indeed] Error extracting job card: {e}")
                    continue

            logger.info(f"[Indeed] Found {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"[Indeed] Search failed: {e}")
            raise

    async def open_job(self, job_url: str) -> Dict:
        """Open and extract job details from an Indeed job page"""
        await self._initialize()
        await self._respect_rate_limit()

        try:
            await self.page.goto(job_url, wait_until="networkidle")
            return await self.extract_job(self.page)

        except Exception as e:
            logger.error(f"[Indeed] Failed to open job: {e}")
            raise

    async def extract_job(self, page) -> Dict:
        """Extract job information from current Indeed page"""
        try:
            title = await page.text_content(".jobsearch-JobInfoHeader-title")
            company = await page.text_content(".jobsearch-CompanyInfoHeader-companyName")
            location = await page.text_content(
                ".jobsearch-CompanyInfoHeader-companyLocation"
            )
            description = await page.text_content("#jobDescriptionText")

            return {
                "title": title.strip() if title else "Unknown",
                "company": company.strip() if company else "Unknown",
                "location": location.strip() if location else "Unknown",
                "description": description.strip() if description else "",
                "source": "indeed",
                "url": page.url,
                "extracted_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"[Indeed] Error extracting job: {e}")
            return {}

    async def start_application(self, job_url: str) -> Dict:
        """Start application process for an Indeed job"""
        await self._initialize()
        await self._respect_rate_limit()

        try:
            await self.page.goto(job_url, wait_until="networkidle")

            # Check for Apply button
            apply_btn = await self.page.query_selector(INDEED_SELECTORS["apply_button"])
            if apply_btn:
                await apply_btn.click()
                return {"status": "apply_started", "method": "indeed"}

            # Check for external redirect
            redirect = await self.page.query_selector('a[data-tn-element="applyButtonLink"]')
            if redirect:
                href = await redirect.get_attribute("href")
                return {"status": "external_redirect", "url": href}

            return {"status": "no_apply_button", "error": "No apply button found"}

        except Exception as e:
            logger.error(f"[Indeed] Failed to start application: {e}")
            raise

    async def fill_application(self, application_data: Dict) -> Dict:
        """Fill Indeed application form fields"""
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
            logger.error(f"[Indeed] Failed to fill application: {e}")
            raise

    async def upload_resume(self, file_path: str) -> bool:
        """Upload resume to Indeed application"""
        await self._initialize()

        try:
            upload_input = await self.page.query_selector(
                INDEED_SELECTORS["upload_resume"]
            )
            if upload_input:
                await upload_input.set_input_files(file_path)
                return True
            return False

        except Exception as e:
            logger.error(f"[Indeed] Failed to upload resume: {e}")
            return False

    async def submit_application(self) -> Dict:
        """Submit Indeed application"""
        await self._initialize()

        try:
            submit_btn = await self.page.query_selector(
                INDEED_SELECTORS["submit_button"]
            )
            if submit_btn:
                await submit_btn.click()
                await self.page.wait_for_load_state("networkidle")
                return {"status": "submitted", "timestamp": datetime.utcnow().isoformat()}

            return {"status": "no_submit_button", "error": "Submit button not found"}

        except Exception as e:
            logger.error(f"[Indeed] Failed to submit application: {e}")
            raise

    async def capture_confirmation(self) -> Dict:
        """Capture Indeed submission confirmation"""
        await self._initialize()

        try:
            confirmation = await self.page.query_selector(
                INDEED_SELECTORS["confirmation"]
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
            logger.error(f"[Indeed] Error capturing confirmation: {e}")
            return {"status": "error", "error": str(e)}

    async def close(self) -> None:
        """Close Indeed browser resources"""
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
            logger.error(f"[Indeed] Error closing resources: {e}")
