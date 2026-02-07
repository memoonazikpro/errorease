# apps/errorease/errorease/hooks.py

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

# Website route
website_route_rules = [
    {"from_route": "/errorease/overlay", "to_route": "errorease/www/error_overlay"}
]
