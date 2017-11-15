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

import socket


class IpAcl(object):
    """
    The IpAcl class holds all the functions assocaiated with
    IP Access Control list.
    Attributes:
        None
    """

    def parse_action(self, **parameters):
        """
        parse supported actions by MLX platform
        Args:
            parameters contains:
                action (string): Allowed actions are 'permit' and 'deny'
        Returns:
            Return parsed string on success
        Raise:
            Raise ValueError exception
        Examples:

        """
        if 'action' not in parameters or not parameters['action']:
            raise ValueError("\'action\' not present in parameters arg")

        action = parameters['action']

        if parameters['action'] in ['permit', 'deny']:
            return parameters['action']

        raise ValueError("The \'action\' value {} is invalid. Specify "
                         "\'deny\' or \'permit\' supported "
                         "values".format(action))

    def _validate_op_str(self, op_str):
        op_str = ' '.join(op_str.split()).split()

        if len(op_str) == 2:
            if (op_str[0] == 'neq' or op_str[0] == 'lt' or
                op_str[0] == 'gt' or op_str[0] == 'eq') and \
                    op_str[1].isdigit():
                return True
        elif len(op_str) == 3 and op_str[0] == 'range':
            return True

        raise ValueError('Invalid tcp-udp-operator: ' + ' '.join(op_str))

    def _validate_ipv4(self, addr):
        addr = ' '.join(addr.split())
        try:
            socket.inet_aton(addr)
        except socket.error:
            raise ValueError('Invalid address: ' + addr)

    def _parse_source_destination(self, protocol_type, input_param):

        v4_str = input_param
        op_str = ''
        op_index = -1
        for tcp_udp_op in ['range', 'neq', 'lt', 'gt', 'eq']:
            op_index = input_param.find(tcp_udp_op)
            if op_index >= 0:
                op_str = input_param[op_index:]
                v4_str = input_param[0:op_index]
                break

        if protocol_type not in ['tcp', 'udp'] and op_str:
            raise ValueError("tcp udp operator is supported only for."
                             "protocol_type = tcp or udp")

        if op_str:
            self._validate_op_str(op_str)

        if v4_str[0:3] == "any":
            return v4_str + ' ' + op_str

        if v4_str[0:4] == "host":
            try:
                self._validate_ipv4(v4_str[5:])
            except:
                # Ignore exception
                # This may be a host string.
                pass
            return v4_str + ' ' + op_str

        if '/' in v4_str:
            ip, prefix_len = v4_str.split('/')
            self._validate_ipv4(ip)

            if not prefix_len.isdigit():
                raise ValueError('Invalid address: ' + v4_str)

            if int(prefix_len) < 0 and int(prefix_len) > 32:
                raise ValueError('Invalid address: ' + v4_str)

            return v4_str + ' ' + op_str

        ip, mask = v4_str.split()
        self._validate_ipv4(ip)
        self._validate_ipv4(mask)
        return v4_str + ' ' + op_str

    def parse_source(self, **parameters):
        """
        parse the source param.
        Args:
            parameters contains:
                source (string): Source filter, can be 'any' or
                    the MAC/Mask in HHHH.HHHH.HHHH/mask or
                    the host Mask in HHHH.HHHH.HHHH or
                    host <name | ip >
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'source' not in parameters or not parameters['source']:
            raise ValueError("Missing \'source\' in parameters")

        src = parameters['source']
        src = ' '.join(src.split())

        return self._parse_source_destination(parameters['protocol_type'], src)

    def parse_destination(self, **parameters):
        """
        parse the destination param.
        Args:
            parameters contains:
                destination (string): destination filter, can be 'any' or
                    the MAC/Mask in HHHH.HHHH.HHHH/mask or
                    the host Mask in HHHH.HHHH.HHHH or
                    host <name | ip >
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'destination' not in parameters or not parameters['destination']:
            return None

        if 'protocol_type' not in parameters or \
                not parameters['protocol_type']:
            raise ValueError("\'protocol_type\' is required for MLX device")

        dst = parameters['destination']
        dst = ' '.join(dst.split())

        return self._parse_source_destination(parameters['protocol_type'], dst)

    def parse_established(self, **parameters):
        """
        parse the established param
        Args:
            parameters contains:
                established(boolean): true/false
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'established' not in parameters or not parameters['established']:
            return None

        return 'established'

    def parse_vlan(self, **parameters):
        """
        parse the vlan param
        Args:
            parameters contains:
                vlan_id(integer): 1-4096
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'vlan_id' not in parameters:
            return None

        vlan = parameters['vlan_id']

        if not vlan:
            return None

        if vlan > 0 and vlan < 4096:
            return str(vlan)

        raise ValueError("The \'vlan\' value {} is invalid."
                         " Specify \'1-4095\' supported values")

    def parse_log(self, **parameters):
        """
        parse the log param
        Args:
            parameters contains:
                log(string): Enables the logging
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'log' in parameters or not parameters['log']:
            return None

        if 'mirror' in parameters or not parameters['mirror']:
            return 'log'

        raise ValueError("log and mirror keywords can not be used together")

    def parse_protocol(self, **parameters):
        """
        parse the protocol param
        Args:
            parameters contains:
                protocol_type: (string) Type of IP packets to be filtered
                    based on protocol. Valid values are <0-255> or
                    key words tcp, udp, icmp or ip
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'protocol_type' not in parameters:
            return None

        protocol_type = parameters['protocol_type']

        if not protocol_type:
            return None

        if protocol_type.isdigit():
            if int(protocol_type) < 0 or int(protocol_type) > 255:
                raise ValueError("The \'protocol\' value {} is invalid."
                                 " Specify \'0-255\' supported values"
                                 .format(protocol_type))

        if protocol_type not in ['a_n', 'ahp', 'argus', 'aris', 'ax25',
                                 'bbn-rcc', 'bna', 'br-sat-mon', 'cbt',
                                 'cftp', 'chaos', 'compaq-peer', 'cphb',
                                 'cpnx', 'crdup', 'crtp', 'dcn', 'ddp', 'ddx',
                                 'dgp', 'divert', 'egp', 'emcon', 'encap',
                                 'esp', 'etherip', 'fc', 'fire', 'ggp', 'gmtp',
                                 'gre', 'hip', 'hmp', 'i-nlsp', 'iatp', 'icmp',
                                 'idpr', 'idpr-cmtp', 'idrp', 'ifmp', 'igmp',
                                 'igp', 'igrp', 'il', 'ip', 'ipcomp', 'ipcv',
                                 'ipencap', 'ipip', 'iplt', 'ippc', 'ipv6',
                                 'ipv6-frag', 'ipv6-icmp', 'ipv6-nonxt',
                                 'ipv6-opts', 'ipv6-route', 'ipx-in-ip',
                                 'irtp', 'isis', 'iso-ip', 'iso-tp4',
                                 'kryptolan', 'l2tp', 'larp', 'leaf-1',
                                 'leaf-2', 'manet', 'merit-inp', 'mfe-nsp',
                                 'mhrp', 'micp', 'mobile', 'mobility-header',
                                 'mpls-in-ip', 'mtp', 'mux', 'narp', 'netblt',
                                 'nsfnet-igp', 'nvp', 'ospf', 'pgm', 'pim',
                                 'pipe', 'pnni', 'prm', 'ptp', 'pup', 'pvp',
                                 'qnx', 'rdp', 'rsvp', 'rsvp-e2e-ignore',
                                 'rvd', 'sat-expak', 'sat-mon', 'scc-sp',
                                 'scps', 'sctp', 'sdrp', 'secure-vmtp', 'sep',
                                 'shim6', 'skip', 'sm', 'smp', 'snp',
                                 'sprite-rpc', 'sps', 'srp', 'sscopmce', 'st',
                                 'st2', 'sun-nd', 'swipe', 'tcf', 'tcp',
                                 'third-pc', 'tlsp', 'tp++', 'trunk-1',
                                 'trunk-2', 'ttp', 'udp', 'udplite', 'uti',
                                 'vines', 'visa', 'vlan', 'vmtp', 'vrrp',
                                 'wb-expak', 'wb-mon', 'wsn', 'xnet',
                                 'xns-idp', 'xtp']:
            raise ValueError("invalid \'protocol_type\' value {}."
                             .format(protocol_type))

        return str(protocol_type)

    def parse_dscp_mapping(self, **parameters):
        """
        parse the dscp mapping param.
        Args:
            parameters contains:
                dscp: (string) Matches the specified value against the DSCP
                    value of the packet to filter.
                     Allowed values are 0 through 63.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'dscp' not in parameters or not parameters['dscp']:
            return None

        dscp_mapping = parameters['dscp']
        dscp_mapping = ' '.join(dscp_mapping.split())

        if dscp_mapping.isdigit():
            if int(dscp_mapping) >= 0 and int(dscp_mapping) <= 63:
                return 'dscp-mapping ' + dscp_mapping

        raise ValueError("Invalid dscp_mapping {}. Supported range is "
                         "<0-63>".format(dscp_mapping))

    def parse_dscp_marking(self, **parameters):
        """
        parse the dscp mapping param.
        Args:
            parameters contains:
                dscp: (string) Matches the specified value against the DSCP
                    value of the packet to filter.
                     Allowed values are 0 through 63.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'dscp_marking' not in parameters or not parameters['dscp_marking']:
            return None

        dscp_marking = parameters['dscp_marking']
        dscp_marking = ' '.join(dscp_marking.split())

        if dscp_marking.isdigit():
            if int(dscp_marking) >= 0 and int(dscp_marking) <= 63:
                return 'dscp-marking ' + dscp_marking

        raise ValueError("Invalid dscp_marking {}. Supported range is "
                         "<0-63>".format(dscp_marking))

    def parse_fragment(self, **parameters):
        """
        parse the dscp mapping param.
        Args:
            parameters contains:
                dscp: (string) Matches the specified value against the DSCP
                    value of the packet to filter.
                     Allowed values are 0 through 63.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'fragment' not in parameters or not parameters['fragment']:
            return None

        fragment = parameters['fragment']
        fragment = ' '.join(fragment.split())

        if fragment in ['fragment', 'non-fragment']:
            return fragment

        raise ValueError("Invalid fragment {}. Supported values are "
                         "fragment or non-fragment".format(fragment))

    def parse_precedence(self, **parameters):
        """
        parse the precedence mapping param.
        Args:
            parameters contains:
                precedence:
                  type: string
                  description: Match packets with given precedence value.
                      Allowed value { <0 to 7> | critical | flash |
                      flash-override | immediate | internet | network |
                      priority | routine  }
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'precedence' not in parameters or not parameters['precedence']:
            return None

        precedence = parameters['precedence']
        precedence = ' '.join(precedence.split())

        if precedence.isdigit():
            if int(precedence) >= 0 and int(precedence) <= 7:
                return 'precedence ' + precedence
        if precedence in ['critical' 'flash', 'flash-override',
                          'immediate', 'internet', 'network',
                          'priority', 'routine']:
                return 'precedence ' + precedence

        raise ValueError("Invalid precedence {}. Supported values are "
                         "<0 to 7> | critical | flash |"
                         "flash-override | immediate | internet | network |"
                         "priority | routine ".format(precedence))

    def _is_tcp_udp_opstr_set(self, protocol_type, input_param):
        for tcp_udp_op in ['range', 'neq', 'lt', 'gt', 'eq']:
            op_index = input_param.find(tcp_udp_op)
            if op_index >= 0:
                raise ValueError('option keyword cannot be used along with TCP'
                                 ' destination port matching')
        return True

    def parse_option(self, **parameters):
        """
        parse the option mapping param.
        Args:
            parameters contains:
                option (string): Match match IP option packets.
                    supported values are -
                        any, eol, extended-security, ignore, loose-source-route
                        no-op, record-route, router-alert, security, streamid,
                        strict-source-route, timestamp
                        Allowed value in decimal <0-255>.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'option' not in parameters or not parameters['option']:
            return None

        if 'protocol_type' in parameters and parameters['protocol_type'] and \
                parameters['protocol_type'] in ['tcp', 'udp']:

            if 'source' in parameters and parameters['source']:
                src = parameters['source']
                src = ' '.join(src.split())
                self._is_tcp_udp_opstr_set(parameters['protocol_type'], src)

            if 'destination' in parameters and parameters['destination']:
                dst = parameters['destination']
                dst = ' '.join(src.split())
                self._is_tcp_udp_opstr_set(parameters['protocol_type'], dst)

        option = parameters['option']
        option = ' '.join(option.split())

        if option.isdigit():
            if int(option) >= 0 and int(option) <= 255:
                return 'option ' + option
        if option in ['any', 'eol', 'extended-security',
                      'ignore', 'loose-source-route',
                      'no-op', 'record-route', 'router-alert',
                      'security', 'streamid',
                      'strict-source-route', 'timestamp']:
                return 'option ' + option

        raise ValueError("Invalid option {}. Supported values are "
                         "any, eol, extended-security, ignore, "
                         "loose-source-route no-op, record-route, "
                         "router-alert, security, streamid, "
                         "strict-source-route, timestamp "
                         "Allowed value in decimal <0-255>."
                         .format(option))

    def parse_suppress_rpf_drop(self, **parameters):
        """
        parse the suppress_rpf_drop mapping param.
        Args:
            parameters contains:
                suppress_rpf_drop (boolean):Permit packets that fail RPF check
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'suppress_rpf_drop' not in parameters or \
                not parameters['suppress_rpf_drop']:
            return None

        return 'suppress-rpf-drop'

    def parse_priority(self, **parameters):
        """
        parse the priority param.
        Args:
            parameters contains:
                priority(integer): set priorityr. Allowed value is <0-7>.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'priority' not in parameters or not parameters['priority']:
            return None

        if 'priority_force' in parameters and parameters['priority_force']:
            raise ValueError('priority and priority-force can not be'
                             ' enabled at the same time!')

        priority = parameters['priority']

        if priority >= 0 and priority <= 7:
            return 'priority ' + str(priority)

        raise ValueError("Invalid priority {}. "
                         "Allowed value in decimal <0-7>."
                         .format(priority))

    def parse_priority_force(self, **parameters):
        """
        parse the priority_force mapping param.
        Args:
            parameters contains:
                priority_force(integer): set priority_forcer.
                    Allowed value is <0-7>.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'priority_force' not in parameters or \
                not parameters['priority_force']:
            return None

        if 'priority' in parameters and parameters['priority']:
            raise ValueError('priority and priority-force can not be'
                             ' enabled at the same time!')

        priority_force = parameters['priority_force']

        if priority_force >= 0 and priority_force <= 7:
            return 'priority-force ' + str(priority_force)

        raise ValueError("Invalid priority_force {}. "
                         "Allowed value in decimal <0-7>."
                         .format(priority_force))

    def parse_priority_mapping(self, **parameters):
        """
        parse the priority_mapping mapping param.
        Args:
            parameters contains:
                priority_mapping(integer): set priority_mappingr.
                    Allowed value is <0-7>.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'priority_mapping' not in parameters or \
                not parameters['priority_mapping']:
            return None

        priority_mapping = parameters['priority_mapping']

        if priority_mapping >= 0 and priority_mapping <= 7:
            return 'priority-mapping ' + str(priority_mapping)

        raise ValueError("Invalid priority_mapping {}. "
                         "Allowed value in decimal <0-7>."
                         .format(priority_mapping))

    def parse_tos(self, **parameters):
        """
        parse the tos mapping param.
        Args:
            parameters contains:
                tos(integer): set tosr. Allowed value is <0-15>.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'tos' not in parameters or not parameters['tos']:
            return None

        tos = parameters['tos']

        if tos >= 0 and tos <= 15:
            return 'tos ' + str(tos)

        raise ValueError("Invalid tos {}. "
                         "Allowed value in decimal <0-15>."
                         .format(tos))

    def parse_mirror(self, **parameters):
        """
        parse the mirror param
        Args:
            parameters contains:
                log(string): Enables the logging
                mirror(string): Enables mirror for the rule.
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'mirror' in parameters or not parameters['mirror']:
            return None

        if 'action' in parameters and parameters['action'] and \
                parameters['action'] != 'permit':
            raise ValueError(" Mirror keyword is applicable only for ACL"
                             " permit clauses")

        if 'log' in parameters or not parameters['log']:
            return 'mirror'

        raise ValueError("log and mirror keywords can not be used together")

    def parse_drop_precedence(self, **parameters):
        """
        parse the drop_precedence mapping param.
        Args:
            parameters contains:
                drop_precedence(string): drop_precedence value of the packet
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'drop_precedence' not in parameters or \
                not parameters['drop_precedence']:
            return None

        if 'drop_precedence_force' in parameters and \
                parameters['drop_precedence_force']:
            raise ValueError('drop-precedence and drop-precedence-force can '
                             'not be enabled at the same time!')

        drop_precedence = parameters['drop_precedence']
        drop_precedence = ' '.join(drop_precedence.split())

        if drop_precedence.isdigit():
            if int(drop_precedence) >= 0 and int(drop_precedence) <= 3:
                return 'drop-precedence ' + drop_precedence

        raise ValueError("drop-precedence value should be 0 - 3")

    def parse_drop_precedence_force(self, **parameters):
        """
        parse the drop_precedence_force mapping param.
        Args:
            parameters contains:
                drop_precedence_force(string):
                    drop_precedence_force value of the packet
        Returns:
            Return None or parsed string on success
        Raise:
            Raise ValueError exception
        Examples:
        """
        if 'drop_precedence_force' not in parameters or \
                not parameters['drop_precedence_force']:
            return None

        if 'drop_precedence' in parameters and \
                parameters['drop_precedence']:
            raise ValueError('drop-precedence and drop-precedence-force can '
                             'not be enabled at the same time!')

        drop_precedence_force = parameters['drop_precedence_force']
        drop_precedence_force = ' '.join(drop_precedence_force.split())

        if drop_precedence_force.isdigit():
            if int(drop_precedence_force) >= 0 and \
                    int(drop_precedence_force) <= 3:
                return 'drop-precedence-force ' + drop_precedence_force

        raise ValueError("drop-precedence-force value should be 0 - 3")