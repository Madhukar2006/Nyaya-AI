import os
import io
from werkzeug.utils import secure_filename
from config import Config


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """Get lowercase file extension."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def save_uploaded_file(file):
    """Save uploaded file and return (filepath, filename)."""
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    # Prevent overwriting by adding a prefix if file exists
    base, ext = os.path.splitext(filename)
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        counter += 1
    file.save(filepath)
    return filepath, filename


def extract_text(filepath, filename):
    """
    Extract text from a file based on its extension.
    Supports: PDF, DOCX, TXT, MD
    Returns (extracted_text, error_message)
    """
    ext = get_file_extension(filename)

    if ext == 'pdf':
        return _extract_from_pdf(filepath)
    elif ext == 'docx':
        return _extract_from_docx(filepath)
    elif ext in ('txt', 'md'):
        return _extract_from_text(filepath)
    else:
        return None, f"Unsupported file type: .{ext}"


def _extract_from_pdf(filepath):
    """Extract text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        if len(reader.pages) == 0:
            return None, 'The PDF appears to be empty.'
        text = ''
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
        if not text.strip():
            return None, 'Could not extract text from this PDF. It may be a scanned image (no selectable text).'
        return text.strip(), None
    except ImportError:
        return None, 'PDF support requires the pypdf library. Please run: pip install pypdf'
    except Exception as e:
        return None, f'Error reading PDF: Could not process the file. Please ensure it is a valid PDF.'


def _extract_from_docx(filepath):
    """Extract text from a DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            return None, 'The DOCX document appears to be empty or contains no readable text.'
        return '\n'.join(paragraphs).strip(), None
    except ImportError:
        return None, 'DOCX support requires python-docx. Please run: pip install python-docx'
    except Exception as e:
        return None, 'Error reading DOCX: Could not process the file. Please ensure it is a valid Word document.'


def _extract_from_text(filepath):
    """Extract text from TXT or MD files."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        if not text.strip():
            return None, 'The file appears to be empty.'
        return text.strip(), None
    except Exception as e:
        return None, 'Error reading file: Could not read the text file.'


def cleanup_file(filepath):
    """Delete a file after processing."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass  # Silent fail — don't expose internal errors
