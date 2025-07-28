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
