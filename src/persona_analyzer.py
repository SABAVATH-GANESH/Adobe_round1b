import json
import time
import re
from typing import Dict, List, Any
from pathlib import Path
from collections import defaultdict
from .pdf_processor import PDFProcessor
from .structure_extractor import StructureExtractor
from sentence_transformers import SentenceTransformer, util
import torch

class PersonaAnalyzer:
    def __init__(self):
        self.processor = PDFProcessor()
        self.extractor = StructureExtractor()
        self.embedder = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.persona = ""
        self.job_to_be_done = ""

    def analyze_documents(self, pdf_files: List[Path], config: Dict[str, Any]) -> Dict[str, Any]:
        self.persona = config.get("persona", "")
        self.job_to_be_done = config.get("job_to_be_done", "")

        documents = self._extract_document_contents(pdf_files)
        relevant_sections = self._extract_relevant_sections(documents)
        subsection_analysis = self._refine_sections_content(relevant_sections)

        return {
            "metadata": {
                "input_documents": [f.name.replace("_", " ") for f in pdf_files],
                "persona": self.persona,
                "job_to_be_done": self.job_to_be_done,
                "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            },
            "extracted_sections": [
                {
                    "document": s["document"].replace("_", " "),
                    "section_title": s["section_title"],
                    "importance_rank": i + 1,
                    "page_number": s["page"]
                }
                for i, s in enumerate(relevant_sections)
            ],
            "subsection_analysis": subsection_analysis
        }

    def _extract_document_contents(self, pdf_files: List[Path]) -> List[Dict[str, Any]]:
        docs = []
        for pdf in pdf_files:
            if not self.processor.load_pdf(pdf):
                continue
            structure = self.extractor.extract_structure(pdf)
            full_text = self.processor.extract_all_text()
            sections = self.processor.extract_sections_by_formatting()
            enriched = []
            for sec in sections:
                page_num = sec["page"] - 1
                if page_num < self.processor.page_count:
                    page_text = self.processor.extract_page_text(page_num)
                    content = self._extract_section_content(page_text, sec["text"])
                    enriched.append({
                        "document": pdf.name,
                        "section_title": sec["text"],
                        "page": sec["page"],
                        "combined": f"{sec['text']} {content}".strip()
                    })
            docs.extend(enriched)
            self.processor.close()
        return docs

    def _extract_section_content(self, page_text: str, section_title: str) -> str:
        lines = page_text.split('\n')
        start_line = -1
        for i, line in enumerate(lines):
            if section_title.lower() in line.lower():
                start_line = i
                break
        if start_line == -1:
            return ""
        end_line = len(lines)
        for i in range(start_line + 1, len(lines)):
            if self._looks_like_heading(lines[i].strip()):
                end_line = i
                break
        return '\n'.join(lines[start_line + 1:end_line]).strip()

    def _looks_like_heading(self, text: str) -> bool:
        if len(text) < 3 or len(text) > 150:
            return False
        patterns = [r'^\d+\.?\s+[A-Z]', r'^[A-Z][A-Z\s]+$', r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$']
        return any(re.match(p, text) for p in patterns)

    def _extract_relevant_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        query = f"{self.persona}. {self.job_to_be_done}"
        q_embed = self.embedder.encode(query, convert_to_tensor=True)
        seen = set()
        scored = []
        for s in sections:
            key = (s["document"], s["section_title"])
            if key in seen:
                continue
            seen.add(key)
            sec_embed = self.embedder.encode(s["combined"], convert_to_tensor=True)
            sim = util.pytorch_cos_sim(q_embed, sec_embed).item()
            if sim > 0.2:
                s["score"] = sim
                scored.append(s)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:5]  # Limit to top 5 most relevant

    def _refine_sections_content(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        refined = []
        for s in sections:
            refined.append({
                "document": s["document"].replace("_", " "),
                "page_number": s["page"],
                "refined_text": f"Key insights from '{s['section_title']}' relevant to {self.persona} for {self.job_to_be_done}."
            })