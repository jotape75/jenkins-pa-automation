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
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'log/*.log', allowEmptyArchive: true
            archiveArtifacts artifacts: '*.pkl', allowEmptyArchive: true
        }
        success {
            echo "PA Automation completed successfully!"
        }
        failure {
            echo "PA Automation failed. Check logs for details."
        }
    }
}