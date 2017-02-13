#!/usr/bin/env python
"""
Copyright 2015 Brocade Communications Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
import sys

import requests.exceptions

import pyswitch.os.base.fabric_service
import pyswitch.os.base.lldp
import pyswitch.os.base.snmp
import pyswitch.os.base.vcs
import pyswitch.os.nos.base.interface
import pyswitch.os.nos.base.services
import pyswitch.os.slxos.base.services
import pyswitch.os.nos.base.system
import pyswitch.os.slxos.base.interface
import pyswitch.os.slxos.base.system
import pyswitch.utilities as util
import pyswitchlib.asset

NOS_ATTRS = ['snmp', 'interface', 'lldp', 'system', 'services',
             'fabric_service', 'vcs']
NOS_VERSIONS = {
    '7.0.1': {
        'snmp': pyswitch.os.base.snmp.SNMP,
        'interface': pyswitch.os.nos.base.interface.Interface,
        'lldp': pyswitch.os.base.lldp.LLDP,
        'system': pyswitch.os.nos.base.system.System,
        'services': pyswitch.os.nos.base.services.Services,
        'fabric_service': pyswitch.os.base.fabric_service.FabricService,
        'vcs': pyswitch.os.base.vcs.VCS

    },
    '7.1.0': {
        'snmp': pyswitch.os.base.snmp.SNMP,
        'interface': pyswitch.os.nos.base.interface.Interface,
        'lldp': pyswitch.os.base.lldp.LLDP,
        'system': pyswitch.os.nos.base.system.System,
        'services': pyswitch.os.nos.base.services.Services,
        'fabric_service': pyswitch.os.base.fabric_service.FabricService,
        'vcs': pyswitch.os.base.vcs.VCS
    },
}

SLXOS_VERSIONS = {
    '17.1.0': {
        'snmp': pyswitch.os.base.snmp.SNMP,
        'interface': pyswitch.os.slxos.base.interface.Interface,
        'lldp': pyswitch.os.base.lldp.LLDP,
        'system': pyswitch.os.slxos.base.system.System,
        'services': pyswitch.os.slxos.base.services.Services,
        'fabric_service': pyswitch.os.base.fabric_service.FabricService,
        'vcs': pyswitch.os.base.vcs.VCS

    },
}


class DeviceCommError(Exception):
    """
    Error with device communication.
    """
    pass


class Reply:
    def __init__(self, json):
        self.json = json


class Device(object):
    """
    Device object holds the state for a single NOS device.

    Attributes:
        bgp: BGP related actions and attributes.
        interface: Interface related actions and attributes.
        snmp: SNMP related actions and attributes.
        lldp: LLDP related actions and attributes.
        system: System level actions and attributes.
    """

    def __init__(self, **kwargs):
        """

        """
        self._conn = kwargs.pop('conn')
        self.host = self._conn[0]
        self.logger = logging.getLogger(__name__)
        self._auth = kwargs.pop('auth', (None, None))
        self._callback = kwargs.pop('callback', None)

        if self._callback is None:
            self._callback = self._callback_main

        self._mgr = None
        self._cli = None

        self.reconnect()

        ver = self.firmware_version
        thismodule = sys.modules[__name__]
        os_table = getattr(thismodule, '%s_VERSIONS' % str(self.os_type).upper())

        for nos_attr in NOS_ATTRS:
            setattr(self, nos_attr, os_table[ver][nos_attr](self._callback))

        setattr(self, 'asset', self._mgr)

    def __enter__(self):
        if not self._mgr:
            self.reconnect()

        """
        if not self._cli:
            self._cli = ConnectHandler(device_type='brocade_nos',
                                       ip=self._conn[0],
                                       username=self._auth[0],
                                       password=self._auth[1])
            self.bgp._cli = self._cli
        """
        return self

    def __exit__(self, exctype, excisnt, exctb):

        if self._mgr:
            self._mgr._cleanup_timer_handle()
            self._mgr._session.close()

    @property
    def mac_table(self):
        """list[dict]: the MAC table of the device.

        """
        table = []

        config = ('get_mac_address_table_rpc', {})

        rest_root = self._callback(config, handler='get')

        for entry in util.find(rest_root.json, '$..mac-address-table'):
            address = util.find(entry, '$..mac-address')
            vlan = util.find(entry, '$..vlanid')
            mac_type = util.find(entry, '$..mac-type')
            state = util.find(entry, '$..mac-state')
            interface = util.find(entry, '$..forwarding-interface')
            interface_type = util.find(interface, '$..interface-type')
            interface_name = util.find(interface, '$..interface-name')
            interface = '%s%s' % (interface_type, interface_name)

            table.append(dict(mac_address=address, interface=interface,
                              state=state, vlan=vlan,
                              type=mac_type))

        return table

    @property
    def os_type(self):
        return self._mgr.get_os_type()

    @property
    def firmware_version(self):
        """
        Returns firmware version.

        Args:
            None

        Returns:
            Dictionary

        Raises:
            None

        """

        config = ('show_firmware_version_rpc', {})

        rest_root = self._callback(config, handler='get')

        return util.find(rest_root.json, '$..os-version')

    def _callback_main(self, call, handler='edit_config', target='running',
                       source='startup'):
        """
        Callback for NETCONF calls.
        Args:
            call: An Element Tree element containing the XML of the NETCONF
                call you intend to make to the device.
            handler: Type of ncclient call to make.
                get_config: NETCONF standard get config.
                get: ncclient dispatch. For custom RPCs.
                edit_config: NETCONF standard edit.
                delete_config: NETCONF standard delete.
                copy_config: NETCONF standard copy.
            target: Target configuration location for action. Only used for
                edit_config, delete_config, and copy_config.
            source: Source of configuration information for copying
                configuration. Only used for copy_config.
        Returns:
            None
        Raises:
            None
        """

        print 'asset.%s(%s)' % (call[0], ", ".join(
            ["=".join([key, '\'%s\'' % str(val) if isinstance(val, str) else str(val)]) for key, val in
             call[1].items()]))
        (status, result) = getattr(self._mgr, call[0])(**call[1])

        if not status:
            op = self._mgr.get_dict_output()
            print op
            if '' != op and 'object already exists' not in op:
                raise ValueError(op)

        if handler == 'get_config':
            return Reply(self._mgr.get_dict_output())
        return Reply(self._mgr.get_dict_output())

    def reconnect(self):
        """
        Reconnect session with device.

        Args:
            None

        Returns:
            bool: True if reconnect succeeds, False if not.

        Raises:
            None
        """

        try:
            self._mgr = pyswitchlib.asset.Asset(ip_addr=self._conn[0],
                                                auth=self._auth)

            self.logger.info('successfully connected to %s' % self._conn[0])
        except AttributeError as e:
            raise ValueError('Failed to connect to %s due to %s', self.host, e.message)
        except ValueError as verr:
            self.logger.error("Error while logging in to %s due to %s",
                              self.host, verr.message)
            raise ValueError("Error while logging in to %s due to %s",
                             self.host, verr.message)
        except requests.exceptions.ConnectionError as cerr:
            self.logger.error("Connection failed while logging in to %s due to %s",
                              self.host, cerr.message.reason)
            raise ValueError("Connection failed while logging in to %s due to %s",
                             self.host, cerr.message.reason)
        except pyswitchlib.asset.RestInterfaceError as rierr:
            self.logger.error("Failed to get a REST response while logging in "
                              "to %s due to %s", self.host, rierr.message)
            raise ValueError("Failed to get a REST response while logging in "
                             "to %s due to %s", self.host, rierr.message)

        return True

    def find_interface_by_mac(self, **kwargs):
        """Find the interface through which a MAC can be reached.
        Args:
            mac_address (str): A MAC address in 'xx:xx:xx:xx:xx:xx' format.
        Returns:
            list[dict]: a list of mac table data.
        Raises:
            KeyError: if `mac_address` is not specified.
        Examples:
            >>> from pprint import pprint
            >>> import pyswitch.device
            >>> conn = ('10.24.39.211', '22')
            >>> auth = ('admin', 'password')
            >>> with pyswitch.device.Device(conn=conn, auth=auth) as dev:
            ...     x = dev.find_interface_by_mac(
            ...     mac_address='10:23:45:67:89:ab')
            ...     pprint(x) # doctest: +ELLIPSIS
            [{'interface'...'mac_address'...'state'...'type'...'vlan'...}]
        """
        mac = kwargs.pop('mac_address')
        results = [x for x in self.mac_table if x['mac_address'] == mac]
        return results

    def close(self):
        """Close REST session.
        Args:
            None
        Returns:
            None
        Raises:
            None
        Examples:
            >>> import pyswitch.device
            >>> conn = ('10.24.39.211', '22')
            >>> auth = ('admin', 'password')
            >>> dev = pyswitch.device.Device(conn=conn, auth=auth)
            >>> dev.connection
            True
            >>> dev.close() # doctest: +ELLIPSIS
            <?xml...<rpc-reply...<ok/>...
            >>> dev.connection
            False
        """
        return self._mgr.close_session()
0
