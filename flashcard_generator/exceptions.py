"""
Custom exceptions for the flashcard generator.

This module defines specific exception types for different error scenarios
to provide better error handling and user feedback.
"""


class FlashcardGeneratorError(Exception):
    """Base exception for all flashcard generator errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        """Initialize the exception with message, error code, and optional details."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
    
    def __str__(self):
        """Return a formatted error message."""
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(FlashcardGeneratorError):
    """Raised when there are configuration-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "CONFIG_ERROR", details)


class APIError(FlashcardGeneratorError):
    """Base class for API-related errors."""
    
    def __init__(self, message: str, error_code: str, details: dict = None):
        super().__init__(message, error_code, details)


class GeminiAPIError(APIError):
    """Raised when there are Gemini API-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "GEMINI_API_ERROR", details)


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    
    def __init__(self, message: str, api_name: str = "Unknown", details: dict = None):
        error_details = {"api_name": api_name}
        if details:
            error_details.update(details)
        super().__init__(message, "AUTH_ERROR", error_details)


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, message: str, api_name: str = "Unknown", retry_after: int = None, details: dict = None):
        error_details = {"api_name": api_name}
        if retry_after:
            error_details["retry_after"] = retry_after
        if details:
            error_details.update(details)
        super().__init__(message, "RATE_LIMIT_ERROR", error_details)


class ImageFetchError(FlashcardGeneratorError):
    """Raised when image fetching fails."""
    
    def __init__(self, message: str, query: str = None, details: dict = None):
        error_details = {"query": query} if query else {}
        if details:
            error_details.update(details)
        super().__init__(message, "IMAGE_FETCH_ERROR", error_details)


class CSVExportError(FlashcardGeneratorError):
    """Raised when CSV export fails."""
    
    def __init__(self, message: str, file_path: str = None, details: dict = None):
        error_details = {"file_path": file_path} if file_path else {}
        if details:
            error_details.update(details)
        super().__init__(message, "CSV_EXPORT_ERROR", error_details)


class ValidationError(FlashcardGeneratorError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: str = None, details: dict = None):
        error_details = {}
        if field:
            error_details["field"] = field
        if value:
            error_details["value"] = value
        if details:
            error_details.update(details)
        super().__init__(message, "VALIDATION_ERROR", error_details)


class FileOperationError(FlashcardGeneratorError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str, file_path: str = None, operation: str = None, details: dict = None):
        error_details = {}
        if file_path:
            error_details["file_path"] = file_path
        if operation:
            error_details["operation"] = operation
        if details:
            error_details.update(details)
        super().__init__(message, "FILE_OPERATION_ERROR", error_details)


class NetworkError(FlashcardGeneratorError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, url: str = None, status_code: int = None, details: dict = None):
        error_details = {}
        if url:
            error_details["url"] = url
        if status_code:
            error_details["status_code"] = status_code
        if details:
            error_details.update(details)
        super().__init__(message, "NETWORK_ERROR", error_details)


class PartialResultsError(FlashcardGeneratorError):
    """Raised when generation partially fails but some results are available."""
    
    def __init__(self, message: str, successful_count: int = 0, failed_count: int = 0, 
                 partial_results: list = None, details: dict = None):
        error_details = {
            "successful_count": successful_count,
            "failed_count": failed_count,
            "total_requested": successful_count + failed_count
        }
        if partial_results:
            error_details["partial_results_available"] = True
            error_details["partial_results_count"] = len(partial_results)
        if details:
            error_details.update(details)
        super().__init__(message, "PARTIAL_RESULTS_ERROR", error_details)
        self.partial_results = partial_results or []