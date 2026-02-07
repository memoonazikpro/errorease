# apps/errorease/errorease/api.py
import frappe
import re
import hashlib
from frappe import _

@frappe.whitelist()
def explain_error(message, doctype=None, docname=None, route=None):
    """
    Called from the client browser via JS.
    Returns:
        {"explanation": "...", "cached": True/False}
    """
    # Log a snippet for debugging
    frappe.log_error("ErrorEase: API Triggered", f"Message snippet: {str(message)[:200]}")
    
    # Prevent guest access
    if frappe.session.user == "Guest":
        return {"explanation": "❌ You must be logged in to use ErrorEase.", "cached": False}
    
    # Load settings
    try:
        settings = frappe.get_single("ErrorEase Settings")
    except Exception as e:
        return {"explanation": f"❌ Failed to load ErrorEase Settings: {str(e)}", "cached": False}

    if not getattr(settings, "enabled", False):
        return {"explanation": "❌ ErrorEase is currently disabled. Enable it in ErrorEase Settings.", "cached": False}

    provider = getattr(settings, "provider", None) or "Groq"
    model = getattr(settings, "model", None) or "llama-3.1-8b-instant"
    cache_seconds = int(getattr(settings, "cache_seconds", 1800) or 1800)

    # Decrypt API key
    try:
        from frappe.utils.password import get_decrypted_password
        api_key = get_decrypted_password("ErrorEase Settings", "ErrorEase Settings", "api_key")
    except Exception:
        return {"explanation": "❌ Could not decrypt API key. Verify ErrorEase Settings.", "cached": False}

    if not api_key:
        return {"explanation": "❌ No API key found. Add an API key in ErrorEase Settings.", "cached": False}

    # Sanitize the message (avoid logging secrets)
    redacted_msg = _redact_message(message or "")

    # Cache key
    cache_key = "errorease:exp:" + hashlib.sha256(
        (redacted_msg + str(doctype or "") + str(docname or "") + provider + model).encode()
    ).hexdigest()

    # Return cached if present
    try:
        cached_value = frappe.cache().get_value(cache_key)
    except Exception:
        cached_value = None

    if cached_value:
        return {"explanation": cached_value, "cached": True}

    # Build prompt for LLM
    prompt = _build_prompt(redacted_msg, doctype, docname, route)

    # Call chosen provider
    try:
        if provider.lower() == "groq":
            raw = _call_groq(api_key, prompt, model)
        elif provider.lower() in ["openai", "chatgpt"]:
            raw = _call_openai(api_key, prompt, model)
        else:
            raw = f"❌ Unsupported provider: {provider}"
            
    except Exception as e:
        err = str(e)
        # Friendly user-facing errors
        if "authentication" in err.lower() or "api key" in err.lower() or "401" in err:
            raw = f"❌ Invalid {provider} API key. Check ErrorEase Settings."
        elif "quota" in err.lower() or "rate limit" in err.lower() or "429" in err:
            raw = f"❌ {provider} API limit reached. Try again later or check your account quota."
        elif "timeout" in err.lower():
            raw = f"❌ {provider} service timeout. Please retry."
        elif "model" in err.lower():
            raw = f"❌ {provider} model '{model}' is unavailable."
        else:
            raw = f"❌ {provider} API error: {err[:150]}"

    # Normalize and ensure structured output
    explanation = _normalize_sections(raw, redacted_msg, doctype)

    # Cache successful (non-error) responses
    if explanation and not explanation.lower().startswith("❌"):
        try:
            frappe.cache().set_value(cache_key, explanation, expires_in_sec=cache_seconds)
        except Exception:
            # don't fail on cache set errors
            pass

    return {"explanation": explanation, "cached": False}


# ============================================================
# Additional API Endpoints
# ============================================================

@frappe.whitelist()
def trigger_test_error(error_type="validation"):
    """Trigger a test error for ErrorEase testing"""
    error_types = {
        "validation": "ValidationError: Test validation error for ErrorEase testing",
        "attribute": "AttributeError: 'Sales Order' object has no attribute 'test_field'",
        "permission": "PermissionError: You don't have permission to access this document",
        "syntax": "SyntaxError: invalid syntax in test_script.py line 10",
        "database": "ProgrammingError: column 'test_column' does not exist",
        "nameerror": "NameError: name 'frape' is not defined",
    }
    
    error_message = error_types.get(error_type, error_types["validation"])
    
    # Get explanation
    result = explain_error(error_message, "Test DocType", "TEST-001")
    
    return {
        "status": "success",
        "error_message": error_message,
        "explanation": result.get("explanation"),
        "cached": result.get("cached", False)
    }

@frappe.whitelist()
def check_health():
    """Check if ErrorEase is healthy and configured"""
    try:
        if not frappe.db.exists("ErrorEase Settings", "ErrorEase Settings"):
            return {"status": "error", "message": "ErrorEase Settings not found"}
        
        settings = frappe.get_single("ErrorEase Settings")
        
        if not getattr(settings, "enabled", False):
            return {"status": "disabled", "message": "ErrorEase is disabled"}
        
        # Try to decrypt API key to check if it's valid
        from frappe.utils.password import get_decrypted_password
        api_key = get_decrypted_password("ErrorEase Settings", "ErrorEase Settings", "api_key")
        
        if not api_key or api_key.strip() == "":
            return {"status": "error", "message": "API key not set"}
        
        provider = getattr(settings, "provider", "Groq").strip().lower()
        
        return {
            "status": "healthy",
            "enabled": True,
            "provider": provider,
            "model": getattr(settings, "model", "llama-3.1-8b-instant")
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# LLM PROVIDER CALLS
# ============================================================

def _call_groq(api_key, prompt, model):
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": (
                    "You are an ERPNext expert assistant. Produce EXACTLY two sections using these exact headings:\n\n"
                    "What Went Wrong:\n"
                    "How to Fix It:\n\n"
                    "IMPORTANT: DO NOT include any 'Prevention Tips', 'Tips', 'Best Practices', or ANY third section. "
                    "Only provide the two required sections.\n\n"
                    "Rules for 'What Went Wrong': identify the DocType and the likely failing field or attribute; explain the root cause in 1-3 short sentences.\n"
                    "Rules for 'How to Fix It': return 5-7 sequential numbered steps (1., 2., 3., ...). Steps must be actionable and ERPNext-specific (include navigation, file / script names or DocType field names if possible). Return plain text only."
                )},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.12,
            timeout=30
        )
        return res.choices[0].message.content.strip()
    except ImportError:
        return "❌ Groq package not installed. Run: pip install groq"
    except Exception as e:
        raise e


def _call_openai(api_key, prompt, model):
    try:
        import openai
        openai.api_key = api_key
        
        res = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": (
                    "You are an ERPNext expert assistant. Produce EXACTLY two sections using these exact headings:\n\n"
                    "What Went Wrong:\n"
                    "How to Fix It:\n\n"
                    "IMPORTANT: DO NOT include any 'Prevention Tips', 'Tips', 'Best Practices', or ANY third section. "
                    "Only provide the two required sections.\n\n"
                    "Rules for 'What Went Wrong': identify the DocType and the likely failing field or attribute; explain the root cause in 1-3 short sentences.\n"
                    "Rules for 'How to Fix It': return 5-7 sequential numbered steps (1., 2., 3., ...). Steps must be actionable and ERPNext-specific (include navigation, file / script names or DocType field names if possible). Return plain text only."
                )},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.12,
            timeout=30
        )
        return res.choices[0].message.content.strip()
    except ImportError:
        return "❌ OpenAI package not installed. Run: pip install openai"
    except Exception as e:
        raise e


# ============================================================
# HELPERS
# ============================================================

def _redact_message(msg: str) -> str:
    if not msg:
        return ""
    s = str(msg)
    s = re.sub(r'[\w\.-]+@[\w\.-]+', "[REDACTED_EMAIL]", s)
    s = re.sub(r'\b\d{6,}\b', "[REDACTED_NUM]", s)
    s = re.sub(r'(/[A-Za-z0-9_\-\.]+)+', "[REDACTED_PATH]", s)
    s = re.sub(r'<[^>]+>', "[REDACTED_HTML]", s)
    return s


def _build_prompt(msg, doctype, docname, route):
    try:
        roles = ", ".join(frappe.get_roles(frappe.session.user))
    except Exception:
        roles = "unknown"

    # Extract doctype from message if not provided
    if not doctype and msg:
        extracted_doctype = _extract_doctype_from_traceback(msg)
        if extracted_doctype:
            doctype = extracted_doctype

    return f"""Analyze the ERPNext error below and produce EXACTLY TWO sections.

ERROR:
{msg}

CONTEXT:
Doctype: {doctype or 'Not specified'}
Document: {docname or 'Not specified'}
Route: {route or 'Not specified'}
User Roles: {roles}

Produce EXACTLY TWO sections titled:
What Went Wrong:
How to Fix It:

IMPORTANT: DO NOT include any 'Prevention Tips', 'Tips', 'Best Practices', or ANY third section. Only provide the two required sections.

- 'What Went Wrong' must identify the DocType and state the likely failing field/attribute or script (1-3 short sentences).
- If it's a NameError or typo, identify the missing variable and suggest corrections (e.g., 'frape' -> 'frappe').
- 'How to Fix It' must provide 5-7 numbered, sequential, actionable steps (start each with 1., 2., 3., etc.). Include ERPNext navigation and mention file/script/DocType field names if available.
- Return plain text only; no extra sections.
"""


def _extract_doctype_from_traceback(traceback_text):
    """Extract doctype from traceback text"""
    if not traceback_text:
        return None
    
    patterns = [
        r'in DocType [\'"]([^\'"]+)[\'"]',
        r'for ([A-Z][a-zA-Z0-9 ]+)',
        r'DocType:\s*([^\n,]+)',
        r'frappe\.get_doc\(\s*[\'"]([^\'"]+)[\'"]',
        r'doctype[\s=]+[\'"]([^\'"]+)[\'"]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, traceback_text, re.IGNORECASE)
        if match:
            doctype = match.group(1).strip()
            if doctype and len(doctype) > 2 and len(doctype) < 100:
                return doctype
    
    return None


def _find_field_in_error(msg: str) -> str:
    if not msg:
        return ""
    text = str(msg)
    patterns = [
        r"field '([^']+)'",
        r'field "([^"]+)"',
        r"attribute '([^']+)'",
        r"AttributeError: '([^']+)'",
        r"KeyError: '([^']+)'",
        r"\'([A-Za-z0-9_]+)\' field",
        r"column \"?([a-zA-Z0-9_]+)\"?",
        r"Undefined field: ([A-Za-z0-9_]+)",
        r"Value missing for: ([A-Za-z0-9_ -]+)",
        r"Invalid value for ([A-Za-z0-9_ -]+)",
        r"LinkValidationError: ([A-Za-z0-9_ -]+)",
        r"Duplicate name ([A-Za-z0-9_ -]+)",
        r"value (.+) for ([A-Za-z0-9_ -]+)",
        r"Property ([A-Za-z0-9_ -]+) not found",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if 1 < len(name) < 120:
                return name
    return ""


def _extract_script_name(msg: str) -> str:
    if not msg:
        return ""
    text = str(msg)
    patterns = [
        r"Server Script[:\s]*['\"]?([^'\"]+)['\"]?",
        r"File \"[^\"]*/([^/]+)\.py\"",
        r"module '([A-Za-z0-9_\-\.]+)'",
        r"script '([^']+)'",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if 1 < len(name) < 200:
                return name
    return ""


def _normalize_sections(raw_text: str, original_msg: str, doctype: str) -> str:
    if not raw_text:
        raw_text = ""
    txt = str(raw_text)
    # Remove unwanted sections
    txt = re.sub(r'(?i)(?:\n\s*)?Prevention Tips[:\s\S]*?(?=\n\n|$)', '', txt)
    txt = re.sub(r'(?i)(?:\n\s*)?Tips[:\s\S]*?(?=\n\n|$)', '', txt)
    txt = re.sub(r'(?i)(?:\n\s*)?Best Practices[:\s\S]*?(?=\n\n|$)', '', txt)
    txt = re.sub(r'(?i)(?:\n\s*)?💡[^\n]*[:\s\S]*?(?=\n\n|$)', '', txt)

    txt = re.sub(r'\*\*(.*?)\*\*', r'\1', txt)
    txt = re.sub(r'`([^`]+)`', r'\1', txt)
    txt = re.sub(r'\r\n?', '\n', txt).strip()

    txt = re.sub(r'(?i)what went wrong[:]*', 'What Went Wrong:', txt)
    txt = re.sub(r'(?i)how to fix it[:]*', 'How to Fix It:', txt)

    def extract_section(start_heading, next_heading=None):
        try:
            start_idx = txt.index(start_heading) + len(start_heading)
        except ValueError:
            return ""
        if next_heading:
            try:
                end_idx = txt.index(next_heading, start_idx)
            except ValueError:
                end_idx = len(txt)
        else:
            end_idx = len(txt)
        return txt[start_idx:end_idx].strip()

    what = extract_section("What Went Wrong:", "How to Fix It:")
    fix = extract_section("How to Fix It:")

    what = re.sub(r'^[\u2600-\u26FF\u2700-\u27BF\uf000-\ufaff]+\s*', '', what).strip()
    fix = re.sub(r'^[\u2600-\u26FF\u2700-\u27BF\uf000-\ufaff]+\s*', '', fix).strip()

    if not what or len(what.split()) < 4:
        detected_field = _find_field_in_error(original_msg)
        script_name = _extract_script_name(original_msg)
        dtype = doctype or _try_find_doctype_in_text(original_msg) or "Unknown DocType"
        error_type = ""
        variable_name = ""
        variable_name_clean = ""

        if "NameError" in original_msg:
            error_type = "NameError"
            m = re.search(r"name '([^']+)' is not defined", original_msg)
            if m:
                variable_name_clean = m.group(1)
                variable_name = variable_name_clean
                if variable_name_clean == "frape":
                    variable_name += " (likely typo for 'frappe')"

        elif "AttributeError" in original_msg:
            error_type = "AttributeError"

        if error_type == "NameError":
            what = "A {} occurred in the {} DocType, likely due to an undefined variable or typo: {}.".format(error_type, dtype, variable_name)
            if script_name:
                what += " The error originated from the script/module '{}'.".format(script_name)
        elif detected_field:
            what = "The {} DocType raised an error referencing the field '{}'; the attribute/field does not appear to exist or is not accessible.".format(dtype, detected_field)
        elif script_name:
            what = "The {} DocType raised an error originating from the script/module '{}'; an attribute or field reference failed at runtime.".format(dtype, script_name)
        else:
            what = "The {} DocType caused an attribute/field reference error that failed at runtime.".format(dtype)

    sents = re.split(r'(?<=[.?!])\s+', what)
    what = " ".join(sents[:3]).strip()

    if doctype and doctype.lower() not in what.lower():
        what = "{} (DocType: {})".format(what, doctype)

    fix_parsed = _parse_numbered_steps(fix)

    if not fix_parsed or len(fix_parsed.strip()) < 8:
        detected_field = _find_field_in_error(original_msg)
        script_name = _extract_script_name(original_msg)
        dtype = doctype or _try_find_doctype_in_text(original_msg) or "the DocType"
        error_type = ""
        variable_name = ""
        variable_name_clean = ""
        if "NameError" in original_msg:
            error_type = "NameError"
            m = re.search(r"name '([^']+)' is not defined", original_msg)
            if m:
                variable_name_clean = m.group(1)
                variable_name = variable_name_clean
                if variable_name_clean == "frape":
                    variable_name += " (likely typo for 'frappe')"

        fallback_steps = []

        fallback_steps.append(
            "Locate where the error originates: check Setup > Logs > Error Log for the full traceback and note file/module lines."
        )

        if script_name:
            fallback_steps.append(
                "Open Setup > Customization > Server Scripts and search for the script named '{}'.".format(script_name)
            )
        else:
            fallback_steps.append(
                "Open Setup > Customization > Server Scripts and search scripts that target {} or review custom apps that touch {}.".format(dtype, dtype)
            )

        if detected_field:
            fallback_steps.append(
                "Search your codebase and DocType for the field or attribute '{}' (use grep / ripgrep or the Desk global search).".format(detected_field)
            )
            fallback_steps.append(
                "If '{}' is a custom field, confirm it exists in the DocType (Customize Form > {}). If it does not exist, either add the field or update the code to use the correct fieldname.".format(detected_field, dtype)
            )
        else:
            fallback_steps.append(
                "Search for likely misspelled attributes or calls in the script (names similar to the one in the traceback)."
            )

        if error_type == "NameError":
            check_typo_step = "Check if '{}' is a typo. Ensure it is defined or imported before use.".format(variable_name_clean)
            if "frape" in variable_name_clean.lower() or "frapp" in variable_name_clean.lower():
                 check_typo_step += " (Did you mean 'frappe'?)"

            fallback_steps = [
                "Locate the error: Check Setup > Logs > Error Log for the full traceback.",
                "Open Setup > Customization > Server Scripts, filter by DocType = '{}' and Event = 'Before Save' (or the event that matches your case), and look for scripts that might contain 'frappe' related code.".format(dtype),
                "Search for the undefined name '{}' in the script code.".format(variable_name_clean),
                check_typo_step,
                "Save the Server Script and clear cache via Setup > System Settings > Clear Cache.",
                "Test by reproducing the action (e.g., saving the Sales Invoice).",
                "If persistent, check custom apps or hooks affecting this DocType."
            ]
        else:
            fallback_steps.append(
                "If code references an attribute on an object, guard the access (e.g., replace `obj.trow` with `getattr(obj, 'trow', None)` or `doc.get('trow')`) or correct the attribute name to the actual fieldname."
            )
            fallback_steps.append(
                "Save your changes, run `bench restart` if you modified Python modules, or save the Server Script and clear the cache via Setup > System Settings > Clear Cache."
            )
            fallback_steps.append(
                "Reproduce the original action that caused the error; confirm the error no longer appears and check Setup > Logs > Error Log for residual traces."
            )

        fix_parsed = "\n".join("{}. {}".format(i+1, step) for i, step in enumerate(fallback_steps))

    final = (
        "What Went Wrong:\n"
        "{}\n\n"
        "How to Fix It:\n"
        "{}"
    ).format(what, fix_parsed)

    final = re.sub(r'(?i)(?:\n\s*)?Prevention Tips[:\s\S]*?(?=\n\n|$)', '', final)
    final = re.sub(r'(?i)(?:\n\s*)?Tips[:\s\S]*?(?=\n\n|$)', '', final)
    final = re.sub(r'(?i)(?:\n\s*)?💡[^\n]*[:\s\S]*?(?=\n\n|$)', '', final)

    return final.strip()


def _try_find_doctype_in_text(text: str) -> str:
    if not text:
        return ""
    patterns = [
        r"DocType[:\s]*['\"]?([A-Za-z0-9 _\-]+)['\"]?",
        r"in ([A-Z][A-Za-z0-9_ ]{2,30}) DocType",
        r"in ([A-Z][A-Za-z0-9_ ]{2,30}) doctype",
        r"([A-Z][A-Za-z0-9_ ]{3,40}) DocType",
        r"'([A-Z][A-Za-z0-9_ ]{3,40})'"
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            candidate = m.group(1).strip()
            if 2 < len(candidate) < 80:
                return candidate
    return ""


def _parse_numbered_steps(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    numbered_pattern = re.compile(r'^\s*\d+\.\s+', flags=re.MULTILINE)
    if numbered_pattern.search(text):
        lines = text.splitlines()
        steps = []
        current = None
        for ln in lines:
            ln_clean = ln.rstrip()
            if not ln_clean:
                continue
            m = re.match(r'^\s*(\d+)\.\s*(.*)', ln_clean)
            if m:
                if current is not None:
                    steps.append(current.strip())
                current = m.group(2).strip()
            else:
                if current is None:
                    current = ln_clean.strip()
                else:
                    current += " " + ln_clean.strip()
        if current is not None:
            steps.append(current.strip())
        cleaned = []
        for s in steps:
            s_clean = s.strip()
            if not s_clean.endswith("."):
                s_clean += "."
            cleaned.append(s_clean)
        return "\n".join("{}. {}".format(i+1, step) for i, step in enumerate(cleaned))

    candidates = re.split(r'\n{1,}|\.\s+|\;\s+|\n-\s+', text)
    candidates = [c.strip() for c in candidates if c.strip()]
    if candidates and re.match(r'^[Ii]t[:\.\s]*$', candidates[0]):
        candidates = candidates[1:]
    steps = candidates[:7]
    final_steps = []
    for s in steps:
        s = re.sub(r'\s+', ' ', s).strip()
        if not s.endswith("."):
            s += "."
        final_steps.append(s)
    if not final_steps:
        return ""
    return "\n".join("{}. {}".format(i+1, step) for i, step in enumerate(final_steps))

# End of file