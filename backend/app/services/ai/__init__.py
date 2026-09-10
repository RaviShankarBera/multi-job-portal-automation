from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """Analyze a job description and extract structured data"""
        pass

    @abstractmethod
    async def match_resume_to_job(self, resume_data: Dict, job_data: Dict) -> Dict[str, Any]:
        """Calculate detailed match between resume and job"""
        pass

    @abstractmethod
    async def tailor_resume(self, resume_data: Dict, job_data: Dict, profile_data: Dict) -> Dict[str, Any]:
        """Generate tailored resume content for a specific job"""
        pass

    @abstractmethod
    async def generate_cover_letter(self, profile_data: Dict, resume_data: Dict, job_data: Dict) -> str:
        """Generate a job-specific cover letter"""
        pass

    @abstractmethod
    async def generate_application_answers(self, profile_data: Dict, job_data: Dict, questions: List[str]) -> Dict[str, str]:
        """Generate answers to application questions"""
        pass

    @abstractmethod
    async def analyze_skill_gap(self, user_skills: List[str], job_market_skills: List[str]) -> Dict[str, Any]:
        """Analyze skill gaps between user and job market"""
        pass

    @abstractmethod
    async def generate_interview_questions(self, job_data: Dict, resume_data: Dict) -> List[Dict[str, str]]:
        """Generate interview preparation questions"""
        pass

    @abstractmethod
    async def extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract important keywords from job description"""
        pass
