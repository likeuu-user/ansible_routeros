#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
'''

EXAMPLES = """
- name: test base module
    routeros_system_identity:
    name: "{{ inventory_hostname }}"
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
    list_param = ['name']

    for num in range(len(list_param)):
        if list_param[num] in module.params:
            dict_param[list_param[num]] = module.params[list_param[num]]

    return dict_param

def parse_output_system_identity(list_output):
    dict_identity = dict()
    list_param = ['name']

    for param in list_param:
        for output in list_output:
            mo = re.search(r'\s' + param + ':\s(.*)$', ' ' + output)
            if mo:
                dict_identity[param] = mo.group(1)

    return dict_identity

def make_command_system_identity(dict_param, dict_object):
    command = ''
    list_param = ['name']
    command_option = ''
    for param in list_param:
        if param in dict_param:
            if dict_param[param] != dict_object[param]:
                command_option = command_option + ' ' + param + '=\"' + dict_param[param] + '\"'


    if command_option.strip() != '':
        command = '/system identity set' + command_option 

    return command

def main():
    """main entry point for module execution
    """
    #### argument spec
    argument_spec = dict(
        name=dict(type='str', required=True)
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
    commands = '/system identity print without-paging'
    responses = run_commands(module, commands)
    list_output = cleaning_output(responses[0])
    list_exec.append({'commands':commands, 'stdout':list_output})

    #### parse output
    dict_object = parse_output_system_identity(list_output)

    #### make commad
    set_commands = make_command_system_identity(dict_param, dict_object)

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
