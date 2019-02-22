# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from operator import itemgetter

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.translation import  ugettext as _
from six import text_type
from django import template
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
from admin_toolbox import settings

from .admin_toolbox_sidebar import admin_sidebar_content

register = template.Library()


@register.tag()
def rebreadcrumbs(parser, token):
    nodelist = parser.parse(('endrebreadcrumbs',))
    parser.delete_first_token()

    return RerenderBreadcrumbs(nodelist)


class RerenderBreadcrumbs(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
        pass

    def parse_node(self, node):
        soup = BeautifulSoup(node)
        if soup.find_all('a'):
            node = soup.a
            return node['href'], text_type(node.text).strip()
        else:
            return None, node.strip()

    def render(self, context):
        tx = self.nodelist.render(context)
        print('----------', tx, '-------------')

        if not settings.breadcrumbs:
            return ''

        if settings.breadcrumbs == 'smart':
            if BeautifulSoup is None:
                raise ImproperlyConfigured('beautifulsoup4 package is required for smart breadcrumbs to operate.')
            soup = BeautifulSoup(tx)
            tx = "".join(map(text_type, soup.div.contents if soup.div else []))

            nodes = [self.parse_node(node) for node in tx.split('›') if node]

            if not nodes:
                nodes = [
                    (None, _('Home'))
                ]

            active_path = admin_sidebar_content(context)['active_path']

            index_node = nodes[0]
            if active_path and active_path[-1]['url'] in set(map(itemgetter(0), nodes)):
                nodes = nodes[list(map(itemgetter(0), nodes)).index(active_path[-1]['url']) + 1:]
                nodes = [index_node] + [
                    (node.get('url'), node['name']) for node in active_path
                ] + nodes
            elif active_path:
                nodes = [index_node] + [
                    (node.get('url'), node['name']) for node in active_path
                ]
                if len(nodes) > 1:
                    nodes[-1] = (None, nodes[-1][1])
            elif len(nodes) > 1:
                nodes = [index_node, nodes[-1]]

            return render_to_string('admin_toolbox/breadcrumbs.html', context={'nodes': nodes})

        return tx
