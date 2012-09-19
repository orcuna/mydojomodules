# -*- coding: utf-8 -*-
#
# Author: Orcun Avsar <orc.avs@gmail.com>

from tastypie.authentication import SessionAuthentication


class SessionAuthenticationWithoutCSRF(SessionAuthentication):

    def is_authenticated(self, request, **kwargs):
        request._dont_enforce_csrf_checks = True
        return super(SessionAuthenticationWithoutCSRF, self).is_authenticated(
            request, **kwargs)
