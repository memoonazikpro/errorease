# apps/errorease/errorease/hooks.py

import frappe

app_name = "errorease"
app_title = "ErrorEase"
app_publisher = "memoona"
app_description = "AI-powered error explanation module"
app_email = "memoonaiqbal3710@gmail.com"
app_license = "mit"

# Include JS and CSS files
app_include_js = [
    "/assets/errorease/js/errorease.js" 
]

app_include_css = [
    "/assets/errorease/css/errorease.css"
]

# Initialize error interceptor on app startup
def after_migrate():
    """Initialize ErrorEase after migration"""
    try:
        # Import and initialize the error interceptor
        from .error_interceptor import intercept_all_errors
        intercept_all_errors()
        frappe.log_error("ErrorEase", "Error interceptor initialized successfully")
        print("ErrorEase: After migrate hook executed successfully")
    except Exception as e:
        frappe.log_error("ErrorEase initialization failed", str(e))
        print(f"ErrorEase: After migrate hook failed: {str(e)}")

# Add route for error overlay
website_route_rules = [
    {"from_route": "/errorease/overlay", "to_route": "errorease/www/error_overlay"}
]

# Set the after_migrate hook - FIXED: Use function reference, not string
after_migrate = after_migrate

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "errorease",
# 		"logo": "/assets/errorease/logo.png",
# 		"title": "ErrorEase",
# 		"route": "/errorease",
# 		"has_permission": "errorease.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of web template
# web_include_css = "/assets/errorease/css/errorease.css"
# web_include_js = "/assets/errorease/js/errorease.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "errorease/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "errorease/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "errorease.utils.jinja_methods",
# 	"filters": "errorease.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "errorease.install.before_install"
# after_install = "errorease.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "errorease.uninstall.before_uninstall"
# after_uninstall = "errorease.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "errorease.utils.before_app_install"
# after_app_install = "errorease.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "errorease.utils.before_app_uninstall"
# after_app_uninstall = "errorease.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "errorease.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"errorease.tasks.all"
# 	],
# 	"daily": [
# 		"errorease.tasks.daily"
# 	],
# 	"hourly": [
# 		"errorease.tasks.hourly"
# 	],
# 	"weekly": [
# 		"errorease.tasks.weekly"
# 	],
# 	"monthly": [
# 		"errorease.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "errorease.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "errorease.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "errorease.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["errorease.utils.before_request"]
# after_request = ["errorease.utils.after_request"]

# Job Events
# ----------
# before_job = ["errorease.utils.before_job"]
# after_job = ["errorease.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"errorease.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }