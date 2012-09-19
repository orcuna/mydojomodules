# -*- coding: utf-8 -*-
#
# Author: Orcun Avsar <orc.avs@gmail.com

"""Module that autodiscovers and registers resources in INSTALLED_APPS.
"""

import sys
import imp
import inspect
from importlib import import_module

from django.conf import settings
from django.conf.urls import patterns

from tastypie.resources import ModelResource, Resource

from dojopie import apistore


RESOURCES_MODULE = 'resources'


def autodiscover():

    for app in settings.INSTALLED_APPS:

        if 'dojopie' in app:
            continue

        try:
            import_module(app)
            app_path = sys.modules[app].__path__
        except AttributeError:
            continue
        try:
            imp.find_module(RESOURCES_MODULE, app_path)
        except ImportError:
            continue

        module_import_path = '%s.%s' % (app, RESOURCES_MODULE)
        import_module(module_import_path)

        for name, Class in inspect.getmembers(sys.modules[module_import_path]):
            if inspect.isclass(Class):

                if Class == ModelResource or Class == Resource:
                    continue

                if issubclass(Class, ModelResource) or \
                   issubclass(Class, Resource):

                    try:
                        api_name = Class.Dojopie.api_name
                    except AttributeError:
                        api_name = 'v1'

                    try:
                        canonical = Class.Dojopie.canonical
                    except AttributeError:
                        canonical = True

                    api = apistore.get_or_create(api_name)
                    api.register(Class(), canonical)

autodiscover()


# Add autodiscovered apis' urls into urlpatterns
urlpatterns = patterns('')
for api in apistore.get_all():
    urlpatterns += api.urls

