"""
Utility functions for the PDF Intelligence System
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def load_json_safely(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load JSON file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {str(e)}")
        return None

def save_json_safely(data: Dict[str, Any], file_path: Path) -> bool:
    """Safely save JSON file with error handling"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON to {file_path}: {str(e)}")
        return False

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    import re
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)
    
    return text.strip()

def extract_keywords_simple(text: str, min_length: int = 3) -> set:
    """Simple keyword extraction"""
    import re
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())
    
    # Common stop words
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

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity using Jaccard coefficient"""
    keywords1 = extract_keywords_simple(text1)
    keywords2 = extract_keywords_simple(text2)
    
    if not keywords1 and not keywords2:
        return 0.0
    
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def validate_pdf_path(pdf_path: Path) -> bool:
    """Validate PDF file path"""
    return (
        pdf_path.exists() and 
        pdf_path.is_file() and 
        pdf_path.suffix.lower() == '.pdf'
    )

def create_error_response(error_message: str, round_type: str = "1A") -> Dict[str, Any]:
    """Create standardized error response"""
    if round_type == "1A":
        return {
            "title": "Error",
            "outline": [],
            "error": error_message
        }
    else:  # Round 1B
        return {
            "metadata": {
                "documents": [],
                "persona": "Unknown",
                "job_to_be_done": "Unknown",
                "timestamp": "",
                "error": error_message
            },
            "extracted_sections": [],
            "subsection_analysis": []
        }
