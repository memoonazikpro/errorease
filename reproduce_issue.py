
import sys
import os

# approximate paths if not running via bench
sys.path.append("/home/ubuntu/frappe-bench/apps/frappe")
sys.path.append("/home/ubuntu/frappe-bench/apps/errorease")

# Mock frappe if needed, or better, run with bench shell
try:
    from errorease.errorease.api import _normalize_sections
except ImportError:
    print("Could not import errorease.api. Ensure you are running this with 'bench shell' or in the correct environment.")
    sys.exit(1)

# Simulating the validation error from the user's screenshot/description
# "Context: Sales Order form, Before Save event, Server Script error" matches the screenshot
# The actual python error usually comes first in tracebacks or message
error_msg = """
NameError: name 'c' is not defined
Traceback (most recent call last):
  File "apps/frappe/frappe/model/document.py", line 941, in save
    return self._save(*args, **kwargs)
  File "apps/frappe/frappe/model/document.py", line 1136, in run_before_save_methods
    self.run_method("before_save")
  File "apps/frappe/frappe/model/document.py", line 911, in run_method
    out = Document.hook(fn)(self, *args, **kwargs)
  File "apps/frappe/frappe/model/document.py", line 1265, in composer
    return composed(self, method, *args, **kwargs)
  File "apps/frappe/frappe/model/document.py", line 1250, in runner
    add_to_return_value(self, fn(self, *args, **kwargs))
  File "apps/frappe/frappe/model/document.py", line 905, in <lambda>
    fn = lambda self, *args, **kwargs: getattr(self, method)(*args, **kwargs)
  File "apps/errorease/errorease/api.py", line 123, in <module>
    # some fake context
Server Script: Context: Sales Order form, Before Save event, Server Script error
"""

print("-" * 30)
print("TESTING _normalize_sections with simulated NameError")
print("-" * 30)
print(f"Input Error Message:\n{error_msg[:100]}...")
print("-" * 30)

# Simulate what happens when cache/AI fails and we fall back to deterministic logic
# The first argument 'raw' is empty string to trigger fallback
explanation = _normalize_sections("", error_msg, "Sales Order")

print("GENERATED EXPLANATION:\n")
print(explanation)
print("-" * 30)
