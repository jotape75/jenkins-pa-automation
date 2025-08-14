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
                    python3 --version
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