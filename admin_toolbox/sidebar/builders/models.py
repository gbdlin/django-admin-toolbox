import six
from collections import defaultdict, OrderedDict

from django.apps import apps

from django.contrib.admin import site
from django.core.urlresolvers import reverse, NoReverseMatch

from .generic import ItemBuilder, ListBuilder


class ModelBuilderMixin(object):

    _app_dict = None

    @staticmethod
    def get_admin_apps():
        """
        For not having to constantly parse admin apps list, this method caches it globally in class
        :return:
        """
        if ModelBuilderMixin._app_dict is None:

            app_dict = defaultdict(list)
            models = site._registry.items()

            for model, model_admin in models:
                app_label = model._meta.app_label
                model_name = model._meta.object_name
                model_path = '.'.join([app_label, model_name])

                app_dict[app_label].append({
                    'name': model._meta.verbose_name_plural,
                    'app_label': app_label,
                    'model_name': model_name,
                    'model_path': model_path,
                })

            app_dict = OrderedDict(sorted(six.iteritems(app_dict), key=lambda x: x[0].lower()))

            for models in six.itervalues(app_dict):
                models.sort(key=lambda x: x['name'])

            ModelBuilderMixin._app_dict = app_dict

        return ModelBuilderMixin._app_dict

    def filter_app_models(self, models, fltr=None, exclude=None):
        if fltr is not None:
            def fltr_cond(x):
                return x['app_label'] in fltr or x['model_path'] in fltr
        else:
            def fltr_cond(x):
                return True

        if exclude is not None:
            def exclude_cond(x):
                return x['app_label'] not in exclude and x['model_path'] not in exclude
        else:
            def exclude_cond(x):
                return True
        return list(filter(fltr_cond, filter(exclude_cond, models)))

    def get_admin_apps_filtered(self, filter=None, exclude=None):
        return OrderedDict((
           (app_label, models) for app_label, models in (
                (al, self.filter_app_models(ml, filter, exclude)) for al, ml in six.iteritems(self.get_admin_apps())
            ) if models
        ))


class ModelBuilder(ModelBuilderMixin, ItemBuilder):
    """
    Element builder based on specified model class. URL will point to registered ModelAdmin for specified Model. Name
    will default to model's `verbose_name`. Icon will default to model's `menu_icon` or to default one (determined by
    how much item is nested) if `menu_icon` not provided in model's Meta.
    """

    def __init__(self, model_path, name=None, icon=None, *args, **kwargs):
        super(ModelBuilder, self).__init__(url=None, name=name, icon=icon, *args, **kwargs)
        app_name, model_name = model_path.rsplit('.', 2)[-2:]
        try:
            app = apps.get_app_config(app_name)
        except LookupError:
            return

        try:
            model = app.get_model(model_name)
        except LookupError:
            # try direct import, in case of fake model
            try:
                model = getattr(app.models_module, model_name)
            except AttributeError:
                # try direct import from admin, in case of fake admin
                try:
                    model = getattr(app.module.admin, model_name)
                except AttributeError:
                    return

        self.admin = site._registry.get(model)
        if self.admin is None:
            return
        opts = model._meta

        try:
            self.url = reverse('admin:{opts.app_label}_{opts.model_name}_changelist'.format(opts=opts))
        except NoReverseMatch:
            return

        self.name = name or opts.verbose_name_plural.capitalize()
        self.icon = icon or getattr(getattr(model, 'Meta', None), 'menu_icon', None)

    def build(self, request=None, context=None, menu_name='default'):
        if self.url is None:
            return None
        if request and not self.admin.has_module_permission(request):
            return None
        return super(ModelBuilder, self).build(context, menu_name)


class ModelsListBuilder(ModelBuilderMixin, ListBuilder):
    """
    Generates menu items from app models. Each subelement will represent one model from specified app. You can also
    """

    def __init__(self, app_name, models=None, exclude=None, name=None, icon=None, items=None, *args, **kwargs):
        if items is None:
            items = []

        super(ModelsListBuilder, self).__init__(name=name, icon=icon, items=items, *args, **kwargs)

        try:
            app_config = apps.get_app_config(app_name)
        except:
            return

        if models is not None:
            models = [
                '.'.join([app_name, model]) if '.' not in model else model for model in models
            ]
        elif exclude is not None:
            exclude = [
                '.'.join([app_name, model]) if '.' not in model else model for model in exclude
            ]
        models = self.get_admin_apps_filtered(filter=models, exclude=exclude).get(app_name, [])

        self.name = self.name or app_config.verbose_name
        self.icon = self.icon or getattr(app_config, 'menu_icon', None)

        self.items = list(self.items) + [
            ModelBuilder(
                model_path=model['model_path']
            ) for model in models
        ]


class AppsListBuilder(ModelBuilderMixin, ListBuilder):
    """
    Generates menu items from apps models (as sub-elements). Each subitem will represent one app. Can be extended with
    custom items which will go first. All other items will be placed at the beginning. Model will be skipped if URL of
    it was already added to menu.

    You can also provide apps to be skipped, using `exclude` or apps to be used using `apps`. You cannot mix those two
    together. If you won't provide `apps`, all apps will be used (except of one provided in `exclude`, if any).

    Apps and exclude can also take models, in form `app_label.model_name`. That way, you can include or exclude only
    particular models.
    """

    def __init__(self, name, apps=None, exclude=None, icon=None, items=None, *args, **kwargs):
        if items is None:
            items = []
        super(AppsListBuilder, self).__init__(name=name, icon=icon, items=items, *args, **kwargs)
        apps = self.get_admin_apps_filtered(filter=apps, exclude=exclude)

        self.items = list(self.items) + [
            ModelsListBuilder(
                app_name=app_name,
                models=[model['model_path'] for model in models],
            ) for app_name, models in six.iteritems(apps)
        ]


