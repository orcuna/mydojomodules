# -*- coding: utf-8 -*-
'''

from django.utils import simplejson as json


class RespectDojoMiddleware(object):

    def process_response(self, request, response):
        if request.path.startswith('/dojopie'):
            response_data = json.loads(response.content)
            if 'objects' in response_data:
                response_data['items'] = response_data['objects']
                del response_data['objects']

                response_data['totalCount'] = response_data['meta']['total_count']
                #del response_data['meta']['total_count']

                new_response_content = json.dumps(response_data)

                response.content = new_response_content

        return response
'''
