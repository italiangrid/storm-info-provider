pipeline {

    agent { label 'generic' }

    options {
      buildDiscarder(logRotator(numToKeepStr: '5'))
      timeout(time: 1, unit: 'HOURS')
    }

    triggers { cron('@daily') }

    stages {

      stage('prepare-report') {
        steps {
          container('generic-runner') {
            sh 'cd src/'
            sh 'coverage run --source=. -m unittest discover'
            sh 'coverage xml'
            archiveArtifacts 'coverage.xml'
          }
          script {
            currentBuild.result = 'SUCCESS'
          }
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
