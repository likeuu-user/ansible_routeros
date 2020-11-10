#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
'''

EXAMPLES = """
- name: test base module
    routeros_snmp_community:
    name: test
    addresses:
        - 192.168.0.0/24
        - 192.168.1.0/24
    security: none
    read_access: True
    write_access: True
    authentication_protocol: MD5
    encryption_protocol: DES
    authentication_password: auth_password
    encryption_password: enc_password
    disabled: False
    status: present

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
    list_param = ['name', 'addresses', 'security', 'read_access', 'write_access',
                'authentication_protocol', 'encryption_protocol', 'authentication_password',
                'encryption_password', 'comment', 'disabled', 'status']
    list_param_conv = ['name', 'addresses', 'security', 'read-access', 'write-access',
                'authentication-protocol', 'encryption-protocol', 'authentication-password',
                'encryption-password', 'comment', 'disabled', 'status']

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

def parse_output_snmp_community(list_output):
    list_snmp_community = list()
    list_param = ['name', 'addresses', 'security', 'read-access', 'write-access',
                'authentication-protocol', 'encryption-protocol', 'authentication-password',
                'encryption-password', 'comment', 'disabled']

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

    for item in list_item:
        dict_snmp_community = dict()
        for param in list_param:
            mo = re.search(r'\s' + param + '=\"(.*?)\"\s', ' ' + item + ' ')
            if mo is None:
                mo = re.search(r'\s' + param + '=(.*?)\s', ' ' + item + ' ')
            if mo:
                dict_snmp_community[param] = mo.group(1)
        if 'addresses' in dict_snmp_community:
            if len(dict_snmp_community['addresses']) > 0:
                dict_snmp_community['addresses'] = dict_snmp_community['addresses'].split(',')
        list_snmp_community.append(dict_snmp_community)

    return list_snmp_community

def make_command_snmp_community(dict_param, list_object):
    command = ''
    list_param = ['name', 'addresses', 'security', 'read-access', 'write-access',
                'authentication-protocol', 'encryption-protocol', 'authentication-password',
                'encryption-password', 'disabled']

    index = None
    for num in range(len(list_object)):
        if 'name' in list_object[num]:
            if dict_param['name'] == list_object[num]['name']:
                index = num
                break

    if dict_param['status'] == 'absent':
        if index is None:
            command = ''
        else:
            command = '/snmp community remove ' + dict_param['name']
        return command

    if index is None:
        command = '/snmp community add'
        for param in list_param:
            if param in dict_param:
                if type(dict_param[param]) == list:
                    temp = ''
                    for item in dict_param[param]:
                        temp = temp + ',' + item
                    command = command + ' ' + param + '=\"' + temp[1:] + '\"'
                elif type(dict_param[param]) == str:
                    command = command + ' ' + param + '=\"' + dict_param[param] + '\"'
                else:
                    command = command + ' ' + param + '=' + dict_param[param]
        return command

    command_option = ''
    for param in list_param:
        if param in dict_param:
            if type(dict_param[param]) == list:
                if sorted(dict_param[param]) != sorted(list_object[index][param]):
                    temp = ''
                    for item in dict_param[param]:
                        temp = temp + ',' + item
                    command_option = command_option + ' ' + param + '=\"' + temp[1:] + '\"'
            elif type(dict_param[param]) == str:
                if dict_param[param] != list_object[index][param]:
                    command_option = command_option + ' ' + param + '=\"' + dict_param[param] + '\"'
            else:
                if dict_param[param] != list_object[index][param]:
                    command_option = command_option + ' ' + param + '=' + dict_param[param]

    if command_option.strip() != '':
        # command = '/snmp community set name=\"' + dict_param['name'] + '\"' + command_option 
        command = '/snmp community set ' + str(index) + ' ' + command_option 

    return command

def main():
    """main entry point for module execution
    """
    #### argument spec
    argument_spec = dict(
        name=dict(type='str', required=True),
        addresses=dict(type='list', elements='str', default='0.0.0.0/0'),
        security=dict(type='str', choices=['authorized', 'none', 'private'], default='none'),
        read_access=dict(type='bool', default=True),
        write_access=dict(type='bool', default=False),
        authentication_protocol=dict(type='str', choices=['MD5', 'SHA1'], default='MD5'),
        encryption_protocol=dict(type='str', choices=['DES', 'AES'], default='DES'),
        authentication_password=dict(type='str', no_log=True),
        encryption_password=dict(type='str', no_log=True),
        comment=dict(type='str'),
        disabled=dict(type='bool'),
        status=dict(type='str', choices=["present", "absent"], required=True)
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
    list_object = list()

    #### get parameter
    dict_param = get_param(module)
  
    #### exec get command
    commands = '/snmp community print detail without-paging'
    responses = run_commands(module, commands)
    list_output = cleaning_output(responses[0])
    list_exec.append({'commands':commands, 'stdout':list_output})

    #### parse output
    list_object = parse_output_snmp_community(list_output)

    #### make commad
    set_commands = make_command_snmp_community(dict_param, list_object)

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
            'object': list_object,
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
        'object': list_object,
        'stdout': list_exec,
        'stdout_lines': list(to_lines(results)),
        'log': list_log
    })

    module.exit_json(**result)

if __name__ == '__main__':
    main()
