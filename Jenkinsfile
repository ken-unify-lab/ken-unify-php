pipeline {
  agent {
    kubernetes {
      cloud 'kubernetes'
      defaultContainer 'php'
      yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: php
      image: php:8.3-cli-alpine
      command: [cat]
      tty: true
      resources:
        requests:
          cpu: 100m
          memory: 256Mi
        limits:
          cpu: "1"
          memory: 768Mi
    - name: python
      image: python:3.12-slim
      command: [cat]
      tty: true
      resources:
        requests:
          cpu: 50m
          memory: 128Mi
        limits:
          cpu: 500m
          memory: 256Mi
'''
    }
  }
  options {
    skipDefaultCheckout(true)
    disableConcurrentBuilds()
    timeout(time: 30, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '10'))
    timestamps()
  }
  parameters {
    booleanParam(name: 'DEPLOY_KEN_DEV', defaultValue: false, description: 'Deploy tested revision to Ken PHP Render service only')
  }
  environment {
    COMPOSER_ALLOW_SUPERUSER = '1'
    KEN_COMPONENT_ID = '08cdce26-9ad4-4175-bdea-d3db567089af'
  }
  stages {
    stage('Prepare PHP 8.3 test tools') {
      steps {
        sh '''
          set -eu
          apk add --no-cache $PHPIZE_DEPS libxml2-dev oniguruma-dev git curl unzip
          docker-php-ext-install dom mbstring xml xmlwriter
          curl -fsSL https://getcomposer.org/download/2.10.3/composer.phar -o /tmp/composer.phar
          php /tmp/composer.phar --version
        '''
      }
    }
    stage('Check out Ken source') {
      steps {
        script {
          def revision = checkout scm
          env.SOURCE_SHA = revision.GIT_COMMIT
          env.EXPECTED_SHA = revision.GIT_COMMIT
        }
        sh 'git log -1 --format=%H'
      }
    }
    stage('PHPUnit tests') {
      steps {
        sh '''
          set -eu
          php /tmp/composer.phar install --no-interaction --prefer-dist --no-progress
          mkdir -p reports
          php /tmp/composer.phar test
        '''
      }
      post {
        always {
          junit testResults: 'reports/junit.xml', allowEmptyResults: false
        }
      }
    }
    stage('Package and register source') {
      steps {
        sh '''
          set -eu
          mkdir -p dist
          printf '%s\n' "$SOURCE_SHA" > VERSION
          tar -czf "dist/ken-php-$SOURCE_SHA.tar.gz" app.php composer.json Dockerfile VERSION
          sha256sum "dist/ken-php-$SOURCE_SHA.tar.gz"
        '''
        archiveArtifacts artifacts: 'dist/*.tar.gz,reports/junit.xml', fingerprint: true
        script {
          env.ARTIFACT_ID = registerBuildArtifactMetadata(
            name: 'ken-php-source',
            version: env.SOURCE_SHA,
            url: "https://github.com/ken-unify-lab/ken-unify-php/tree/${env.SOURCE_SHA}",
            type: 'source',
            label: 'ken,source-based-demo',
            componentId: env.KEN_COMPONENT_ID,
            commit: env.SOURCE_SHA,
            commitUrl: "https://github.com/ken-unify-lab/ken-unify-php/commit/${env.SOURCE_SHA}",
            repositoryUrl: 'https://github.com/ken-unify-lab/ken-unify-php.git',
            ref: 'refs/heads/main'
          )
          echo "Unify source artifact ID: ${env.ARTIFACT_ID}"
        }
      }
    }
    stage('Deploy and verify Ken PHP') {
      when { expression { params.DEPLOY_KEN_DEV && env.BRANCH_NAME == 'main' } }
      steps {
        container('python') {
          withCredentials([string(credentialsId: 'ken-php-render-deploy-hook', variable: 'RENDER_DEPLOY_HOOK_URL')]) {
            sh 'python3 scripts/deploy_render.py'
          }
        }
      }
      post {
        always {
          script {
            if (fileExists('reports/deployment-attempted.txt')) {
              registerDeployedArtifactMetadata(
                artifactId: env.ARTIFACT_ID,
                targetEnvironment: 'ken-dev',
                labels: 'ken,render,source-based-demo',
                allowNoMatchingComponent: false
              )
            }
          }
        }
      }
    }
  }
  post {
    always {
      archiveArtifacts artifacts: 'reports/*.txt', allowEmptyArchive: true
    }
  }
}
