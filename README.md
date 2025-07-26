# Round 1A: PDF Structure Extractor

An intelligent PDF analysis tool that extracts hierarchical outline structures from PDF documents using advanced font analysis and pattern recognition techniques.

## 🎯 Project Overview

The PDF Structure Extractor is designed to automatically analyze PDF documents and generate structured outlines by identifying headings, sections, and hierarchical elements. It uses sophisticated font analysis, pattern matching, and text processing to understand document structure without relying on embedded bookmarks or table of contents.

## ✨ Key Features

- **Intelligent Font Analysis**: Identifies headings based on font size, style, weight, and formatting
- **Pattern Recognition**: Detects various heading patterns including:
  - Numbered sections (1., 1.1., 1.1.1.)
  - Chapter/Section markers
  - Roman numerals (I, II, III, IV)
  - Alphabetic markers (A, B, C)
  - Common document sections (Introduction, Conclusion, Abstract, etc.)
- **Form Field Filtering**: Excludes form fields and table entries from outline extraction
- **Multi-page Processing**: Handles documents of any length with page-level tracking
- **Robust Error Handling**: Graceful handling of corrupted or problematic PDF files
- **JSON Output**: Structured, machine-readable output format

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PyMuPDF library
- NumPy for numerical computations
- Flask (optional, for web interface)

### Installation

#### Method 1: Direct Python Setup
```bash
# Navigate to the project directory
cd round1a

# Install dependencies
pip install -r requirements.txt

# Run the extractor
python pdf_extractor.py
```

#### Method 2: Docker (Recommended)
```bash
# Build the Docker image
docker build -t pdf-structure-extractor .

# Run with volume mounting for input/output
docker run -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" pdf-structure-extractor
```

### Basic Usage

1. **Place PDF files** in the `input/` directory
2. **Run the extractor**:
   ```bash
   python pdf_extractor.py
   ```
3. **Check results** in the `output/` directory

## 📁 Project Structure

```
round1a/
├── pdf_extractor.py          # Main extraction engine (422 lines)
├── input/                    # Input PDF files directory
│   ├── file01.pdf           # Sample: Application form
│   ├── file02.pdf           # Sample: Document 2
│   ├── file03.pdf           # Sample: Document 3
│   ├── file04.pdf           # Sample: Document 4
│   └── file05.pdf           # Sample: Document 5
├── output/                   # Generated JSON outputs
│   ├── file01.json          # Extracted structure for file01.pdf
│   ├── file02.json          # Extracted structure for file02.pdf
│   ├── file03.json          # Extracted structure for file03.pdf
│   ├── file04.json          # Extracted structure for file04.pdf
│   └── file05.json          # Extracted structure for file05.pdf
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
└── README.md               # This documentation
```

## 🔧 Technical Architecture

### Core Components

#### 1. TextElement Class
```python
@dataclass
class TextElement:
    text: str                    # Extracted text content
    font_name: str              # Font family name
    font_size: float            # Font size in points
    font_flags: int             # Font style flags (bold, italic, etc.)
    page_num: int               # Source page number
    bbox: Tuple[float, ...]     # Bounding box coordinates
    y_position: float           # Vertical position on page
```

#### 2. Heading Class
```python
@dataclass
class Heading:
    level: str                  # Heading level (H1, H2, H3, etc.)
    text: str                   # Heading text content
    page: int                   # Page number where heading appears
```

#### 3. PDFStructureExtractor Class
Main processing engine with methods for:
- Text extraction with formatting preservation
- Font analysis and size clustering
- Pattern-based heading detection
- Hierarchical level assignment
- JSON output generation

### Algorithm Flow

1. **Text Extraction**: Extract all text blocks with complete formatting information
2. **Font Analysis**: Analyze font sizes, weights, and styles across the document
3. **Pattern Matching**: Apply regex patterns to identify potential headings
4. **Clustering**: Group similar font characteristics to determine heading levels
5. **Filtering**: Remove form fields, table entries, and noise
6. **Hierarchy Generation**: Assign hierarchical levels (H1, H2, H3, etc.)
7. **Output Generation**: Create structured JSON with metadata

## 📋 Input/Output Format

### Input
- **Supported Formats**: PDF files (.pdf)
- **Location**: `input/` directory
- **Requirements**: No special formatting or embedded bookmarks needed

### Output Format
```json
{
  "title": "Document Title (if detectable)",
  "outline": [
    {
      "level": "H1",
      "text": "Main Section Heading",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "Subsection Heading",
      "page": 2
    }
  ]
}
```

### Sample Output
```json
{
  "title": "Application form for grant of LTC advance",
  "outline": [
    {
      "level": "H1",
      "text": "1. Name of the Government Servant",
      "page": 1
    },
    {
      "level": "H1",
      "text": "2. Designation", 
      "page": 1
    },
    {
      "level": "H1",
      "text": "12. Amount of advance required. Rs.",
      "page": 1
    }
  ]
}
```

## 🐳 Docker Configuration

### Dockerfile Features
- **Base Image**: Python 3.11-slim for optimal size and performance
- **System Dependencies**: Includes libraries required for PyMuPDF
- **Multi-stage Optimization**: Efficient layer caching for faster builds
- **Volume Support**: Configurable input/output directories

### Docker Commands
```bash
# Build the image
docker build -t pdf-structure-extractor .

# Run with current directory mounting
docker run -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" pdf-structure-extractor

# Run with custom input/output paths
docker run -v "/path/to/pdfs:/app/input" -v "/path/to/results:/app/output" pdf-structure-extractor
```

## ⚙️ Configuration Options

### Environment Variables
- `PYTHONUNBUFFERED=1`: Ensures real-time log output
- `PYTHONPATH=/app`: Sets Python module search path

### Logging Configuration
- **Level**: DEBUG (detailed processing information)
- **Format**: Timestamp, level, and message
- **Output**: Console with structured formatting

## 🔍 Pattern Recognition Details

### Supported Heading Patterns
1. **Numbered Sections**: `1.`, `1.1.`, `1.1.1.`
2. **Chapter Markers**: `Chapter 1`, `Section A`
3. **Roman Numerals**: `I.`, `II.`, `III.`
4. **Alphabetic**: `A.`, `B.`, `C.`
5. **Document Sections**: `Introduction`, `Conclusion`, `Abstract`

### Form Field Exclusions
- Table headers and data entries
- Signature lines and date fields
- Version history tables
- Revision tracking information

## 📊 Performance Characteristics

- **Processing Speed**: Fast text extraction with minimal memory usage
- **Scalability**: Handles documents from single pages to hundreds of pages
- **Accuracy**: High precision in identifying actual headings vs. noise
- **Memory Efficiency**: Processes large documents without excessive RAM usage

## 🛠️ Dependencies

```txt
PyMuPDF==1.23.8     # PDF processing and text extraction
numpy==1.24.3       # Numerical computations for font analysis
Flask               # Optional web interface framework
Flask-CORS          # Cross-origin resource sharing for web API
```

## 🚨 Error Handling

The extractor includes comprehensive error handling:
- **Corrupted PDFs**: Graceful handling with detailed error logging
- **Missing Fonts**: Fallback font analysis when font information is unavailable
- **Empty Documents**: Proper handling of empty or image-only PDFs
- **Memory Issues**: Efficient memory management for large documents

## 🔧 Customization

### Extending Pattern Recognition
Add custom heading patterns to the `common_heading_patterns` list:
```python
self.common_heading_patterns = [
    r'^(?:chapter|section|part)\s+\d+',
    r'^\d+\.\s+.+',
    # Add your custom patterns here
    r'^your_custom_pattern',
]
```

### Modifying Font Analysis
Adjust font size thresholds and clustering parameters in the `PDFStructureExtractor` class.

## 🎯 Use Cases

- **Document Indexing**: Generate table of contents for large documents
- **Content Management**: Automated document structure analysis
- **Accessibility**: Create navigation aids for screen readers
- **Data Mining**: Extract structured information from PDF repositories
- **Legal Documents**: Analyze contracts, regulations, and legal texts
- **Academic Papers**: Extract paper sections and hierarchies

## 🤝 Integration

### API Integration
The extractor can be integrated with web services using Flask:
```python
from pdf_extractor import PDFStructureExtractor

extractor = PDFStructureExtractor()
result = extractor.extract_structure("document.pdf")
```

### Batch Processing
Process multiple PDFs programmatically:
```python
from pathlib import Path

input_dir = Path("input")
output_dir = Path("output")

for pdf_file in input_dir.glob("*.pdf"):
    result = extractor.extract_structure(str(pdf_file))
    output_file = output_dir / f"{pdf_file.stem}.json"
    # Save result to JSON
```

## 📈 Future Enhancements

- **Machine Learning Integration**: Train models on document structure patterns
- **Multi-language Support**: Enhanced support for non-English documents
- **OCR Integration**: Handle scanned documents with text recognition
- **Advanced Formatting**: Detect tables, lists, and other structural elements
- **Web Interface**: Complete Flask-based web application
- **API Endpoints**: RESTful API for remote processing

---

**Developed for Adobe Hackathon 2025** | **Round 1A: PDF Structure Extraction**
