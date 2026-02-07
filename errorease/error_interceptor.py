# apps/errorease/errorease/error_interceptor.py

import frappe
import sys

def intercept_all_errors():
    """
    Initialize error interception for ErrorEase
    Safe version that doesn't interfere with core functions
    """
    print("ErrorEase: Initializing safe error interceptor...")
    
    try:
        # Set up system exception hook (non-invasive)
        setup_exception_hook()
        
        # Log initialization
        frappe.log_error("ErrorEase", "Safe error interceptor initialized")
        print("ErrorEase: Safe error interceptor ready")
        
    except Exception as e:
        print(f"ErrorEase: Error interceptor setup failed: {str(e)}")
        frappe.log_error("ErrorEase interceptor failed", str(e))

def setup_exception_hook():
    """Setup system exception hook to catch unhandled exceptions"""
    original_excepthook = sys.excepthook
    
    def error_ease_excepthook(exc_type, exc_value, exc_traceback):
        # First call the original handler
        original_excepthook(exc_type, exc_value, exc_traceback)
        
        # Then log to ErrorEase if it's not KeyboardInterrupt
        if exc_type != KeyboardInterrupt:
            try:
                process_error_for_errorease(exc_type, exc_value, exc_traceback)
            except Exception:
                # Don't let ErrorEase errors break the system
                pass
    
    sys.excepthook = error_ease_excepthook

def process_error_for_errorease(exc_type, exc_value, exc_traceback):
    """Process error for ErrorEase analysis (async)"""
    import traceback
    
    # Check if ErrorEase is enabled
    if not is_errorease_enabled():
        return
    
    error_message = f"{exc_type.__name__}: {exc_value}"
    traceback_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Extract context
    doctype, docname = extract_context_from_traceback(traceback_text)
    
    # Queue for async processing to avoid blocking
    frappe.enqueue(
        "errorease.api.explain_error",
        message=error_message + "\n\n" + traceback_text[:2000],
        doctype=doctype,
        docname=docname,
        route=None,
        queue="short",
        enqueue_after_commit=True,
        job_name=f"ErrorEase analysis: {error_message[:50]}..."
    )

def is_errorease_enabled():
    """Check if ErrorEase is enabled in settings"""
    try:
        if not frappe.db.exists("ErrorEase Settings", "ErrorEase Settings"):
            return False
        
        settings = frappe.get_single("ErrorEase Settings")
        return getattr(settings, "enabled", False)
    except Exception:
        return False

def extract_context_from_traceback(traceback_text):
    """Extract doctype and docname from traceback"""
    import re
    
    doctype = None
    docname = None
    
    # Look for frappe.get_doc patterns
    patterns = [
        r'frappe\.get_doc\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]',
        r'get_doc\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, traceback_text)
        if match:
            doctype = match.group(1)
            docname = match.group(2)
            break
    
    return doctype, docname