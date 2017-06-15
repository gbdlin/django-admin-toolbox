# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import apps
from django.contrib import admin
from django.core.urlresolvers import reverse, NoReverseMatch, resolve
from django.shortcuts import resolve_url
from django import template
from django.utils.module_loading import import_string
from six import string_types

from admin_toolbox import settings

register = template.Library()


@register.simple_tag()
def check_show_breadcrumbs():
    return settings.ADMIN_TOOLBOX.get('breadcrumbs', False)


@register.inclusion_tag('admin_toolbox/sidebar.html', takes_context=True)
def admin_sidebar_content(context, menu_name=None):

    if not menu_name:
        menu_name = 'default'

    request = context.request
    print(context)

    template_response = get_admin_site(context.request.resolver_match.namespace).index(request)

    config = settings.ADMIN_TOOLBOX.get('sidebar', {}).get(menu_name)

    if not config and menu_name != 'default':
        config = settings.ADMIN_TOOLBOX.get('sidebar', {}).get('default')

    app_list = template_response.context_data['app_list']

    if config:
        if callable(config):
            config = config()
        items = list(get_menu_from_config(config))
    else:
        items = list(get_menu_from_app_list(app_list))

    for item in items:
        if 'sub' in item:
            for sub in item['sub']:
                if 'url' in sub and request.path.startswith(sub['url']):
                    sub['active'] = True
                    break
            else:
                continue
            item['active'] = True
            break
        if 'url' in item and request.path.startswith(item['url']):
            item['active'] = True
            break

    return {
        'toolbox_admin_menu': items,
    }


def get_admin_site(current_app):
    """
    Tries to get actual admin.site class, if any custom admin sites
    were used.
    """
    # Couldn't find any other references to actual class other than in func_closer dict in index() func returned by
    # resolver.
    try:
        resolver_match = resolve(reverse('%s:index' % current_app))
        # Django 1.9 exposes AdminSite instance directly on view function
        if hasattr(resolver_match.func, 'admin_site'):
            return resolver_match.func.admin_site

        for func_closure in resolver_match.func.__closure__:
            if isinstance(func_closure.cell_contents, admin.AdminSite):
                return func_closure.cell_contents
    except:
        pass
    return admin.site


def get_item_from_model(model_path):
    opts = model_path.rsplit('.', 1)
    try:
        model = apps.get_model(*opts)
    except LookupError:
        return None

    try:
        url = reverse('admin:{}_{}_changelist'.format(*opts))
    except NoReverseMatch:
        return None

    return {
        'label': model._meta.verbose_name_plural.capitalize(),
        'url': url,
    }


def get_item_with_subitems(items):
    item = {
        'sub': [get_menu_entry(item, False) for item in items if item]
    }

    item['sub'] = list(filter(None, item['sub']))

    if not item['sub']:
        return None

    item['url'] = item['sub'][0]['url']

    return item


def get_menu_entry(it, with_sub=True):
    item = None
    if 'model' in it:
        item = get_item_from_model(it['model'])
    elif 'items' in it and with_sub:
        item = get_item_with_subitems(it['items'])
    elif 'items_callable' in it and with_sub:
        if isinstance(it['items_callable'], string_types):
            func = import_string(it['items_callable'])
        else:
            func = it['items_callable']
        item = get_item_with_subitems(func())

    elif 'url' in it:
        item = {
            'url': resolve_url(it['url']),
        }
    if not item:
        return None

    item.update({
        k: v for k, v in it.items() if k in ('label', 'icon') and v
    })

    item['active'] = False

    # Setting default icon or fixing class name of icon
    if 'icon' not in item:
        item['icon'] = 'fa fa-angle-double-right' if with_sub else None
    elif item['icon'].startswith('fa-'):
        item['icon'] = "fa " + item['icon']
    elif not item['icon'].startswith('fa fa-'):
        item['icon'] = "fa fa-" + item['icon']

    return item


def get_menu_from_config(config):
    return filter(None, map(get_menu_entry, config))


def get_menu_from_app_list(app_list):

    return [
        {
            'label': app['name'],
            'icon': 'fa fa-angle-double-right',
            'active': False,
            'sub': [
                {
                    'label': model['name'],
                    'url': model['admin_url'],
                    'active': False,
                    'icon': None,
                } for model in app['models']
            ],
            'url': app['models'][0]['admin_url']
        } for app in app_list if app['models']
    ]
