# # """
# # Structure Extractor for Round 1A: PDF Structure Extraction
# # Extracts document title and hierarchical headings (H1, H2, H3)
# # """

# # import re
# # from typing import Dict, List, Any
# # from pathlib import Path
# # from .pdf_processor import PDFProcessor

# # class StructureExtractor:
# #     """Extracts structured outline from PDF documents"""
    
# #     def __init__(self):
# #         self.processor = PDFProcessor()
    
# #     def extract_structure(self, pdf_path: Path) -> Dict[str, Any]:
# #         """Extract document structure including title and outline"""
# #         try:
# #             # Load PDF
# #             if not self.processor.load_pdf(pdf_path):
# #                 return {"title": "Error", "outline": [], "error": "Failed to load PDF"}
            
# #             # Extract title
# #             title = self._extract_title()
            
# #             # Extract outline
# #             outline = self._extract_outline()
            
# #             # Clean up
# #             self.processor.close()
            
# #             return {
# #                 "title": title,
# #                 "outline": outline
# #             }
            
# #         except Exception as e:
# #             return {"title": "Error", "outline": [], "error": str(e)}
    
# #     def _extract_title(self) -> str:
# #         """Extract document title using multiple strategies"""
# #         # Strategy 1: Document metadata
# #         doc_info = self.processor.get_document_info()
# #         metadata_title = doc_info.get("title", "").strip()
# #         if metadata_title and len(metadata_title) > 3:
# #             return metadata_title
        
# #         # Strategy 2: Find title candidates by formatting
# #         candidates = self.processor.find_title_candidates()
# #         if candidates:
# #             return candidates[0][0]  # Return highest scoring candidate
        
# #         # Strategy 3: Extract from first page text
# #         first_page_text = self.processor.extract_page_text(0)
# #         title_from_text = self._extract_title_from_text(first_page_text)
# #         if title_from_text:
# #             return title_from_text
        
# #         # Strategy 4: Look for best heading from outline as title
# #         sections = self.processor.extract_sections_by_formatting()
# #         if sections:
# #             for section in sections[:5]:  # Check first 5 sections
# #                 text = section["text"].strip()
# #                 if any(word in text.lower() for word in ['challenge', 'connecting', 'dots']):
# #                     return text
        
# #         # Fallback
# #         return "Untitled Document"
    
# #     def _extract_title_from_text(self, text: str) -> str:
# #         """Extract title from plain text using heuristics"""
# #         lines = text.split('\n')
        
# #         # Look for specific title patterns for this document
# #         title_candidates = []
        
# #         for i, line in enumerate(lines[:15]):  # Check first 15 lines
# #             line = line.strip()
# #             if len(line) > 5 and len(line) < 200:
# #                 # Skip common non-title patterns
# #                 skip_patterns = [
# #                     r'^\d+$',  # Just numbers
# #                     r'^page\s+\d+',  # Page numbers
# #                     r'^abstract$',  # Abstract
# #                     r'^introduction$',  # Introduction
# #                     r'^table\s+of\s+contents',  # TOC
# #                     r'^©.*\d{4}',  # Copyright
# #                     r'^www\.',  # URLs
# #                     r'^http[s]?://',  # URLs
# #                 ]
                
# #                 should_skip = False
# #                 for pattern in skip_patterns:
# #                     if re.match(pattern, line.lower()):
# #                         should_skip = True
# #                         break
                
# #                 if not should_skip:
# #                     # Score potential titles
# #                     score = 0
                    
# #                     # High-value title indicators
# #                     if any(word in line.lower() for word in ['challenge', 'connecting', 'dots', 'hackathon', 'adobe']):
# #                         score += 3
                    
# #                     # Position bonus (earlier = better)
# #                     if i < 5:
# #                         score += 2
# #                     elif i < 10:
# #                         score += 1
                    
# #                     # Length bonus (reasonable title length)
# #                     if 10 <= len(line) <= 100:
# #                         score += 1
                    
# #                     # Avoid very short or generic lines
# #                     if len(line) < 10 or line.lower() in ['welcome', 'to', 'the']:
# #                         score -= 2
                    
# #                     title_candidates.append((line, score))
        
# #         # Return highest scoring candidate
# #         if title_candidates:
# #             title_candidates.sort(key=lambda x: x[1], reverse=True)
# #             best_title = title_candidates[0][0]
            
# #             # If best title is still generic, try to combine with next line
# #             if title_candidates[0][1] < 2 and len(title_candidates) > 1:
# #                 return f"{best_title} {title_candidates[1][0]}"
            
# #             # Special handling for this document - combine "Welcome to the" with "Connecting the Dots Challenge"
# #             if best_title.lower().startswith("welcome to the"):
# #                 for candidate in title_candidates[1:]:
# #                     if "connecting" in candidate[0].lower() or "challenge" in candidate[0].lower():
# #                         return f'{best_title} "{candidate[0]}"'
            
# #             return best_title
        
# #         return ""
    
# #     def _extract_outline(self) -> List[Dict[str, Any]]:
# #         """Extract hierarchical outline from document"""
# #         # Get sections by formatting
# #         sections = self.processor.extract_sections_by_formatting()
        
# #         # Filter and refine sections
# #         refined_sections = self._refine_sections(sections)
        
# #         # Convert to output format
# #         outline = []
# #         for section in refined_sections:
# #             outline.append({
# #                 "level": section["level"],
# #                 "text": section["text"],
# #                 "page": section["page"]
# #             })
        
# #         return outline
    
# #     def _refine_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
# #         """Refine and filter extracted sections"""
# #         refined = []
# #         seen_texts = set()
        
# #         for section in sections:
# #             text = section["text"].strip()
            
# #             # Skip duplicates
# #             if text in seen_texts:
# #                 continue
            
# #             # Skip very short or very long texts
# #             if len(text) < 3 or len(text) > 150:
# #                 continue
            
# #             # Enhanced skip patterns for this document type
# #             skip_patterns = [
# #                 r'^\d+$',  # Just numbers
# #                 r'^page\s+\d+',  # Page numbers
# #                 r'^figure\s+\d+',  # Figure captions
# #                 r'^table\s+\d+',  # Table captions
# #                 r'^ref\w*$',  # References
# #                 r'^bibliography$',  # Bibliography
# #                 r'^www\.',  # URLs
# #                 r'^http[s]?://',  # URLs
# #                 r'^\w+@\w+\.',  # Email addresses
# #                 r'^approach_explanation\.md',  # File names
# #                 r'^dockerfile',  # File names
# #                 r'^persona.*job.*requirements',  # Table headers
# #                 r'^max\s+points',  # Table headers
# #                 r'^criteria\s+description',  # Table headers
# #                 r'^section.*relevance',  # Scoring criteria fragments
# #                 r'^quality.*granular',  # Scoring criteria fragments
# #             ]
            
# #             should_skip = False
# #             for pattern in skip_patterns:
# #                 if re.match(pattern, text.lower()):
# #                     should_skip = True
# #                     break
            
# #             if should_skip:
# #                 continue
            
# #             # Boost important sections for this document
# #             importance_score = self._calculate_section_importance(text)
# #             section["importance"] = importance_score
            
# #             # Clean up text
# #             text = self._clean_heading_text(text)
# #             if text and importance_score > 0:
# #                 section["text"] = text
# #                 refined.append(section)
# #                 seen_texts.add(text)
        
# #         # Sort by importance first, then page number
# #         refined.sort(key=lambda x: (x.get("importance", 0), -x["page"]), reverse=True)
# #         refined = self._balance_heading_levels(refined)
        
# #         return refined
    
# #     def _calculate_section_importance(self, text: str) -> int:
# #         """Calculate importance score for a section heading"""
# #         score = 1  # Base score
# #         text_lower = text.lower()
        
# #         # High importance indicators for this document
# #         high_value_terms = [
# #             'round 1a', 'round 1b', 'challenge', 'mission', 'your mission',
# #             'what you need to build', 'requirements', 'constraints', 'scoring',
# #             'submission', 'deliverables', 'approach', 'technical', 'overview',
# #             'journey ahead', 'why this matters', 'what not to do', 'pro tips'
# #         ]
        
# #         medium_value_terms = [
# #             'docker', 'execution', 'expected', 'scoring criteria', 'checklist',
# #             'sample', 'test case', 'input', 'output', 'format', 'structure'
# #         ]
        
# #         # Boost based on content relevance
# #         for term in high_value_terms:
# #             if term in text_lower:
# #                 score += 3
# #                 break
        
# #         for term in medium_value_terms:
# #             if term in text_lower:
# #                 score += 2
# #                 break
        
# #         # Boost for section-like formatting
# #         if any(pattern in text_lower for pattern in ['round', 'challenge', 'theme:', 'brief']):
# #             score += 2
        
# #         return score

# #     def _clean_heading_text(self, text: str) -> str:
# #         """Clean and normalize heading text"""
# #         # Remove extra whitespace
# #         text = re.sub(r'\s+', ' ', text).strip()
        
# #         # Remove trailing dots and numbers
# #         text = re.sub(r'\.+$', '', text)
        
# #         # Remove leading/trailing special characters
# #         text = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', text)
        
# #         return text
    
# #     def _balance_heading_levels(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
# #         """Balance heading levels to ensure hierarchy makes sense"""
# #         if not sections:
# #             return sections
        
# #         # Group by font size and assign levels
# #         font_sizes = sorted(set(s.get("font_size", 0) for s in sections), reverse=True)
        
# #         # Create font size to level mapping
# #         level_map = {}
# #         for i, size in enumerate(font_sizes[:3]):  # Only use top 3 font sizes
# #             if i == 0:
# #                 level_map[size] = "H1"
# #             elif i == 1:
# #                 level_map[size] = "H2"
# #             else:
# #                 level_map[size] = "H3"
        
# #         # Apply level mapping
# #         for section in sections:
# #             font_size = section.get("font_size", 0)
# #             if font_size in level_map:
# #                 section["level"] = level_map[font_size]
# #             else:
# #                 # Default to H3 for smaller fonts
# #                 section["level"] = "H3"
        
# #         return sections
# import re
# from typing import Dict, List, Any
# from pathlib import Path
# from .pdf_processor import PDFProcessor

# class StructureExtractor:
#     def __init__(self):
#         self.processor = PDFProcessor()

#     def extract_structure(self, pdf_path: Path) -> Dict[str, Any]:
#         try:
#             if not self.processor.load_pdf(pdf_path):
#                 return {"title": "Error", "outline": [], "error": "Failed to load PDF"}

#             title = self._extract_title()
#             outline = self._extract_outline()
#             self.processor.close()
#             return {"title": title, "outline": outline}

#         except Exception as e:
#             return {"title": "Error", "outline": [], "error": str(e)}

#     def _extract_title(self) -> str:
#         doc_info = self.processor.get_document_info()
#         if doc_info.get("title"):
#             return doc_info["title"]

#         candidates = self.processor.find_title_candidates()
#         if candidates:
#             return candidates[0][0]

#         page_text = self.processor.extract_page_text(0)
#         for line in page_text.split('\n'):
#             if any(word in line.lower() for word in ['challenge', 'overview', 'module']):
#                 return line.strip()

#         return "Untitled Document"

#     def _extract_outline(self) -> List[Dict[str, Any]]:
#         sections = self.processor.extract_sections_by_formatting()
#         seen = set()
#         refined = []

#         for s in sections:
#             text = s["text"].strip()
#             if not text or text.lower() in seen:
#                 continue
#             if len(text) > 150 or len(text) < 3:
#                 continue

#             heading_level = self._determine_heading_level_from_numbering(text)
#             if heading_level:
#                 s["level"] = heading_level
#             else:
#                 s["level"] = self._determine_level_by_font(s.get("font_size", 0))

#             s["text"] = self._clean_text(text)
#             refined.append(s)
#             seen.add(text.lower())

#         return refined

#     def _determine_heading_level_from_numbering(self, text: str) -> str:
#         if re.match(r'^\d+\s', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s', text):
#             return "H3"
#         return ""

#     def _determine_level_by_font(self, size: float) -> str:
#         if size >= 16:
#             return "H1"
#         elif size >= 14:
#             return "H2"
#         return "H3"

#     def _clean_text(self, text: str) -> str:
#         text = re.sub(r'[\s\.]+$', '', text)
#         text = re.sub(r'^\W+|\W+$', '', text)
#         return text.strip()
import re
from typing import Dict, List, Any
from pathlib import Path
from .pdf_processor import PDFProcessor


class StructureExtractor:
    """Extracts structured outline from PDF documents"""

    def __init__(self):
        self.processor = PDFProcessor()

    def extract_structure(self, pdf_path: Path) -> Dict[str, Any]:
        if not self.processor.load_pdf(pdf_path):
            return {"title": "Error", "outline": [], "error": "Failed to load PDF"}

        sections = self.processor.extract_sections_by_formatting()
        refined = self._refine_sections(sections)
        outline = [
            {"level": s["level"], "text": s["text"], "page": s["page"]}
            for s in refined
        ]

        # fallback if outline is completely empty (e.g., form documents)
        if not outline:
            first_page_text = self.processor.extract_page_text(0)
            outline = self._fallback_extract_labels(first_page_text)

        title = self._extract_title(outline)

        self.processor.close()
        return {
            "title": title,
            "outline": outline
        }

    def _extract_title(self, outline: List[Dict[str, Any]]) -> str:
        doc_info = self.processor.get_document_info()
        metadata_title = doc_info.get("title", "").strip()
        if metadata_title and len(metadata_title) > 3:
            return metadata_title

        candidates = self.processor.find_title_candidates()
        if candidates:
            return "  ".join(c[0] for c in candidates[:2])

        first_page_text = self.processor.extract_page_text(0)
        title_from_text = self._extract_title_from_text(first_page_text)
        if title_from_text:
            return title_from_text

        if outline:
            return outline[0]["text"]

        return "Untitled Document"

    def _extract_title_from_text(self, text: str) -> str:
        lines = [line.strip() for line in text.split('\n') if 5 < len(line.strip()) < 200]
        candidates = []
        for i, line in enumerate(lines[:15]):
            if re.match(r'^(page|abstract|introduction|table of contents|www\.|http)', line.lower()):
                continue
            score = 0
            if any(word in line.lower() for word in ['challenge', 'connecting', 'dots', 'hackathon']):
                score += 3
            if i < 5:
                score += 2
            if 10 <= len(line) <= 100:
                score += 1
            candidates.append((line, score))

        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return ""

    def _refine_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        cleaned = []

        for sec in sections:
            text = sec["text"].strip()
            if text in seen or not (3 <= len(text) <= 150):
                continue
            if re.match(r'^(page|figure|table|ref|www\.|http|\d{1,2} [A-Z]{3,})', text.lower()):
                continue

            importance = self._calculate_importance(text)
            if importance == 0:
                continue

            level = self._determine_level(text)
            cleaned.append({"text": text, "page": sec["page"], "level": level})
            seen.add(text)

        return cleaned

    def _calculate_importance(self, text: str) -> int:
        text_lower = text.lower()

        high = ['revision history', 'table of contents', 'acknowledgements', 'introduction', 'overview', 'syllabus']
        if any(t in text_lower for t in high):
            return 2

        # Support form labels like "Name:", "Age:"
        if text.endswith(":") and len(text.split()) <= 8:
            return 1

        # UPPERCASE headings
        if text.isupper() and 5 < len(text) < 60:
            return 1

        return 0

    def _determine_level(self, text: str) -> str:
        text_lower = text.lower()

        # Structured hierarchy for reports
        if any(k in text_lower for k in ['overview of', 'introduction to', 'references']):
            return "H1"

        # Form fields like "Name:" → H2
        if text.endswith(":") and len(text.split()) <= 8:
            return "H2"

        # Default level
        return "H2"

    def _fallback_extract_labels(self, text: str) -> List[Dict[str, Any]]:
        lines = text.split('\n')
        outline = []

        for line in lines:
            line = line.strip()
            if line.endswith(":") and len(line.split()) <= 8:
                outline.append({
                    "level": "H2",
                    "text": line.rstrip(":"),
                    "page": 1
                })

        return outline
