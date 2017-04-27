from django.conf import settings

ADMIN_TOOLBOX = getattr(settings, 'ADMIN_TOOLBOX', {
    'sidebar': {
    }
})
