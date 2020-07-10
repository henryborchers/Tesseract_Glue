// @Library(["devpi", "PythonHelpers"]) _


def remove_files(artifacts){
    script{
        def files = findFiles glob: "${artifacts}"
        files.each { file_name ->
            bat "del ${file_name}"
        }
    }
}

def getDevPiStagingIndex(){

    if (env.TAG_NAME?.trim()){
        return "tag_staging"
    } else{
        return "${env.BRANCH_NAME}_staging"
    }
}

def remove_from_devpi(pkgName, pkgVersion, devpiIndex, devpiUsername, devpiPassword){
        script {
            docker.build("devpi", "-f ci/docker/deploy/devpi/deploy/Dockerfile .").inside{
                try {
                    sh "devpi login ${devpiUsername} --password ${devpiPassword} --clientdir ${WORKSPACE}/devpi"
                    sh "devpi use ${devpiIndex} --clientdir ${WORKSPACE}/devpi"
                    sh "devpi remove -y ${pkgName}==${pkgVersion} --clientdir ${WORKSPACE}/devpi"
                } catch (Exception ex) {
                    echo "Failed to remove ${pkgName}==${pkgVersion} from ${devpiIndex}"
                }

            }
        }

    }
def create_venv(python_exe, venv_path){
    script {
        bat "${python_exe} -m venv ${venv_path}"
        try {
            bat "${venv_path}\\Scripts\\python.exe -m pip install -U pip"
        }
        catch (exc) {
            bat "${python_exe} -m venv ${venv_path} && call ${venv_path}\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
        }
    }
}



              
def deploy_docs(pkgName, prefix){
    script{
        try{
            timeout(30) {
                input "Update project documentation to https://www.library.illinois.edu/dccdocs/${pkgName}"
            }
            sshPublisher(
                publishers: [
                    sshPublisherDesc(
                        configName: 'apache-ns - lib-dccuser-updater', 
                        sshLabel: [label: 'Linux'], 
                        transfers: [sshTransfer(excludes: '', 
                        execCommand: '', 
                        execTimeout: 120000, 
                        flatten: false, 
                        makeEmptyDirs: false, 
                        noDefaultExcludes: false, 
                        patternSeparator: '[, ]+', 
                        remoteDirectory: "${pkgName}",
                        remoteDirectorySDF: false, 
                        removePrefix: "${prefix}",
                        sourceFiles: "${prefix}/**")],
                    usePromotionTimestamp: false, 
                    useWorkspaceInPromotion: false, 
                    verbose: true
                    )
                ]
            )
        } catch(exc){
            echo "User response timed out. Documentation not published."
        }
    }
}



def get_package_version(stashName, metadataFile){
    ws {
        unstash "${stashName}"
        script{
            def props = readProperties interpolate: true, file: "${metadataFile}"
            deleteDir()
            return props.Version
        }
    }
}

def get_package_name(stashName, metadataFile){
    ws {
        unstash "${stashName}"
        script{
            def props = readProperties interpolate: true, file: "${metadataFile}"
            deleteDir()
            return props.Name
        }
    }
}

def CONFIGURATIONS = [
        "3.6" : [
            os: [
                windows:[
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        test:[
                            whl: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/test/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.6-windowsservercore --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.6-windowsservercore'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ]
                        ]
                    ],
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "36m-win*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp36*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ],
                linux: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/linux/build/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/linux/package/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            whl: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                        ],
                    ],
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "36m-manylinux*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp36*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ]
            ],
            tox_env: "py36",
            devpiSelector: [
                sdist: "zip",
                whl: "36.*whl",
            ],
            pkgRegex: [
                whl: "*cp36*.whl",
                sdist: "*.zip"
            ]
        ],
        "3.7" : [
            os: [
                windows: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            whl: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/test/msvc/Dockerfile',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.7',
                                    label: 'windows && docker',
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.7'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ]
                        ]
                    ],
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "37m-win*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp37*.whl",
                        sdist: "*.zip"
                    ]
                ],
                linux: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/linux/build/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/linux/package/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            whl: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ]
                    ],
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "37m-manylinux*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp37*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ],
            ],
            tox_env: "py37",
            devpiSelector: [
                sdist: "zip",
                whl: "37.*whl",
            ],
            pkgRegex: [
                whl: "*cp37*.whl",
                sdist: "*.zip"
            ]
        ],
        "3.8" : [
            os: [
                windows: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            whl: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/test/msvc/Dockerfile',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.8',
                                    label: 'windows && docker',
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.8'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ]
                        ]

                    ],
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "38-win*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp38*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ],
                linux: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/linux/build/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/linux/package/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            whl: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ]
                    ],
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "38-manylinux*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp38*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ]
            ],
            tox_env: "py38",
            devpiSelector: [
                sdist: "zip",
                wheel: "38.*whl",
            ],
            pkgRegex: [
                whl: "*cp38*.whl",
                sdist: "*.zip"
            ]
        ],
    ]

def test_pkg(glob, timeout_time){

    findFiles( glob: glob).each{
        timeout(timeout_time){
            if(isUnix()){
                sh(label: "Testing ${it}",
                   script: """python --version
                              tox --installpkg=${it.path} -e py -vv
                              """
                )
            } else {
                bat(label: "Testing ${it}",
                    script: """python --version
                               tox --installpkg=${it.path} -e py -vv
                               """
                )
            }
        }
    }
}

pipeline {
    agent none
    triggers {
       parameterizedCron '@weekly % DEPLOY_DEVPI=true; TEST_RUN_TOX=true'
    }
    options {
        timeout(time: 1, unit: 'DAYS')
        buildDiscarder logRotator(artifactDaysToKeepStr: '30', artifactNumToKeepStr: '30', daysToKeepStr: '100', numToKeepStr: '100')
    }
    environment {
        build_number = VersionNumber(projectStartDate: '2018-7-30', versionNumberString: '${BUILD_DATE_FORMATTED, "yy"}${BUILD_MONTH, XX}${BUILDS_THIS_MONTH, XX}', versionPrefix: '', worstResultForIncrement: 'SUCCESS')
    }
    parameters {
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        booleanParam(name: "DEPLOY_ADD_TAG", defaultValue: false, description: "Tag commit to current version")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "ocr", description: 'The directory that the docs should be saved under')
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
    }
    stages {
        stage("Configure") {
            agent {
                dockerfile {
                    filename 'ci/docker/linux/build/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                }
            }
            stages{
                stage("Getting Distribution Info"){
                    steps{
                        timeout(2){
                            sh "python setup.py dist_info"
                        }
                    }
                    post{
                        success{
                            stash includes: "uiucprescon.ocr.dist-info/**", name: 'DIST-INFO'
                            archiveArtifacts artifacts: "uiucprescon.ocr.dist-info/**"
                        }
                        cleanup{
                             cleanWs(
                                notFailBuild: true
                                )
                        }
                    }
                }
           }
        }
        stage("Building") {
            agent {
                dockerfile {
                    filename 'ci/docker/linux/build/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                }
            }
            stages{
                stage("Building Python Package"){
                    steps {
                        timeout(20){
                            sh(
                                label: "Build python package",
                                script: '''mkdir -p logs
                                        python setup.py build -b build --build-lib build/lib/ --build-temp build/temp build_ext -j $(grep -c ^processor /proc/cpuinfo) --inplace  2>&1 | tee logs/python_build.log
                                        '''
                            )
                        }
                    }
                    post{
                        always{
                            stash includes: 'uiucprescon/**/*.dll,uiucprescon/**/*.pyd,uiucprescon/**/*.exe,uiucprescon/**/*.so', name: "COMPILED_BINARIES"
                            recordIssues(filters: [excludeFile('build/*')], tools: [gcc(pattern: 'logs/python_build.log')])
                        }
                        cleanup{
                            cleanWs(
                                patterns: [
                                        [pattern: 'logs/build.log', type: 'INCLUDE'],
                                        [pattern: "logs/built_package.log", type: 'INCLUDE'],
                                        [pattern: "logs/env_vars.log", type: 'INCLUDE'],
                                    ],
                                notFailBuild: true
                                )
                        }
                    }
                }
                stage("Building Documentation"){
                    environment {
                        PKG_NAME = get_package_name("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA")
                        PKG_VERSION = get_package_version("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA")
                    }
                    steps{
                        timeout(3){
                            sh '''mkdir -p logs
                                  python -m sphinx docs/source build/docs/html -d build/docs/.doctrees -w logs/build_sphinx.log
                                  '''
                        }
                    }
                    post{
                        always {
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log', id: 'sphinx_build')])
                            archiveArtifacts artifacts: 'logs/build_sphinx.log', allowEmptyArchive: true

                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                def DOC_ZIP_FILENAME = "${env.PKG_NAME}-${env.PKG_VERSION}.doc.zip"
                                zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                            }
                            stash includes: 'build/docs/html/**,dist/${DOC_ZIP_FILENAME}', name: 'DOCS_ARCHIVE'
                        }
                    }
                }
            }
            post{
                cleanup{
                    cleanWs(
                        patterns: [
                                [pattern: 'build', type: 'INCLUDE'],
                            ],
                        notFailBuild: true,
                        deleteDirs: true
                        )
                }
            }
        }
        stage("Testing") {
            agent {
                dockerfile {
                    filename 'ci/docker/linux/build/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                }
            }
            failFast true
            stages{
                stage("Setting up Tests"){
                    steps{
                        timeout(3){
                            unstash "COMPILED_BINARIES"
                            unstash "DOCS_ARCHIVE"
                            sh '''mkdir -p logs
                                  mkdir -p reports
                                  '''
                        }
                    }
                }
                stage("Running Tests"){
                    parallel {
                        stage("Run Tox test") {
                            when {
                               equals expected: true, actual: params.TEST_RUN_TOX
                            }
                            stages{
                                stage("Run Tox"){

                                    steps {
                                        timeout(60){
                                            sh  (
                                                label: "Run Tox",
                                                script: "tox -e py -vv "
                                            )
                                        }
                                    }
                                    post{
                                        cleanup{
                                            cleanWs(
                                                deleteDirs: true,
                                                patterns: [
                                                    [pattern: '.tox', type: 'INCLUDE'],
                                                ]
                                            )
                                        }
                                    }
                                }

                            }
                            post{
                                always{
                                    archiveArtifacts allowEmptyArchive: true, artifacts: '.tox/py*/log/*.log,.tox/log/*.log,logs/tox_report.json'
                                }
                                cleanup{
                                    cleanWs deleteDirs: true, patterns: [
                                        [pattern: '.tox/py*/log/*.log', type: 'INCLUDE'],
                                        [pattern: '.tox/log/*.log', type: 'INCLUDE'],
                                        [pattern: 'logs/rox_report.json', type: 'INCLUDE']
                                    ]
                                }

                            }
                        }
                        stage("Run Pytest Unit Tests"){
                            steps{
                                timeout(10){
                                    sh(
                                        label: "Running pytest",
                                        script: '''mkdir -p reports/pytestcoverage
                                                   python -m pytest --junitxml=reports/pytest.xml --cov-report html:reports/pytestcoverage/  --cov-report xml:reports/coverage.xml --cov=uiucprescon --integration --cov-config=setup.cfg
                                                   '''
                                    )
                                }
                            }
                            post {
                                always {
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/pytestcoverage", reportFiles: 'index.html', reportName: 'Coverage.py', reportTitles: ''])
                                    junit "reports/pytest.xml"
                                    publishCoverage(
                                        adapters: [
                                            coberturaAdapter('reports/coverage.xml')
                                        ],
                                        sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                                    )

                                }
                            }
                        }
                        stage("Run Doctest Tests"){
                            steps {
                                timeout(3){
                                    sh "python -m sphinx -b doctest docs/source build/docs -d build/docs/doctrees -w logs/doctest_warnings.log"
                                }
                            }
                            post{
                                always {
                                    recordIssues(tools: [sphinxBuild(name: 'Doctest', pattern: 'logs/doctest_warnings.log', id: 'doctest')])
                                }
                            }
                        }
                        stage("Run Flake8 Static Analysis") {
                            steps{
                                timeout(2){
                                    catchError(buildResult: "SUCCESS", message: 'Flake8 found issues', stageResult: "UNSTABLE") {
                                        sh(
                                            label: "Running Flake8",
                                            script: "flake8 uiucprescon --tee --output-file logs/flake8.log"
                                        )
                                    }
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                }
                            }
                        }
                        stage("Run MyPy Static Analysis") {
                            steps{
                                timeout(3){
                                    sh(
                                        label: "Running MyPy",
                                        script: """stubgen uiucprescon -o mypy_stubs
                                                   mkdir -p reports/mypy/html
                                                   MYPYPATH="${WORKSPACE}/mypy_stubs" mypy -p uiucprescon --cache-dir=nul --html-report reports/mypy/html > logs/mypy.log
                                                   """
                                    )
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/mypy/html/", reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true, patterns: [
                                            [pattern: '.eggs', type: 'INCLUDE'],
                                            [pattern: '*egg-info', type: 'INCLUDE'],
                                            [pattern: 'mypy_stubs', type: 'INCLUDE'],
                                            [pattern: 'reports', type: 'INCLUDE'],
                                            [pattern: 'build', type: 'INCLUDE']
                                        ]
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
        stage("Python packaging"){
            stages{
                stage("Build sdist"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                        }
                    }
                    steps {
                        sh "python setup.py sdist -d dist --format zip"
                    }
                    post{
                        always{
                            stash includes: 'dist/*.zip,dist/*.tar.gz', name: "sdist"
                        }
                    }
                }
                stage("Testing Packages"){
                    matrix{
                        axes {
                            axis {
                                name 'PYTHON_VERSION'
                                values(
                                    '3.6',
                                    '3.7',
                                    '3.8'
                                )
                            }
                            axis {
                                name 'PLATFORM'
                                values(
                                    "windows",
                                    "linux"
                                )
                            }
                        }
                        stages {
                            stage("Testing sdist package"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test['sdist'].dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test['sdist'].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                steps{
                                    catchError(stageResult: 'FAILURE') {
                                        unstash "sdist"
                                        test_pkg("dist/**/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex['sdist']}", 20)
                                    }
                                }
                            }
                            stage("Building Wheel"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.package.dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.package.dockerfile.additionalBuildArgs}"
                                     }
                                }
                                steps{
                                    script{
                                        if(isUnix()){
                                            sh(
                                                label: 'Building Python Wheel',
                                                script: "python setup.py build -b build build_ext bdist_wheel -d ./dist"
                                            )
                                        } else {
                                            bat(
                                                label: 'Building Python Wheel',
                                                script: "python setup.py build -b build build_ext bdist_wheel -d .\\dist"
                                            )
                                        }
                                    }
                                }
                                post {
                                    always{
                                        stash includes: "dist/*.whl", name: "whl ${PYTHON_VERSION}-${PLATFORM}"
                                    }
                                    success{
                                        script{
                                            if(!isUnix()){
                                                findFiles(excludes: '', glob: '**/*.pyd').each{
                                                    bat(
                                                        label: "Scanning dll dependencies of ${it.name}",
                                                        script:"dumpbin /DEPENDENTS ${it.path}"
                                                        )
                                                }
                                            }
                                        }
                                    }
                                    cleanup{
                                        cleanWs(
                                                deleteDirs: true,
                                                patterns: [
                                                    [pattern: 'dist', type: 'INCLUDE'],
                                                    [pattern: 'build', type: 'INCLUDE']
                                                ]
                                            )
                                    }
                                }
                            }
                            stage("Create manylinux wheel"){
                                agent {
                                  docker {
                                    image 'quay.io/pypa/manylinux2014_x86_64'
                                    label 'linux && docker'
                                  }
                                }
                                when{
                                    equals expected: "linux", actual: PLATFORM
                                    beforeAgent true
                                }
                                steps{
                                    unstash "whl ${PYTHON_VERSION}-${PLATFORM}"
                                    sh "auditwheel repair ./dist/*.whl -w ./dist"
                                }
                                post{
                                    always{
                                        stash includes: 'dist/*manylinux*.whl', name: "whl ${PYTHON_VERSION}-manylinux"
                                    }
                                    success{
                                        archiveArtifacts(
                                            artifacts: "dist/*manylinux*.whl",
                                            fingerprint: true
                                        )
                                    }
                                }
                            }
                            stage("Testing Package"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test['whl'].dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test['whl'].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                steps{
                                    script{
                                        if( PLATFORM == "linux"){
                                            unstash "whl ${PYTHON_VERSION}-manylinux"
                                        } else{
                                            unstash "whl ${PYTHON_VERSION}-${PLATFORM}"
                                        }
                                        test_pkg("dist/**/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex['whl']}", 20)
                                    }
                                }
                                post{
                                    success{
                                        archiveArtifacts allowEmptyArchive: true, artifacts: "dist/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex['whl']}"
                                    }
                                    cleanup{
                                        cleanWs(
                                            notFailBuild: true,
                                            deleteDirs: true,
                                            patterns: [
                                                    [pattern: 'dist', type: 'INCLUDE'],
                                                    [pattern: 'build', type: 'INCLUDE'],
                                                    [pattern: '.tox', type: 'INCLUDE'],
                                                ]
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        stage("Deploy to DevPi") {
            agent{
                label "linux && docker"
            }
            options{
                lock("uiucprescon.ocr-devpi")
            }
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            environment{
                DEVPI = credentials("DS_devpi")
                devpiStagingIndex = getDevPiStagingIndex()
            }
            stages{
                stage("Upload to DevPi Staging"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    steps {
                            unstash "whl 3.6-windows"
                            unstash "whl 3.6-manylinux"
                            unstash "whl 3.7-windows"
                            unstash "whl 3.7-manylinux"
                            unstash "whl 3.8-windows"
                            unstash "whl 3.8-manylinux"
                            unstash "sdist"
                            unstash "DOCS_ARCHIVE"
                            sh(
                                label: "Uploading to DevPi Staging",
                                script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                           devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                           devpi use /${env.DEVPI_USR}/${env.devpiStagingIndex} --clientdir ./devpi
                                           devpi upload --from-dir dist --clientdir ./devpi
                                           """
                            )
                    }
                    post{
                        cleanup{
                            cleanWs(
                                notFailBuild: true
                            )
                        }
                    }
                }
                stage("Test DevPi packages") {
                    matrix{
                        axes {
                            axis {
                                name 'PYTHON_VERSION'
                                values(
                                    '3.6',
                                    '3.7',
                                    '3.8'
                                )
                            }
                            axis {
                                name 'PLATFORM'
                                values(
                                    "windows",
                                    "linux"
                                )
                            }
                            axis {
                                name 'FORMAT'
                                values(
                                    "sdist",
                                    "wheel"
                                )
                            }
                        }
                        stages {
                            stage("Testing Package on DevPi Server"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi[FORMAT].dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi[FORMAT].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                steps{
                                    unstash "DIST-INFO"
                                    script{
                                        def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"

                                        if(isUnix()){
                                            sh(
                                                label: "Running tests on Packages on DevPi",
                                                script: """python --version
                                                           devpi use https://devpi.library.illinois.edu --clientdir certs
                                                           devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir certs
                                                           devpi use ${env.devpiStagingIndex} --clientdir certs
                                                           devpi test --index ${env.devpiStagingIndex} ${props.Name}==${props.Version} -s ${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].devpiSelector[FORMAT]} --clientdir certs -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v
                                                           """
                                            )
                                        } else {
                                            bat(
                                                label: "Running tests on Packages on DevPi",
                                                script: """python --version
                                                           devpi use https://devpi.library.illinois.edu --clientdir certs\\
                                                           devpi login %DEVPI_USR% --password %DEVPI_PSW% --clientdir certs\\
                                                           devpi use ${env.devpiStagingIndex} --clientdir certs\\
                                                           devpi test --index ${env.devpiStagingIndex} ${props.Name}==${props.Version} -s ${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].devpiSelector[FORMAT]} --clientdir certs\\ -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v
                                                           """
                                            )
                                        }
                                    }
                                }
                                post {
                                    cleanup{
                                        cleanWs(
                                            deleteDirs: true,
                                            disableDeferredWipeout: true,
                                            patterns: [
                                                [pattern: '*tmp', type: 'INCLUDE'],
                                                [pattern: 'certs', type: 'INCLUDE'],
                                                [pattern: 'uiucprescon.ocr.dist-info', type: 'INCLUDE'],
                                            ]
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            anyOf {
                                branch "master"
                                tag "*"
                            }
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                      timeout(time: 1, unit: 'DAYS')
                    }
                    input {
                      message 'Release to DevPi Production?'
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                        }
                    }
                    steps {
                        script {
                            unstash "DIST-INFO"
                            def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"
                            sh(
                                label: "Pushing to DS_Jenkins/${env.BRANCH_NAME} index",
                                script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                           devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                           devpi push --index DS_Jenkins/${env.devpiStagingIndex} ${props.Name}==${props.Version} production/release --clientdir ./devpi
                                           """
                            )
                        }
                    }
                }
            }
            post {
                success{
                    node('linux && docker') {
                        checkout scm
                        script{
                            docker.build("ocr:devpi.${env.BUILD_ID}",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                if (!env.TAG_NAME?.trim()){
                                    unstash "DIST-INFO"
                                    def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"
                                    sh(
                                        label: "Connecting to DevPi Server",
                                        script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                                   devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                                   devpi use /DS_Jenkins/${env.devpiStagingIndex} --clientdir ./devpi
                                                   devpi push ${props.Name}==${props.Version} DS_Jenkins/${env.BRANCH_NAME} --clientdir ./devpi
                                                   """
                                    )
                                }
                            }
                        }
                    }
                }
                cleanup{
                    node('linux && docker') {
                       script{
                            docker.build("ocr:devpi.${env.BUILD_ID}",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"
                                sh(
                                label: "Connecting to DevPi Server",
                                script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                           devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                           devpi use /DS_Jenkins/${env.devpiStagingIndex} --clientdir ./devpi
                                           devpi remove -y ${props.Name}==${props.Version} --clientdir ./devpi
                                           """
                               )
                            }
                       }
                    }
                }
            }
        }
        stage("Deploy"){
            parallel{
                stage("Tagging git Commit"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                        }
                    }
                    when{
                        allOf{
                            equals expected: true, actual: params.DEPLOY_ADD_TAG
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                        timeout(time: 1, unit: 'DAYS')
                        retry(3)
                    }
                    input {
                          message 'Add a version tag to git commit?'
                          parameters {
                                credentials credentialType: 'com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl', defaultValue: 'github.com', description: '', name: 'gitCreds', required: true
                          }
                    }
                    steps{
                        unstash "DIST-INFO"
                        script{
                            def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"
                            def commitTag = input message: 'git commit', parameters: [string(defaultValue: "v${props.Version}", description: 'Version to use a a git tag', name: 'Tag', trim: false)]
                            withCredentials([usernamePassword(credentialsId: gitCreds, passwordVariable: 'password', usernameVariable: 'username')]) {
                                sh(label: "Tagging ${commitTag}",
                                   script: """git config --local credential.helper "!f() { echo username=\\$username; echo password=\\$password; }; f"
                                              git tag -a ${commitTag} -m 'Tagged by Jenkins'
                                              git push origin --tags
                                   """
                                )
                            }
                        }
                    }
                    post{
                        cleanup{
                            deleteDir()
                        }
                    }
                }
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                        beforeAgent true
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                        }
                    }
                    environment{
                        PKG_NAME = get_package_name("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA")
                    }
                    steps{
                        unstash "DOCS_ARCHIVE"
                        deploy_docs(env.PKG_NAME, "build/docs/html")
                    }
                }
            }
        }
    }
}
