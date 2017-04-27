Django Admin Toolbox
====================

This package provides bunch of useful tools for default django admin site, such as:

- `Admin sidebar`_

Tools are suited in separate packages, so you can pick ones that suits your needs.

All configuration is held in ``ADMIN_TOOLBOX`` dict that should be placed in your ``settings.py`` file.

Admin sidebar
*************

This django app adds sidebar to the left of standard django admin template.

Purpose of this sidebar is to replace default list of models in django admin with
something more customizable and useful.

Instalation
-----------

2. add ``admin_toolbox.sidebar`` (or anything you've named it) at the top of your ``INSTALLED_APPS`` (at least above ``django.contrib.admin``)

Configuration
-------------


