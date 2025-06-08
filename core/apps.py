from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    
    def ready(self):
        """Initialize core services when Django starts."""
        from core.services import configure_services
        configure_services()
        
        # Register system checks for settings validation
        try:
            import config.checks  # This will auto-register the checks
        except ImportError:
            # Gracefully handle missing checks in case of dependency issues
            pass