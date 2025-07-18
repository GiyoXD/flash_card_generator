"""
Logging configuration for the flashcard generator.

This module provides comprehensive logging setup with different levels,
formatters, and handlers for various components.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Format the log record with colors."""
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class FlashcardLogger:
    """Enhanced logging system for the flashcard generator."""
    
    def __init__(self, name: str = "flashcard_generator", log_dir: str = "./logs"):
        """Initialize the logger with specified name and log directory."""
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up different log handlers for various output targets."""
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for all logs
        log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler for errors and critical issues
        error_file = self.log_dir / f"{self.name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n' + '-' * 80,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # Rotating file handler to prevent log files from getting too large
        rotating_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_rotating.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        rotating_handler.setLevel(logging.DEBUG)
        rotating_handler.setFormatter(file_formatter)
        self.logger.addHandler(rotating_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any] = None):
        """Log an error with additional context information."""
        context_str = ""
        if context:
            context_items = [f"{k}={v}" for k, v in context.items()]
            context_str = f" | Context: {', '.join(context_items)}"
        
        self.logger.error(f"{type(error).__name__}: {error}{context_str}", exc_info=True)
    
    def log_api_call(self, api_name: str, endpoint: str, status: str, 
                     duration: float = None, details: Dict[str, Any] = None):
        """Log API call information."""
        duration_str = f" ({duration:.2f}s)" if duration else ""
        details_str = ""
        if details:
            details_items = [f"{k}={v}" for k, v in details.items()]
            details_str = f" | {', '.join(details_items)}"
        
        self.logger.info(f"API Call: {api_name} -> {endpoint} | Status: {status}{duration_str}{details_str}")
    
    def log_file_operation(self, operation: str, file_path: str, status: str, 
                          size: int = None, details: Dict[str, Any] = None):
        """Log file operation information."""
        size_str = f" ({size} bytes)" if size else ""
        details_str = ""
        if details:
            details_items = [f"{k}={v}" for k, v in details.items()]
            details_str = f" | {', '.join(details_items)}"
        
        self.logger.info(f"File Op: {operation} -> {file_path} | Status: {status}{size_str}{details_str}")
    
    def log_generation_stats(self, stats: Dict[str, Any]):
        """Log generation statistics."""
        stats_items = [f"{k}={v}" for k, v in stats.items()]
        self.logger.info(f"Generation Stats: {', '.join(stats_items)}")
    
    @staticmethod
    def setup_component_logger(component_name: str, log_dir: str = "./logs") -> logging.Logger:
        """Set up a logger for a specific component."""
        logger_name = f"flashcard_generator.{component_name}"
        flashcard_logger = FlashcardLogger(logger_name, log_dir)
        return flashcard_logger.get_logger()


def get_user_friendly_error_message(error: Exception) -> str:
    """Convert technical errors into user-friendly messages."""
    
    error_messages = {
        # Configuration errors
        "GEMINI_API_KEY environment variable is required": 
            "❌ Missing API Key: Please set your GEMINI_API_KEY environment variable.\n"
            "   You can get an API key from: https://makersuite.google.com/app/apikey\n"
            "   Set it by running: export GEMINI_API_KEY='your-api-key-here'",
        
        # Network errors
        "Failed to authenticate with Gemini API":
            "❌ Authentication Failed: Unable to connect to Google Gemini API.\n"
            "   Please check:\n"
            "   • Your API key is valid and active\n"
            "   • You have internet connectivity\n"
            "   • The Gemini API service is available",
        
        # Rate limiting
        "rate limit":
            "⏳ Rate Limited: Too many requests to the API.\n"
            "   Please wait a moment and try again with fewer flashcards.",
        
        # File operation errors
        "Permission denied":
            "❌ Permission Error: Cannot write to the output directory.\n"
            "   Please check that you have write permissions to the specified folder.",
        
        "No space left on device":
            "❌ Storage Full: Not enough disk space to save files.\n"
            "   Please free up some space and try again.",
        
        # Image errors
        "No image found":
            "⚠️  Image Warning: Some images couldn't be downloaded.\n"
            "   This won't affect your flashcards, but they'll be missing pictures.",
        
        # Validation errors
        "Chinese translation must contain Chinese characters":
            "❌ Translation Error: The AI didn't provide valid Chinese translations.\n"
            "   This might be due to an unusual topic. Try a different topic or try again.",
    }
    
    error_str = str(error).lower()
    
    # Check for specific error patterns
    for pattern, message in error_messages.items():
        if pattern.lower() in error_str:
            return message
    
    # Generic error message
    return f"❌ Unexpected Error: {error}\n" \
           "   Please check the logs for more details or try again."


def log_system_info(logger: logging.Logger):
    """Log system information for debugging purposes."""
    import platform
    import sys
    
    logger.info("System Information:")
    logger.info(f"  Python Version: {sys.version}")
    logger.info(f"  Platform: {platform.platform()}")
    logger.info(f"  Architecture: {platform.architecture()}")
    logger.info(f"  Processor: {platform.processor()}")
    
    # Log installed packages versions
    try:
        import google.generativeai
        logger.info(f"  google-generativeai: {google.generativeai.__version__}")
    except:
        logger.warning("  google-generativeai: Not installed or version unavailable")
    
    try:
        import requests
        logger.info(f"  requests: {requests.__version__}")
    except:
        logger.warning("  requests: Not installed or version unavailable")