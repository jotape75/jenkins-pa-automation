pipeline {
    agent any
    
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
        
        stage('Generate API Keys') {
            steps {
                sh 'python3 src/main.py --step api_keys'
            }
        }
        
        stage('Discovery') {
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
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'log/*.log', allowEmptyArchive: true
        }
        success {
            echo "PA Automation completed successfully!"
        }
        failure {
            echo "PA Automation failed. Check logs for details."
        }
    }
}