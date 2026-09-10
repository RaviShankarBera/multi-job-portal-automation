from typing import List, Optional


class JobMatchingService:
    """Service for calculating job-user match scores"""

    DEFAULT_WEIGHTS = {
        "skills": 0.30,
        "experience": 0.20,
        "title": 0.15,
        "industry": 0.10,
        "location": 0.10,
        "salary": 0.10,
        "education": 0.03,
        "certification": 0.02,
    }

    def __init__(self, weights: Optional[dict] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            self.weights = {
                k: v / total for k, v in self.weights.items()
            }

    def calculate_skills_score(
        self,
        user_skills: List[str],
        job_required: List[str],
        job_preferred: List[str],
    ) -> float:
        if not job_required and not job_preferred:
            return 70.0

        user_skills_lower = {s.lower().strip() for s in user_skills}

        required_matches = 0
        for skill in job_required:
            if skill.lower().strip() in user_skills_lower:
                required_matches += 1

        required_score = 0.0
        if job_required:
            required_score = (required_matches / len(job_required)) * 100

        preferred_matches = 0
        for skill in job_preferred:
            if skill.lower().strip() in user_skills_lower:
                preferred_matches += 1

        preferred_bonus = 0.0
        if job_preferred:
            preferred_bonus = (preferred_matches / len(job_preferred)) * 20

        score = min(100.0, required_score + preferred_bonus)

        if required_matches > 0 and required_matches < len(job_required):
            score = max(score, 30.0)

        return round(score, 2)

    def calculate_experience_score(
        self, user_years: int, job_years: Optional[int]
    ) -> float:
        if job_years is None:
            return 70.0

        if user_years >= job_years:
            excess = user_years - job_years
            if excess <= 2:
                return 100.0
            elif excess <= 5:
                return max(70.0, 100.0 - (excess - 2) * 10)
            else:
                return max(50.0, 70.0 - (excess - 5) * 5)

        deficit = job_years - user_years
        if deficit <= 1:
            return 80.0
        elif deficit <= 2:
            return 60.0
        elif deficit <= 3:
            return 40.0
        else:
            return max(10.0, 40.0 - (deficit - 3) * 10)

    def calculate_title_score(self, user_title: str, job_title: str) -> float:
        if not user_title or not job_title:
            return 50.0

        user_words = set(user_title.lower().split())
        job_words = set(job_title.lower().split())

        if not job_words:
            return 50.0

        overlap = user_words & job_words
        if overlap:
            score = min(100.0, 60.0 + len(overlap) * 15)
            return round(score, 2)

        title_hierarchy = {
            "intern": 0,
            "junior": 1,
            "mid": 2,
            "senior": 3,
            "lead": 4,
            "principal": 5,
            "staff": 5,
            "director": 6,
            "vp": 7,
            "vice president": 7,
            "c-level": 8,
            "cto": 8,
            "ceo": 8,
        }

        user_level = -1
        job_level = -1
        for key, level in title_hierarchy.items():
            if key in user_title.lower():
                user_level = max(user_level, level)
            if key in job_title.lower():
                job_level = max(job_level, level)

        if user_level >= 0 and job_level >= 0:
            diff = abs(user_level - job_level)
            if diff == 0:
                return 90.0
            elif diff == 1:
                return 75.0
            elif diff == 2:
                return 50.0
            else:
                return 30.0

        user_categories = self._extract_categories(user_title)
        job_categories = self._extract_categories(job_title)

        if user_categories & job_categories:
            return 65.0

        return 35.0

    def _extract_categories(self, title: str) -> set:
        categories = {
            "engineering": ["engineer", "developer", "programmer", "swe"],
            "data": ["data", "analytics", "analyst", "scientist"],
            "management": ["manager", "director", "lead", "head"],
            "design": ["designer", "ux", "ui", "creative"],
            "product": ["product", "pm", "product manager"],
            "marketing": ["marketing", "growth", "seo", "content"],
            "sales": ["sales", "account executive", "business development"],
            "operations": ["operations", "ops", "devops", "sre"],
            "finance": ["finance", "accounting", "controller"],
            "hr": ["human resources", "hr", "recruiter", "talent"],
        }
        title_lower = title.lower()
        found = set()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in title_lower:
                    found.add(category)
                    break
        return found

    def calculate_location_score(
        self,
        user_location: str,
        job_location: str,
        job_remote_status: Optional[str],
        user_remote_preference: Optional[str] = None,
    ) -> float:
        if job_remote_status == "remote":
            if user_remote_preference == "remote":
                return 100.0
            elif user_remote_preference == "hybrid":
                return 80.0
            return 90.0

        if not user_location or not job_location:
            return 60.0

        user_loc_lower = user_location.lower().strip()
        job_loc_lower = job_location.lower().strip()

        if user_loc_lower == job_loc_lower:
            return 100.0

        user_parts = set(user_loc_lower.replace(",", " ").split())
        job_parts = set(job_loc_lower.replace(",", " ").split())

        overlap = user_parts & job_parts
        if overlap:
            return min(95.0, 60.0 + len(overlap) * 15)

        if job_remote_status == "hybrid":
            return 70.0

        return 40.0

    def calculate_salary_score(
        self,
        user_expected: Optional[float],
        job_min: Optional[float],
        job_max: Optional[float],
    ) -> float:
        if user_expected is None:
            return 70.0

        if job_min is None and job_max is None:
            return 60.0

        if job_min is not None and job_max is not None:
            if user_expected >= job_min and user_expected <= job_max:
                return 100.0
            elif user_expected < job_min:
                diff_pct = (job_min - user_expected) / job_min * 100
                if diff_pct <= 10:
                    return 85.0
                elif diff_pct <= 20:
                    return 70.0
                elif diff_pct <= 30:
                    return 50.0
                return 30.0
            else:
                diff_pct = (user_expected - job_max) / job_max * 100
                if diff_pct <= 10:
                    return 80.0
                elif diff_pct <= 20:
                    return 60.0
                elif diff_pct <= 30:
                    return 40.0
                return 20.0

        if job_min is not None:
            if user_expected <= job_min:
                return 90.0
            diff_pct = (user_expected - job_min) / job_min * 100
            if diff_pct <= 20:
                return 70.0
            return 40.0

        if job_max is not None:
            if user_expected >= job_max:
                return 90.0
            diff_pct = (job_max - user_expected) / job_max * 100
            if diff_pct <= 20:
                return 70.0
            return 40.0

        return 60.0

    def calculate_certification_score(
        self, user_certs: List[str], job_qualifications: List[str]
    ) -> float:
        if not job_qualifications:
            return 80.0

        cert_keywords = ["certification", "certified", "license", "degree", "bachelor", "master", "mba"]
        job_cert_reqs = [
            q for q in job_qualifications
            if any(kw in q.lower() for kw in cert_keywords)
        ]

        if not job_cert_reqs:
            return 80.0

        user_certs_lower = {c.lower().strip() for c in user_certs}
        matched = sum(
            1 for req in job_cert_reqs
            if any(uc in req.lower() or req.lower() in uc for uc in user_certs_lower)
        )

        if matched == len(job_cert_reqs):
            return 100.0
        elif matched > 0:
            return 60.0 + (matched / len(job_cert_reqs)) * 30
        return 40.0

    def calculate_overall_score(self, scores: dict) -> float:
        weighted_sum = 0.0
        total_weight = 0.0

        score_mapping = {
            "skills": "skills_score",
            "experience": "experience_score",
            "title": "title_score",
            "industry": "industry_score",
            "location": "location_score",
            "salary": "salary_score",
            "education": "education_score",
            "certification": "certification_score",
        }

        for key, weight in self.weights.items():
            score_key = score_mapping.get(key)
            if score_key and score_key in scores:
                weighted_sum += scores[score_key] * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 2)

    def generate_explanation(self, scores: dict) -> str:
        explanations = []

        if scores.get("skills_score", 0) >= 80:
            explanations.append(
                "Strong skills match with the job requirements"
            )
        elif scores.get("skills_score", 0) >= 50:
            explanations.append(
                "Good skills alignment, some skills match the requirements"
            )
        else:
            explanations.append(
                "Limited skills match, consider upskilling for this role"
            )

        if scores.get("experience_score", 0) >= 80:
            explanations.append(
                "Experience level is well-suited for this position"
            )
        elif scores.get("experience_score", 0) >= 50:
            explanations.append(
                "Experience is within acceptable range"
            )
        else:
            explanations.append(
                "Experience level may not fully match job requirements"
            )

        if scores.get("title_score", 0) >= 80:
            explanations.append(
                "Role title closely aligns with your career target"
            )
        elif scores.get("title_score", 0) >= 50:
            explanations.append(
                "Role has some alignment with your career path"
            )

        if scores.get("location_score", 0) >= 80:
            explanations.append(
                "Location is compatible with your preferences"
            )
        elif scores.get("location_score", 0) < 50:
            explanations.append(
                "Location may require relocation or commute adjustment"
            )

        if scores.get("salary_score", 0) >= 80:
            explanations.append(
                "Salary range meets your expectations"
            )
        elif scores.get("salary_score", 0) < 50:
            explanations.append(
                "Salary range may differ from your expectations"
            )

        if not explanations:
            explanations.append(
                "This job has moderate alignment with your profile"
            )

        return ". ".join(explanations) + "."
