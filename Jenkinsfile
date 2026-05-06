pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.9'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                echo 'Setting up Python environment...'
                sh '''
                    python3 --version || python --version
                    python3 -m pip install --upgrade pip || python -m pip install --upgrade pip
                '''
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo 'Installing dependencies...'
                sh '''
                    pip3 install -r requirements.txt || pip install -r requirements.txt
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                echo 'Running payment tests...'
                sh '''
                    pytest tests/ -v --junitxml=test-results.xml --html=test-report.html --self-contained-html
                '''
            }
        }
        
        stage('Code Coverage') {
            steps {
                echo 'Generating code coverage report...'
                sh '''
                    pytest tests/ --cov=src --cov-report=html --cov-report=xml
                '''
            }
        }
        
        stage('Publish Results') {
            steps {
                echo 'Publishing test results...'
                junit 'test-results.xml'
                
                publishHTML(target: [
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
                
                publishHTML(target: [
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'test-report.html',
                    reportName: 'Test Report'
                ])
            }
        }
    }
    
    post {
        always {
            echo 'Cleaning up...'
            cleanWs(patterns: [
                [pattern: '**/__pycache__', type: 'INCLUDE'],
                [pattern: '**/*.pyc', type: 'INCLUDE']
            ])
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
