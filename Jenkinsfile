parameters {
    // Network Diagram Reference
    text(
        name: 'NETWORK_DIAGRAM',
        defaultValue: '',
        description: '''
        <img src="https://raw.githubusercontent.com/jotape75/jenkins-pa-automation/main/docs/PA_diagram.png" 
             alt="Palo Alto Network Diagram" 
             style="max-width: 600px; height: auto; border: 1px solid #ccc; margin: 10px 0;">
        '''
    )
    
    // HA Interface Configuration
    choice(
        name: 'HA_INTERFACE_1',
        choices: ['ethernet1/4', 'ethernet1/5', 'ethernet1/6', 'ethernet1/7'],
        description: 'First HA Interface'
    )
    choice(
        name: 'HA_INTERFACE_2', 
        choices: ['ethernet1/5', 'ethernet1/6', 'ethernet1/7', 'ethernet1/8'],
        description: 'Second HA Interface'
    )
    
    // Data Interface IP Addresses
    string(
        name: 'ETHERNET1_1_IP',
        defaultValue: '',
        description: 'Ethernet1/1 IP Address (CIDR format) - Example: 10.10.10.5/24'
    )
    string(
        name: 'ETHERNET1_2_IP',
        defaultValue: '', 
        description: 'Ethernet1/2 IP Address (CIDR format) - Example: 200.200.200.2/24'
    )
    string(
        name: 'ETHERNET1_3_IP',
        defaultValue: '',
        description: 'Ethernet1/3 IP Address (CIDR format) - Example: 10.30.30.5/24'
    )
    
    // Gateway/Routing Configuration
    string(
        name: 'DEFAULT_GATEWAY',
        defaultValue: '',
        description: 'Default Gateway IP Address - Example: 200.200.200.1'
    )
    string(
        name: 'STATIC_ROUTE_NETWORK',
        defaultValue: '',
        description: 'Static Route Network (CIDR format) - Example: 10.0.0.0/8'
    )
    string(
        name: 'STATIC_ROUTE_NEXTHOP',
        defaultValue: '',
        description: 'Static Route Next Hop IP - Example: 10.10.10.1'
    )
    
    // NAT Configuration
    string(
        name: 'SOURCE_NAT_IP',
        defaultValue: '',
        description: 'Source NAT IP Address - Example: 200.200.200.10'
    )
    
    // Security Zone Configuration  
    string(
        name: 'INTERNAL_ZONE_INTERFACE',
        defaultValue: 'ethernet1/1',
        description: 'Internal Zone Interface'
    )
    string(
        name: 'EXTERNAL_ZONE_INTERFACE', 
        defaultValue: 'ethernet1/2',
        description: 'External Zone Interface'
    )
    string(
        name: 'DMZ_ZONE_INTERFACE',
        defaultValue: 'ethernet1/3', 
        description: 'DMZ Zone Interface'
    )
    
    // Firewall Device Configuration
    string(
        name: 'FIREWALL_HOSTS',
        defaultValue: '192.168.0.225,192.168.0.226',
        description: 'Firewall IP Addresses (comma-separated)'
    )
    string(
        name: 'USERNAME',
        defaultValue: 'admin',
        description: 'Firewall Username'
    )
    password(
        name: 'PASSWORD',
        defaultValue: 'admin',
        description: 'Firewall Password'
    )
}