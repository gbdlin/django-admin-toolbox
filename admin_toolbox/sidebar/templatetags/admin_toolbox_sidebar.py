# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six
from django import template
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from six import string_types

from admin_toolbox import settings

register = template.Library()


@register.filter()
def check_show_breadcrumbs(_):
    return settings.ADMIN_TOOLBOX.get('breadcrumbs', False)


@register.inclusion_tag('admin_toolbox/sidebar.html', takes_context=True)
def admin_sidebar_content(context, menu_name='default'):

    request = context.request

    config = settings.sidebar.get(menu_name)

    if isinstance(config, string_types):
        config = (config, {})

    if not isinstance(config, (list, tuple)) or len(config) != 2:
        raise ImproperlyConfigured(menu_name)

    builder_class_path, builder_kwargs = config
    builder_kwargs.setdefault('name', 'Django admin')

    builder_class = import_string(builder_class_path)
    builder = builder_class(**builder_kwargs)

    items = builder.build(request, context, menu_name)['items']

    track_active = {}
    track_existing = set()

    current_url = request.path

    level_stack = [(0, items, 0)]
    last_remove = False

    while level_stack:
        level = level_stack[-1]
        current_items = level[1]
        item_no = level[2]

        if last_remove:
            current_items.pop(item_no)
            last_remove = False
        if item_no >= len(current_items):
            level_stack.pop()
            if item_no == 0:
                last_remove = True
            else:
                try:
                    parent = level_stack[-1]
                except IndexError:
                    break
                level_stack[-1] = (
                    parent[0],
                    parent[1],
                    parent[2] + 1,
                )
            continue

        item = current_items[item_no]
        if 'items' in item:
            level_stack.append((len(level_stack), item['items'], 0))
            continue

        if 'url' in item:
            if item['url'] in track_existing:
                current_items.pop(item_no)
                continue
            if current_url.startswith(item['url']):
                track_active[
                    tuple(s[2] for s in level_stack)
                ] = item['url']
            track_existing.add(item['url'])
        item_no += 1
        level_stack[-1] = (level[0], level[1], item_no)

    track_active = sorted(
        six.iteritems(track_active),
        key=lambda x: (-len(x[1]), x[0])
    )
    current_items = items
    if track_active:
        for index in track_active[0][0]:
            current_items[index]['active'] = True
            current_items = current_items[index]['items'] if 'items' in current_items[index] else []

    return {
        'items': items,

    }


@register.filter
def get_by_key(var, key):
    return var.get(key)

