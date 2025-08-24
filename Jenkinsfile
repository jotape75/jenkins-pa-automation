pipeline {
    agent any
    
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
                    env.HA_INTERFACE_1 = params.HA_INTERFACE_1
                    env.HA_INTERFACE_2 = params.HA_INTERFACE_2
                    env.ETHERNET1_1_IP = params.ETHERNET1_1_IP
                    env.ETHERNET1_2_IP = params.ETHERNET1_2_IP
                    env.ETHERNET1_3_IP = params.ETHERNET1_3_IP
                    env.DEFAULT_GATEWAY = params.DEFAULT_GATEWAY
                    env.STATIC_ROUTE_NETWORK = params.STATIC_ROUTE_NETWORK
                    env.STATIC_ROUTE_NEXTHOP = params.STATIC_ROUTE_NEXTHOP
                    env.SOURCE_NAT_IP = params.SOURCE_NAT_IP
                    env.INTERNAL_ZONE_INTERFACE = params.INTERNAL_ZONE_INTERFACE
                    env.EXTERNAL_ZONE_INTERFACE = params.EXTERNAL_ZONE_INTERFACE
                    env.DMZ_ZONE_INTERFACE = params.DMZ_ZONE_INTERFACE
                    env.FIREWALL_HOSTS = params.FIREWALL_HOSTS
                    env.USERNAME = params.USERNAME
                    env.PASSWORD = params.PASSWORD
                    
                    // Update XML templates with parameters
                    sh 'python3 src/update_templates.py'
                    
                    // Show what was configured
                    echo "Configuration Summary:"
                    echo "HA Interfaces: ${params.HA_INTERFACE_1}, ${params.HA_INTERFACE_2}"
                    echo "Data Interface IPs: ${params.ETHERNET1_1_IP}, ${params.ETHERNET1_2_IP}, ${params.ETHERNET1_3_IP}"
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

        stage('Current Config Discovery') {
            steps {
                sh 'python3 src/main.py --step discovery'
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
            echo "- HA Interfaces: ${params.HA_INTERFACE_1}, ${params.HA_INTERFACE_2}"
            echo "- Gateway: ${params.DEFAULT_GATEWAY}"
            echo "- NAT IP: ${params.SOURCE_NAT_IP}"
        }
        failure {
            echo "PA Automation failed. Check logs for details."
            echo "Failed with parameters:"
            echo "- HA Interfaces: ${params.HA_INTERFACE_1}, ${params.HA_INTERFACE_2}"
            echo "- Firewall Hosts: ${params.FIREWALL_HOSTS}"
        }
    }
}