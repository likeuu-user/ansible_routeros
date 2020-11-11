#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
'''

EXAMPLES = """
- name: test base module
    routeros_ip_address:
        address: 192.168.88.1/24
        interface: ether5
        comment: test for ansible
        disabled: False
        status: present

- name: test base module
    routeros_ip_address:
        address: 192.168.88.1/24
        interface: ether5
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
    list_param = ['address', 'interface', 'comment', 'disabled', 'network', 'status']

    for num in range(len(list_param)):
        if list_param[num] in module.params:
            if type(module.params[list_param[num]]) == bool:
                if module.params[list_param[num]]:
                    dict_param[list_param[num]] = 'yes'
                else:
                    dict_param[list_param[num]] = 'no'
            else:
                dict_param[list_param[num]] = module.params[list_param[num]]

    return dict_param

def parse_output_ip_address(list_output):
    list_ip_address = list()
    list_param = ['id', 'address', 'interface', 'comment', 'disabled', 'network']

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
            mo = re.search(r'^\d.*\s(address=.*)$', output.strip())
            if mo:
                temp = temp + ' ' + mo.group(1)
        elif output.strip() != '':
            temp = temp + ' ' + output.strip()
    if temp != '':
        list_item.append(temp)

    for item in list_item:
        dict_ip_address = dict()
        for param in list_param:
            mo = re.search(r'\s' + param + '=\"(.*?)\"\s', ' ' + item + ' ')
            if mo is None:
                mo = re.search(r'\s' + param + '=(.*?)\s', ' ' + item + ' ')
            if mo:
                dict_ip_address[param] = mo.group(1)
        list_ip_address.append(dict_ip_address)

    return list_ip_address

def make_command_ip_address(dict_param, list_object):
    command = ''
    list_param = ['address', 'interface', 'comment', 'disabled', 'network']

    index = None
    for num in range(len(list_object)):
        if 'address' in list_object[num] and 'interface' in list_object[num]:
            if dict_param['address'] == list_object[num]['address'] and dict_param['interface'] == list_object[num]['interface']:
                index = num
                break

    if dict_param['status'] == 'absent':
        if index is None:
            command = ''
        else:
            command = '/ip address remove numbers=' + list_object[index]['id']
        return command

    if index is None:
        command = '/ip address add'
        for param in list_param:
            if param in dict_param:
                if type(dict_param[param]) == list:
                    temp = ''
                    for item in dict_param[param]:
                        temp = temp + ',' + item
                    command = command + ' ' + param + '=\"' + temp[1:] + '\"'
                elif type(dict_param[param]) == str:
                    command = command + ' ' + param + '=\"' + dict_param[param] + '\"'
                elif dict_param[param] is not None:
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
                    if dict_param[param] is not None:
                        command_option = command_option + ' ' + param + '=' + dict_param[param]

    if command_option.strip() != '':
        # command = '/snmp community set name=\"' + dict_param['name'] + '\"' + command_option 
        command = '/ip address set ' + list_object[index]['id'] + ' ' + command_option 

    return command

def main():
    """main entry point for module execution
    """
    #### argument spec
    argument_spec = dict(
       	address=dict(type='str', required=True),
        interface=dict(type='str', required=True),
        comment=dict(type='str'),
        disabled=dict(type='bool'),
        network=dict(type='str'),
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
    commands = '/ip address print detail without-paging'
    responses = run_commands(module, commands)
    list_output = cleaning_output(responses[0])
    list_exec.append({'commands':commands, 'stdout':list_output})

    #### parse output
    list_object = parse_output_ip_address(list_output)

    #### make commad
    set_commands = make_command_ip_address(dict_param, list_object)

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
