from __future__ import absolute_import

import unittest

import yaml
from attrdict import AttrDict

from pyswitch.device import Device


class InterfaceISISTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(InterfaceISISTestCase, self).__init__(*args, **kwargs)
        with open('config.yaml') as fileobj:
            cfg = AttrDict(yaml.safe_load(fileobj))
            switch = cfg.InterfaceISISTestCase.switch

            self.switch_ip = switch.ip
            self.switch_username = switch.username
            self.switch_pasword = switch.password

            self.intf_name = str(switch.intf_name)
            self.intf_type = str(switch.intf_type)

            self.conn = (self.switch_ip, '22')
            self.auth = (self.switch_username, self.switch_pasword)

    def setUp(self):
        with Device(conn=self.conn, auth=self.auth) as dev:

    def tearDown(self):
        with Device(conn=self.conn, auth=self.auth) as dev:

    def test_enable_isis_on_intf(self):
        with Device(conn=self.conn, auth=self.auth) as dev:
            dev.interface.ip_router_isis(
                intf_type='loopback',
                intf_name='11')
            op = dev.interface.ip_ospf(
                intf_type='loopback',
                intf_name='11',
                get=True)
            self.assertEqual(op)
            op = dev.interface.ip_ospf(
                intf_type='loopback',
                intf_name='11',
                delete=True)
