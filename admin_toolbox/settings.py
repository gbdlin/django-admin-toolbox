from django.conf import settings

ADMIN_TOOLBOX = getattr(settings, 'ADMIN_TOOLBOX', {})

sidebar = ADMIN_TOOLBOX.get('sidebar', {
    'default': 'admin_toolbox.sidebar.builders.AppsListBuilder',
})
