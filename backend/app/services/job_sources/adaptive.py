import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import httpx

from app.services.job_sources import JobSourceAdapter

logger = logging.getLogger(__name__)


class AdaptiveJobAdapter(JobSourceAdapter):
    """Generic adapter for RSS feeds and public job APIs"""

    def __init__(
        self,
        source_name: str,
        base_url: str,
        feed_url: Optional[str] = None,
        api_url: Optional[str] = None,
        headers: Optional[dict] = None,
        parsing_rules: Optional[dict] = None,
    ):
        super().__init__(source_name)
        self.base_url = base_url
        self.feed_url = feed_url
        self.api_url = api_url
        self.headers = headers or {}
        self.parsing_rules = parsing_rules or {}

    async def search_jobs(self, params: dict) -> List[dict]:
        jobs = []
        if self.feed_url:
            jobs = await self._fetch_rss_feed(params)
        elif self.api_url:
            jobs = await self._fetch_api(params)
        return [self.normalize_job(job) for job in jobs]

    async def _fetch_rss_feed(self, params: dict) -> List[dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.feed_url, headers=self.headers)
                response.raise_for_status()
                return self._parse_rss(response.text)
        except Exception as e:
            logger.error(f"Error fetching RSS feed from {self.feed_url}: {e}")
            return []

    async def _fetch_api(self, params: dict) -> List[dict]:
        try:
            query_params = {}
            if "keywords" in params and params["keywords"]:
                keyword_field = self.parsing_rules.get("keyword_field", "q")
                query_params[keyword_field] = params["keywords"]
            if "location" in params and params["location"]:
                location_field = self.parsing_rules.get("location_field", "location")
                query_params[location_field] = params["location"]

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.api_url, params=query_params, headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_api_response(data)
        except Exception as e:
            logger.error(f"Error fetching from API {self.api_url}: {e}")
            return []

    def _parse_rss(self, xml_content: str) -> List[dict]:
        jobs = []
        try:
            root = ET.fromstring(xml_content)
            item_tag = self.parsing_rules.get("item_tag", "item")
            for item in root.iter(item_tag):
                job = {
                    "title": self._get_rss_field(item, "title"),
                    "company": self._get_rss_field(item, "company"),
                    "location": self._get_rss_field(item, "location"),
                    "description": self._get_rss_field(item, "description"),
                    "url": self._get_rss_field(item, "link"),
                    "posted_date": self._parse_date(
                        self._get_rss_field(item, "pubDate")
                    ),
                }
                if job["title"]:
                    jobs.append(job)
        except ET.ParseError as e:
            logger.error(f"Error parsing RSS XML: {e}")
        return jobs

    def _get_rss_field(self, element: ET.Element, field_name: str) -> str:
        field_mapping = self.parsing_rules.get("field_mapping", {})
        tag_name = field_mapping.get(field_name, field_name)
        child = element.find(tag_name)
        return child.text.strip() if child is not None and child.text else ""

    def _parse_api_response(self, data: dict) -> List[dict]:
        jobs = []
        results_key = self.parsing_rules.get("results_key", "results")
        items = data.get(results_key, data) if isinstance(data, dict) else data

        if isinstance(items, list):
            field_map = self.parsing_rules.get("field_mapping", {})
            for item in items:
                job = {
                    "title": item.get(field_map.get("title", "title"), ""),
                    "company": item.get(field_map.get("company", "company"), ""),
                    "location": item.get(field_map.get("location", "location"), ""),
                    "description": item.get(
                        field_map.get("description", "description"), ""
                    ),
                    "url": item.get(field_map.get("url", "url"), ""),
                }
                if job["title"]:
                    jobs.append(job)
        return jobs

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    async def get_job_details(self, job_id: str) -> Optional[dict]:
        return None
