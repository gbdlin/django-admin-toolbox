======================
 Django Admin Toolbox
======================

This package provides bunch of useful tools for default django admin site, such as:

- `Admin sidebar`_

Tools are suited in separate packages, so you can pick ones that suits your needs.

All configuration is held in ``ADMIN_TOOLBOX`` dict that should be placed in your ``settings.py`` file.

Admin sidebar
=============

This django app adds sidebar to the left of standard django admin template.

Purpose of this sidebar is to replace default list of models in django admin with
something more customizable and useful.

Instalation
-----------

1. Install admin toolbox (if not installed already)
2. add ``admin_toolbox.sidebar`` (or anything you've named it) at the top of your ``INSTALLED_APPS`` (at least above ``django.contrib.admin``)

Configuration
-------------

By default, sidebar will just contain categories for all apps with models inside of them, which just corresponds to
list of apps and models on standard django admin dashboard. But you can customize that menu using builders. Example
below shows how admin menu is built by default:

.. code-block:: python

    ADMIN_TOOLBOX = {
        'sidebar': {
            'default': ('admin_toolbox.sidebar.builder.AppsListBuilder', {}),
        }
    }

``sidebar`` element inside ``ADMIN_TOOLBOX`` settings contains all defined menus (like for ``DATABASES``, you can
specify more than one menu). For now, only ``default`` menu is used, other ones will be ignored. Each menu consists of
root element. Each element is specified by tuple containing string and dictionary. String should be valid python dot
path to builder class, dictionary contains all default arguments that will be passed to that class when initializing.

Each builder is one of ``ListBuilder`` or ``ItemBuilder`` from ``admin_toolbox.sidebar.builder`` module or any subclass
of them. For root element, only ``ListBuilder`` and it's subclasses are allowed.

Root element of each menu is a container for whole menu, but it's logic is still invoked, but it won't be rendered as
a whole, only it's subitems will be. How to nest items is explained below.

Also, each element, except of root one, should have specified name (if specified builder cannot generate it
automatically).

There is default limit for nesting set to 3 levels. It is enforced on template level, so if you want to create menu
with more nested levels, simply overwrite template (and probably CSS) and implement displaying more than 3 levels in it.

Built-in builders
-----------------

Each builder can take ``name`` and ``icon`` parameter. For builders that cannot generate ``name`` by themselves (by for
example taking them from model or app name), ``name`` must be specified, unless builder is used as root element

``ListBuilder``
***************

Builder that contains sub-elements. It's just a container, so by default, does nothing. ``name`` argument is required if
not used as root element. ``items`` argument is required and should be a list or tuple of 2-tuples defined like root
element.

``ItemBuilder``
***************

Builder that represents simple url. ``name`` argument is required. ``url`` argument is required. It also can take
``permissions_check`` that should be either callable or dotted path to callable that will return True or False
determining if user can see this option in menu. It should take ``request``, ``context`` and ``menu_name`` parameters.

``ModelBuilder``
****************

Builder that represents ``ModelAdmin``. It simply looks for ``ModelAdmin`` for specified model and puts URL to it's
changelist in menu. ``model`` is required and should be in form of ``app_name.ModelName`` or ``path_to_app.ModelName``,
there should be no ``.models`` inside path to model. ``name`` is optional, if not provided will default to model's
name. If icon is not provided, builder will try to get it from ``menu_icon`` attribute of Model's ``Meta`` class and if
it fails, will default to one based on navigation level.

``ModelsBuilder``
*****************

Builder that represents all model admins from specified app. It will scan for models in specified app and put them as
sub-elements, using ``ModelBuilder`` for each of them. You can also specify ``items`` that can contain any sub-items.
Any subitem manually specified in ``items`` will come before items automatically added from scanning app. If Model or
path to Model admin is referenced in ``items`` it will be automatically skipped later on, when creating automatic
list of app models, so every model is used only once. This is global behaviour for every URL You can also set
``models`` or ``exclude`` parameters that will limit which models should be used. They can't be used together. If
``models`` is used, only models specified in ``models`` will be used. ``models`` and ``exclude`` should be just in form
of list of model names (without app name). As for model, ``name`` is optional and if not provided, will default to
app name. Also, similarly to model, builder will try to fetch icon from ``AppConfig``'s ``menu_icon`` attribute and
fall back to default one based on navigation level.

``AppsBuilder``
***************

Builder that represents all apps with their models. It will scan for apps in project and put every app as sub-item
using ``ModelsBuilder`` (which will build sub-item for every model in app). You can specify ``apps`` and ``exclude``
which works like ``models`` and ``exclude`` in ``ModelsBuilder``, but instead put app names as list (without full path).
You can also specify single models in ``apps`` and ``exclude`` together with app names. Models should be in form of
``app_name.ModelName``, models specified without app name will be treated like apps and may result in unexpected
behaviour. ``name`` is required if item is not used as root item, because there is no place from which we can get
default name. ``icon`` may be customized like in other items, but there is no special place for defining it.

Icons
-----

You can use any icon from font awesome icons in menu, just by providing it's name. Version 4.6.2 is embedded, if you
need newer one, just edit base template and put there your own version (or replace font awesome files in staticfiles,
that works too). Icon can be defined in every builder, using ``icon`` argument (icon for root element will be ignored,
for obvious reasons) or in case of models and apps (and using ``ModelBuilder``, ``ModelsBuilder`` or ``AppsBuilder``),
you can set default icon accordingly in models ``Meta`` or in apps ``AppConfig`` using ``menu_icon`` attribute. If no
icon is defined for particular item, it defaults to icon based on navigation level (``angle-right`` for 1st level,
``angle-double-right`` for 2nd level and no icon for 3rd level).
