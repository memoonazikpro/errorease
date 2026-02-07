# apps/errorease/errorease/patches/v1_0/intercept_all_errors.py

import frappe

def execute():
    """
    Patch for ErrorEase - creates default settings if they don't exist
    This runs once when the app is installed/updated
    """
    print("ErrorEase: Running patch v1.0...")
    
    try:
        # Check if ErrorEase Settings doctype exists
        if not frappe.db.exists("DocType", "ErrorEase Settings"):
            print("ErrorEase: DocType not created yet, skipping patch")
            return True
        
        # Check if settings record exists, create if not
        if not frappe.db.exists("ErrorEase Settings", "ErrorEase Settings"):
            doc = frappe.get_doc({
                "doctype": "ErrorEase Settings",
                "enabled": 0,  # Disabled by default for safety
                "provider": "Groq",
                "cache_seconds": 1800
            })
            doc.insert(ignore_permissions=True)
            print("ErrorEase: Created default settings")
        else:
            print("ErrorEase: Settings already exist")
        
        print("ErrorEase: Patch v1.0 completed successfully")
        return True
        
    except Exception as e:
        print(f"ErrorEase patch warning: {str(e)}")
        # Don't fail migration if patch has issues
        return True