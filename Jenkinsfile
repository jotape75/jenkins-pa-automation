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
                script {
                    echo "Setting up PA Automation environment..."
                }
                sh '''
                    # Check available Python versions
                    echo "Checking Python availability..."
                    which python3 || which python || echo "Python not found in PATH"
                    
                    # Try different Python commands
                    if command -v python3 &> /dev/null; then
                        PYTHON_CMD=python3
                        PIP_CMD=pip3
                    elif command -v python &> /dev/null; then
                        PYTHON_CMD=python
                        PIP_CMD=pip
                    else
                        echo "No Python found! Installing Python..."
                        apt-get update && apt-get install -y python3 python3-pip
                        PYTHON_CMD=python3
                        PIP_CMD=pip3
                    fi
                    
                    echo "Using Python: $PYTHON_CMD"
                    $PYTHON_CMD --version
                    
                    echo "Installing requirements..."
                    $PIP_CMD install -r requirements.txt
                '''
            }
        }
        
        stage('Generate API Keys') {
            steps {
                script {
                    echo "Generating API keys for PA firewalls..."
                }
                sh '''
                    # Use the same Python detection logic
                    if command -v python3 &> /dev/null; then
                        PYTHON_CMD=python3
                    elif command -v python &> /dev/null; then
                        PYTHON_CMD=python
                    else
                        PYTHON_CMD=python3
                    fi
                    
                    echo "Executing PA automation with: $PYTHON_CMD"
                    $PYTHON_CMD src/main.py --step api_keys
                '''
            }
        }
    }
    
    post {
        always {
            script {
                echo "Archiving logs and artifacts..."
            }
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