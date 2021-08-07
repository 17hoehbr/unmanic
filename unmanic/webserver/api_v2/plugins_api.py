#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic.plugins_api.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     01 Aug 2021, (9:30 AM)

    Copyright:
           Copyright (C) Josh Sunnex - All Rights Reserved

           Permission is hereby granted, free of charge, to any person obtaining a copy
           of this software and associated documentation files (the "Software"), to deal
           in the Software without restriction, including without limitation the rights
           to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
           copies of the Software, and to permit persons to whom the Software is
           furnished to do so, subject to the following conditions:

           The above copyright notice and this permission notice shall be included in all
           copies or substantial portions of the Software.

           THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
           EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
           MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
           IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
           DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
           OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
           OR OTHER DEALINGS IN THE SOFTWARE.

"""

import tornado.log
from unmanic.libs import session
from unmanic.libs.uiserver import UnmanicDataQueues
from unmanic.webserver.api_v2.base_api_handler import BaseApiHandler, BaseApiError
from unmanic.webserver.api_v2.schema.schemas import PluginsDataSchema, PluginsInfoResultsSchema, \
    PluginsInstallableResultsSchema, RequestPluginsInfoSchema, \
    RequestPluginsSettingsSaveSchema, RequestPluginsTableDataSchema, \
    RequestTableUpdateByIdList
from unmanic.webserver.helpers import plugins


class ApiPluginsHandler(BaseApiHandler):
    session = None
    config = None
    params = None
    unmanic_data_queues = None

    routes = [
        {
            "path_pattern":      r"/plugins/installed",
            "supported_methods": ["POST"],
            "call_method":       "get_installed_plugins",
        },
        {
            "path_pattern":      r"/plugins/enable",
            "supported_methods": ["POST"],
            "call_method":       "enable_plugins",
        },
        {
            "path_pattern":      r"/plugins/disable",
            "supported_methods": ["POST"],
            "call_method":       "disable_plugins",
        },
        {
            "path_pattern":      r"/plugins/update",
            "supported_methods": ["POST"],
            "call_method":       "update_plugins",
        },
        {
            "path_pattern":      r"/plugins/remove",
            "supported_methods": ["DELETE"],
            "call_method":       "remove_plugins",
        },
        {
            "path_pattern":      r"/plugins/info",
            "supported_methods": ["POST"],
            "call_method":       "get_plugin_info",
        },
        {
            "path_pattern":      r"/plugins/settings/update",
            "supported_methods": ["POST"],
            "call_method":       "update_plugin_settings",
        },
        {
            "path_pattern":      r"/plugins/installable",
            "supported_methods": ["GET"],
            "call_method":       "get_installable_plugin_list",
        },
    ]

    def initialize(self, **kwargs):
        self.session = session.Session()
        self.params = kwargs.get("params")
        udq = UnmanicDataQueues()
        self.unmanic_data_queues = udq.get_unmanic_data_queues()

    def get_installed_plugins(self):
        """
        Plugins - list installed plugins
        ---
        description: Returns a list of installed plugins.
        requestBody:
            description: Returns a list of installed plugins.
            required: True
            content:
                application/json:
                    schema:
                        RequestPluginsTableDataSchema
        responses:
            200:
                description: 'Sample response: Returns a list of installed plugins.'
                content:
                    application/json:
                        schema:
                            PluginsDataSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            json_request = self.read_json_request(RequestPluginsTableDataSchema())

            params = {
                'start':        json_request.get('start', '0'),
                'length':       json_request.get('length', '10'),
                'search_value': json_request.get('search_value', ''),
                'order':        {
                    "column": json_request.get('order_by', 'name'),
                    "dir":    json_request.get('order_direction', 'asc'),
                }
            }
            plugins_list = plugins.prepare_filtered_plugins(params)

            response = self.build_response(
                PluginsDataSchema(),
                {
                    "recordsTotal":    plugins_list.get('recordsTotal'),
                    "recordsFiltered": plugins_list.get('recordsFiltered'),
                    "results":         plugins_list.get('results'),
                }
            )
            self.write_success(response)
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()

    def enable_plugins(self):
        """
        Plugins - enable
        ---
        description: Enable a list of plugins.
        requestBody:
            description: Requested list of plugins to enable.
            required: True
            content:
                application/json:
                    schema:
                        RequestTableUpdateByIdList
        responses:
            200:
                description: 'Success: Deleted a list of completed tasks.'
                content:
                    application/json:
                        schema:
                            BaseSuccessSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            json_request = self.read_json_request(RequestTableUpdateByIdList())

            if not plugins.enable_plugins(json_request.get('id_list', [])):
                self.set_status(self.STATUS_ERROR_INTERNAL, reason="Failed to enable the plugins by their IDs")
                self.write_error()
                return

            self.write_success()
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()

    def disable_plugins(self):
        """
        Plugins - disable
        ---
        description: Disable a list of plugins.
        requestBody:
            description: Requested list of plugins to disable.
            required: True
            content:
                application/json:
                    schema:
                        RequestTableUpdateByIdList
        responses:
            200:
                description: 'Success: Deleted a list of completed tasks.'
                content:
                    application/json:
                        schema:
                            BaseSuccessSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            json_request = self.read_json_request(RequestTableUpdateByIdList())

            if not plugins.disable_plugins(json_request.get('id_list', [])):
                self.set_status(self.STATUS_ERROR_INTERNAL, reason="Failed to disable the plugins by their IDs")
                self.write_error()
                return

            self.write_success()
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()

    def update_plugins(self):
        """
        Plugins - update
        ---
        description: Update a list of plugins.
        requestBody:
            description: Requested list of plugins to update.
            required: True
            content:
                application/json:
                    schema:
                        RequestTableUpdateByIdList
        responses:
            200:
                description: 'Success: Deleted a list of completed tasks.'
                content:
                    application/json:
                        schema:
                            BaseSuccessSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            json_request = self.read_json_request(RequestTableUpdateByIdList())

            if not plugins.update_plugins(json_request.get('id_list', [])):
                self.set_status(self.STATUS_ERROR_INTERNAL, reason="Failed to update the plugins by their IDs")
                self.write_error()
                return

            self.write_success()
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()

    def remove_plugins(self):
        """
        Plugins - remove
        ---
        description: Remove a list of plugins.
        requestBody:
            description: Requested list of plugins to remove.
            required: True
            content:
                application/json:
                    schema:
                        RequestTableUpdateByIdList
        responses:
            200:
                description: 'Success: Deleted a list of completed tasks.'
                content:
                    application/json:
                        schema:
                            BaseSuccessSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            json_request = self.read_json_request(RequestTableUpdateByIdList())

            if not plugins.remove_plugins(json_request.get('id_list', [])):
                self.set_status(self.STATUS_ERROR_INTERNAL, reason="Failed to remove the plugins by their IDs")
                self.write_error()
                return

            self.write_success()
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()

    def get_plugin_info(self):
        """
        Plugins - return a requested plugin's metadata and settings
        ---
        description: Returns a the metadata and settings of a requested plugin.
        requestBody:
            description: Returns a list of installed plugins.
            required: True
            content:
                application/json:
                    schema:
                        RequestPluginsInfoSchema
        responses:
            200:
                description: 'Sample response: Returns a the metadata and settings of a requested plugin.'
                content:
                    application/json:
                        schema:
                            PluginsInfoResultsSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            json_request = self.read_json_request(RequestPluginsInfoSchema())

            plugin_id = json_request.get('plugin_id')
            prefer_local = json_request.get('prefer_local')

            plugins_info = plugins.prepare_plugin_info_and_settings(plugin_id, prefer_local)

            response = self.build_response(
                PluginsInfoResultsSchema(),
                {
                    "plugin_id":   plugins_info.get('plugin_id'),
                    "icon":        plugins_info.get('icon'),
                    "name":        plugins_info.get('name'),
                    "description": plugins_info.get('description'),
                    "tags":        plugins_info.get('tags'),
                    "author":      plugins_info.get('author'),
                    "version":     plugins_info.get('version'),
                    "changelog":   plugins_info.get('changelog'),
                    "status":      plugins_info.get('status'),
                    "settings":    plugins_info.get('settings')
                }
            )
            self.write_success(response)
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()

    def update_plugin_settings(self):
        """
        Plugins - Save the settings of a single plugin
        ---
        description: Saves the settings of a single plugin.
        requestBody:
            description: Returns a list of installed plugins.
            required: True
            content:
                application/json:
                    schema:
                        RequestPluginsSettingsSaveSchema
        responses:
            200:
                description: 'Sample response: Saves the settings of a single plugin.'
                content:
                    application/json:
                        schema:
                            BaseSuccessSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            json_request = self.read_json_request(RequestPluginsSettingsSaveSchema())

            if not plugins.update_plugin_settings(json_request.get('plugin_id'), json_request.get('settings')):
                self.set_status(self.STATUS_ERROR_INTERNAL, reason="Failed to save plugins settings")
                self.write_error()
                return

            self.write_success()
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()

    def get_installable_plugin_list(self):
        """
        Plugins - Read all installable plugins
        ---
        description: Returns a list of installable plugins.
        responses:
            200:
                description: 'Sample response: Returns a list of installable plugins.'
                content:
                    application/json:
                        schema:
                            PluginsInstallableResultsSchema
            400:
                description: Bad request; Check `messages` for any validation errors
                content:
                    application/json:
                        schema:
                            BadRequestSchema
            404:
                description: Bad request; Requested endpoint not found
                content:
                    application/json:
                        schema:
                            BadEndpointSchema
            405:
                description: Bad request; Requested method is not allowed
                content:
                    application/json:
                        schema:
                            BadMethodSchema
            500:
                description: Internal error; Check `error` for exception
                content:
                    application/json:
                        schema:
                            InternalErrorSchema
        """
        try:
            installable_plugins_list = plugins.prepare_installable_plugins_list()

            response = self.build_response(
                PluginsInstallableResultsSchema(),
                {
                    "plugins": installable_plugins_list
                }
            )
            self.write_success(response)
            return
        except BaseApiError as bae:
            tornado.log.app_log.error("BaseApiError.{}: {}".format(self.route.get('call_method'), str(bae)))
            return
        except Exception as e:
            self.set_status(self.STATUS_ERROR_INTERNAL, reason=str(e))
            self.write_error()