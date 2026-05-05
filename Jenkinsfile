pipeline {
    agent any

    stages {
        stage('Info') {
            steps {
                echo "Branch: ${env.BRANCH_NAME}"
                echo "PR ID: ${env.CHANGE_ID}"
                echo "Target: ${env.CHANGE_TARGET}"
            }
        }

        stage('Build') {
            steps {
                sh 'echo "Building..."'
            }
        }

        stage('Test') {
            steps {
                sh 'echo "Running tests..."'
            }
        }

        stage('Deploy') {
            when {
                expression {
                    env.CHANGE_ID == null && 
                    (env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'master')
                }
            }
            steps {
                echo "🚀 Deploying from ${env.BRANCH_NAME}"
            }
        }
    }
}
