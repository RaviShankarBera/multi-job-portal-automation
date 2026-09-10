import os
import re
import uuid
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.resume import Resume, ResumeVersion
from app.schemas.resume import (
    ResumeCreate,
    ResumeParseResult,
    ATSScoreResponse,
    ResumeVersionResponse,
)
from app.core.config import settings


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_resume(self, user_id: int, file: UploadFile, title: Optional[str] = None, tags: Optional[List[str]] = None) -> Resume:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided",
            )

        file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_ext}' not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )

        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
            )

        upload_dir = os.path.join(settings.RESUME_UPLOAD_DIR, str(user_id))
        os.makedirs(upload_dir, exist_ok=True)

        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        parsed_content = ""
        structured_data = None

        try:
            parse_result = await self.parse_resume_content(file_path, file_ext)
            parsed_content = parse_result.get("raw_text", "")
            structured_data = {
                "contact_info": parse_result.get("contact_info"),
                "summary": parse_result.get("summary"),
                "experience": parse_result.get("experience"),
                "education": parse_result.get("education"),
                "skills": parse_result.get("skills"),
                "certifications": parse_result.get("certifications"),
            }
        except Exception:
            parsed_content = ""
            structured_data = {}

        resume = Resume(
            user_id=user_id,
            title=title or file.filename.rsplit(".", 1)[0],
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            file_type=file_ext,
            parsed_content=parsed_content,
            structured_data=structured_data,
            is_primary=False,
            tags=tags or [],
        )

        self.db.add(resume)
        await self.db.flush()
        await self.db.refresh(resume)
        return resume

    async def get_resumes(self, user_id: int) -> List[Resume]:
        result = await self.db.execute(
            select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_resume(self, resume_id: int, user_id: int) -> Resume:
        result = await self.db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )
        return resume

    async def delete_resume(self, resume_id: int, user_id: int) -> bool:
        resume = await self.get_resume(resume_id, user_id)

        if resume.file_path and os.path.exists(resume.file_path):
            try:
                os.remove(resume.file_path)
            except OSError:
                pass

        await self.db.delete(resume)
        await self.db.flush()
        return True

    async def set_primary_resume(self, resume_id: int, user_id: int) -> Resume:
        resume = await self.get_resume(resume_id, user_id)

        result = await self.db.execute(
            select(Resume).where(Resume.user_id == user_id, Resume.is_primary == True)
        )
        existing_primary = result.scalars().all()
        for r in existing_primary:
            r.is_primary = False

        resume.is_primary = True
        await self.db.flush()
        await self.db.refresh(resume)
        return resume

    async def create_version(
        self, resume_id: int, user_id: int, job_id: Optional[int] = None, tailored_content: Optional[Dict[str, Any]] = None
    ) -> ResumeVersion:
        resume = await self.get_resume(resume_id, user_id)

        result = await self.db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        last_version = result.scalar_one_or_none()
        next_version = (last_version.version_number + 1) if last_version else 1

        version = ResumeVersion(
            resume_id=resume_id,
            version_number=next_version,
            tailored_content=tailored_content or {},
            job_id=job_id,
        )

        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def get_versions(self, resume_id: int, user_id: int) -> List[ResumeVersion]:
        await self.get_resume(resume_id, user_id)

        result = await self.db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def reparse_resume(self, resume_id: int, user_id: int) -> Resume:
        resume = await self.get_resume(resume_id, user_id)

        try:
            parse_result = await self.parse_resume_content(resume.file_path, resume.file_type)
            resume.parsed_content = parse_result.get("raw_text", "")
            resume.structured_data = {
                "contact_info": parse_result.get("contact_info"),
                "summary": parse_result.get("summary"),
                "experience": parse_result.get("experience"),
                "education": parse_result.get("education"),
                "skills": parse_result.get("skills"),
                "certifications": parse_result.get("certifications"),
            }
        except Exception:
            pass

        await self.db.flush()
        await self.db.refresh(resume)
        return resume

    async def calculate_ats_score(self, resume_id: int, user_id: int, job_description: str) -> ATSScoreResponse:
        resume = await self.get_resume(resume_id, user_id)

        resume_text = resume.parsed_content or ""
        if not resume.structured_data:
            await self.reparse_resume(resume_id, user_id)
            resume_text = resume.parsed_content or ""

        job_keywords = self._extract_keywords(job_description)
        resume_keywords = self._extract_keywords(resume_text)

        matched_keywords = job_keywords.intersection(resume_keywords)
        keyword_match = len(matched_keywords) / len(job_keywords) if job_keywords else 0.0
        missing_keywords = list(job_keywords - resume_keywords)

        sections_present = {
            "contact": bool(resume.structured_data and resume.structured_data.get("contact_info")),
            "summary": bool(resume.structured_data and resume.structured_data.get("summary")),
            "experience": bool(resume.structured_data and resume.structured_data.get("experience")),
            "education": bool(resume.structured_data and resume.structured_data.get("education")),
            "skills": bool(resume.structured_data and resume.structured_data.get("skills")),
        }

        sections_score = sum(sections_present.values()) / len(sections_present) if sections_present else 0.0

        ats_score = (keyword_match * 0.6 + sections_score * 0.4) * 100

        suggestions = []
        if keyword_match < 0.5:
            suggestions.append("Add more relevant keywords from the job description")
        if not sections_present.get("summary"):
            suggestions.append("Add a professional summary section")
        if not sections_present.get("skills"):
            suggestions.append("Add a dedicated skills section")
        if missing_keywords:
            suggestions.append(f"Consider adding keywords: {', '.join(missing_keywords[:5])}")
        if resume.file_type not in ["pdf"]:
            suggestions.append("PDF format is preferred for ATS compatibility")

        return ATSScoreResponse(
            ats_score=round(min(ats_score, 100.0), 2),
            keyword_match=round(keyword_match * 100, 2),
            missing_keywords=missing_keywords,
            suggestions=suggestions,
            sections_present=sections_present,
        )

    async def parse_resume_content(self, file_path: str, file_type: str) -> Dict[str, Any]:
        raw_text = ""

        if file_type == "pdf":
            raw_text = self._extract_text_from_pdf(file_path)
        elif file_type in ["docx", "doc"]:
            raw_text = self._extract_text_from_docx(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()

        contact_info = self._extract_contact_info(raw_text)
        summary = self._extract_summary(raw_text)
        experience = self._extract_experience(raw_text)
        education = self._extract_education(raw_text)
        skills = self._extract_skills(raw_text)
        certifications = self._extract_certifications(raw_text)

        return {
            "raw_text": raw_text,
            "contact_info": contact_info,
            "summary": summary,
            "experience": experience,
            "education": education,
            "skills": skills,
            "certifications": certifications,
        }

    def _extract_text_from_pdf(self, file_path: str) -> str:
        try:
            import PyPDF2

            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
        except ImportError:
            pass
        except Exception:
            pass

        try:
            with open(file_path, "rb") as f:
                content = f.read()
                text = content.decode("utf-8", errors="ignore")
                return text[:10000]
        except Exception:
            return ""

    def _extract_text_from_docx(self, file_path: str) -> str:
        try:
            import docx

            doc = docx.Document(file_path)
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_parts.append(paragraph.text)
            return "\n".join(text_parts)
        except ImportError:
            pass
        except Exception:
            pass

        return ""

    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        contact = {}

        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if email_match:
            contact["email"] = email_match.group(0)

        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        if phone_match:
            contact["phone"] = phone_match.group(0)

        linkedin_match = re.search(r"linkedin\.com/in/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
        if linkedin_match:
            contact["linkedin"] = linkedin_match.group(0)

        github_match = re.search(r"github\.com/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
        if github_match:
            contact["github"] = github_match.group(0)

        return contact

    def _extract_summary(self, text: str) -> Optional[str]:
        summary_patterns = [
            r"(?:summary|profile|about|objective)\s*[:\n](.*?)(?:\n\n|\n(?=experience|education|skills|work|employment))",
            r"(?:professional\s+(?:summary|profile|objective))\s*[:\n](.*?)(?:\n\n|\n(?=experience|education|skills|work|employment))",
        ]

        text_lower = text.lower()
        for pattern in summary_patterns:
            match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
            if match:
                summary_text = match.group(1).strip()
                lines = [line.strip() for line in summary_text.split("\n") if line.strip()]
                return " ".join(lines[:5])

        return None

    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        experiences = []

        experience_section = re.search(
            r"(?:experience|work\s+history|employment|professional\s+experience)\s*[:\n](.*?)(?:\n(?=education|skills|certifications|summary|profile)|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if experience_section:
            section_text = experience_section.group(1)
            job_entries = re.split(r"\n(?=\S.*(?:engineer|developer|manager|analyst|lead|director|senior|junior|associate|intern|consultant|architect|specialist))", section_text, flags=re.IGNORECASE)

            for entry in job_entries[:10]:
                entry = entry.strip()
                if not entry:
                    continue

                title_match = re.search(
                    r"^([^\n]+?)(?:\s+at\s+|\s*[-–]\s*)([^\n]+)",
                    entry,
                    re.IGNORECASE,
                )

                dates = re.findall(
                    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}\s*[-–]\s*(?:present|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}",
                    entry,
                    re.IGNORECASE,
                )

                exp = {
                    "title": title_match.group(1).strip() if title_match else entry.split("\n")[0],
                    "company": title_match.group(2).strip() if title_match else "",
                    "dates": dates[0] if dates else "",
                    "description": entry[:500],
                }
                experiences.append(exp)

        return experiences

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        education = []

        education_section = re.search(
            r"(?:education|academic)\s*[:\n](.*?)(?:\n(?=experience|skills|certifications|summary|profile)|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if education_section:
            section_text = education_section.group(1)

            degree_patterns = [
                r"(?:bachelor|master|phd|doctorate|mba|b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?|b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?)\w*",
            ]

            edu_entries = section_text.split("\n")
            for entry in edu_entries:
                entry = entry.strip()
                if not entry:
                    continue

                for pattern in degree_patterns:
                    if re.search(pattern, entry, re.IGNORECASE):
                        year_match = re.search(r"\b(19|20)\d{2}\b", entry)
                        edu = {
                            "degree": entry,
                            "year": year_match.group(0) if year_match else "",
                        }
                        education.append(edu)
                        break

        return education

    def _extract_skills(self, text: str) -> List[str]:
        skills = set()

        skills_section = re.search(
            r"(?:skills|technical\s+skills|core\s+competencies|technologies)\s*[:\n](.*?)(?:\n(?=experience|education|certifications|summary|profile)|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if skills_section:
            section_text = skills_section.group(1)
            skill_entries = re.split(r"[,;\n]+", section_text)
            for skill in skill_entries:
                skill = skill.strip()
                if skill and len(skill) < 50 and not skill.startswith("•"):
                    skills.add(skill)

        tech_keywords = [
            "python", "javascript", "typescript", "java", "c\\+\\+", "c#", "ruby", "go", "rust", "php",
            "react", "angular", "vue", "node\\.?js", "django", "flask", "fastapi", "spring", "rails",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
            "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "html", "css", "sass", "less", "bootstrap", "tailwind",
            "git", "jenkins", "ci/cd", "agile", "scrum", "jira",
            "machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "keras",
            "linux", "unix", "windows", "bash", "powershell",
            "rest", "graphql", "grpc", "microservices", "api",
        ]

        text_lower = text.lower()
        for keyword in tech_keywords:
            if re.search(r"\b" + keyword + r"\b", text_lower):
                clean_skill = keyword.replace("\\", "").replace(".", "")
                skills.add(clean_skill)

        return sorted(list(skills))

    def _extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        certifications = []

        cert_section = re.search(
            r"(?:certifications|licenses|certificates)\s*[:\n](.*?)(?:\n(?=experience|education|skills|summary|profile)|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if cert_section:
            section_text = cert_section.group(1)
            cert_entries = section_text.split("\n")
            for entry in cert_entries:
                entry = entry.strip()
                if entry and len(entry) > 3:
                    cert = {"name": entry, "issuer": ""}
                    certifications.append(cert)

        return certifications

    def _extract_keywords(self, text: str) -> set:
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "shall", "can", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "what", "which", "who", "whom", "where", "when", "why", "how",
            "all", "each", "every", "both", "few", "more", "most", "other",
            "some", "such", "no", "not", "only", "same", "so", "than", "too",
            "very", "just", "because", "if", "then", "else", "while", "about",
            "up", "out", "off", "over", "under", "again", "further", "once",
            "here", "there", "also", "after", "before", "above", "below",
            "between", "through", "during", "without", "within", "along",
            "across", "behind", "beyond", "around", "into", "onto", "upon",
        }

        words = re.findall(r"[a-zA-Z]+", text.lower())
        return {word for word in words if len(word) > 2 and word not in stopwords}
