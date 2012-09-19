# -*- coding: utf-8 -*-
#
# Author: Orcun Avsar <orc.avs@gmail.com>

from tastypie.authorization import DjangoAuthorization


class OwnerAuthorization(object):

    def __init__(self, owner_field_name='user'):
        self._owner_field_name = owner_field_name

    def apply_limits(self, request, object_list=None):

        if (request and request.method in ('GET', 'POST', 'DELETE') and
            not request.user.is_superuser):
            kwargs = {self._owner_field_name: request.user}
            return object_list.filter(**kwargs)
        else:
            return object_list

    def is_authorized(self, *args, **kwargs):
        return True
