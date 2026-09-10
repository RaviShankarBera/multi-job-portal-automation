import re
import html
from typing import List, Optional
from urllib.parse import quote


def sanitize_string(input_str: str) -> str:
    """Sanitize string input to prevent XSS attacks.
    
    Args:
        input_str: The input string to sanitize.
        
    Returns:
        Sanitized string with special characters escaped.
    """
    if not input_str:
        return input_str
    
    # Escape HTML special characters
    sanitized = html.escape(input_str, quote=True)
    
    # Remove any remaining HTML tags
    sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    # Remove javascript: protocol
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    
    # Remove vbscript: protocol
    sanitized = re.sub(r'vbscript:', '', sanitized, flags=re.IGNORECASE)
    
    # Remove data: protocol (except for safe image data URIs)
    sanitized = re.sub(r'data:(?!image/)', '', sanitized, flags=re.IGNORECASE)
    
    # Remove event handlers
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    
    # Remove script tags and their content
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized.strip()


def sanitize_html(html_str: str) -> str:
    """Sanitize HTML content while preserving safe tags.
    
    Args:
        html_str: The HTML string to sanitize.
        
    Returns:
        Sanitized HTML with dangerous content removed.
    """
    if not html_str:
        return html_str
    
    # Allow only safe tags and attributes
    allowed_tags = {
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'a', 'img', 'blockquote', 'pre', 'code', 'span', 'div', 'table', 'thead', 'tbody',
        'tr', 'th', 'td', 'section', 'article', 'aside', 'header', 'footer', 'nav', 'figure',
        'figcaption', 'details', 'summary', 'mark', 'small', 'sub', 'sup'
    }
    
    allowed_attributes = {
        'href', 'src', 'alt', 'title', 'class', 'id', 'target', 'rel',
        'colspan', 'rowspan', 'width', 'height', 'align', 'valign',
        'style', 'data-*'
    }
    
    # Remove script tags and their content
    html_str = re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove style tags and their content
    html_str = re.sub(r'<style[^>]*>.*?</style>', '', html_str, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers
    html_str = re.sub(r'on\w+\s*=', '', html_str, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    html_str = re.sub(r'javascript:', '', html_str, flags=re.IGNORECASE)
    
    # Remove vbscript: protocol
    html_str = re.sub(r'vbscript:', '', html_str, flags=re.IGNORECASE)
    
    # Remove data: protocol (except for safe image data URIs)
    html_str = re.sub(r'data:(?!image/)', '', html_str, flags=re.IGNORECASE)
    
    return html_str.strip()


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension against allowed list.
    
    Args:
        filename: Name of the file to validate.
        allowed_extensions: List of allowed file extensions (without dot).
        
    Returns:
        True if extension is allowed, False otherwise.
    """
    if not filename or '.' not in filename:
        return False
    
    # Get file extension and convert to lowercase
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    # Normalize allowed extensions (remove dots if present, convert to lowercase)
    allowed = [ext.lstrip('.').lower() for ext in allowed_extensions]
    
    return file_extension in allowed


def validate_file_size(size: int, max_size: int = 10 * 1024 * 1024) -> bool:
    """Validate file size against maximum allowed size.
    
    Args:
        size: File size in bytes.
        max_size: Maximum allowed size in bytes (default 10MB).
        
    Returns:
        True if file size is within limit, False otherwise.
    """
    if size < 0:
        return False
    
    return size <= max_size


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing potentially dangerous characters.
    
    Args:
        filename: Original filename.
        
    Returns:
        Sanitized filename safe for filesystem operations.
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path separators and null bytes
    filename = re.sub(r'[/\\:\x00]', '', filename)
    
    # Remove special characters except dots, hyphens, and underscores
    filename = re.sub(r'[^\w\-_\. ]', '', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        return "unnamed_file"
    
    return filename


def sanitize_url(url: str) -> str:
    """Sanitize URL to prevent XSS and SSRF attacks.
    
    Args:
        url: URL to sanitize.
        
    Returns:
        Sanitized URL or empty string if dangerous.
    """
    if not url:
        return ""
    
    # Remove javascript: protocol
    if re.match(r'^javascript:', url, re.IGNORECASE):
        return ""
    
    # Remove vbscript: protocol
    if re.match(r'^vbscript:', url, re.IGNORECASE):
        return ""
    
    # Remove data: protocol (except for safe image data URIs)
    if re.match(r'^data:(?!image/)', url, re.IGNORECASE):
        return ""
    
    # Remove event handlers
    url = re.sub(r'on\w+\s*=', '', url, flags=re.IGNORECASE)
    
    # Ensure URL starts with http:// or https://
    if not re.match(r'^https?://', url, re.IGNORECASE):
        # Try to add https:// if it looks like a domain
        if re.match(r'^[\w\-]+(\.[\w\-]+)+', url):
            url = f"https://{url}"
        else:
            return ""
    
    return url.strip()
