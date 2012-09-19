'''
# -*- coding: utf-8 -*-
#
# Author: Orcun Avsar <orc.avs@gmail.com>

""" Monkey-patches to workaround Tastypie-Dojo compatibility issue.

Replaces 'objects' -> 'items'

See here:
http://stackoverflow.com/questions/11933182/using-dojo-grid-with-rest-tastypie

Monkey-patched methods are originally copied from tastypie==0.9.12alpha
"""

import tastypie
import tastypie.resources
import tastypie.serializers


def get_list(self, request, **kwargs):
    # TODO: Uncached for now. Invalidation that works for everyone may be
    #       impossible.
    objects = self.obj_get_list(request=request, **self.remove_api_resource_names(kwargs))
    sorted_objects = self.apply_sorting(objects, options=request.GET)

    paginator = self._meta.paginator_class(request.GET, sorted_objects, resource_uri=self.get_resource_uri(), limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name)
    to_be_serialized = paginator.page()

    # Dehydrate the bundles in preparation for serialization.
    bundles = [self.build_bundle(obj=obj, request=request) for obj in to_be_serialized['items']]
    to_be_serialized['items'] = [self.full_dehydrate(bundle) for bundle in bundles]
    to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
    return self.create_response(request, to_be_serialized)

tastypie.resources.Resource.get_list = get_list

from tastypie.resources import ObjectDoesNotExist, convert_post_to_patch, BadRequest, MultipleObjectsReturned, http, ImmediateHttpResponse, dict_strip_unicode_keys
def patch_list(self, request, **kwargs):
    request = convert_post_to_patch(request)
    deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))

    if "items" not in deserialized:
        raise BadRequest("Invalid data sent.")

    if len(deserialized["objects"]) and 'put' not in self._meta.detail_allowed_methods:
        raise ImmediateHttpResponse(response=http.HttpMethodNotAllowed())

    for data in deserialized["objects"]:
        # If there's a resource_uri then this is either an
        # update-in-place or a create-via-PUT.
        if "resource_uri" in data:
            uri = data.pop('resource_uri')

            try:
                obj = self.get_via_uri(uri, request=request)

                # The object does exist, so this is an update-in-place.
                bundle = self.build_bundle(obj=obj, request=request)
                bundle = self.full_dehydrate(bundle)
                bundle = self.alter_detail_data_to_serialize(request, bundle)
                self.update_in_place(request, bundle, data)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # The object referenced by resource_uri doesn't exist,
                # so this is a create-by-PUT equivalent.
                data = self.alter_deserialized_detail_data(request, data)
                bundle = self.build_bundle(data=dict_strip_unicode_keys(data), request=request)
                self.obj_create(bundle, request=request)
        else:
            # There's no resource URI, so this is a create call just
            # like a POST to the list resource.
            data = self.alter_deserialized_detail_data(request, data)
            bundle = self.build_bundle(data=dict_strip_unicode_keys(data), request=request)
            self.obj_create(bundle, request=request)

    if len(deserialized.get('deleted_items', [])) and 'delete' not in self._meta.detail_allowed_methods:
        raise ImmediateHttpResponse(response=http.HttpMethodNotAllowed())

    for uri in deserialized.get('deleted_items', []):
        obj = self.get_via_uri(uri, request=request)
        self.obj_delete(request=request, _obj=obj)

    return http.HttpAccepted()

tastypie.resources.Resource.patch_list = patch_list


def put_list(self, request, **kwargs):
    deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
    deserialized = self.alter_deserialized_list_data(request, deserialized)

    if not 'items' in deserialized:
        raise BadRequest("Invalid data sent.")
    self.obj_delete_list(request=request, **self.remove_api_resource_names(kwargs))
    bundles_seen = []

    for object_data in deserialized['items']:
        bundle = self.build_bundle(data=dict_strip_unicode_keys(object_data), request=request)

        # Attempt to be transactional, deleting any previously created
        # objects if validation fails.
        try:
            self.obj_create(bundle, request=request, **self.remove_api_resource_names(kwargs))
            bundles_seen.append(bundle)
        except ImmediateHttpResponse:
            self.rollback(bundles_seen)
            raise

    if not self._meta.always_return_data:
        return http.HttpNoContent()
    else:
        to_be_serialized = {}
        to_be_serialized['items'] = [self.full_dehydrate(bundle) for bundle in bundles_seen]
        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        return self.create_response(request, to_be_serialized, response_class=http.HttpAccepted)

tastypie.resources.Resource.put_list = put_list

from tastypie.serializers import *
def to_etree(self, data, options=None, name=None, depth=0):
    """
    Given some data, converts that data to an ``etree.Element`` suitable
    for use in the XML output.
    """
    if isinstance(data, (list, tuple)):
        element = Element(name or 'items')
        if name:
            element = Element(name)
            element.set('type', 'list')
        else:
            element = Element('items')
        for item in data:
            element.append(self.to_etree(item, options, depth=depth+1))
    elif isinstance(data, dict):
        if depth == 0:
            element = Element(name or 'response')
        else:
            element = Element(name or 'object')
            element.set('type', 'hash')
        for (key, value) in data.iteritems():
            element.append(self.to_etree(value, options, name=key, depth=depth+1))
    elif isinstance(data, Bundle):
        element = Element(name or 'object')
        for field_name, field_object in data.data.items():
            element.append(self.to_etree(field_object, options, name=field_name, depth=depth+1))
    elif hasattr(data, 'dehydrated_type'):
        if getattr(data, 'dehydrated_type', None) == 'related' and data.is_m2m == False:
            if data.full:
                return self.to_etree(data.fk_resource, options, name, depth+1)
            else:
                return self.to_etree(data.value, options, name, depth+1)
        elif getattr(data, 'dehydrated_type', None) == 'related' and data.is_m2m == True:
            if data.full:
                element = Element(name or 'items')
                for bundle in data.m2m_bundles:
                    element.append(self.to_etree(bundle, options, bundle.resource_name, depth+1))
            else:
                element = Element(name or 'items')
                for value in data.value:
                    element.append(self.to_etree(value, options, name, depth=depth+1))
        else:
            return self.to_etree(data.value, options, name)
    else:
        element = Element(name or 'value')
        simple_data = self.to_simple(data, options)
        data_type = get_type_string(simple_data)

        if data_type != 'string':
            element.set('type', get_type_string(simple_data))

        if data_type != 'null':
            if isinstance(simple_data, unicode):
                element.text = simple_data
            else:
                element.text = force_unicode(simple_data)

    return element

tastypie.serializers.Serializer.to_etree = to_etree


def from_etree(self, data):
    if data.tag == 'request':
        # if "object" or "objects" exists, return deserialized forms.
        elements = data.getchildren()
        for element in elements:
            if element.tag in ('object', 'items'):
                return self.from_etree(element)
        return dict((element.tag, self.from_etree(element)) for element in elements)
    elif data.tag == 'object' or data.get('type') == 'hash':
        return dict((element.tag, self.from_etree(element)) for element in data.getchildren())
    elif data.tag == 'items' or data.get('type') == 'list':
        return [self.from_etree(element) for element in data.getchildren()]
    else:
        type_string = data.get('type')
        if type_string in ('string', None):
            return data.text
        elif type_string == 'integer':
            return int(data.text)
        elif type_string == 'float':
            return float(data.text)
        elif type_string == 'boolean':
            if data.text == 'True':
                return True
            else:
                return False
        else:
            return None
tastypie.serializers.Serializer.from_etree = from_etree
'''
