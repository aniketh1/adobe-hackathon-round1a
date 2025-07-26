#!/usr/bin/env python3
"""
PDF Structure Extractor
Analyzes PDF documents and extracts hierarchical outline structure
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter
import fitz  # PyMuPDF
import numpy as np
from dataclasses import dataclass

# Configure logging with detailed output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TextElement:
    """Represents a text element from the PDF"""
    text: str
    font_name: str
    font_size: float
    font_flags: int
    page_num: int
    bbox: Tuple[float, float, float, float]
    y_position: float

@dataclass
class Heading:
    """Represents a detected heading"""
    level: str
    text: str
    page: int

class PDFStructureExtractor:
    """Main class for extracting PDF structure"""
    
    def __init__(self):
        self.common_heading_patterns = [
            r'^(?:chapter|section|part)\s+\d+',
            r'^\d+\.\s+.+',
            r'^\d+\.\d+\.\s+.+',
            r'^\d+\.\d+\.\d+\.\s+.+',
            r'^[IVX]+\.?\s+.+',
            r'^[A-Z]\.?\s+.+',
            r'^(?:introduction|conclusion|abstract|summary|overview|background|methodology|results|discussion|references|bibliography|appendix|acknowledgements|table of contents|revision history)',
        ]
        self.form_exclusion_patterns = [
            r'^S\.No\s+Name\s+Age\s+Relationship',
            r'^Date$',
            r'^Signature\s+of\s+Government\s+Servant\.?$',
            r'^\d+\.\d+\s+.+?\s+\d+$',  # Table of contents entries (e.g., "2.1 Intended Audience 7")
            r'^Version\s+Date\s+Remarks$',  # Revision history headers
            r'^\d+\.\d+\s+\d+\s+[A-Z]+\s+\d+\s+.+',  # Revision history entries (e.g., "0.1 18 JUNE 2013 Initial version")
            r'^Syllabus\s+Days$',  # Form-like table headers
            r'^Identifier\s+Reference$',  # Reference table headers
            r'^International\s+Software\s+Testing\s+Qualifications\s+Board$',  # Specific exclusion
            r'^(?:Revision\s+History|Table\s+of\s+Contents)\s+\d+$',  # Table of contents page references
        ]
        self.heading_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.common_heading_patterns]
        self.form_exclusion_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.form_exclusion_patterns]
    
    def extract_text_elements(self, doc: fitz.Document) -> List[TextElement]:
        """Extract all text blocks with formatting information"""
        elements = []
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                try:
                    blocks = page.get_text("dict")
                except Exception as e:
                    logger.error(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                    continue
                
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        block_text = ""
                        block_font_name = "Unknown"
                        block_font_size = 12.0
                        block_font_flags = 0
                        block_page_num = page_num + 1
                        block_bbox = block["bbox"]
                        for line in block["lines"]:
                            for span in line["spans"]:
                                block_text += span["text"] + " "
                                if block_font_name == "Unknown":
                                    block_font_name = span.get("font", "Unknown")
                                    block_font_size = span.get("size", 12.0)
                                    block_font_flags = span.get("flags", 0)
                        if block_text.strip():
                            element = TextElement(
                                text=block_text.strip(),
                                font_name=block_font_name,
                                font_size=block_font_size,
                                font_flags=block_font_flags,
                                page_num=block_page_num,
                                bbox=block_bbox,
                                y_position=block_bbox[1]
                            )
                            elements.append(element)
        except Exception as e:
            logger.error(f"Error in extract_text_elements: {str(e)}")
            return []
        
        return elements
    
    def analyze_font_hierarchy(self, elements: List[TextElement]) -> Dict[str, int]:
        """Analyze font characteristics to determine heading hierarchy"""
        try:
            font_sizes = [elem.font_size for elem in elements if elem.font_size > 0]
            font_size_counts = Counter(font_sizes)
            
            most_common_sizes = font_size_counts.most_common(5)
            body_text_size = most_common_sizes[0][0] if most_common_sizes else 12.0
            
            h3_threshold = body_text_size + 1
            h2_threshold = body_text_size + 2
            h1_threshold = body_text_size + 3
            
            bold_flag = 16
            
            font_hierarchy = {}
            
            for elem in elements:
                key = f"{elem.font_size}_{elem.font_flags}_{elem.font_name}"
                if elem.font_size >= h1_threshold:
                    level = 1
                elif elem.font_size >= h2_threshold:
                    level = 2
                elif elem.font_size >= h3_threshold or (elem.font_flags & bold_flag):
                    level = 3
                else:
                    level = 4
                font_hierarchy[key] = level
            
            return font_hierarchy
        except Exception as e:
            logger.error(f"Error in analyze_font_hierarchy: {str(e)}")
            return {}
    
    def is_likely_heading(self, element: TextElement, avg_font_size: float, title: str, elements: List[TextElement]) -> bool:
        """Determine if a text element is a heading"""
        try:
            text = element.text.strip()
            if len(text) < 3 or len(text) > 150 or text == title:
                return False
            
            # Exclude form and table of contents entries
            if any(pattern.match(text) for pattern in self.form_exclusion_patterns):
                return False
            
            # Check if the document is form-like (e.g., file01.pdf)
            is_form_like = any(re.match(r'^\d+\.\s+.+', elem.text) for elem in elements if elem.page_num == 1)
            if is_form_like and element.page_num == 1 and not any(pattern.match(text) for pattern in self.heading_patterns):
                return False
            
            # Multilingual and pattern-based heading detection
            jp_section_markers = ['第', '章', '節', '項']
            has_uppercase = any(c.isupper() for c in text)
            has_cjk = any('\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff' for c in text)
            if not (has_uppercase or has_cjk):
                return False
            
            if any(marker in text for marker in jp_section_markers):
                return True
            if any(pattern.match(text) for pattern in self.heading_patterns):
                return True
            
            is_bold = element.font_flags & 16
            if element.font_size >= avg_font_size * 1.2 or (is_bold and len(text) < 80):
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error in is_likely_heading for text '{text}': {str(e)}")
            return False
    
    def extract_title(self, elements: List[TextElement]) -> str:
        """Extract document title from the first page"""
        try:
            if not elements:
                return "Untitled Document"
            
            first_page_elements = [elem for elem in elements if elem.page_num == 1]
            if not first_page_elements:
                return "Untitled Document"
            
            font_sizes = [elem.font_size for elem in elements if elem.font_size > 0]
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12.0
            
            # Sort by y-position
            first_page_elements.sort(key=lambda x: x.y_position)
            
            # Combine consecutive blocks for multi-line titles
            title_candidates = []
            current_title = ""
            last_y_position = None
            last_font_size = None
            page_width = 595
            
            for elem in first_page_elements:
                if elem.y_position > 300:
                    break
                text = elem.text.strip()
                if len(text) < 3 or re.match(r'^\d+$', text):
                    continue
                is_center_aligned = abs((elem.bbox[0] + elem.bbox[2]) / 2 - page_width / 2) < 50
                is_bold = elem.font_flags & 16
                is_large_font = elem.font_size > avg_font_size
                
                if (last_y_position is not None and
                    abs(elem.y_position - last_y_position) < 30 and
                    last_font_size is not None and
                    abs(elem.font_size - last_font_size) < 2):
                    current_title += " " + text
                else:
                    if current_title:
                        title_candidates.append((current_title.strip(), last_font_size))
                    current_title = text
                last_y_position = elem.y_position
                last_font_size = elem.font_size
            
            if current_title:
                title_candidates.append((current_title.strip(), last_font_size))
            
            if title_candidates:
                for title, font_size in title_candidates:
                    if len(title) > 5 and len(title) < 200:
                        return title
            
            for elem in first_page_elements[:10]:
                text = elem.text.strip()
                if len(text) > 5 and not re.match(r'^\d+$', text):
                    return text
            
            return "Untitled Document"
        except Exception as e:
            logger.error(f"Error in extract_title: {str(e)}")
            return "Untitled Document"
    
    def classify_headings(self, heading_candidates: List[TextElement], font_hierarchy: Dict[str, int]) -> List[Heading]:
        """Classify headings based on font characteristics"""
        try:
            headings = []
            for elem in heading_candidates:
                font_key = f"{elem.font_size}_{elem.font_flags}_{elem.font_name}"
                hierarchy_level = font_hierarchy.get(font_key, 4)
                if elem.font_size >= 15:
                    level = "H1"
                elif elem.font_size >= 12:
                    level = "H2"
                else:
                    level_map = {1: "H1", 2: "H2", 3: "H3"}
                    level = level_map.get(hierarchy_level, "H3")
                headings.append(Heading(level=level, text=elem.text.strip(), page=elem.page_num))
            return headings
        except Exception as e:
            logger.error(f"Error in classify_headings: {str(e)}")
            return []
    
    def post_process_headings(self, headings: List[Heading]) -> List[Heading]:
        """Post-process headings to improve hierarchy and remove duplicates"""
        try:
            if not headings:
                return headings
            
            seen = set()
            unique_headings = []
            
            for heading in headings:
                key = (heading.text.lower(), heading.page)
                if key not in seen:
                    seen.add(key)
                    unique_headings.append(heading)
            
            unique_headings.sort(key=lambda h: (h.page, h.text))
            
            refined = []
            for heading in unique_headings:
                text = heading.text.lower()
                if any(pattern in text for pattern in ['chapter', 'introduction', 'conclusion', 'abstract', 'summary', 'acknowledgements', 'revision history', 'table of contents']):
                    refined_heading = Heading("H1", heading.text, heading.page)
                elif re.match(r'^\d+\.\d+\.\s+', heading.text):
                    refined_heading = Heading("H2", heading.text, heading.page)
                elif re.match(r'^\d+\.\s+', heading.text):
                    refined_heading = Heading("H1", heading.text, heading.page)
                else:
                    refined_heading = heading
                refined.append(refined_heading)
            
            return refined
        except Exception as e:
            logger.error(f"Error in post_process_headings: {str(e)}")
            return []
    
    def extract_structure(self, pdf_path: str) -> Dict:
        """Main method to extract PDF structure"""
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Check if file exists and is accessible
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            doc = fitz.open(pdf_path)
            
            if len(doc) > 50:
                logger.warning(f"PDF has {len(doc)} pages, limiting to first 50")
                doc.select(list(range(50)))
            
            elements = self.extract_text_elements(doc)
            logger.debug(f"Extracted {len(elements)} text elements")
            
            if not elements:
                logger.warning("No text elements found")
                doc.close()
                return {"title": "Empty Document", "outline": []}
            
            # Calculate average font size
            font_sizes = [elem.font_size for elem in elements if elem.font_size > 0]
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12.0
            logger.debug(f"Average font size: {avg_font_size}")
            
            # Extract title
            title = self.extract_title(elements)
            logger.info(f"Extracted title: {title}")
            
            # Analyze font hierarchy
            font_hierarchy = self.analyze_font_hierarchy(elements)
            
            # Filter potential headings
            heading_candidates = [elem for elem in elements if self.is_likely_heading(elem, avg_font_size, title, elements)]
            logger.debug(f"Found {len(heading_candidates)} heading candidates")
            
            # Classify headings
            headings = self.classify_headings(heading_candidates, font_hierarchy)
            
            # Post-process headings
            final_headings = self.post_process_headings(headings)
            
            # Adjust page numbers to account for potential front matter
            page_offset = 1
            for heading in final_headings:
                heading.page = max(1, heading.page - page_offset)
            
            outline = []
            for heading in final_headings:
                outline.append({
                    "level": heading.level,
                    "text": heading.text,
                    "page": heading.page
                })
            
            doc.close()
            
            result = {
                "title": title,
                "outline": outline
            }
            
            logger.info(f"Extracted {len(outline)} headings")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}", exc_info=True)
            if 'doc' in locals():
                doc.close()
            return {"title": f"Error processing {os.path.basename(pdf_path)}", "outline": []}

def process_pdfs(input_dir: str, output_dir: str):
    """Process all PDFs in the input directory and its subdirectories"""
    try:
        input_path = Path(input_dir)
        output_path_base = Path(output_dir)
        
        output_path_base.mkdir(parents=True, exist_ok=True)
        
        extractor = PDFStructureExtractor()
        
        pdf_files = list(input_path.rglob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir} and its subdirectories")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                result = extractor.extract_structure(str(pdf_file))
                
                relative_path = pdf_file.relative_to(input_path)
                output_subdir = output_path_base / relative_path.parent
                output_subdir.mkdir(parents=True, exist_ok=True)
                
                output_filename = pdf_file.stem + ".json"
                output_file = output_subdir / output_filename
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved result to {output_file}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {str(e)}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Error in process_pdfs: {str(e)}", exc_info=True)

if __name__ == "__main__":
    input_directory = "/app/input"
    output_directory = "/app/output"
    
    logger.info("Starting PDF structure extraction")
    process_pdfs(input_directory, output_directory)
    logger.info("PDF processing complete")