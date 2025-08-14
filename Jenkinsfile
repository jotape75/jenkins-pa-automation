pipeline {
    agent any
    
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', 
                    url: 'https://github.com/jotape75/jenkins-pa-automation.git'
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    echo "Checking for Python..."
                    
                    # Install Python if not available
                    if ! command -v python3 &> /dev/null; then
                        echo "Python3 not found, installing..."
                        apt-get update
                        apt-get install -y python3 python3-pip
                    else
                        echo "Python3 found"
                    fi
                    
                    python3 --version
                    
                    # Install pip if not available
                    if ! command -v pip3 &> /dev/null; then
                        echo "pip3 not found, installing..."
                        apt-get install -y python3-pip
                    fi
                    
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
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'log/*.log', allowEmptyArchive: true
            archiveArtifacts artifacts: '*.pkl', allowEmptyArchive: true
        }
    }
}