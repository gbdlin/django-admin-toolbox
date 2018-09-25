from six import string_types

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from .base import BaseBuilder


class ItemBuilder(BaseBuilder):
    """
    Simple manual element builder. You have to specify url and name of element. You can specify icon. If icon is not
    provided, will fallback to default one (determined by how much item is nested).
    """
    def __init__(self, url, name, icon=None, *args, **kwargs):
        super(ItemBuilder, self).__init__(*args, **kwargs)
        self.url = url
        self.name = name
        self.icon = icon

    def build(self, request=None, context=None, menu_name='default'):
        return {
            'url': self.url,
            'name': self.name,
            'icon': self.icon,
        }


class ListBuilder(BaseBuilder):
    """
    Simple sub-list builder. Each sub-item must be specified manually. Elements can be of any class.

    Each sub-list builder must inherit by this class.
    """

    def __init__(self, items, name, icon=None, *args, **kwargs):
        super(ListBuilder, self).__init__(*args, **kwargs)

        if not isinstance(items, (list, tuple)):
            raise ImproperlyConfigured(
                "`items` has to be list or tuple of elements that are either strings or 2-tuples of string and dict"
            )

        for i, item in enumerate(items):
            if any([
                not isinstance(item, string_types + (list, tuple)),
                isinstance(item, (list, tuple)) and len(item) != 2,
                isinstance(item, (list, tuple)) and len(item) == 2 and not isinstance(item[0], string_types),
                isinstance(item, (list, tuple)) and len(item) == 2 and not isinstance(item[1], dict),
            ]):
                raise ImproperlyConfigured(
                    "Each item has to be either string or 2-tuple of string and dict (error on item {})".format(i)
                )

        # normalize
        items = [
            (item, {}) if isinstance(item, string_types) else item
            for item in items
        ]

        self.items = [
            import_string(builder_path)(**kwargs)
            for builder_path, kwargs in items
        ]
        self.name = name
        self.icon = icon

    def build(self, request=None, context=None, menu_name='default'):
        return {
            'name': self.name,
            'icon': self.icon,
            'items': self.build_items(request, context, menu_name)
        }

    def build_items(self, request=None, context=None, menu_name='default'):
        return [item.build(request, context, menu_name) for item in self.items]
