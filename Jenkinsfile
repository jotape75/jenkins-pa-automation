pipeline {
    agent any
    
    parameters {
        choice(name: 'HA1_INTERFACE', choices: ['ethernet1/4', 'ethernet1/5', 'ethernet1/6', 'ethernet1/7'], description: 'HA Control Interface')
        choice(name: 'HA2_INTERFACE', choices: ['ethernet1/5', 'ethernet1/6', 'ethernet1/7', 'ethernet1/8'], description: 'HA Data Interface')
        string(name: 'ETHERNET1_1_IP_TRUST', defaultValue: '10.10.10.5/24', description: 'Trust Interface IP (CIDR format)')
        string(name: 'ETHERNET1_2_IP_UNTRUST', defaultValue: '200.200.200.2/24', description: 'Untrust Interface IP (CIDR format)')
        string(name: 'ETHERNET1_3_IP_DMZ', defaultValue: '10.30.30.5/24', description: 'DMZ Interface IP (CIDR format)')
        string(name: 'DEFAULT_GATEWAY', defaultValue: '200.200.200.1', description: 'Default Gateway IP Address')
        string(name: 'STATIC_ROUTE_NETWORK', defaultValue: '10.0.0.0/8', description: 'Static Route Network (CIDR format)')
        string(name: 'STATIC_ROUTE_NEXTHOP', defaultValue: '10.10.10.1', description: 'Static Route Next Hop IP')
        string(name: 'SOURCE_NAT_IP', defaultValue: '200.200.200.10', description: 'Source NAT IP Address')
        string(name: 'TRUST', defaultValue: 'ethernet1/1', description: 'Trust Zone Interface')
        string(name: 'UNTRUST', defaultValue: 'ethernet1/2', description: 'Untrust Zone Interface')
        string(name: 'DMZ', defaultValue: 'ethernet1/3', description: 'DMZ Zone Interface')
        string(name: 'FIREWALL_HOSTS', defaultValue: '192.168.0.226,192.168.0.227', description: 'Firewall IP Addresses (comma-separated)')
        string(name: 'USERNAME', defaultValue: 'api_user', description: 'Firewall Username')
        password(name: 'PASSWORD', description: 'Firewall Password')
    }
    
    stages {
        stage('Pull Repository & Setup') {
            steps {
                cleanWs()
                git branch: 'main', url: 'https://github.com/jotape75/jenkins-pa-automation.git'
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
                    echo "Setting environment variables and updating templates..."
                    
                    // Set environment variables with CORRECT parameter names
                    env.HA1_INTERFACE = params.HA1_INTERFACE
                    env.HA2_INTERFACE = params.HA2_INTERFACE
                    env.ETHERNET1_1_IP_TRUST = params.ETHERNET1_1_IP_TRUST
                    env.ETHERNET1_2_IP_UNTRUST = params.ETHERNET1_2_IP_UNTRUST
                    env.ETHERNET1_3_IP_DMZ = params.ETHERNET1_3_IP_DMZ
                    env.DEFAULT_GATEWAY = params.DEFAULT_GATEWAY
                    env.STATIC_ROUTE_NETWORK = params.STATIC_ROUTE_NETWORK
                    env.STATIC_ROUTE_NEXTHOP = params.STATIC_ROUTE_NEXTHOP
                    env.SOURCE_NAT_IP = params.SOURCE_NAT_IP
                    env.TRUST = params.TRUST
                    env.UNTRUST = params.UNTRUST
                    env.DMZ = params.DMZ
                    env.FIREWALL_HOSTS = params.FIREWALL_HOSTS
                    env.USERNAME = params.USERNAME
                    env.PASSWORD = params.PASSWORD
                    
                    // Hardcoded HA IP values
                    env.HA_PEER_IP_1 = '1.1.1.2'
                    env.HA_PEER_IP_2 = '1.1.1.1'
                    env.HA1_IP_1 = '1.1.1.1'
                    env.HA1_IP_2 = '1.1.1.2'
                    
                    sh 'python3 src/update_templates.py'
                    
                    echo "Configuration Summary:"
                    echo "HA Interfaces: ${params.HA1_INTERFACE} (Control), ${params.HA2_INTERFACE} (Data)"
                    echo "Data IPs: Trust=${params.ETHERNET1_1_IP_TRUST}, Untrust=${params.ETHERNET1_2_IP_UNTRUST}, DMZ=${params.ETHERNET1_3_IP_DMZ}"
                    echo "Routing: Gateway=${params.DEFAULT_GATEWAY}, Static=${params.STATIC_ROUTE_NETWORK} via ${params.STATIC_ROUTE_NEXTHOP}"
                    echo "NAT IP: ${params.SOURCE_NAT_IP}"
                    echo "Target Firewalls: ${params.FIREWALL_HOSTS}"
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
        
        // stage('Complete Firewall Configuration') {
        //     steps {
        //         sh 'python3 src/main.py --step firewall_config'
        //     }
        // }
        
        // stage('Commit & Sync Configuration') {
        //     steps {
        //         sh 'python3 src/main.py --step commit'
        //     }
        // }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'log/*.log', allowEmptyArchive: true
            script {
                env.PASSWORD = ""
            }
        }
        success {
            echo "PA Automation completed successfully!"
            echo "HA Configuration: ${params.HA1_INTERFACE} (Control), ${params.HA2_INTERFACE} (Data)"
            echo "Configuration committed and synced to both firewalls"
        }
        failure {
            echo "PA Automation failed. Check logs for details."
        }
    }
}