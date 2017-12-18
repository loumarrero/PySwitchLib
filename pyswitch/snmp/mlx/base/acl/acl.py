"""
Copyright 2017 Brocade Communications Systems, Inc.
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
import inspect
import jinja2
import re
import acl_template

from pyswitch.snmp.base.acl.acl import Acl as BaseAcl
from pyswitch.snmp.base.acl.macacl import MacAcl
from pyswitch.snmp.base.acl.ipacl import IpAcl
from pyswitch.snmp.base.acl.ipv6acl import Ipv6Acl
import pyswitch.snmp.base.acl.params_validator as params_validator


class Acl(BaseAcl):
    """
    The Acl class holds all the functions assocaiated with the
    Access Control list of a MLX device.
    Attributes:
        None
    """

    def __init__(self, callback):
        """
        ACL init function.
        Args:
            callback: Callback function that will be called for each action.
        Returns:
            ACL Object
        Raises:
            ValueError
        """
        super(Acl, self).__init__(callback)

        self._mac = MacAcl()
        self._ip = IpAcl()
        self._ipv6 = Ipv6Acl()

    @property
    def mac(self):
        return self._mac

    @property
    def ip(self):
        return self._ip

    @property
    def ipv6(self):
        return self._ipv6

    def create_acl(self, **parameters):
        """
        Create an Access Control List.
        Args:
            address_type (str): ACL address type, ip or ipv6 or mac.
            acl_type (str): ACL type, extended or standard.
            acl_name (str): Unique name for ACL.
            callback (function): A function executed upon completion of the
                method. The only parameter passed to `callback` will be the
                ``ElementTree`` `config`.
        Returns:
            Return value of `string` message.
        Raise:
            Raises ValueError, Exception
        Examples:
            >>> from pyswitch.device import Device
            >>> with Device(conn=conn, auth=auth,
            ...             connection_type='NETCONF') as dev:
            ...     print dev.firmware_version
            ...     print dev.os_type
            ...     print dev.acl.create_acl(acl_name='Acl_1',
            ...                              acl_type='standard',
            ...                              address_type='mac')
            ...     print dev.acl.create_acl(acl_name='Acl_2',
            ...                              acl_type='extended',
            ...                              address_type='ip')
        """
        params_validator.validate_params_mlx_create_acl(**parameters)

        address_type = parameters['address_type']
        acl_type = parameters.get('acl_type', None)
        acl_name = self.mac.parse_acl_name(**parameters)

        if address_type == 'mac':
            config = 'mac access-list ' + acl_name
        elif address_type == 'ip':
            if not acl_type:
                raise ValueError("acl_type is required param for ip ACL")
            config = 'ip access-list ' + acl_type + ' ' + acl_name
        elif address_type == 'ipv6':
            config = 'ipv6 access-list ' + acl_name
        else:
            raise ValueError("Address Type: {} not supported".format(
                             address_type))

        output = self._callback([config], handler='cli-set')
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def delete_acl(self, **parameters):
        """
        Delete Access Control List.
        Args:
            parameters contains:
                acl_name (str): Name of the access list.
        Returns:
            Return value of `string` message.
        Raise:
            Raises ValueError, Exception
            >>> from pyswitch.device import Device
            >>> conn=('10.37.73.148', 22)
            >>> auth=('admin', 'admin')
            >>> with Device(conn=conn, auth=auth,
            ...             connection_type='NETCONF') as dev:
            ...     print dev.firmware_version
            ...     print dev.os_type
            ...     print dev.acl.create_acl(acl_name='Acl_1',
            ...                              acl_type='standard',
            ...                              address_type='mac')
            ...     print dev.acl.delete_acl(acl_name='Acl_1')
        """
        params_validator.validate_params_mlx_delete_acl(**parameters)

        acl_name = parameters['acl_name']

        ret = self.get_acl_address_and_acl_type(acl_name)
        acl_type = ret['type']
        address_type = ret['protocol']

        if address_type == 'mac':
            cmd = acl_template.delete_acl_template
            t = jinja2.Template(cmd)
            config = t.render(acl_name_str=acl_name)
        elif address_type == 'ip':
            config = 'no ip access-list ' + acl_type + ' ' + acl_name
        elif address_type == 'ipv6':
            config = 'no ipv6 access-list ' + acl_name
        else:
            raise ValueError("Address Type: {} not supported".format(
                             address_type))

        output = self._callback([config], handler='cli-set')
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def add_l2_acl_rule(self, **parameters):
        """
        Delete Access Control List.
        Args:
            parameters contains:
                acl_name: Name of the access list.
                seq_id: Sequence number of the rule. For add operation,
                    if not specified, the rule is added at the end of the list.
                action: Action apply on the traffic, either to deny or permit.
                source: Source filter, can be 'any' or the actual MAC in
                    HHHH.HHHH.HHHH format.
                src_mac_addr_mask: Mask for the source HHHH.HHHH.HHHH format.
                dst: Destination filter, can be 'any' or the actual MAC in
                        HHHH.HHHH.HHHH format.
                dst_mac_addr_mask: Mask for the dst in HHHH.HHHH.HHHH format.
                vlan: VLAN IDs - 'any' or 1-4096
                ethertype: EtherType, can be 'arp', 'fcoe', 'ipv4-15', 'ipv6'
                    or custom value between 1536 and 65535.
                arp_guard: Enables arp-guard for the rule
                drop_precedence_force: Matches the specified value against the
                    drop_precedence_force value of the packet to filter.
                    Allowed values are 0 through 3.
                log: Enables the logging
                mirror: Enables mirror for the rule
                drop_precedence: Matches the specified value against the
                    drop_precedence value of the packet to filter.
                    Allowed values are 0 through 3.
                priority: Matches the specified value against the priority
                    value of the packet to filter.
                    Allowed values are 0 through 7.
                priority_force: Matches the specified value against the
                    priority_force value of the packet to filter.
                    Allowed values are 0 through 7.
               priority_mapping: Matches the specified value against the
                    priority_mapping value of the packet to filter.
                    Allowed values are 0 through 7.
        Returns:
            Return value of `string` message.
        Raise:
            Raises ValueError, Exception
        Examples:
            >>> from pyswitch.device import Device
            >>> conn=('10.37.73.148', 22)
            >>> auth=('admin', 'admin')
            >>> with Device(conn=conn, auth=auth,
            ...             connection_type='NETCONF') as dev:
            ...     print dev.firmware_version
            ...     print dev.os_type
            ...     print dev.acl.create_acl(acl_name='Acl_1',
            ...                              acl_type='extended',
            ...                              address_type='mac')
            ...     print dev.acl.add_l2_acl_rule(acl_name='Acl_1',
            ...                                   action='permit',
            ...                                   source='any',
            ...                                   dst='any',
            ...                                   vlan=10)
        """
        params_validator.\
            validate_params_mlx_add_or_remove_l2_acl_rule(**parameters)

        cli_arr = []
        user_data = self.parse_params_for_add_l2_acl_rule(**parameters)

        cmd = acl_template.create_acl_template
        t = jinja2.Template(cmd)
        config = t.render(acl_name_str=user_data['acl_name_str'])
        cli_arr.append(config)

        cmd = acl_template.add_l2_acl_rule_template
        t = jinja2.Template(cmd)
        config = t.render(**user_data)

        config = re.sub(r'[^a-zA-Z0-9 .-]', r'', config)
        config = ' '.join(config.split())

        cli_arr.append(config)
        output = self._callback(cli_arr, handler='cli-set')
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def delete_l2_acl_rule(self, **parameters):
        """
        Delete Rule from Access Control List.
        Args:
            parameters contains:
                acl_name: Name of the access list.
                seq_id: Sequence number of the rule. For add operation,
                    if not specified, the rule is added at the end of the list.
        Returns:
            Return value of `string` message.
        Raise:
            Raises ValueError, Exception
        Examples:
            >>> from pyswitch.device import Device
            >>> conn=('10.37.73.148', 22)
            >>> auth=('admin', 'admin')
            >>> with Device(conn=conn, auth=auth,
            ...             connection_type='NETCONF') as dev:
            ...     print dev.firmware_version
            ...     print dev.os_type
            ...     print dev.acl.create_acl(acl_name='Acl_1',
            ...                              acl_type='extended',
            ...                              address_type='mac')
            ...     print dev.acl.add_l2_acl_rule(acl_name='Acl_1',
            ...                                   action='permit',
            ...                                   source='any',
            ...                                   dst='any',
            ...                                   vlan=10)
            ...     print dev.acl.delete_l2_acl_rule(acl_name='Acl_1',
            ...                                   vlan=10)
        """

        if 'seq_id' not in parameters or not parameters['seq_id']:
            raise ValueError("missing required parameters: ['seq_id']")

        if 'acl_name' not in parameters or not parameters['acl_name']:
            raise ValueError("missing required parameters: ['acl_name']")

        acl_name = self.mac.parse_acl_name(**parameters)
        seq_id = parameters['seq_id']

        self.is_valid_seq_id(seq_id, acl_name)

        cli_arr = []

        cmd = acl_template.create_acl_template
        t = jinja2.Template(cmd)
        config = t.render(acl_name_str=acl_name)
        config = ' '.join(config.split())
        cli_arr.append(config)

        cmd = acl_template.delete_rule_by_seq_id
        t = jinja2.Template(cmd)
        config = t.render(seq_id_str=parameters['seq_id'])
        config = re.sub(r'[^a-zA-Z0-9 .-]', r'', config)
        config = ' '.join(config.split())
        cli_arr.append(config)

        output = self._callback(cli_arr, handler='cli-set')
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def parse_params_for_add_l2_acl_rule(self, **parameters):
        """
        Parses params for l2 Rule to be added to Access Control List.
        Args:
            Parse below params if contained in parameters.
                action:
                source:
                dst:
                vlan:
                ethertype:
                arp_guard:
                drop_precedence:
                drop_precedence_force:
                log:
                mirror:
                priority:
                priority_force:
                priority_mapping:

        Returns:
            Return a dict cotaining the parameters in string format
            key name will be key name in the parameter followed by _str.
        Raise:
            Raises ValueError, Exception
        Examples:
        """
        user_data = {}
        user_data['acl_name_str'] = self.mac.parse_acl_name(**parameters)
        user_data['seq_id_str'] = self.mac.parse_seq_id(**parameters)
        user_data['action_str'] = self.mac.parse_action(**parameters)
        user_data['source_str'] = self.mac.parse_source(**parameters)
        user_data['dst_str'] = self.mac.parse_dst(**parameters)
        user_data['vlan_str'] = self.mac.parse_vlan(**parameters)
        user_data['ethertype_str'] = self.mac.parse_ethertype(**parameters)
        user_data['arp_guard_str'] = self.mac.parse_arp_guard(**parameters)
        user_data['drop_precedence_str'] = \
            self.mac.parse_drop_precedence(**parameters)
        user_data['drop_precedence_force_str'] = \
            self.mac.parse_drop_precedence_force(**parameters)
        user_data['log_str'] = self.mac.parse_log(**parameters)
        user_data['mirror_str'] = self.mac.parse_mirror(**parameters)
        user_data['priority_str'] = self.mac.parse_priority(**parameters)
        user_data['priority_force_str'] = \
            self.mac.parse_priority_force(**parameters)
        user_data['priority_mapping_str'] = \
            self.mac.parse_priority_mapping(**parameters)

        parameters['user_data'] = user_data
        return user_data

    def is_valid_seq_id(self, seq_id, acl_name):
        """
        is_valid_seq_id checks for existane of seq_id.
        Args:
            acl_name (str): Name of the access list.
            seq_id, action, source, srchost,
        Returns:
            Return True
        Raises:
            Exception, ValueError for invalid seq_id.
        Examples:
        """
        if not acl_name:
            raise ValueError('Acl Name is manadatory parameter')

        if not seq_id:
            raise ValueError('Sequence Id is manadatory parameter')

        address_type = self.get_address_type(acl_name)
        cmd = ''

        if address_type == 'mac':
            cmd = acl_template.show_l2_access_list
        elif address_type == 'ip':
            cmd = acl_template.show_ip_access_list
        elif address_type == 'ipv6':
            cmd = acl_template.show_ipv6_access_list
        else:
            raise ValueError('{} not supported'.format(address_type))

        t = jinja2.Template(cmd)
        config = t.render(acl_name_str=acl_name)
        config = ' '.join(config.split())

        output = self._callback(config, handler='cli-get')

        # Check if there is any error
        self._process_cli_output(inspect.stack()[0][3], config, output)

        # Now check if seq id exists
        for line in output.split('\n'):
            if not line:
                continue

            line_seq_id = line.split(':')[0]
            line_seq_id = ' '.join(line_seq_id.split())
            if not line_seq_id.isdigit():
                continue

            if int(line_seq_id) == seq_id:
                return True

        raise ValueError('{} not exists for acl {}'.format(seq_id, acl_name))

    def apply_acl(self, **parameters):
        """
        Apply Access Control List on interface.
        Args:
            parameters contains:
                acl_name: Name of the access list.
                intf_type: - ethernet, ve
                intf_name: array of interfaces
                acl_direction: Direction of ACL binding on the specified
                    interface
        Returns:
            Return True
        Raises:
            Exception, ValueError for invalid seq_id.
        """
        params_validator.validate_params_mlx_apply_acl(**parameters)

        acl_name = parameters['acl_name']
        intf_type = parameters['intf_type']
        intf_name = parameters.pop('intf_name', None)

        if not intf_name:
            raise ValueError('No Interface specified')

        address_type = self.get_address_type(acl_name)

        if address_type not in ['mac', 'ip', 'ipv6']:
            raise ValueError('{} not supported'.format(address_type))

        if address_type == 'mac':
            if intf_type != 'ethernet':
                raise ValueError('intf type:{} not supported'
                                 .format(intf_type))

        if intf_type == 'port_channel':
            raise ValueError("MLX does not allow ACL configuration on "
                             " port channel interface. Configure ACL on "
                             " ports part of port channel")

        # This iteration will validate that interface exists
        # It will also validate for interfaces part of lag
        for intf in intf_name:
            cmd = acl_template.interface_submode_template
            t = jinja2.Template(cmd)
            config = t.render(intf_name=intf, **parameters)
            config = ' '.join(config.split())
            output = self._callback([config], handler='cli-set')
            self._process_cli_output(inspect.stack()[0][3], config, output)

        for intf in intf_name:
            cli_arr = []

            cmd = acl_template.interface_submode_template
            t = jinja2.Template(cmd)
            config = t.render(intf_name=intf, **parameters)
            config = ' '.join(config.split())
            cli_arr.append(config)

            cmd = acl_template.apply_acl_template
            t = jinja2.Template(cmd)
            config = t.render(address_type=address_type, **parameters)
            config = ' '.join(config.split())
            cli_arr.append(config)

            cli_arr.append('exit')

            output = self._callback(cli_arr, handler='cli-set')
            if 'Error: ' in output and acl_name in output:
                self.logger.info('{} pre-existing on intf {}'
                         .format(acl_name, intf))
                continue
            self._process_cli_output(inspect.stack()[0][3], config, output)

        return 'apply_acl: Successful'

    def remove_acl(self, **parameters):
        """
        Remove Access Control List from interface.
        Args:
            parameters contains:
                acl_name: Name of the access list.
                intf_type: - ethernet, ve
                intf_name: array of interfaces
                acl_direction: Direction of ACL binding on the specified
                    interface
        Returns:
            Return True
        Raises:
            Exception, ValueError for invalid seq_id.
        """
        params_validator.validate_params_mlx_remove_acl(**parameters)

        cli_arr = []
        acl_name = parameters['acl_name']
        intf_type = parameters['intf_type']
        intf_name = parameters.pop('intf_name', None)

        if not intf_name:
            raise ValueError('No Interface specified')

        address_type = self.get_address_type(acl_name)

        if address_type not in ['mac', 'ip', 'ipv6']:
            raise ValueError('{} not supported'.format(address_type))

        if address_type == 'mac':
            if intf_type != 'ethernet':
                raise ValueError('intf type:{} not supported'
                                 .format(intf_type))

        if intf_type == 'port_channel':
            raise ValueError("MLX does not allow ACL configuration on "
                             " port channel interface. Configure ACL on "
                             " ports part of port channel")

        # This iteration will validate that interface exists
        # It will also validate for interfaces part of lag
        for intf in intf_name:
            cmd = acl_template.interface_submode_template
            t = jinja2.Template(cmd)
            config = t.render(intf_name=intf, **parameters)
            config = ' '.join(config.split())
            output = self._callback([config], handler='cli-set')
            self._process_cli_output(inspect.stack()[0][3], config, output)

        for intf in intf_name:
            cmd = acl_template.interface_submode_template
            t = jinja2.Template(cmd)
            config = t.render(intf_name=intf, **parameters)
            config = ' '.join(config.split())
            cli_arr.append(config)

            cmd = acl_template.remove_acl_template
            t = jinja2.Template(cmd)
            config = t.render(address_type=address_type, **parameters)
            config = ' '.join(config.split())
            cli_arr.append(config)

            cli_arr.append('exit')

        output = self._callback(cli_arr, handler='cli-set')
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def add_ipv4_rule_acl(self, **parameters):
        """
        Add rules to Access Control List of ipv4.
        Args:
            parameters contains:
                acl_name: (string) Name of the access list
                seq_id: (integer) Sequence number of the rule,
                    if not specified, the rule is added at the end of the list.
                    Valid range is 0 to 4294967290
                action: (string) Action performed by ACL rule
                    - permit
                    - deny
                protocol_type: (string) Type of IP packets to be filtered
                    based on protocol. Valid values are <0-255> or key words
                    tcp, udp, icmp or ip
                source: (string) Source address filters
                    { any | S_IPaddress/mask(0.0.0.255) |
                    host,S_IPaddress } [ source-operator [ S_port-numbers ] ]
                destination: (string) Destination address filters
                    { any | S_IPaddress/mask(0.0.0.255) |
                    host,S_IPaddress } [ source-operator [ S_port-numbers ] ]
                dscp: (string) Matches the specified value against the DSCP
                    value of the packet to filter.
                     Allowed values are 0 through 63.
                drop_precedence_force: (string) Matches the drop_precedence
                    value of the packet.  Allowed values are 0 through 2.
                urg: (string) Enables urg for the rule
                ack: (string) Enables ack for the rule
                push: (string) Enables push for the rule
                fin: (string) Enables fin for the rule
                rst: (string) Enables rst for the rule
                sync: (string) Enables sync for the rule
                vlan_id: (integer) VLAN interface to which the ACL is bound
                count: (string) Enables statistics for the rule
                log: (string) Enables logging for the rule
                    (Available for permit or deny only)
                mirror: (string) Enables mirror for the rule
                copy_sflow: (string) Enables copy-sflow for the rule

                dscp-marking: (string) dscp-marking number is used to mark the
                    DSCP value in the incoming packet with the value you
                    specify to filter.  Allowed values are 0 through 63.
                fragment: (string) Use fragment keyword to allow the ACL to
                    filter fragmented packets. Use the non-fragment keyword to
                    filter non-fragmented packets.
                    Allowed values are- fragment, non-fragment
                precedence: (integer) Match packets with given precedence value
                    Allowed value in range 0 to 7.
                option: (string) Match match IP option packets.
                    supported values are:
                        any, eol, extended-security, ignore, loose-source-route
                        no-op, record-route, router-alert, security, streamid,
                        strict-source-route, timestamp
                        Allowed value in decimal <0-255>.
                suppress-rpf-drop: (boolean) Permit packets that fail RPF check
                priority: (integer) set priority
                priority-force: (integer) force packet outgoing priority.
                priority-mapping: (integer) map incoming packet priority.
                tos: (integer) Match packets with given TOS value.
                    Allowed value in decimal <0-15>.
        Returns:
            Return True
        Raises:
            Exception, ValueError for invalid seq_id.
            >>> from pyswitch.device import Device
            >>> conn=('10.37.73.148', 22)
            >>> auth=('admin', 'admin')
            >>> with Device(conn=conn, auth=auth,
            ...             connection_type='NETCONF') as dev:
            ...     print dev.firmware_version
            ...     print dev.os_type
            ...     print dev.acl.create_acl(acl_name='Acl_1',
            ...                              acl_type='standard',
            ...                              address_type='ip')
            ...     print dev.acl.add_ipv4_rule_acl(acl_name='Acl_1',
            ...                                   action='permit',
            ...                                   source='any',
            ...                                   dst='any',
            ...                                   vlan=10)
        """
        params_validator.validate_params_mlx_add_ipv4_rule_acl(**parameters)

        acl_name = parameters['acl_name']
        ret = self.get_acl_address_and_acl_type(acl_name)
        acl_type = ret['type']
        address_type = ret['protocol']

        if address_type != 'ip':
            raise ValueError('{} not supported'.format(address_type))

        cli_arr = ['ip access-list ' + ' ' + acl_type + ' ' + acl_name]

        if acl_type == 'standard':
            user_data = self.parse_params_for_add_ipv4_standard(**parameters)
            cmd = acl_template.add_ip_standard_acl_rule_template
        elif acl_type == 'extended':
            user_data = self.parse_params_for_add_ipv4_extended(**parameters)
            cmd = acl_template.add_ip_extended_acl_rule_template
        else:
            raise ValueError('{} not supported'.format(acl_type))

        t = jinja2.Template(cmd)
        config = t.render(**user_data)
        config = ' '.join(config.split())
        cli_arr.append(config)

        output = self._callback(cli_arr, handler='cli-set')
        if 'Failed to initialize dns request' in output:
            raise ValueError('ACL DNS: Errno(5) Failed '
                             'to initialize dns request')
        if 'are undefined' in output:
            raise ValueError('Invlaid icmp filter: {}'
                             .format(parameters['icmp_filter']))
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def parse_params_for_add_ipv4_standard(self, **parameters):
        """
        Parses params for l2 Rule to be added to standard Access Control List.
        Args:
            Parse below params if contained in parameters.
                acl_name: (string) Name of the access list
                seq_id: (integer) Sequence number of the rule,
                    if not specified, the rule is added at the end of the list.
                    Valid range is 0 to 4294967290
                action: (string) Action performed by ACL rule
                    - permit
                    - deny
                source: (string) Source address filters
                    { any | S_IPaddress/mask(0.0.0.255) |
                    host,S_IPaddress } [ source-operator [ S_port-numbers ] ]
                vlan_id: (integer) VLAN interface to which the ACL is bound
                log: (string) Enables logging for the rule
                    (Available for permit or deny only)
        Returns:
            Return a dict cotaining the parameters in string format
            key name will be key name in the parameter followed by _str.
        Raise:
            Raises ValueError, Exception
        Examples:
        """
        supported_params = ['acl_name', 'seq_id', 'action', 'source',
                            'vlan_id', 'log']
        self._is_parameter_supported(supported_params, parameters)

        user_data = {}

        user_data['acl_name_str'] = parameters['acl_name']
        user_data['seq_id_str'] = self.ip.parse_seq_id(**parameters)
        user_data['action_str'] = self.ip.parse_action(**parameters)
        user_data['source_str'] = self.ip.parse_source(**parameters)
        user_data['vlan_str'] = self.ip.parse_vlan(**parameters)
        user_data['log_str'] = self.ip.parse_log(**parameters)
        parameters['user_data'] = user_data
        return user_data

    def parse_params_for_add_ipv4_extended(self, **parameters):
        """
        Parses params for l2 Rule to be added to Access Control List.
        Args:
            Parse below params if contained in parameters.
                acl_name: (string) Name of the access list
                seq_id: (integer) Sequence number of the rule,
                    if not specified, the rule is added at the end of the list.
                    Valid range is 0 to 4294967290
                action: (string) Action performed by ACL rule
                    - permit
                    - deny
                protocol_type: (string) Type of IP packets to be filtered
                    based on protocol. Valid values are <0-255> or key words
                    tcp, udp, icmp or ip
                source: (string) Source address filters
                    { any | S_IPaddress/mask(0.0.0.255) |
                    host,S_IPaddress } [ source-operator [ S_port-numbers ] ]
                destination: (string) Destination address filters
                    { any | S_IPaddress/mask(0.0.0.255) |
                    host,S_IPaddress } [ source-operator [ S_port-numbers ] ]
                dscp: (string) Matches the specified value against the DSCP
                    value of the packet to filter.
                     Allowed values are 0 through 63.
                drop_precedence_force: (string) Matches the drop_precedence
                    value of the packet.  Allowed values are 0 through 2.
                urg: (string) Enables urg for the rule
                ack: (string) Enables ack for the rule
                push: (string) Enables push for the rule
                fin: (string) Enables fin for the rule
                rst: (string) Enables rst for the rule
                sync: (string) Enables sync for the rule
                vlan_id: (integer) VLAN interface to which the ACL is bound
                count: (string) Enables statistics for the rule
                log: (string) Enables logging for the rule
                    (Available for permit or deny only)
                mirror: (string) Enables mirror for the rule
                copy_sflow: (string) Enables copy-sflow for the rule

                dscp-marking: (string) dscp-marking number is used to mark the
                    DSCP value in the incoming packet with the value you
                    specify to filter.  Allowed values are 0 through 63.
                fragment: (string) Use fragment keyword to allow the ACL to
                    filter fragmented packets. Use the non-fragment keyword to
                    filter non-fragmented packets.
                    Allowed values are- fragment, non-fragment
                precedence: (integer) Match packets with given precedence value
                    Allowed value in range 0 to 7.
                option: (string) Match match IP option packets.
                    supported values are:
                        any, eol, extended-security, ignore, loose-source-route
                        no-op, record-route, router-alert, security, streamid,
                        strict-source-route, timestamp
                        Allowed value in decimal <0-255>.
                suppress-rpf-drop: (boolean) Permit packets that fail RPF check
                priority: (integer) set priority
                priority-force: (integer) force packet outgoing priority.
                priority-mapping: (integer) map incoming packet priority.
                tos: (integer) Match packets with given TOS value.
                    Allowed value in decimal <0-15>.


        Returns:
            Return a dict cotaining the parameters in string format
            key name will be key name in the parameter followed by _str.
        Raise:
            Raises ValueError, Exception
        Examples:
        """
        user_data = {}
        user_data['acl_name_str'] = parameters['acl_name']
        user_data['seq_id_str'] = self.ip.parse_seq_id(**parameters)
        user_data['action_str'] = self.ip.parse_action(**parameters)
        user_data['vlan_str'] = self.ip.parse_vlan(**parameters)
        user_data['protocol_str'] = self.ip.parse_protocol(**parameters)
        user_data['source_str'] = self.ip.parse_source(**parameters)
        user_data['dst_str'] = self.ip.parse_destination(**parameters)
        user_data['copy_sflow'] = self.ip.parse_copy_sflow(**parameters)
        user_data['established_str'] = self.ip.parse_established(**parameters)
        user_data['icmp_filter_str'] = \
            self.ip.parse_icmp_filter(**parameters)
        user_data['dscp_mapping_str'] = \
            self.ip.parse_dscp_mapping(**parameters)
        user_data['dscp_marking_str'] = \
            self.ip.parse_dscp_marking(**parameters)
        user_data['fragment_str'] = self.ip.parse_fragment(**parameters)
        user_data['precedence_str'] = self.ip.parse_precedence(**parameters)
        user_data['option_str'] = self.ip.parse_option(**parameters)
        user_data['suppress_rpf_drop_str'] = \
            self.ip.parse_suppress_rpf_drop(**parameters)
        user_data['priority_str'] = self.ip.parse_priority(**parameters)
        user_data['priority_force_str'] = \
            self.ip.parse_priority_force(**parameters)
        user_data['priority_mapping_str'] = \
            self.ip.parse_priority_mapping(**parameters)
        user_data['tos_str'] = self.ip.parse_tos(**parameters)
        user_data['drop_precedence_str'] = \
            self.ip.parse_drop_precedence(**parameters)
        user_data['drop_precedence_force_str'] = \
            self.ip.parse_drop_precedence_force(**parameters)
        user_data['log_str'] = self.ip.parse_log(**parameters)
        user_data['mirror_str'] = self.ip.parse_mirror(**parameters)

        return user_data

    def delete_ipv4_acl_rule(self, **parameters):
        """
        Delete Rule from Access Control List.
        Args:
            parameters contains:
                acl_name: Name of the access list.
                seq_id: Sequence number of the rule. For add operation,
                    if not specified, the rule is added at the end of the list.
        Returns:
            Return value of `string` message.
        Raise:
            Raises ValueError, Exception
        Examples:
            >>> from pyswitch.device import Device
            >>> conn=('10.37.73.148', 22)
            >>> auth=('admin', 'admin')
            >>> with Device(conn=conn, auth=auth,
            ...             connection_type='NETCONF') as dev:
            ...     print dev.firmware_version
            ...     print dev.os_type
            ...     print dev.acl.create_acl(acl_name='Acl_1',
            ...                              acl_type='extended',
            ...                              address_type='mac')
            ...     print dev.acl.add_ipv4_rule_acl(acl_name='Acl_1',
            ...                                   action='permit',
            ...                                   source='any',
            ...                                   dst='any',
            ...                                   vlan=10)
            ...     print dev.acl.delete_ipv4_acl_rule(acl_name='Acl_1',
            ...                                   seq_id=10)
        """
        params_validator.validate_params_mlx_delete_ipv4_rule_acl(**parameters)

        acl_name = parameters['acl_name']
        seq_id = parameters['seq_id']
        acl_type = self.get_acl_type(acl_name)
        self.is_valid_seq_id(seq_id, acl_name)

        cli_arr = ['ip access-list ' + ' ' + acl_type + ' ' + acl_name]

        cmd = acl_template.delete_rule_by_seq_id
        t = jinja2.Template(cmd)
        config = t.render(seq_id_str=parameters['seq_id'])
        config = re.sub(r'[^a-zA-Z0-9 .-]', r'', config)
        config = ' '.join(config.split())
        cli_arr.append(config)

        output = self._callback(cli_arr, handler='cli-set')
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def add_ipv6_rule_acl(self, **parameters):
        """
        Add rules to Access Control List of ipv6.
        Args:
            parameters contains:
                acl_name(string): Name of the access list
                seq_id(integer): Sequence number of the rule,
                    if not specified, the rule is added
                    at the end of the list. Valid range is 0 to 4294967290
                action(string): Action performed by ACL rule
                    - permit (default)
                    - deny
                protocol_type(string): Type of IP packets to be filtered based
                    on protocol. Valid values are 0 through 255 or key words
                    ahp, esp, icmp, ipv6, sctp, tcp, udp
                source(string): Source address filters
                    { any | S_IPaddress mask | host S_IPaddress }
                        [ source-operator [ S_port-numbers ] ]
                destination(string):Destination address filters
                    { any | S_IPaddress mask | host S_IPaddress }
                        [ source-operator [ S_port-numbers ] ]
                dscp(string): Matches the specified value against the DSCP
                    value of the packet to filter.
                    Can be either a numerical value or DSCP name
                drop_precedence_force(string): Matches the drop_precedence
                    value of the packet.  Allowed values are 0 through 2.
                urg(string): Enables urg for the rule
                ack(string): Enables ack for the rule
                push(string): Enables push for the rule
                fin(string): Enables fin for the rule
                rst(string): Enables rst for the rule
                sync(string): Enables sync for the rule
                vlan_id:(integer): VLAN interface to which the ACL is bound
                count(string): Enables statistics for the rule
                log(string): Enables logging for the rule
                mirror(string): Enables mirror for the rule
                copy_sflow(string): Enables copy-sflow for the rule
        Returns:
            Return True
        Raises:
            Exception, ValueError for invalid seq_id.
        """
        params_validator.validate_params_mlx_add_ipv6_rule_acl(**parameters)

        acl_name = parameters['acl_name']
        ret = self.get_acl_address_and_acl_type(acl_name)
        address_type = ret['protocol']

        if address_type != 'ipv6':
            raise ValueError('{} not supported'.format(address_type))

        cli_arr = ['ipv6 access-list ' + ' ' + acl_name]

        user_data = self.parse_params_for_add_ipv6_extended(**parameters)
        cmd = acl_template.add_ipv6_standard_acl_rule_template

        t = jinja2.Template(cmd)
        config = t.render(**user_data)
        config = ' '.join(config.split())
        cli_arr.append(config)

        output = self._callback(cli_arr, handler='cli-set')
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def parse_params_for_add_ipv6_extended(self, **parameters):
        """
        Parase parameters passed to add_ipv6_rule_acl method.
        Args:
            parameters contains:
                all parameters passed to add_ipv6_rule_acl
        Returns:
            Return a dict cotaining the parameters in string format
            key name will be key name in the parameter followed by _str.
        Raise:
            Raises ValueError, Exception
        """
        user_data = {}
        user_data['acl_name_str'] = parameters['acl_name']
        user_data['seq_id_str'] = self.ipv6.parse_seq_id(**parameters)
        user_data['action_str'] = self.ipv6.parse_action(**parameters)
        user_data['vlan_str'] = self.ipv6.parse_vlan(**parameters)
        user_data['protocol_str'] = self.ipv6.parse_protocol(**parameters)
        user_data['source_str'] = self.ipv6.parse_source(**parameters)
        user_data['dst_str'] = self.ipv6.parse_destination(**parameters)
        user_data['dscp_mapping_str'] = \
            self.ipv6.parse_dscp_mapping(**parameters)
        user_data['fragment_str'] = self.ipv6.parse_fragment(**parameters)
        user_data['tcp_operator_str'] = \
            self.ipv6.parse_tcp_operator(**parameters)
        user_data['icmp_filter_str'] = \
            self.ipv6.parse_icmp_filter(**parameters)
        user_data['copy_sflow_str'] = self.ipv6.parse_copy_sflow(**parameters)
        user_data['drop_precedence_str'] = \
            self.ipv6.parse_drop_precedence(**parameters)
        user_data['drop_precedence_force_str'] = \
            self.ipv6.parse_drop_precedence_force(**parameters)
        user_data['dscp_marking_str'] = \
            self.ipv6.parse_dscp_marking(**parameters)
        user_data['priority_force_str'] = \
            self.ipv6.parse_priority_force(**parameters)
        user_data['priority_mapping_str'] = \
            self.ipv6.parse_priority_mapping(**parameters)
        user_data['suppress_rpf_drop_str'] = \
            self.ipv6.parse_suppress_rpf_drop(**parameters)
        user_data['mirror_str'] = self.ipv6.parse_mirror(**parameters)
        user_data['log_str'] = self.ipv6.parse_log(**parameters)
        return user_data

    def delete_ipv6_acl_rule(self, **parameters):
        """
        Delete Rule from Access Control List.
        Args:
            parameters contains:
                acl_name: Name of the access list.
                seq_id: Sequence number of the rule. For add operation,
                    if not specified, the rule is added at the end of the list.
        Returns:
            Return value of `string` message.
        Raise:
            Raises ValueError, Exception
        Examples:
            >>> from pyswitch.device import Device
            >>> conn=('10.37.73.148', 22)
            >>> auth=('admin', 'admin')
            >>> with Device(conn=conn, auth=auth,
            ...             connection_type='NETCONF') as dev:
            ...     print dev.firmware_version
            ...     print dev.os_type
            ...     print dev.acl.create_acl(acl_name='Acl_1',
            ...                              acl_type='extended',
            ...                              address_type='ipv6')
            ...     print dev.acl.add_ipv6_rule_acl(acl_name='Acl_1',
            ...                                   action='permit',
            ...                                   source='any',
            ...                                   dst='any',
            ...                                   vlan=10)
            ...     print dev.acl.delete_ipv6_acl_rule(acl_name='Acl_1',
            ...                                   seq_id=10)
        """
        params_validator.validate_params_mlx_delete_ipv6_rule_acl(**parameters)

        acl_name = parameters['acl_name']
        seq_id = parameters['seq_id']
        self.is_valid_seq_id(seq_id, acl_name)

        cli_arr = ['ipv6 access-list ' + ' ' + acl_name]

        cmd = acl_template.delete_rule_by_seq_id
        t = jinja2.Template(cmd)
        config = t.render(seq_id_str=parameters['seq_id'])
        config = re.sub(r'[^a-zA-Z0-9 .-]', r'', config)
        config = ' '.join(config.split())
        cli_arr.append(config)

        output = self._callback(cli_arr, handler='cli-set')
        return self._process_cli_output(inspect.stack()[0][3], config, output)

    def get_address_type(self, acl_name):
        """
        get_address_type determines address type for the provided acl_name

        Args:
            acl_name (str): Name of the access list.
        Returns:
            Returns a string containing address type.
        Raises:
            Exception, ValueError
        Examples:
        """
        ret = self.get_acl_address_and_acl_type(acl_name)
        return ret['protocol']

    def get_acl_type(self, acl_name):
        """
        get_acl_type determines acl type for the provided acl_name

        Args:
            acl_name (str): Name of the access list.
        Returns:
            Returns a string containing acl type.
        Raises:
            Exception, ValueError
        Examples:
        """

        ret = self.get_acl_address_and_acl_type(acl_name)
        return ret['type']

    def get_acl_address_and_acl_type(self, acl_name):
        """
        get_acl_address_and_acl_type determines acl type and address
        type for the provided acl_name

        Args:
            acl_name (str): Name of the access list.
        Returns:
            Return a dict
            {'type':'standard'/'extended;, 'protocol':'mac'/'ip'/'ipv6'}.
        Raises:
            Exception, ValueError
        Examples:
        """

        ret = {'type': '', 'protocol': ''}
        res = self._callback('show access-list all',
                             handler='cli-get').split('\n')
        res += self._callback('show ipv6 access-list',
                              handler='cli-get').split('\n')

        for line in res:
            if acl_name in line:
                if line[0:4] == 'mac ':
                    ret['protocol'] = 'mac'
                    ret['type'] = 'extended'
                elif line[0:3] == 'ip ':
                    ret['protocol'] = 'ip'
                    if 'extended' in line:
                        ret['type'] = 'extended'
                    else:
                        ret['type'] = 'standard'
                elif line[0:5] == 'ipv6 ':
                    ret['protocol'] = 'ipv6'
                    ret['type'] = 'standard'
                break

        if ret['protocol'] != '':
            return ret

        raise ValueError("Failed to identify acl_type."
                         " Check if the ACL {} exists".format(acl_name))
