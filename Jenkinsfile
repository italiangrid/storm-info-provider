pipeline {
    agent {
        kubernetes {
            cloud 'Kube mwdevel'
            label 'python-pod'
            containerTemplate {
                name 'python-runner'
                image 'python:2.7'
                ttyEnabled true
                command 'cat'
            }
        }
    }
    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 1, unit: 'HOURS')
    }
    triggers {
        cron('@daily')
    }
    stages {
        stage('prepare') {
            steps {
                container('python-runner') {
                    sh 'apt-get -y update'
                    sh 'apt-get -y install libsasl2-dev python-dev libldap2-dev libssl-dev'
                    sh 'pip install mock unittest2 coverage python-ldap==2.3.13'
                }
            }
        }
        stage('tests') {
            steps {
                container('python-runner') {
                    dir('src') {
                        sh 'coverage run --source=. -m unittest discover'
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