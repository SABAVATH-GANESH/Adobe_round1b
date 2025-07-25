"""
PDF Processing utilities for extracting text and structure from PDF documents
"""

import fitz  # PyMuPDF
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

class PDFProcessor:
    """Base class for PDF processing operations"""
    
    def __init__(self):
        self.doc = None
        self.page_count = 0
        
    def load_pdf(self, pdf_path: Path) -> bool:
        """Load PDF document"""
        try:
            self.doc = fitz.open(pdf_path)
            self.page_count = len(self.doc)
            return True
        except Exception as e:
            print(f"Error loading PDF {pdf_path}: {str(e)}")
            return False
    
    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
            self.doc = None
    
    def extract_text_with_formatting(self, page_num: int) -> List[Dict[str, Any]]:
        """Extract text with formatting information from a specific page"""
        if not self.doc or page_num >= self.page_count:
            return []
        
        page = self.doc[page_num]
        text_dict = page.get_text("dict")
        
        blocks = []
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            blocks.append({
                                "text": span["text"],
                                "font": span.get("font", ""),
                                "size": span.get("size", 0),
                                "flags": span.get("flags", 0),
                                "bbox": span.get("bbox", [0, 0, 0, 0]),
                                "page": page_num
                            })
        
        return blocks
    
    def extract_page_text(self, page_num: int) -> str:
        """Extract plain text from a specific page"""
        if not self.doc or page_num >= self.page_count:
            return ""
        
        page = self.doc[page_num]
        return page.get_text()
    
    def extract_all_text(self) -> str:
        """Extract all text from the document"""
        if not self.doc:
            return ""
        
        full_text = ""
        for page_num in range(self.page_count):
            full_text += self.extract_page_text(page_num) + "\n"
        
        return full_text
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get document metadata"""
        if not self.doc:
            return {}
        
        metadata = self.doc.metadata
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": self.page_count
        }
    
    def find_title_candidates(self) -> List[Tuple[str, float, int]]:
        """Find potential document titles based on text analysis"""
        if not self.doc:
            return []
        
        candidates = []
        
        # Check first few pages for title candidates
        for page_num in range(min(3, self.page_count)):
            blocks = self.extract_text_with_formatting(page_num)
            
            for block in blocks:
                text = block["text"].strip()
                if len(text) > 5 and len(text) < 200:  # Reasonable title length
                    # Score based on font size, position, and formatting
                    score = self._calculate_title_score(block, page_num)
                    if score > 0:
                        candidates.append((text, score, page_num))
        
        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
    
    def _calculate_title_score(self, block: Dict[str, Any], page_num: int) -> float:
        """Calculate title score based on formatting and position"""
        score = 0.0
        
        # Font size contribution
        size = block.get("size", 0)
        if size > 16:
            score += 2.0
        elif size > 14:
            score += 1.5
        elif size > 12:
            score += 1.0
        
        # Bold formatting
        flags = block.get("flags", 0)
        if flags & 2**4:  # Bold flag
            score += 1.0
        
        # Position on page (higher = better for title)
        bbox = block.get("bbox", [0, 0, 0, 0])
        y_pos = bbox[1]
        if y_pos < 200:  # Top of page
            score += 1.0
        
        # First page bonus
        if page_num == 0:
            score += 0.5
        
        # Penalize very long text
        text_length = len(block["text"])
        if text_length > 100:
            score -= 0.5
        
        return score
    
    def extract_sections_by_formatting(self) -> List[Dict[str, Any]]:
        """Extract sections based on formatting patterns"""
        sections = []
        
        for page_num in range(self.page_count):
            blocks = self.extract_text_with_formatting(page_num)
            
            for block in blocks:
                text = block["text"].strip()
                if self._is_potential_heading(block, text):
                    level = self._determine_heading_level(block)
                    sections.append({
                        "text": text,
                        "level": level,
                        "page": page_num + 1,  # 1-based page numbering
                        "font_size": block.get("size", 0),
                        "font": block.get("font", "")
                    })
        
        return sections
    
    def _is_potential_heading(self, block: Dict[str, Any], text: str) -> bool:
        """Determine if a text block is likely a heading"""
        # Basic filters
        if len(text) < 3 or len(text) > 150:
            return False
        
        # Check for heading patterns
        heading_patterns = [
            r'^\d+\.?\s+[A-Z]',  # Numbered headings
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',  # Title Case
            r'^\d+\.\d+\.?\s+',  # Numbered subsections
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        # Check formatting
        size = block.get("size", 0)
        flags = block.get("flags", 0)
        
        # Larger font size
        if size > 12:
            return True
        
        # Bold formatting
        if flags & 2**4:
            return True
        
        return False
    
    def _determine_heading_level(self, block: Dict[str, Any]) -> str:
        """Determine heading level based on formatting"""
        size = block.get("size", 0)
        text = block["text"].strip()
        
        # Check for numbered patterns
        if re.match(r'^\d+\.?\s+', text):
            return "H1"
        elif re.match(r'^\d+\.\d+\.?\s+', text):
            return "H2"
        elif re.match(r'^\d+\.\d+\.\d+\.?\s+', text):
            return "H3"
        
        # Font size based classification
        if size >= 16:
            return "H1"
        elif size >= 14:
            return "H2"
        else:
            return "H3"
