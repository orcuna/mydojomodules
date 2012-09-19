# -*- coding: utf-8 -*-
#
# author: Orcun Avsar <orc.avs@gmail.com>

from django import template
from django.db import models
from django.template import Context
from django.core.urlresolvers import reverse

from dojopie import apistore


register = template.Library()


DOJO_CELL_MAPPINGS = {
    models.DateTimeField: 'dojox.grid.cells.DateTextBox',
}


@register.simple_tag
def create_datagrid(grid_id, place_at_id, resource_name, api_name='v1'):
    """Creates dojox.data.DataGrid that talks to given resource over tastypie.
    """

    context_data = {}

    url = reverse('api_dispatch_list', kwargs={'resource_name': resource_name,
                                               'api_name': api_name})

    api = apistore.get(api_name)
    Resource = api.canonical_resource_for(resource_name)
    Model = Resource.Meta.queryset.model

    try:
        editables = Resource.Dojopie.editables
    except AttributeError:
        editables = [field_name for field_name in Resource.fields]

    try:
        editable_excludes = Resource.Dojopie.editable_excludes
    except AttributeError:
        editable_excludes = []

    fields = []

    iteration = hasattr(Resource.Meta, 'fields') and Resource.Meta.fields or \
                Resource.fields
    for field_name in iteration:

        if field_name in ('resource_uri', 'id'):
            continue

        _django_field = Model()._meta.get_field(field_name)
        _field = {}

        _field['editable'] = (field_name in editables and
                              field_name not in editable_excludes)
        _field['type'] = DOJO_CELL_MAPPINGS.get(type(_django_field))
        _field['verbose_name'] = _django_field.verbose_name
        _field['name'] = field_name

        fields.append(_field)

    context_data['target_url'] = url
    context_data['grid_id'] = grid_id
    context_data['place_at_id'] = place_at_id
    context_data['fields'] = fields

    t = template.loader.get_template('dojopie/_datagrid.html')
    return t.render(Context(context_data))
