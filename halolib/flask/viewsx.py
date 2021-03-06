from __future__ import print_function

# python
import datetime
import logging
import os
import traceback
from abc import ABCMeta

import jwt
from flask import Response as HttpResponse
from flask import redirect
# from flask_api import status
# from flask import request
# flask
from flask.views import MethodView

# halolib
from .utilx import Util
from ..const import HTTPChoice
from ..logs import log_json
from ..response import HaloResponse
from ..settingsx import settingsx

settings = settingsx()
# aws
# other

# Create your views here.
logger = logging.getLogger(__name__)


class AbsBaseLinkX(MethodView):
    __metaclass__ = ABCMeta

    """
        View to list all users in the system.

        * Requires token authentication.
        * Only admin users are able to access this view.
        """

    def __init__(self, **kwargs):
        super(AbsBaseLinkX, self).__init__(**kwargs)

    def do_process(self, request, typer, args=None):
        """

        :param request:
        :param typer:
        :param vars:
        :return:
        """
        now = datetime.datetime.now()

        self.req_context = Util.get_req_context(request)
        self.correlate_id = self.req_context["x-correlation-id"]
        self.user_agent = self.req_context["x-user-agent"]
        error_message = None
        error = None
        orig_log_level = 0

        if Util.isDebugEnabled(self.req_context, request):
            orig_log_level = logger.getEffectiveLevel()
            logger.setLevel(logging.DEBUG)
            logger.debug("DebugEnabled - in debug mode",
                         extra=log_json(self.req_context, Util.get_req_params(request)))

        logger.debug("headers", extra=log_json(self.req_context, Util.get_headers(request)))

        logger.debug("environ", extra=log_json(self.req_context, os.environ))

        if settings.HALO_HOST is None and 'HTTP_HOST' in request.headers:
            settings.HALO_HOST = request.headers['HTTP_HOST']
            from halolib.ssm import set_app_param_config
            set_app_param_config(settings.AWS_REGION, settings.HALO_HOST)


        try:
            ret = self.process(request, typer, args)
            total = datetime.datetime.now() - now
            logger.info("performance_data", extra=log_json(self.req_context,
                                                           {"type": "LAMBDA",
                                                            "milliseconds": int(total.total_seconds() * 1000)}))
            return ret

        except Exception as e:
            error = e
            error_message = str(error)
            e.stack = traceback.format_exc()
            logger.error(error_message, extra=log_json(self.req_context, Util.get_req_params(request), e))
            # exc_type, exc_obj, exc_tb = sys.exc_info()
            # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            # logger.debug('An error occured in '+str(fname)+' lineno: '+str(exc_tb.tb_lineno)+' exc_type '+str(exc_type)+' '+e.message)

        finally:
            self.process_finally(request, orig_log_level)

        total = datetime.datetime.now() - now
        logger.info("error performance_data", extra=log_json(self.req_context,
                                                             {"type": "LAMBDA",
                                                              "milliseconds": int(total.total_seconds() * 1000)}))

        error_code, json_error = Util.json_error_response(self.req_context, settings.ERR_MSG_CLASS, error)
        if settings.FRONT_WEB:
            return redirect("/" + str(error_code))
        ret = HaloResponse()
        ret.code = error_code
        ret.payload = json_error
        ret.headers = {'content-type': 'application/json'}
        return ret

    def process_finally(self, request, orig_log_level):
        """

        :param request:
        :param orig_log_level:
        """
        if Util.isDebugEnabled(self.req_context, request):
            if logger.getEffectiveLevel() != orig_log_level:
                logger.setLevel(orig_log_level)
                logger.info("process_finally - back to orig:" + str(orig_log_level),
                            extra=log_json(self.req_context))

    def process(self, request, typer, args):
        """
        Return a list of all users.
        """

        if typer == HTTPChoice.get:
            return self.process_get(request, args)

        if typer == HTTPChoice.post:
            return self.process_post(request, args)

        if typer == HTTPChoice.put:
            return self.process_put(request, args)

        if typer == HTTPChoice.patch:
            return self.process_patch(request, args)

        if typer == HTTPChoice.delete:
            return self.process_delete(request, args)

        return HttpResponse('this is a ' + str(typer) + ' on ' + self.get_view_name())

    def process_get(self, request, args):
        """

        :param request:
        :param vars:
        :return:
        """
        # return HttpResponse('this is process get on ' + self.get_view_name())
        ret = HaloResponse()
        ret.payload = 'this is process get on '  # + self.get_view_name()
        ret.code = 200
        ret.headers = []
        return ret

    def process_post(self, request, args):
        """

        :param request:
        :param vars:
        :return:
        """
        # return HttpResponse('this is process post on ' + self.get_view_name())
        ret = HaloResponse()
        ret.payload = 'this is process post on '  # + self.get_view_name()
        ret.code = 201
        ret.headers = []
        return ret

    def process_put(self, request, args):
        """

        :param request:
        :param vars:
        :return:
        """
        # return HttpResponse('this is process put on ' + self.get_view_name())
        ret = HaloResponse()
        ret.payload = 'this is process put on '  # + self.get_view_name()
        ret.code = 200
        ret.headers = []
        return ret

    def process_patch(self, request, args):
        """

        :param request:
        :param vars:
        :return:
        """
        # return HttpResponse('this is process patch on ' + self.get_view_name())
        ret = HaloResponse()
        ret.payload = 'this is process patch on '  # + self.get_view_name()
        ret.code = 200
        ret.headers = []
        return ret

    def process_delete(self, request, args):
        """

        :param request:
        :param vars:
        :return:
        """
        # return HttpResponse('this is process delete on ' + self.get_view_name())
        ret = HaloResponse()
        ret.payload = 'this is process delete on '  # + self.get_view_name()
        ret.code = 200
        ret.headers = []
        return ret

    def get_client_ip(self, request):
        """

        :param request:
        :return:
        """
        ip = request.headers.get('REMOTE_ADDR')
        logger.debug("get_client_ip: " + str(ip), extra=log_json(self.req_context))
        return ip

    def get_jwt(self, request):
        """

        :param request:
        :return:
        """
        ip = self.get_client_ip(request)
        encoded_token = jwt.encode({'ip': ip}, settings.SECRET_JWT_KEY, algorithm='HS256')
        return encoded_token

    def check_jwt(self, request):  # return true if token matches
        """

        :param request:
        :return:
        """
        ip = self.get_client_ip(request)
        encoded_token = request.GET.get('jwt', None)
        if not encoded_token:
            return False
        decoded_token = jwt.decode(encoded_token, settings.SECRET_JWT_KEY, algorithm='HS256')
        return ip == decoded_token['ip']

    def get_jwt_str(self, request):
        """

        :param request:
        :return:
        """
        return '&jwt=' + self.get_jwt(request).decode()


import flask_restful as restful


class Resource(restful.Resource):
    pass

from ..flask.mixinx import PerfMixinX
from flask import request

class PerfLinkX(Resource, PerfMixinX, AbsBaseLinkX):
    def get(self):
        ret = self.do_process(request, HTTPChoice.get)
        return Util.json_data_response(ret.payload, ret.code, ret.headers)

    def post(self):
        ret = self.do_process(request, HTTPChoice.post)
        return Util.json_data_response(ret.payload, ret.code, ret.headers)

    def put(self):
        ret = self.do_process(request, HTTPChoice.put)
        return Util.json_data_response(ret.payload, ret.code, ret.headers)

    def delete(self):
        ret = self.do_process(request, HTTPChoice.delete)
        return Util.json_data_response(ret.payload, ret.code, ret.headers)


##################################### test ##########################

from ..flask.mixinx import TestMixinX

class TestLinkX(Resource, TestMixinX, AbsBaseLinkX):

    def get(self):
        ret = self.do_process(request, HTTPChoice.get)
        return Util.json_data_response(ret.payload, ret.code, ret.headers)

    def post(self):
        ret = self.do_process(request, HTTPChoice.post)
        return Util.json_data_response(ret.payload, ret.code, ret.headers)

    def put(self):
        ret = self.do_process(request, HTTPChoice.put)
        return Util.json_data_response(ret.payload, ret.code, ret.headers)

    def delete(self):
        ret = self.do_process(request, HTTPChoice.delete)
        return Util.json_data_response(ret.payload, ret.code, ret.headers)
