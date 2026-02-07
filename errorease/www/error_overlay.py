# apps/errorease/errorease/www/error_overlay.py

import frappe
from frappe import _

def get_context(context):
    context.no_cache = 1
    
    # Get error from query params
    error_message = frappe.form_dict.get("error")
    error_hash = frappe.form_dict.get("hash")
    
    if error_message:
        context.error_message = error_message
    elif error_hash:
        # Get from cache
        cache_key = f"errorease:ui:{error_hash}"
        cached = frappe.cache().get_value(cache_key)
        if cached:
            context.error_message = cached.get("error")
            context.explanation = cached.get("explanation")
    
    return context