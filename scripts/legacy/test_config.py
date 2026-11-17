from app.core.config import settings

print("Application:", settings.app_name)
print("Database configuration loaded:", bool(settings.database_url))