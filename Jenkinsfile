pipeline {
    agent any
    
    parameters {
        // HA Interface Configuration
        choice(
            name: 'HA1_INTERFACE',
            choices: ['ethernet1/4', 'ethernet1/5', 'ethernet1/6', 'ethernet1/7'],
            description: 'Control Links'
        ),
        choice(
            name: 'HA2_INTERFACE', 
            choices: ['ethernet1/5', 'ethernet1/6', 'ethernet1/7', 'ethernet1/8'],
            description: 'Data Links'
        ),
        string(
            name: 'HA1_IP_1',
            defaultValue: '1.1.1.1',
            description: 'HA1 Interface IP for first firewall'
        ),
        string(
            name: 'HA1_IP_2',
            defaultValue: '1.1.1.2', 
            description: 'HA1 Interface IP for second firewall'
        ),
        string(
            name: 'HA_PEER_IP_1',
            defaultValue: '1.1.1.2',
            description: 'HA Peer IP for first firewall'
        ),
        string(
            name: 'HA_PEER_IP_2',
            defaultValue: '1.1.1.1',
            description: 'HA Peer IP for second firewall'
        ),
        
        // Data Interface IP Addresses
        string(
            name: 'ETHERNET1_1_IP_trust',
            defaultValue: '',
            description: 'Ethernet1/1 IP Address (CIDR format) - Example: 10.10.10.5/24'
        ),
        string(
            name: 'ETHERNET1_2_IP_untrust',
            defaultValue: '', 
            description: 'Ethernet1/2 IP Address (CIDR format) - Example: 200.200.200.2/24'
        ),
        string(
            name: 'ETHERNET1_3_IP_dmz',
            defaultValue: '',
            description: 'Ethernet1/3 IP Address (CIDR format) - Example: 10.30.30.5/24'
        ),
        
        // Gateway/Routing Configuration
        string(
            name: 'DEFAULT_GATEWAY',
            defaultValue: '',
            description: 'Default Gateway IP Address - Example: 200.200.200.1'
        ),
        string(
            name: 'STATIC_ROUTE_NETWORK',
            defaultValue: '',
            description: 'Static Route Network (CIDR format) - Example: 10.0.0.0/8'
        ),
        string(
            name: 'STATIC_ROUTE_NEXTHOP',
            defaultValue: '',
            description: 'Static Route Next Hop IP - Example: 10.10.10.1'
        ),
        
        // NAT Configuration
        string(
            name: 'SOURCE_NAT_IP',
            defaultValue: '',
            description: 'Source NAT IP Address - Example: 200.200.200.10'
        ),
        
        // Security Zone Configuration  
        string(
            name: 'trust',
            defaultValue: 'ethernet1/1',
            description: 'Trust Zone'
        ),
        string(
            name: 'untrust', 
            defaultValue: 'ethernet1/2',
            description: 'Untrust Zone'
        ),
        string(
            name: 'dmz',
            defaultValue: 'ethernet1/3', 
            description: 'DMZ Zone'
        ),
        
        // Firewall Device Configuration
        string(
            name: 'FIREWALL_HOSTS',
            defaultValue: '192.168.0.226,192.168.0.227',
            description: 'Firewall IP Addresses (comma-separated)'
        ),
        string(
            name: 'USERNAME',
            defaultValue: 'admin',
            description: 'Firewall Username'
        ),
        password(
            name: 'PASSWORD',
            description: 'Firewall Password'
        )
    }
    
    stages {
        stage('Pull Repository & Setup') {
            steps {
                cleanWs()
                git branch: 'main', 
                    url: 'https://github.com/jotape75/jenkins-pa-automation.git'
                    
                sh '''
                    echo "Setting up environment..."
                    python3 --version
                    pip3 --version
                    pip3 install -r requirements.txt
                '''
            }
        }
        
        stage('Update Configuration Templates') {
            steps {
                script {
                    echo "Updating XML templates with Jenkins parameters..."
                    
                    // Export Jenkins parameters as environment variables
                    env.HA1_INTERFACE = params.HA1_INTERFACE
                    env.HA2_INTERFACE = params.HA2_INTERFACE
                    env.HA1_IP_1 = params.HA1_IP_1
                    env.HA1_IP_2 = params.HA1_IP_2
                    env.HA_PEER_IP_1 = params.HA_PEER_IP_1
                    env.HA_PEER_IP_2 = params.HA_PEER_IP_2
                    env.ETHERNET1_1_IP_trust = params.ETHERNET1_1_IP_trust
                    env.ETHERNET1_2_IP_untrust = params.ETHERNET1_2_IP_untrust
                    env.ETHERNET1_3_IP_dmz = params.ETHERNET1_3_IP_dmz
                    env.DEFAULT_GATEWAY = params.DEFAULT_GATEWAY
                    env.STATIC_ROUTE_NETWORK = params.STATIC_ROUTE_NETWORK
                    env.STATIC_ROUTE_NEXTHOP = params.STATIC_ROUTE_NEXTHOP
                    env.SOURCE_NAT_IP = params.SOURCE_NAT_IP
                    env.trust = params.trust
                    env.untrust = params.untrust
                    env.dmz = params.dmz
                    env.FIREWALL_HOSTS = params.FIREWALL_HOSTS
                    env.USERNAME = params.USERNAME
                    env.PASSWORD = params.PASSWORD
                    
                    // Update XML templates with parameters
                    sh 'python3 src/update_templates.py'
                    
                    // Show what was configured
                    echo "Configuration Summary:"
                    echo "HA Interfaces: ${params.HA1_INTERFACE} (Control), ${params.HA2_INTERFACE} (Data)"
                    echo "HA IP Addresses: ${params.HA1_IP_1}, ${params.HA1_IP_2}"
                    echo "HA Peer IPs: ${params.HA_PEER_IP_1}, ${params.HA_PEER_IP_2}"
                    echo "Data Interface IPs: ${params.ETHERNET1_1_IP_trust}, ${params.ETHERNET1_2_IP_untrust}, ${params.ETHERNET1_3_IP_dmz}"
                    echo "Security Zones: Trust=${params.trust}, Untrust=${params.untrust}, DMZ=${params.dmz}"
                    echo "Default Gateway: ${params.DEFAULT_GATEWAY}"
                    echo "Source NAT IP: ${params.SOURCE_NAT_IP}"
                    echo "Firewall Hosts: ${params.FIREWALL_HOSTS}"
                }
            }
        }
        
        stage('Generate API Keys') {
            steps {
                sh 'python3 src/main.py --step api_keys'
            }
        }
        
        stage('Enable HA Interfaces') {
            steps {
                sh 'python3 src/main.py --step ha_interfaces'
            }
        }
        
        stage('Configure HA Settings') {
            steps {
                sh 'python3 src/main.py --step ha_config'
            }
        }
        
        stage('Identify Active Firewall') {
            steps {
                sh 'python3 src/main.py --step identify_active'
            }
        }
        
        stage('Complete Firewall Configuration') {
            steps {
                sh 'python3 src/main.py --step firewall_config'
            }
        }
        
        stage('Commit & Sync Configuration') {
            steps {
                sh 'python3 src/main.py --step commit'
            }
        }
        
        stage('Archive Updated Templates') {
            steps {
                script {
                    // Archive the generated templates for audit
                    sh '''
                        echo "Generated template files:"
                        ls -la data/payload/ || echo "Payload directory not found"
                        echo "Sample interface configuration:"
                        head -10 data/payload/data_interface.xml || echo "Interface template not found"
                    '''
                }
            }
        }
    }
    
    post {
        always {
            // Archive logs and generated templates
            archiveArtifacts artifacts: 'log/*.log', allowEmptyArchive: true
            archiveArtifacts artifacts: 'data/payload/*.xml', allowEmptyArchive: true
            
            // Cleanup sensitive environment variables
            script {
                env.PASSWORD = ""
            }
        }
        success {
            echo "PA Automation completed successfully!"
            echo "Configuration deployed with parameters:"
            echo "- HA Interfaces: ${params.HA1_INTERFACE} (Control), ${params.HA2_INTERFACE} (Data)"
            echo "- HA IPs: ${params.HA1_IP_1}, ${params.HA1_IP_2}"
            echo "- Security Zones: Trust=${params.trust}, Untrust=${params.untrust}, DMZ=${params.dmz}"
            echo "- Gateway: ${params.DEFAULT_GATEWAY}"
            echo "- NAT IP: ${params.SOURCE_NAT_IP}"
        }
        failure {
            echo "PA Automation failed. Check logs for details."
            echo "Failed with parameters:"
            echo "- HA Interfaces: ${params.HA1_INTERFACE}, ${params.HA2_INTERFACE}"
            echo "- HA IPs: ${params.HA1_IP_1}, ${params.HA1_IP_2}"
            echo "- Firewall Hosts: ${params.FIREWALL_HOSTS}"
        }
    }
}