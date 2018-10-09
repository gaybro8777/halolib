from __future__ import print_function

# python
import logging
from abc import ABCMeta

# aws
# common
# django
# from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from rest_framework import status
from rest_framework.response import Response

from .const import HTTPChoice
from .const import settingsx
from .exceptions import AuthException
from .util import Util

settings = settingsx()

# Create your mixin here.

# DRF

# When a service is not responding for a certain amount of time, there should be a fallback path so users are not waiting for the response,
# but are immediately notified about the internal problem with a default response. It is the essence of a responsive design.

logger = logging.getLogger(__name__)


class AbsBaseMixin(object):
    __metaclass__ = ABCMeta

    name = 'Base'

    def __init__(self):
        self.name = self.get_name()

    def get_the_template(self, request, name):
        return loader.get_template(name)

    def get_root_url(self):
        if not settings.STAGE_URL:
            root = '/'
        else:
            root = "/" + settings.ENV_NAME + "/"
        return root

    def get_name(self):
        name = self.__class__.__name__
        new_name = name.replace('Link', '')
        return new_name

    def process_get(self, request, vars):
        try:
            t = self.get_the_template(request, self.name + '.html')
            root = self.get_root_url()
            c = {'the_title_string': 'welcome', 'the_site_string': settings.SITE_NAME, 'the_env_static_string': root,
                 'the_content': 'this is a get on view ' + self.name, 'version': settings.VERSION,
                 'messages': messages.get_messages(request)}
            if t:
                html = t.render(c)
            else:
                html = 'this is a get on view ' + self.name
        except TemplateDoesNotExist:
            html = 'this is a get on view ' + self.name
        return HttpResponse(html)

    def process_post(self, request, vars):
        return HttpResponse('this is a post on view ' + self.name)

    def process_put(self, request, vars):
        return HttpResponse('this is a put on view ' + self.name)

    def process_patch(self, request, vars):
        return HttpResponse('this is a patch on view ' + self.name)

    def process_delete(self, request, vars):
        return HttpResponse('this is a delete on view ' + self.name)

    def check_author(self, request, vars, json):
        # @TODO check authorization and do masking
        return True, json, None

    def check_authen(self, typer, request, vars):
        # @TODO check authentication and do masking
        return True, None


class AbsApiMixin(AbsBaseMixin):
    __metaclass__ = ABCMeta

    name = 'Api'
    class_name = None
    correlate_id = None
    req_context = None

    def __init__(self):
        AbsBaseMixin.__init__(self)
        self.class_name = self.__class__.__name__

    def process_in_auth(self, typer, request, vars):
        # who can use this resource with this method - api product,app,user,role,scope
        ret, cause = self.check_authen(typer, request, vars)
        if ret:
            ctx = Util.get_auth_context(request)
            logger.debug("ctx:" + str(ctx), extra=log_json(self.req_context))
            return ctx
        raise AuthException(request, cause)

    def process_out_auth(self, request, vars, json):
        ret, jsonx, cause = self.check_author(request, vars, json)
        # who can use this model with this method - object,field
        if ret:
            logger.debug("jsonx:" + str(jsonx), extra=log_json(self.req_context))
            return jsonx
        raise AuthException(request, cause)

    # raise AuthException(typer,resource,cause)

    def process_get(self, request, vars):
        try:
            ctx = self.process_in_auth(HTTPChoice.get, request, vars)
        except AuthException as e:
            return HttpResponse(e.cause, status=status.HTTP_400_BAD_REQUEST)
        json, ret_status = self.process_api(ctx, HTTPChoice.get, request, vars)
        if ret_status == status.HTTP_200_OK:
            jsonx = self.process_out_auth(request, vars, json)
            return Response(jsonx, status=ret_status)
        return HttpResponse(status=ret_status)

    def process_post(self, request, vars):
        try:
            ctx = self.process_in_auth(HTTPChoice.post, request, vars)
        except AuthException as e:
            return HttpResponse(e.cause, status=status.HTTP_400_BAD_REQUEST)
        json, ret_status = self.process_api(ctx, HTTPChoice.post, request, vars)
        if ret_status == status.HTTP_201_CREATED:
            jsonx = self.process_out_auth(request, vars, json)
            return Response(jsonx, status=ret_status)
        return HttpResponse(status=ret_status)

    def process_put(self, request, vars):
        try:
            ctx = self.process_in_auth(HTTPChoice.put, request, vars)
        except AuthException as e:
            return HttpResponse(e.cause, status=status.HTTP_400_BAD_REQUEST)
        json, ret_status = self.process_api(ctx, HTTPChoice.put, request, vars)
        if ret_status == status.HTTP_202_ACCEPTED:
            jsonx = self.process_out_auth(request, vars, json)
            return Response(jsonx, status=ret_status)
        return HttpResponse(status=ret_status)

    def process_patch(self, request, vars):
        try:
            ctx = self.process_in_auth(HTTPChoice.patch, request, vars)
        except AuthException as e:
            return HttpResponse(e.cause, status=status.HTTP_400_BAD_REQUEST)
        json, ret_status = self.process_api(ctx, HTTPChoice.patch, request, vars)
        if ret_status == status.HTTP_202_ACCEPTED:
            jsonx = self.process_out_auth(request, vars, json)
            return Response(jsonx, status=ret_status)
        return HttpResponse(status=ret_status)

    def process_delete(self, request, vars):
        try:
            ctx = self.process_in_auth(HTTPChoice.delete, request, vars)
        except AuthException as e:
            return HttpResponse(e.cause, status=status.HTTP_400_BAD_REQUEST)
        json, ret_status = self.process_api(ctx, HTTPChoice.delete, request, vars)
        if ret_status == status.HTTP_200_OK:
            return Response(status=ret_status)
        return HttpResponse(status=ret_status)

    def process_api(self, ctx, typer, request, vars):
        return {}, 200

##################################### test #########################
import json
from .logs import log_json
from .apis import ApiTest
from .exceptions import ApiError
from .saga import load_saga, SagaRollBack
class TestMixin(AbsApiMixin):
    def process_api(self, ctx, typer, request, vars):
        self.upc = "123"
        self.typer = typer
        if typer == typer.get:
            logger.debug("start get")
            api = ApiTest(self.req_context)
            # api.set_api_url("upcid", upc)
            # api.set_api_query(request)
            try:
                ret = api.get()
            except ApiError as e:
                logger.debug("we did it", extra=log_json(self.req_context, Util.get_req_params(request), e))
                return {"test": "bad"}, 400
            # except NoReturnApiException as e:
            #    print("NoReturnApiException="+e.message)
            # log_json(self.req_context, LogLevels.DEBUG._name_, "we did it", Util.get_req_params(request))
            return {"test": "good"}, 200

        if typer == typer.post or typer == typer.put:
            logger.debug("start " + str(typer))
            with open("C:\\dev\\projects\\halo\halo_lib\\saga.json") as f:
                jsonx = json.load(f)
            sagax = load_saga(jsonx)
            payloads = {"BookHotel": {"abc": "def"}, "BookFlight": {"abc": "def"}, "BookRental": {"abc": "def"},
                        "CancelHotel": {"abc": "def"}, "CancelFlight": {"abc": "def"}, "CancelRental": {"abc": "def"}}
            apis = {"BookHotel": self.create_api1, "BookFlight": self.create_api2, "BookRental": self.create_api3,
                    "CancelHotel": self.create_api4, "CancelFlight": self.create_api5, "CancelRental": self.create_api6}
            try:
                ret = sagax.execute(self.req_context, payloads, apis)
                return {"test": "good"}, 200
            except SagaRollBack as e:
                return {"test": "bad"}, 500

    def create_api1(self, api, results, payload):
        print("create_api1=" + str(api) + " result=" + str(results))
        api.set_api_url("upcid", self.upc)
        return api.get(payload)

    def create_api2(self, api, results, payload):
        print("create_api2=" + str(api) + " result=" + str(results))
        api.set_api_url("upcid", self.upc)
        return api.get(payload)

    def create_api3(self, api, results, payload):
        print("create_api3=" + str(api) + " result=" + str(results))
        api.set_api_url("upcid", self.upc)
        if self.typer == self.typer.post:
            return api.post(payload)
        return api.get(payload)

    def create_api4(self, api, results, payload):
        print("create_api4=" + str(api) + " result=" + str(results))
        api.set_api_url("upcid", self.upc)
        return api.get(payload)

    def create_api5(self, api, results, payload):
        print("create_api5=" + str(api) + " result=" + str(results))
        api.set_api_url("upcid", self.upc)
        return api.get(payload)

    def create_api6(self, api, results, payload):
        print("create_api6=" + str(api) + " result=" + str(results))
        api.set_api_url("upcid", self.upc)
        return api.get(payload)


"""
class JSMixin(AbsApiMixin):
    def process_api(self, ctx, typer, request, vars):
        api = ApiLambda()
        try:
            event = get_event(request)
            func_name = "nodejs"
            swagger = get_code(api_key_id)
            code = get_code(swagger,method_id)
            event.append(code)
            ret = api.call_lambda(func_name, event)
            print str(ret.content)
        except HaloException, e:
            print str(e.message)
        return {}, 200
"""
