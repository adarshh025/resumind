import os
from pathlib import Path
from typing import Dict, Any

from resumind.models.resume import ResumeData
from resumind.ingestion.factory import get_extractor
from resumind.preprocessing.cleaner import ResumeCleaner
from resumind.segmentation.sectionizer import Sectionizer
from resumind.extraction.contact import ContactExtractor
from resumind.nlp.ner import SemanticEntityExtractor
from resumind.extraction.skills import SkillExtractor
from resumind.assembly.assembler import ResumeAssembler

class ResumeParser:
    """
    Core parsing engine for Resumind.
    Extracts, cleans, segments, and parses resumes into structured data.
    """
    
    def __init__(self):
        self.cleaner = ResumeCleaner()
        self.sectionizer = Sectionizer()
        self.contact_extractor = ContactExtractor()
        self.ner_extractor = SemanticEntityExtractor()
        self.skill_extractor = SkillExtractor()
        self.assembler = ResumeAssembler()
        
    def parsefile(self, filepath: str) -> Dict[str, Any]:
        """
        Parses a resume file and returns the structured extraction.
        
        Args:
            filepath (str): Path to the PDF or DOCX resume.
            
        Returns:
            Dict[str, Any]: A dictionary representing the structured resume data.
                            Compatible with ResumeData model.
        """
        path_obj = Path(filepath)
        
        # 1. Ingestion Phase
        extractor = get_extractor(path_obj)
        extraction_result = extractor.extract(path_obj)
        
        # 2. Cleaning Phase
        cleaned_lines = self.cleaner.clean(extraction_result.raw_text)
        
        # 3. Segmentation Phase
        sections = self.sectionizer.segment(cleaned_lines)
        
        # 4. Extraction Phase
        contact_info = self.contact_extractor.extract(sections)
        entities = self.ner_extractor.extract(sections)
        skills = self.skill_extractor.extract(sections)
        
        # 5. Assembly Phase
        resume = self.assembler.assemble(
            raw_text=extraction_result.raw_text,
            cleaned_text="\n".join(cleaned_lines),
            sections=sections,
            contact_info=contact_info,
            entities=entities,
            skills=skills,
            file_name=path_obj.name
        )
        
        return resume.model_dump()
