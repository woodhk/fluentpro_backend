# Import tasks to register them with Celery
from .generate_recommendations import generate_user_recommendations, analyze_onboarding_completion

__all__ = [
    'generate_user_recommendations', 
    'analyze_onboarding_completion',
]