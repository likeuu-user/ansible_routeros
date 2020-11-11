# ansible_routeros
## required
- python 3.6.8
- Ansible 2.10
- community/routeros
- community/network
## component
- routeros_snmp
- routeros_snmp_community
- routeros_system_identity
- routeros_system_ntp_client
## inventory
```ini
[routeros]
router01 ansible_ssh_host=192.168.0.1
router02 ansible_ssh_host=192.168.0.2
```
## vars
```yaml
ansible_connection: ansible.netcommon.network_cli
ansible_network_os: community.network.routeros
ansible_user: username+cet512w
ansible_password: password
```
Note:
- Add `+cet512w` after the username.
## Playbook
```yaml
---
- hosts: routeros
  gather_facts: false
  connection: network_cli
  tasks:
    - name: xxx xxx
      routeros_xxx_xxx:
        parameter1: xxx
        parameter2: xxx
```
