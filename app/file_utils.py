# app/file_utils.py
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
    logging.error("PyPDF2 library not installed. PDF support is disabled.")

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    logging.error("python-docx library not installed. DOCX support is disabled.")

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
        logger.error("PDF extraction failed: PyPDF2 library not installed")
        raise ImportError("PDF extraction requires PyPDF2 library")
    
    try:
        text = ""
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Log PDF details
        logger.info(f"PDF contains {len(pdf_reader.pages)} pages")
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            text += page_text + "\n\n"
            
            # Log empty pages
            if not page_text.strip():
                logger.warning(f"Page {page_num + 1} appears to be empty or contains no extractable text")
        
        # Log if extracted text is too short
        if len(text.strip()) < 100:
            logger.warning(f"Extracted PDF text is suspiciously short ({len(text.strip())} chars)")
            
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
        raise  # Re-raise the exception instead of returning an error string

async def extract_text_from_docx_bytes(docx_bytes: bytes) -> str:
    """
    Extract text from DOCX bytes using python-docx
    
    Args:
        docx_bytes: DOCX content as bytes
        
    Returns:
        Extracted text
    """
    if not DOCX_SUPPORT:
        logger.error("DOCX extraction failed: python-docx library not installed")
        raise ImportError("DOCX extraction requires python-docx library")
    
    try:
        text = ""
        docx_file = io.BytesIO(docx_bytes)
        doc = docx.Document(docx_file)
        
        # Log document details
        logger.info(f"DOCX contains {len(doc.paragraphs)} paragraphs and {len(doc.tables)} tables")
        
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        # Also extract tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " | "
                text += "\n"
        
        # Log if extracted text is too short
        if len(text.strip()) < 100:
            logger.warning(f"Extracted DOCX text is suspiciously short ({len(text.strip())} chars)")
            
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}", exc_info=True)
        raise  # Re-raise the exception instead of returning an error string

async def download_file(url: str) -> Optional[bytes]:
    """
    Download a file from a URL
    
    Args:
        url: The URL to download from
        
    Returns:
        The file content as bytes, or None if download fails
    """
    try:
        logger.info(f"Downloading file from URL: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    logger.info(f"Successfully downloaded file: {len(content)} bytes")
                    return content
                else:
                    logger.error(f"Failed to download file: HTTP {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error response: {error_text[:200]}...")
                    raise Exception(f"Failed to download file: HTTP {response.status}")
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}", exc_info=True)
        raise  # Re-raise instead of returning None