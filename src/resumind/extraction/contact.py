import re
from typing import List
from resumind.models.resume import ContactInfo, PhoneExtracted
from resumind.segmentation.models import SectionBlock

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

PHONE_CANDIDATE_PATTERN = re.compile(r"\+?[\d\-\s\(\)\.]{9,25}")

URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+(?:/[^\s]*)?")

class ContactExtractor:
    """
    Extracts contact metadata (emails, phones, URLs) from segmented resume sections.
    """
    def extract(self, sections: List[SectionBlock]) -> ContactInfo:
        emails = []
        phones = []
        linkedin = []
        github = []
        portfolios = []
        other_urls = []
        
        for section in sections:
            for line in section.lines:
                # 1. Email Extraction
                for match in EMAIL_PATTERN.finditer(line):
                    email_raw = match.group()
                    # Strip trailing punctuation that might be caught
                    email_raw = email_raw.rstrip(".,;")
                    email_norm = email_raw.lower()
                    if email_norm not in [e.lower() for e in emails]:
                        emails.append(email_norm)
                        
                # 2. Phone Extraction
                for match in PHONE_CANDIDATE_PATTERN.finditer(line):
                    raw_phone = match.group().strip()
                    if self._is_valid_phone(raw_phone):
                        norm_phone = self._normalize_phone(raw_phone)
                        if not any(p.normalized == norm_phone for p in phones):
                            phones.append(PhoneExtracted(raw=raw_phone, normalized=norm_phone))
                            
                # 3. URL Extraction
                for match in URL_PATTERN.finditer(line):
                    raw_url = match.group().strip().rstrip(".,;)")
                    if "@" in raw_url:
                        continue
                    # Ignore matches that have no letters (likely version numbers or dates)
                    if not re.search(r"[a-zA-Z]", raw_url):
                        continue
                    # ignore common file extensions if they are alone
                    if re.match(r"^[a-zA-Z0-9-]+\.(pdf|docx|txt|csv|png|jpg)$", raw_url.lower()):
                        continue
                        
                    norm_url = self._normalize_url(raw_url)
                    
                    if "linkedin.com/in/" in norm_url:
                        if norm_url not in linkedin:
                            linkedin.append(norm_url)
                    elif "github.com/" in norm_url:
                        if norm_url not in github:
                            github.append(norm_url)
                    elif "linkedin.com/company" in norm_url:
                        # Exclude company URLs from personal linkedin
                        if norm_url not in other_urls:
                            other_urls.append(norm_url)
                    else:
                        # Treat as portfolio if it's in a contact header, or has common TLDs
                        if section.canonical_name == "contact_header" or self._is_portfolio(norm_url):
                            if norm_url not in portfolios:
                                portfolios.append(norm_url)
                        else:
                            if norm_url not in other_urls:
                                other_urls.append(norm_url)

        return ContactInfo(
            emails=emails,
            phones=phones,
            linkedin=linkedin,
            github=github,
            portfolios=portfolios,
            other_urls=other_urls
        )

    def _is_valid_phone(self, raw: str) -> bool:
        digits = re.sub(r"\D", "", raw)
        
        # Phone must have between 9 and 15 digits
        if len(digits) < 9 or len(digits) > 15:
            return False
            
        # Reject year ranges e.g. 2021-2025, 01/2021 - 05/2025
        if re.search(r"20\d{2}\s*[-to]+\s*20\d{2}", raw.strip().lower()):
            return False
            
        # Reject dates like 12-05-2024
        if re.match(r"^\d{2}[-/]\d{2}[-/]\d{4}$", raw.strip()):
            return False
            
        # Reject decimals or fractions that look like GPAs (e.g. 3.8 / 4.0 or just 3.84)
        if " / " in raw or re.match(r"^\d{1,2}\.\d{1,2}$", raw.strip()):
            return False
            
        # Avoid things that are just repeated digits (like 0000000000)
        if len(set(digits)) == 1:
            return False
            
        return True
        
    def _normalize_phone(self, raw: str) -> str:
        has_plus = raw.startswith("+")
        digits = re.sub(r"\D", "", raw)
        if has_plus:
            return "+" + digits
        return digits

    def _normalize_url(self, raw: str) -> str:
        norm = raw.lower()
        if not norm.startswith("http"):
            norm = "https://" + norm
        return norm
        
    def _is_portfolio(self, url: str) -> bool:
        return any(ext in url for ext in [".dev", ".me", ".io", ".tech", "portfolio"])
