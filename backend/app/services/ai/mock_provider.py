import json
import random
from typing import Dict, Any, List
import logging

from app.services.ai import AIProvider

logger = logging.getLogger(__name__)


class MockAIProvider(AIProvider):
    """Mock AI provider for development and testing"""

    def __init__(self):
        logger.info("Using MockAIProvider - no external API calls")

    async def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        logger.info("MockAIProvider: analyze_job_description called")
        words = job_description.lower().split()

        skills = []
        skill_keywords = [
            "python", "javascript", "react", "node.js", "sql", "aws", "docker",
            "kubernetes", "git", "agile", "java", "typescript", "mongodb", "postgresql",
            "redis", "graphql", "rest", "api", "microservices", "ci/cd", "linux",
            "machine learning", "data analysis", "tensorflow", "pytorch",
        ]
        for skill in skill_keywords:
            if skill in words or skill.replace(".", "") in job_description.lower():
                skills.append(skill)

        if not skills:
            skills = random.sample(["python", "javascript", "react", "sql", "aws"], 3)

        experience_match = None
        for i, word in enumerate(words):
            if word.isdigit() and i > 0 and any(exp in words[max(0, i - 2):i + 2] for exp in ["years", "year", "experience"]):
                experience_match = int(word)
                break

        return {
            "title": "Senior Software Engineer",
            "company": "Tech Company",
            "required_skills": skills[:5],
            "preferred_skills": skills[5:] if len(skills) > 5 else skills[:2],
            "experience_years": experience_match or 3,
            "responsibilities": [
                "Design and develop scalable software solutions",
                "Collaborate with cross-functional teams",
                "Write clean, maintainable code",
                "Participate in code reviews",
                "Contribute to technical documentation",
            ],
            "qualifications": [
                "Bachelor's degree in Computer Science or related field",
                f"Experience with {', '.join(skills[:3])}",
                "Strong problem-solving skills",
                "Excellent communication abilities",
            ],
            "salary_range": {"min": 90000, "max": 140000, "currency": "USD"},
            "remote_status": "hybrid",
            "employment_type": "full-time",
            "industry": "Technology",
            "key_requirements": f"Looking for a skilled developer with experience in {', '.join(skills[:3])}",
        }

    async def match_resume_to_job(self, resume_data: Dict, job_data: Dict) -> Dict[str, Any]:
        logger.info("MockAIProvider: match_resume_to_job called")

        resume_skills = set()
        if isinstance(resume_data.get("structured_data"), dict):
            resume_skills = set(resume_data["structured_data"].get("skills", []))
        elif isinstance(resume_data.get("skills"), list):
            resume_skills = set(resume_data["skills"])

        job_skills = set(job_data.get("required_skills", []))
        if isinstance(job_skills, str):
            job_skills = set(json.loads(job_skills)) if job_skills.startswith("[") else {job_skills}
        else:
            job_skills = set(job_skills)

        matching = resume_skills & job_skills
        missing = job_skills - resume_skills

        skills_score = len(matching) / max(len(job_skills), 1) * 100

        return {
            "overall_score": round(min(skills_score + 15, 95), 1),
            "skills_score": round(skills_score, 1),
            "experience_score": round(random.uniform(60, 90), 1),
            "education_score": round(random.uniform(70, 95), 1),
            "keyword_match_score": round(skills_score * 0.9, 1),
            "matching_skills": list(matching),
            "missing_skills": list(missing),
            "matching_experience": [
                "Relevant project experience",
                "Related internship work",
            ],
            "recommendations": [
                f"Highlight experience with {', '.join(list(matching)[:3])}",
                f"Consider learning {', '.join(list(missing)[:2])}",
                "Quantify achievements with metrics",
            ],
            "summary": f"Strong match with {len(matching)} out of {len(job_skills)} required skills.",
        }

    async def tailor_resume(self, resume_data: Dict, job_data: Dict, profile_data: Dict) -> Dict[str, Any]:
        logger.info("MockAIProvider: tailor_resume called")

        job_skills = job_data.get("required_skills", [])
        if isinstance(job_skills, str):
            job_skills = json.loads(job_skills) if job_skills.startswith("[") else [job_skills]

        summary = profile_data.get("current_title", "Software Engineer")
        years = profile_data.get("years_of_experience", 5)
        location = profile_data.get("location", "Remote")

        return {
            "tailored_summary": f"Experienced {summary} with {years}+ years of expertise in "
            f"{', '.join(job_skills[:3])}. Based in {location}, bringing a proven track record "
            "of delivering high-quality solutions.",
            "tailored_skills": job_skills[:10],
            "tailored_experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "bullets": [
                        f"Led development of applications using {job_skills[0] if job_skills else 'modern technologies'}",
                        "Improved system performance by 40% through optimization",
                        "Mentored junior developers and conducted code reviews",
                    ],
                }
            ],
            "tailored_education": profile_data.get("education", []),
            "ats_score": round(random.uniform(75, 95), 1),
            "changes_made": [
                {
                    "section": "summary",
                    "description": "Tailored summary to emphasize relevant skills",
                },
                {
                    "section": "skills",
                    "description": f"Reordered skills to prioritize {', '.join(job_skills[:3])}",
                },
            ],
            "original_vs_tailored": {
                "original_ats_score": round(random.uniform(50, 70), 1),
                "tailored_ats_score": round(random.uniform(75, 95), 1),
                "keyword_improvement": f"+{random.randint(5, 15)}%",
            },
        }

    async def generate_cover_letter(self, profile_data: Dict, resume_data: Dict, job_data: Dict) -> str:
        logger.info("MockAIProvider: generate_cover_letter called")

        name = profile_data.get("name", "Applicant")
        title = job_data.get("title", "Software Engineer")
        company = job_data.get("company", "Your Company")

        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}. With my background in software development and passion for creating innovative solutions, I am confident I would be a valuable addition to your team.

Throughout my career, I have developed expertise in building scalable applications and collaborating with cross-functional teams. My experience includes working with modern technologies and delivering high-quality solutions that meet business objectives.

I am particularly drawn to {company}'s mission and values, and I believe my skills align well with your requirements. I am excited about the opportunity to contribute to your team's success and grow professionally.

Thank you for considering my application. I look forward to discussing how I can contribute to {company}.

Best regards,
{name}"""

    async def generate_application_answers(self, profile_data: Dict, job_data: Dict, questions: List[str]) -> Dict[str, str]:
        logger.info("MockAIProvider: generate_application_answers called")

        answers = {}
        for i, question in enumerate(questions, 1):
            answers[str(i)] = (
                f"Based on my experience and qualifications, I believe I am well-suited for this "
                f"role. My background in {profile_data.get('current_title', 'software development')} "
                f"has prepared me to handle the challenges described in this position."
            )
        return answers

    async def analyze_skill_gap(self, user_skills: List[str], job_market_skills: List[str]) -> Dict[str, Any]:
        logger.info("MockAIProvider: analyze_skill_gap called")

        user_set = set(s.lower() for s in user_skills)
        market_set = set(s.lower() for s in job_market_skills)

        strong = [s for s in job_market_skills if s.lower() in user_set]
        missing = [s for s in job_market_skills if s.lower() not in user_set]

        learning_recs = {}
        for skill in missing[:5]:
            learning_recs[skill] = {
                "resource_type": "online_course",
                "resource_name": f"Mastering {skill.title()} - Udemy",
                "estimated_time": "4-6 weeks",
                "difficulty_level": "intermediate",
            }

        overlap_ratio = len(strong) / max(len(market_set), 1)

        return {
            "strong_skills": strong,
            "missing_skills": missing,
            "overlapping_skills": strong,
            "priority_skills": [
                {"skill": s, "reason": f"In demand for {job_market_skills[0] if job_market_skills else 'target role'}"}
                for s in missing[:5]
            ],
            "learning_recommendations": learning_recs,
            "overall_gap_score": round(overlap_ratio * 100, 1),
            "summary": f"You have {len(strong)} out of {len(market_set)} required skills. "
            f"Focus on learning: {', '.join(missing[:3])}",
        }

    async def generate_interview_questions(self, job_data: Dict, resume_data: Dict) -> List[Dict[str, str]]:
        logger.info("MockAIProvider: generate_interview_questions called")

        return [
            {
                "question": "Tell me about a challenging project you've worked on and how you handled it.",
                "category": "behavioral",
                "difficulty": "medium",
                "tips": "Use the STAR method: Situation, Task, Action, Result",
                "suggested_answer_points": [
                    "Describe the challenge clearly",
                    "Explain your specific role",
                    "Highlight the outcome with metrics",
                ],
            },
            {
                "question": "How do you stay updated with the latest technologies?",
                "category": "behavioral",
                "difficulty": "easy",
                "tips": "Show genuine passion for learning",
                "suggested_answer_points": [
                    "Mention specific resources",
                    "Give examples of recent learning",
                ],
            },
            {
                "question": "Describe your experience with agile methodologies.",
                "category": "technical",
                "difficulty": "medium",
                "tips": "Be specific about your role in agile teams",
                "suggested_answer_points": [
                    "Mention specific ceremonies",
                    "Talk about collaboration tools",
                ],
            },
            {
                "question": "How do you handle tight deadlines?",
                "category": "situational",
                "difficulty": "medium",
                "tips": "Show your prioritization skills",
                "suggested_answer_points": [
                    "Prioritization strategies",
                    "Communication with stakeholders",
                ],
            },
            {
                "question": "Why are you interested in working at our company?",
                "category": "company",
                "difficulty": "easy",
                "tips": "Research the company beforehand",
                "suggested_answer_points": [
                    "Company mission alignment",
                    "Specific products or values",
                ],
            },
        ]

    async def extract_job_keywords(self, job_description: str) -> List[str]:
        logger.info("MockAIProvider: extract_job_keywords called")

        all_keywords = [
            "python", "javascript", "react", "node.js", "sql", "aws", "docker",
            "kubernetes", "git", "agile", "scrum", "ci/cd", "api", "rest",
            "microservices", "teamwork", "communication", "problem-solving",
            "leadership", "analytical", "detail-oriented", "self-motivated",
        ]

        desc_lower = job_description.lower()
        found = [kw for kw in all_keywords if kw in desc_lower]

        if not found:
            found = random.sample(all_keywords, 8)

        return found
