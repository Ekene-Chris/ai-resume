# app/utils/file_utils.py
import io
import logging
from typing import Optional
import aiohttp
import asyncio

# Try to import PDF and DOCX handling libraries
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

logger = logging.getLogger(__name__)

async def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyPDF2
    
    Args:
        pdf_bytes: PDF content as bytes
        
    Returns:
        Extracted text
    """
    if not PDF_SUPPORT:
        return "[PDF extraction requires PyPDF2 library]"
    
    try:
        text = ""
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return f"[Error extracting PDF text: {str(e)}]"

async def extract_text_from_docx_bytes(docx_bytes: bytes) -> str:
    """
    Extract text from DOCX bytes using python-docx
    
    Args:
        docx_bytes: DOCX content as bytes
        
    Returns:
        Extracted text
    """
    if not DOCX_SUPPORT:
        return "[DOCX extraction requires python-docx library]"
    
    try:
        text = ""
        docx_file = io.BytesIO(docx_bytes)
        doc = docx.Document(docx_file)
        
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        # Also extract tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " | "
                text += "\n"
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return f"[Error extracting DOCX text: {str(e)}]"

async def download_file(url: str) -> Optional[bytes]:
    """
    Download a file from a URL
    
    Args:
        url: The URL to download from
        
    Returns:
        The file content as bytes, or None if download fails
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"Failed to download file: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return None