
import re

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
            # if 1 < len(name) < 120: target function logic, simplified here
            return name
    return ""

test_cases = [
    ("MandatoryError: Value missing for: customer_name", "customer_name"),
    ("LinkValidationError: Could not find Customer XYZ", ""), # Regex expects: LinkValidationError: (captured). This might need tuning if message is "Could not find..."
    ("Duplicate name Sales Order-2024-001", "Sales Order-2024-001"),
    ("Property hidden_field not found", "hidden_field"),
    ("Invalid value for posting_date", "posting_date")
]

print("Testing Regex Patterns...")
for msg, expected in test_cases:
    res = _find_field_in_error(msg)
    print(f"Msg: '{msg}' -> Found: '{res}' | Expected: '{expected}'")
