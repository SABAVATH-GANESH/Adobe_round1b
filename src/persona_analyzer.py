"""
Persona Analyzer for Round 1B: Persona-Driven Document Intelligence
Analyzes multiple documents based on persona and job requirements
"""

import json
import time
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
from collections import defaultdict
from .pdf_processor import PDFProcessor
from .structure_extractor import StructureExtractor

class PersonaAnalyzer:
    """Analyzes documents based on persona and job requirements"""
    
    def __init__(self):
        self.processor = PDFProcessor()
        self.extractor = StructureExtractor()
        self.documents = []
        self.persona = ""
        self.job_to_be_done = ""
        
    def analyze_documents(self, pdf_files: List[Path], config: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis function for persona-driven document intelligence"""
        # Store configuration
        self.persona = config.get("persona", "")
        self.job_to_be_done = config.get("job_to_be_done", "")
        
        # Extract content from all documents
        document_contents = self._extract_document_contents(pdf_files)
        
        # Analyze relevance based on persona and job
        relevant_sections = self._extract_relevant_sections(document_contents)
        
        # Perform subsection analysis
        subsection_analysis = self._analyze_subsections(relevant_sections)
        
        # Prepare output
        result = {
            "metadata": {
                "documents": [f.name for f in pdf_files],
                "persona": self.persona,
                "job_to_be_done": self.job_to_be_done,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "extracted_sections": relevant_sections,
            "subsection_analysis": subsection_analysis
        }
        
        return result
    
    def _extract_document_contents(self, pdf_files: List[Path]) -> List[Dict[str, Any]]:
        """Extract structured content from all documents"""
        documents = []
        
        for pdf_file in pdf_files:
            try:
                # Load PDF
                if not self.processor.load_pdf(pdf_file):
                    continue
                
                # Extract basic structure
                structure = self.extractor.extract_structure(pdf_file)
                
                # Extract detailed content
                content = self._extract_detailed_content(pdf_file)
                
                documents.append({
                    "filename": pdf_file.name,
                    "title": structure.get("title", ""),
                    "outline": structure.get("outline", []),
                    "content": content
                })
                
                self.processor.close()
                
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {str(e)}")
                continue
        
        return documents
    
    def _extract_detailed_content(self, pdf_file: Path) -> Dict[str, Any]:
        """Extract detailed content including sections and subsections"""
        content = {
            "full_text": "",
            "sections": [],
            "page_texts": {}
        }
        
        # Extract full text
        full_text = self.processor.extract_all_text()
        content["full_text"] = full_text
        
        # Extract page-wise text
        for page_num in range(self.processor.page_count):
            page_text = self.processor.extract_page_text(page_num)
            content["page_texts"][page_num + 1] = page_text
        
        # Extract sections with detailed analysis
        sections = self.processor.extract_sections_by_formatting()
        content["sections"] = self._enrich_sections(sections)
        
        return content
    
    def _enrich_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich sections with additional context and content"""
        enriched = []
        
        for i, section in enumerate(sections):
            enriched_section = section.copy()
            
            # Extract surrounding context
            page_num = section["page"] - 1  # Convert to 0-based
            if page_num < self.processor.page_count:
                page_text = self.processor.extract_page_text(page_num)
                
                # Find section content
                section_content = self._extract_section_content(
                    page_text, section["text"], i, sections
                )
                enriched_section["content"] = section_content
            
            enriched.append(enriched_section)
        
        return enriched
    
    def _extract_section_content(self, page_text: str, section_title: str, 
                                section_index: int, all_sections: List[Dict[str, Any]]) -> str:
        """Extract content for a specific section"""
        lines = page_text.split('\n')
        
        # Find section start
        start_line = -1
        for i, line in enumerate(lines):
            if section_title.lower() in line.lower():
                start_line = i
                break
        
        if start_line == -1:
            return ""
        
        # Find section end (next section or end of page)
        end_line = len(lines)
        
        # Look for next section on same page
        for i in range(start_line + 1, len(lines)):
            line = lines[i].strip()
            if len(line) > 3 and self._looks_like_heading(line):
                end_line = i
                break
        
        # Extract content
        content_lines = lines[start_line + 1:end_line]
        content = '\n'.join(content_lines).strip()
        
        return content
    
    def _looks_like_heading(self, text: str) -> bool:
        """Check if text looks like a heading"""
        # Basic heuristics for heading detection
        if len(text) < 3 or len(text) > 150:
            return False
        
        # Check for heading patterns
        heading_patterns = [
            r'^\d+\.?\s+[A-Z]',  # Numbered headings
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',  # Title Case
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _extract_relevant_sections(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract sections relevant to persona and job"""
        relevant_sections = []
        
        # Create keyword sets for persona and job
        persona_keywords = self._extract_keywords(self.persona)
        job_keywords = self._extract_keywords(self.job_to_be_done)
        
        for doc in documents:
            for section in doc["content"]["sections"]:
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(
                    section, persona_keywords, job_keywords
                )
                
                if relevance_score > 0.1:  # Threshold for relevance
                    relevant_sections.append({
                        "document": doc["filename"],
                        "page": section["page"],
                        "section_title": section["text"],
                        "importance_rank": relevance_score
                    })
        
        # Sort by importance rank
        relevant_sections.sort(key=lambda x: x["importance_rank"], reverse=True)
        
        # Add rank numbers
        for i, section in enumerate(relevant_sections):
            section["importance_rank"] = i + 1
        
        return relevant_sections
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was',
            'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now',
            'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she',
            'too', 'use', 'with', 'have', 'this', 'will', 'your', 'from', 'they', 'know', 'want',
            'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like',
            'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'
        }
        
        keywords = set(word for word in words if word not in stop_words)
        return keywords
    
    def _calculate_relevance_score(self, section: Dict[str, Any], 
                                  persona_keywords: set, job_keywords: set) -> float:
        """Calculate relevance score for a section"""
        score = 0.0
        
        # Get section text
        section_text = section.get("text", "").lower()
        section_content = section.get("content", "").lower()
        combined_text = f"{section_text} {section_content}"
        
        # Extract section keywords
        section_keywords = self._extract_keywords(combined_text)
        
        # Calculate persona relevance
        persona_overlap = len(persona_keywords.intersection(section_keywords))
        persona_score = persona_overlap / max(len(persona_keywords), 1)
        
        # Calculate job relevance
        job_overlap = len(job_keywords.intersection(section_keywords))
        job_score = job_overlap / max(len(job_keywords), 1)
        
        # Combined score
        score = 0.6 * job_score + 0.4 * persona_score
        
        # Bonus for specific domain matches
        domain_bonuses = self._get_domain_bonuses(combined_text)
        score += domain_bonuses
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_domain_bonuses(self, text: str) -> float:
        """Get domain-specific bonuses based on persona and job"""
        bonus = 0.0
        
        # Academic/Research bonuses
        if any(word in self.persona.lower() for word in ['researcher', 'phd', 'academic', 'student']):
            research_terms = ['methodology', 'analysis', 'results', 'conclusion', 'abstract', 
                            'literature', 'experiment', 'data', 'findings', 'hypothesis']
            matches = sum(1 for term in research_terms if term in text)
            bonus += matches * 0.05
        
        # Business/Investment bonuses
        if any(word in self.persona.lower() for word in ['analyst', 'investment', 'business']):
            business_terms = ['revenue', 'profit', 'growth', 'market', 'financial', 'strategy',
                            'competitive', 'performance', 'roi', 'analysis']
            matches = sum(1 for term in business_terms if term in text)
            bonus += matches * 0.05
        
        # Educational bonuses
        if any(word in self.persona.lower() for word in ['student', 'learner', 'education']):
            educational_terms = ['concept', 'principle', 'theory', 'example', 'definition',
                               'explanation', 'practice', 'exercise', 'summary']
            matches = sum(1 for term in educational_terms if term in text)
            bonus += matches * 0.05
        
        return min(bonus, 0.3)  # Cap bonus at 0.3
    
    def _analyze_subsections(self, relevant_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze subsections for relevant sections"""
        subsection_analysis = []
        
        for section in relevant_sections[:10]:  # Analyze top 10 sections
            # Extract refined content
            refined_content = self._refine_section_content(section)
            
            subsection_analysis.append({
                "document": section["document"],
                "page": section["page"],
                "section_title": section["section_title"],
                "refined_text": refined_content,
                "relevance_score": section["importance_rank"]
            })
        
        return subsection_analysis
    
    def _refine_section_content(self, section: Dict[str, Any]) -> str:
        """Refine and summarize section content"""
        # For now, return a placeholder refined text
        # In a full implementation, this would use NLP to summarize content
        return f"Key insights from {section['section_title']} relevant to {self.persona} for {self.job_to_be_done}"
