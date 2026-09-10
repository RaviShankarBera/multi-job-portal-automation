import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.services.ai import AIProvider
from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProviderError(Exception):
    """Base exception for OpenAI provider errors"""
    pass


class RateLimitError(OpenAIProviderError):
    """Rate limit exceeded"""
    pass


class APIError(OpenAIProviderError):
    """API call failed"""
    pass


class OpenAIProvider(AIProvider):
    """OpenAI API implementation of AIProvider"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.AI_MODEL
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. OpenAI provider may not work.")

    async def _get_redis(self):
        try:
            return await get_redis()
        except Exception:
            return None

    async def _get_cached(self, key: str) -> Optional[Dict]:
        redis = await self._get_redis()
        if redis:
            try:
                cached = await redis.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        return None

    async def _set_cached(self, key: str, data: Dict, ttl: int = 3600):
        redis = await self._get_redis()
        if redis:
            try:
                await redis.set(key, json.dumps(data), ex=ttl)
            except Exception:
                pass

    def _build_cache_key(self, prefix: str, *args) -> str:
        import hashlib
        content = json.dumps(args, sort_keys=True, default=str)
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"ai:{prefix}:{hash_val}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _call_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Call OpenAI API with retry logic and error handling"""
        if not self.api_key:
            raise OpenAIProviderError("OPENAI_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("retry-after", 60))
                    logger.warning(f"Rate limited. Retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    raise RateLimitError(f"Rate limited: {e.response.text}")
                logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
                raise APIError(f"API error: {e.response.status_code}")
            except httpx.ConnectError as e:
                logger.error(f"Connection error to OpenAI: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error calling OpenAI: {e}")
                raise OpenAIProviderError(str(e))

    def _extract_content(self, result: Dict) -> str:
        """Extract content from OpenAI response"""
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise OpenAIProviderError(f"Invalid response format: {e}")

    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON from AI response, handling markdown code blocks"""
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nContent: {content[:500]}")
            return {"raw_response": content}

    async def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        cache_key = self._build_cache_key("analyze_job", job_description[:500])
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert HR analyst. Analyze the job description and extract "
                    "structured data. Return a JSON object with: title, company, required_skills (array), "
                    "preferred_skills (array), experience_years (int or null), responsibilities (array), "
                    "qualifications (array), salary_range (object with min/max/currency or null), "
                    "remote_status ('remote', 'hybrid', 'onsite', or null), employment_type, "
                    "industry, key_requirements (summary string). "
                    "Return ONLY valid JSON, no additional text."
                ),
            },
            {
                "role": "user",
                "content": f"Analyze this job description:\n\n{job_description}",
            },
        ]

        result = await self._call_openai(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = self._extract_content(result)
        parsed = self._parse_json_response(content)

        await self._set_cached(cache_key, parsed, ttl=86400)
        return parsed

    async def match_resume_to_job(self, resume_data: Dict, job_data: Dict) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert career matching analyst. Compare the resume to the job "
                    "requirements and calculate detailed match scores. Return a JSON object with: "
                    "overall_score (0-100), skills_score (0-100), experience_score (0-100), "
                    "education_score (0-100), keyword_match_score (0-100), matching_skills (array), "
                    "missing_skills (array), matching_experience (array), "
                    "recommendations (array of strings), summary (string). "
                    "Be objective and data-driven. Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"RESUME DATA:\n{json.dumps(resume_data, default=str)}\n\n"
                    f"JOB DATA:\n{json.dumps(job_data, default=str)}"
                ),
            },
        ]

        result = await self._call_openai(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = self._extract_content(result)
        return self._parse_json_response(content)

    async def tailor_resume(self, resume_data: Dict, job_data: Dict, profile_data: Dict) -> Dict[str, Any]:
        cache_key = self._build_cache_key("tailor_resume", str(resume_data.get("id")), str(job_data.get("id")))
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert resume writer. Tailor the resume for the specific job. "
                    "IMPORTANT RULES:\n"
                    "- DO NOT fabricate experience, skills, or achievements that don't exist\n"
                    "- DO NOT add false dates, companies, or roles\n"
                    "- ONLY rephrase existing content to better match job keywords\n"
                    "- ONLY reorder sections to highlight most relevant experience\n"
                    "- ONLY suggest which skills to emphasize from existing ones\n"
                    "Return a JSON object with:\n"
                    "- tailored_summary: optimized professional summary\n"
                    "- tailored_skills: reordered/emphasized skills list\n"
                    "- tailored_experience: rephrased experience bullets\n"
                    "- tailored_education: rephrased education section\n"
                    "- ats_score: estimated ATS score (0-100)\n"
                    "- changes_made: array of changes with description and section\n"
                    "- original_vs_tailored: comparison object\n"
                    "Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"RESUME:\n{json.dumps(resume_data, default=str)}\n\n"
                    f"JOB:\n{json.dumps(job_data, default=str)}\n\n"
                    f"PROFILE:\n{json.dumps(profile_data, default=str)}"
                ),
            },
        ]

        result = await self._call_openai(
            messages=messages,
            temperature=0.5,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )

        content = self._extract_content(result)
        parsed = self._parse_json_response(content)

        await self._set_cached(cache_key, parsed, ttl=3600)
        return parsed

    async def generate_cover_letter(self, profile_data: Dict, resume_data: Dict, job_data: Dict) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional cover letter writer. Generate a personalized, "
                    "professional cover letter. Rules:\n"
                    "- Be specific to the job and company\n"
                    "- Highlight relevant experience from the resume\n"
                    "- Show enthusiasm and cultural fit\n"
                    "- Keep it under 400 words\n"
                    "- Use professional tone\n"
                    "- DO NOT fabricate achievements\n"
                    "- Format: greeting, 2-3 paragraphs, closing\n"
                    "Return ONLY the cover letter text, no JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"PROFILE:\n{json.dumps(profile_data, default=str)}\n\n"
                    f"RESUME:\n{json.dumps(resume_data, default=str)}\n\n"
                    f"JOB:\n{json.dumps(job_data, default=str)}"
                ),
            },
        ]

        result = await self._call_openai(
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        return self._extract_content(result)

    async def generate_application_answers(self, profile_data: Dict, job_data: Dict, questions: List[str]) -> Dict[str, str]:
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert career consultant. Answer job application questions "
                    "based on the profile and job. Rules:\n"
                    "- Be honest and use actual experience from profile\n"
                    "- Do NOT fabricate achievements\n"
                    "- Be specific and provide examples when possible\n"
                    "- Keep answers concise but complete\n"
                    "- Match the tone of the company\n"
                    "Return a JSON object where keys are question numbers (as strings) "
                    "and values are the answers. Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"PROFILE:\n{json.dumps(profile_data, default=str)}\n\n"
                    f"JOB:\n{json.dumps(job_data, default=str)}\n\n"
                    f"QUESTIONS:\n{questions_text}"
                ),
            },
        ]

        result = await self._call_openai(
            messages=messages,
            temperature=0.5,
            response_format={"type": "json_object"},
        )

        content = self._extract_content(result)
        return self._parse_json_response(content)

    async def analyze_skill_gap(self, user_skills: List[str], job_market_skills: List[str]) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a career development expert. Analyze skill gaps and provide "
                    "actionable recommendations. Return a JSON object with:\n"
                    "- strong_skills: skills user has that are in demand\n"
                    "- missing_skills: skills in demand that user lacks\n"
                    "- overlapping_skills: skills that align well\n"
                    "- priority_skills: top 5 skills to learn first (with reasoning)\n"
                    "- learning_recommendations: object mapping each missing skill to "
                    "{resource_type, resource_name, estimated_time, difficulty_level}\n"
                    "- overall_gap_score: 0-100 (100 = perfect match)\n"
                    "- summary: brief analysis summary\n"
                    "Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"USER SKILLS: {json.dumps(user_skills)}\n\n"
                    f"JOB MARKET SKILLS: {json.dumps(job_market_skills)}"
                ),
            },
        ]

        result = await self._call_openai(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = self._extract_content(result)
        return self._parse_json_response(content)

    async def generate_interview_questions(self, job_data: Dict, resume_data: Dict) -> List[Dict[str, str]]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert interview coach. Generate interview preparation "
                    "questions tailored to the job and resume. Return a JSON array of objects with:\n"
                    "- question: the interview question\n"
                    "- category: 'technical', 'behavioral', 'situational', or 'company'\n"
                    "- difficulty: 'easy', 'medium', or 'hard'\n"
                    "- tips: brief tips on how to answer\n"
                    "- suggested_answer_points: array of key points to cover\n"
                    "Generate 10-15 diverse questions. Return ONLY valid JSON array."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"JOB:\n{json.dumps(job_data, default=str)}\n\n"
                    f"RESUME:\n{json.dumps(resume_data, default=str)}"
                ),
            },
        ]

        result = await self._call_openai(
            messages=messages,
            temperature=0.5,
            max_tokens=3000,
        )

        content = self._extract_content(result)
        parsed = self._parse_json_response(content)
        if isinstance(parsed, list):
            return parsed
        return parsed.get("questions", [])

    async def extract_job_keywords(self, job_description: str) -> List[str]:
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract important keywords from this job description. Include:\n"
                    "- Technical skills and tools\n"
                    "- Soft skills\n"
                    "- Industry terms\n"
                    "- Required qualifications\n"
                    "- Job-specific terminology\n"
                    "Return a JSON array of unique keywords, ordered by importance. "
                    "Include 15-30 keywords. Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"Extract keywords from this job description:\n\n{job_description}",
            },
        ]

        result = await self._call_openai(
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = self._extract_content(result)
        parsed = self._parse_json_response(content)
        if isinstance(parsed, list):
            return parsed
        return parsed.get("keywords", [])
