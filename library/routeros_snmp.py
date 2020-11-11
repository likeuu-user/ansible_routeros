#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
'''

EXAMPLES = """
- name: test base module\
    routeros_snmp:
    enabled: True
    contact: aaa@aaa.aaa.aaa
    location: country
    engine_id: test1
    trap_target:
        - 192.168.0.100
    src_address: "{{ hostvars[inventory_hostname]['ansible_ssh_host'] }}"
    trap_community: public
    trap_version: 1
    trap_generators:
        - 'interfaces'
        - 'start-trap'
        - 'temp-exception'
    trap_interfaces:
        - ether4

- name: test base module
    routeros_snmp_community:
    name: test
    status: absent
"""

RETURN = """
"""
import re

from ansible_collections.community.network.plugins.module_utils.network.routeros.routeros import run_commands
from ansible_collections.community.network.plugins.module_utils.network.routeros.routeros import routeros_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types

def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item

def cleaning_output(respons):
    list_result = list()
    list_temp = respons.splitlines()
    for temp in list_temp:
        if temp.find('[') != 0:
            list_result.append(temp)
    if len(list_result) == 0:
        list_result.append('')
    return list_result 

def check_exec_error(respons):
    list_error_message = list()
    list_error_string = [
        'bad command name',
        'no such item',
        'expected end of command',
        'syntax error',
        'invalid value for argument'
    ]
    for temp in respons:
        for error_string in list_error_string:
            if temp.find(error_string) == 0:
                list_error_message.append('ERROR: ' + temp)
    return list_error_message

def get_param(module):
    dict_param = dict()
    list_param = ['contact', 'enabled', 'engine_id', 'location', 'src_address', 'trap_community',
                'trap_generators', 'trap_interfaces', 'trap_target', 'trap_version']
    list_param_conv = ['contact', 'enabled', 'engine-id', 'location', 'src-address', 'trap-community',
                'trap-generators', 'trap-interfaces', 'trap-target', 'trap-version']

    for num in range(len(list_param)):
        if list_param[num] in module.params:
            if type(module.params[list_param[num]]) == bool:
                if module.params[list_param[num]]:
                    dict_param[list_param_conv[num]] = 'yes'
                else:
                    dict_param[list_param_conv[num]] = 'no'
            else:
                dict_param[list_param_conv[num]] = module.params[list_param[num]]

    return dict_param

def parse_output_snmp(list_output):
    dict_snmp = dict()
    list_param = ['contact', 'enabled', 'engine-id', 'location', 'src-address', 'trap-community',
                'trap-generators', 'trap-interfaces', 'trap-target', 'trap-version']
    list_list_param = ['trap-target', 'trap-generators', 'trap-interfaces']

    list_item = list()
    temp = ''
    for output in list_output:
        if re.match(r'Flags:', output.strip()):
            continue
        if re.match(r'\d+\s', output.strip()):
            if temp != '':
                list_item.append(temp)
                temp = ''
            mo = re.search(r'^(\d+)\s', output.strip())
            if mo:
                temp = 'id=' + mo.group(1)
            mo = re.search(r'^\d+\s(.*?)\s[n;]', output.strip())
            if mo:
                if 'X' in mo.group(1):
                    temp = temp + ' disabled=yes'
                else:
                    temp = temp + ' disabled=no'
            mo = re.search(r';;;\s(.*)$', output.strip())
            if mo:
                temp = temp + ' comment=\"' + (mo.group(1)).strip() + '\"'
            mo = re.search(r'^\d.*\s(name=.*)$', output.strip())
            if mo:
                temp = temp + ' ' + mo.group(1)
        elif output.strip() != '':
            temp = temp + ' ' + output.strip()
    if temp != '':
        list_item.append(temp)

    for param in list_param:
        for output in list_output:
            mo = re.search(r'\s' + param + ':\s\"(.*?)\"$', ' ' + output)
            if mo is None:
                mo = re.search(r'\s' + param + ':\s(.*?)$', ' ' + output)
            if mo:
                dict_snmp[param] = mo.group(1)

    for list_param in list_list_param:
        if list_param in dict_snmp:
            if len(dict_snmp[list_param]) > 0:
                dict_snmp[list_param] = dict_snmp[list_param].split(',')
 
    if 'trap-version' in dict_snmp:
        if type(dict_snmp['trap-version']) != int:
            dict_snmp['trap-version'] = int(dict_snmp['trap-version'])

    if 'src-address' not in dict_snmp:
        dict_snmp['src-address'] = ''

    if 'trap-interfaces' not in dict_snmp:
        dict_snmp['trap-interfaces'] = []

    return dict_snmp

def make_command_snmp(dict_param, dict_object):
    command = ''
    list_param = ['contact', 'enabled', 'engine-id', 'location', 'src-address', 'trap-community',
                'trap-generators', 'trap-interfaces', 'trap-target', 'trap-version']

    command_option = ''
    for param in list_param:
        if param in dict_param:
            if type(dict_param[param]) == list:
                if sorted(dict_param[param]) != sorted(dict_object[param]):
                    temp = ''
                    for item in dict_param[param]:
                        temp = temp + ',' + item
                    command_option = command_option + ' ' + param + '=\"' + temp[1:] + '\"'
            elif type(dict_param[param]) == str:
                if dict_param[param] != dict_object[param]:
                    command_option = command_option + ' ' + param + '=\"' + dict_param[param] + '\"'
            elif type(dict_param[param]) == int:
                if dict_param[param] != dict_object[param]:
                    command_option = command_option + ' ' + param + '=' + str(dict_param[param])
            else:
                if dict_param[param] != dict_object[param]:
                    command_option = command_option + ' ' + param + '=' + dict_param[param]

    if command_option.strip() != '':
        # command = '/snmp community set name=\"' + dict_param['name'] + '\"' + command_option 
        command = '/snmp set' + command_option 

    return command

def main():
    """main entry point for module execution
    """
    #### argument spec
    argument_spec = dict(
        enabled=dict(type='bool'),
        contact=dict(type='str'),
        location=dict(type='str'),
        engine_id=dict(type='str'),
        trap_target=dict(type='list', elements='str'),
        trap_community=dict(type='str'),
        trap_version=dict(type='int', choices=[1, 2, 3]),
        trap_generators=dict(type='list', elements='str', choice=('interfaces', 'start-trap', 'temp-exception')),
        trap_interfaces=dict(type='list', elements='str'),
        src_address=dict(type='str')
    )
    # required=True
    # type='list', elements='int'
    # default='xxxx'
    # choices=["present", "absent"]

    argument_spec.update(routeros_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    result = {'changed': False}

    #### initialize
    changed_status = False
    failed_status = False
    list_exec = list()
    list_log = list()
    dict_param = dict()
    dict_object = dict()

    #### get parameter
    dict_param = get_param(module)
  
    #### exec get command
    commands = '/snmp print without-paging'
    responses = run_commands(module, commands)
    list_output = cleaning_output(responses[0])
    list_exec.append({'commands':commands, 'stdout':list_output})

    #### parse output
    dict_object = parse_output_snmp(list_output)

    #### make commad
    set_commands = make_command_snmp(dict_param, dict_object)

    #### check error
    error_messages = check_exec_error(list_output)
    if len(error_messages) > 0:
        msg = error_messages[0]
        module.fail_json(msg=msg, failed_conditions=list_exec)

    #### check mode and not changed
    if module.check_mode:
        list_log.append('INFO: CheckMode = True')
    if module.check_mode or set_commands == '':
        results = list()
        if set_commands != '':
            list_exec.append({'commands':set_commands, 'stdout':''})
        for exec_output in list_exec:
            for output in exec_output['stdout']:
                results.append(output)
        result.update({
            'changed': changed_status,
            'failed': failed_status,
            'parameter': dict_param,
            'object': dict_object,
            'stdout': list_exec,
            'stdout_lines': list(to_lines(results)),
            'log': list_log
        })      
        module.exit_json(**result) 

    #### exec set command
    commands = set_commands
    responses = run_commands(module, commands)
    list_output = cleaning_output(responses[0])
    list_exec.append({'commands':commands, 'stdout':list_output})

    #### check error
    if list_output[0] != '':
        msg = 'ERROR: ' + list_output[0]
        module.fail_json(msg=msg, failed_conditions=list_exec)        
    else:
        changed_status = True

    #### return result
    results = list()
    for exec_output in list_exec:
        for output in exec_output['stdout']:
            results.append(output)
    result.update({
        'changed': changed_status,
        'failed': failed_status,
        'parameter': dict_param,
        'object': dict_object,
        'stdout': list_exec,
        'stdout_lines': list(to_lines(results)),
        'log': list_log
    })

    module.exit_json(**result)

if __name__ == '__main__':
    main()
