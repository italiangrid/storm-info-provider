pipeline {
    agent {
        kubernetes {
            cloud 'Kube mwdevel'
            label 'python-pod'
            containerTemplate {
                name 'python-runner'
                image 'italiangrid/storm-info-provider:latest'
                ttyEnabled true
                command 'cat'
            }
        }
    }
    environment {
        GIT_BRANCH = "${env.BRANCH_NAME}"
    }
    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 1, unit: 'HOURS')
    }
    triggers {
        cron('@daily')
    }
    stages {
        stage('tests') {
            steps {
                container('python-runner') {
                    dir('src') {
                        sh 'coverage run tests.py'
                        sh 'coverage html'
                    }
                    script {
                        publishHTML(target: [
                            reportName           : 'Coverage Report',
                            reportDir            : './src/htmlcov',
                            reportFiles          : 'index.html',
                            keepAll              : true,
                            alwaysLinkToLastBuild: true,
                            allowMissing         : false
                        ])
                    }
                }
            }
        }
        stage('result') {
            steps {
                script { currentBuild.result = 'SUCCESS' }
            }
        }
    }
    post {
        failure {
            slackSend color: 'danger', message: "${env.JOB_NAME} - #${env.BUILD_NUMBER} Failure (<${env.BUILD_URL}|Open>)"
        }
        unstable {
            slackSend color: 'warning', message: "${env.JOB_NAME} - #${env.BUILD_NUMBER} Unstable (<${env.BUILD_URL}|Open>)"
        }
        changed {
            script{
                if('SUCCESS'.equals(currentBuild.result)) {
                    slackSend color: 'good', message: "${env.JOB_NAME} - #${env.BUILD_NUMBER} Back to normal (<${env.BUILD_URL}|Open>)"
                }
            }
        }
    }
}
