from typing import Any, Dict, Optional
from datetime import datetime


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat()


def parse_json_field(json_str: Optional[str]) -> Any:
    """Safely parse JSON string field."""
    import json
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def create_response(
    success: bool,
    message: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized API response."""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if data:
        response["data"] = data
    return response


def paginate_query(query, page: int = 1, page_size: int = 20):
    """
    Add pagination to SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Modified query with LIMIT and OFFSET
    """
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    import os
    
    # Get file extension
    name, ext = os.path.splitext(filename)
    
    # Remove any non-alphanumeric characters (except dash and underscore)
    name = re.sub(r'[^\w\-]', '_', name)
    
    # Limit length
    name = name[:100]
    
    return f"{name}{ext}"


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate unique filename with timestamp.
    
    Args:
        original_filename: Original filename
        prefix: Optional prefix
        
    Returns:
        Unique filename
    """
    import os
    import uuid
    from datetime import datetime
    
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate unique name
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    if prefix:
        return f"{prefix}_{timestamp}_{unique_id}{ext}"
    else:
        return f"{timestamp}_{unique_id}{ext}"
