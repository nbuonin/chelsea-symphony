"""Context Processors"""
from django.conf import settings


def global_vars(request):
    """Add global settings to templates"""
    return {
        'GA_TRACKING_ID': getattr(settings, 'GA_TRACKING_ID', None),
        'META_TRACKING_ID': getattr(settings, 'META_TRACKING_ID', None)
    }
