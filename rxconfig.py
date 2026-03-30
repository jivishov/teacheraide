
# rxconfig.py
import reflex as rx
import os
from dotenv import load_dotenv
load_dotenv()
from reflex.utils.console import LogLevel

# Get environment variables with defaults
PRODUCTION = os.getenv("ENV", "dev") == "prod"
BACKEND_HOST = os.getenv("REFLEX_BACKEND_HOST", "0.0.0.0")
FRONTEND_HOST = os.getenv("REFLEX_FRONTEND_HOST", "0.0.0.0")
APP_URL = os.getenv("API_URL", "https://teacheraide.fly.dev")

# Base configuration
config_dict = {
    "app_name": "app",
    "show_built_with_reflex": False,
    "backend_port": 8000,
    "frontend_port": 3000,
}

config_dict.update({
        # External URL for API calls from browser
        "api_url": APP_URL,
        # Backend configuration
        "backend_host": BACKEND_HOST,
        # Frontend configuration  
        "frontend_host": FRONTEND_HOST,
        # Deployment settings
        "deploy_url": APP_URL,
    })

# # Production-specific configuration
# if PRODUCTION:
#     config_dict.update({
#         # External URL for API calls from browser
#         "api_url": "https://maindoctor.fly.dev",
#         # Backend configuration
#         # "backend_host": BACKEND_HOST,
#         # # Frontend configuration
#         # "frontend_host": FRONTEND_HOST,
#     })
# else:
#     # Development configuration
#     config_dict.update({
#         "api_url": "http://localhost:8000",
#         "backend_host": "localhost",
#         "frontend_host": "localhost",
#     })

# Database configuration with fallback handling
database_url = os.getenv("DATABASE_URL")
is_dev_mode = os.getenv("ENV", "dev").lower() in ("dev", "development")

# Handle database URL based on mode and availability
if database_url:
    # DATABASE_URL is explicitly set, use it
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    # print(f"Using configured database: {database_url}")
elif is_dev_mode:
    # Development mode with no DATABASE_URL - use SQLite
    database_url = "sqlite:///reflex.db"
    # print("Development mode: Using SQLite database")
else:
    # Production mode with no DATABASE_URL - use SQLite as fallback
    database_url = "sqlite:///reflex.db"
    # print("DATABASE_URL not set - using local SQLite database")



# Create config
config = rx.Config(
    **config_dict,
    db_url=database_url,
    loglevel=LogLevel.INFO,
    telemetry_enabled=True,
    plugins=[rx.plugins.TailwindV3Plugin(), rx.plugins.sitemap.SitemapPlugin()],
)
