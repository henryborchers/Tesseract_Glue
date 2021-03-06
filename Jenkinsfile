def getDevPiStagingIndex(){

    if (env.TAG_NAME?.trim()){
        return "tag_staging"
    } else{
        return "${env.BRANCH_NAME}_staging"
    }
}

SONARQUBE_CREDENTIAL_ID = 'sonarcloud-uiucprescon.ocr'
SUPPORTED_MAC_VERSIONS = ['3.8', '3.9']
SUPPORTED_LINUX_VERSIONS = ['3.6', '3.7', '3.8', '3.9']
SUPPORTED_WINDOWS_VERSIONS = ['3.6', '3.7', '3.8', '3.9']

def DEVPI_CONFIG = [
    stagingIndex: getDevPiStagingIndex(),
    server: 'https://devpi.library.illinois.edu',
    credentialsId: 'DS_devpi',
]

def get_sonarqube_unresolved_issues(report_task_file){
    script{

        def props = readProperties  file: '.scannerwork/report-task.txt'
        def response = httpRequest url : props['serverUrl'] + "/api/issues/search?componentKeys=" + props['projectKey'] + "&resolved=no"
        def outstandingIssues = readJSON text: response.content
        return outstandingIssues
    }
}

def sonarcloudSubmit(metadataFile, outputJson, sonarCredentials){
    def props = readProperties interpolate: true, file: metadataFile
    withSonarQubeEnv(installationName:"sonarcloud", credentialsId: sonarCredentials) {
        if (env.CHANGE_ID){
            sh(
                label: "Running Sonar Scanner",
                script:"sonar-scanner -Dsonar.projectVersion=${props.Version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.pullrequest.key=${env.CHANGE_ID} -Dsonar.pullrequest.base=${env.CHANGE_TARGET} -Dsonar.cfamily.cache.enabled=false -Dsonar.cfamily.threads=\$(grep -c ^processor /proc/cpuinfo) -Dsonar.cfamily.build-wrapper-output=build/build_wrapper_output_directory"
                )
        } else {
            sh(
                label: "Running Sonar Scanner",
                script: "sonar-scanner -Dsonar.projectVersion=${props.Version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.branch.name=${env.BRANCH_NAME} -Dsonar.cfamily.cache.enabled=false -Dsonar.cfamily.threads=\$(grep -c ^processor /proc/cpuinfo) -Dsonar.cfamily.build-wrapper-output=build/build_wrapper_output_directory"
                )
        }
    }
     timeout(time: 1, unit: 'HOURS') {
         def sonarqube_result = waitForQualityGate(abortPipeline: false)
         if (sonarqube_result.status != 'OK') {
             unstable "SonarQube quality gate: ${sonarqube_result.status}"
         }
         def outstandingIssues = get_sonarqube_unresolved_issues(".scannerwork/report-task.txt")
         writeJSON file: outputJson, json: outstandingIssues
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

wheelStashes = []
configurations = loadConfigs()
def loadConfigs(){
    node(){
        echo "loading configurations"
        checkout scm
        return load("ci/jenkins/scripts/configs.groovy").getConfigurations()
    }
}


def test_pkg(glob, timeout_time){

    findFiles( glob: glob).each{
        cleanWs(
            deleteDirs: true,
            disableDeferredWipeout: true,
            patterns: [
                [pattern: 'dist/', type: 'EXCLUDE'],
                [pattern: 'tests/', type: 'EXCLUDE'],
                [pattern: 'tox.ini', type: 'EXCLUDE'],
                [pattern: 'setup.cfg', type: 'EXCLUDE'],
            ]
        )
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

def getMacDevpiName(pythonVersion, format){
    if(format == "wheel"){
        return "${pythonVersion.replace('.','')}-*macosx*.*whl"
    } else if(format == "sdist"){
        return "tar.gz"
    } else{
        error "unknown format ${format}"
    }
}
def run_tox_envs(){
    script {
        def cmds
        def envs
        if(isUnix()){
            envs = sh(returnStdout: true, script: "tox -l").trim().split('\n')
            cmds = envs.collectEntries({ tox_env ->
                [tox_env, {
                    sh( label: "Running Tox with ${tox_env} environment", script: "tox  -vv -e $tox_env --parallel--safe-build")
                }]
            })
        } else{
            envs = bat(returnStdout: true, script: "@tox -l").trim().split('\n')
            cmds = envs.collectEntries({ tox_env ->
                [tox_env, {
                    bat( label: "Running Tox with ${tox_env} environment", script: "tox  -vv -e $tox_env")
                }]
            })
        }
        echo "Setting up tox tests for ${envs.join(', ')}"
        parallel(cmds)
    }
}
defaultParameterValues = [
    USE_SONARQUBE: false
]

def get_props(){
    stage("Reading Package Metadata"){
        node() {
            try{
                unstash "DIST-INFO"
                def metadataFile = findFiles(excludes: '', glob: '*.dist-info/METADATA')[0]
                def package_metadata = readProperties interpolate: true, file: metadataFile.path
                echo """Metadata:

    Name      ${package_metadata.Name}
    Version   ${package_metadata.Version}
    """
                return package_metadata
            } finally {
                cleanWs(
                    patterns: [
                            [pattern: '*.dist-info/**', type: 'INCLUDE'],
                        ],
                    notFailBuild: true,
                    deleteDirs: true
                )
            }
        }
    }
}
def startup(){
    def SONARQUBE_CREDENTIAL_ID = SONARQUBE_CREDENTIAL_ID
    node(){
        checkout scm
//         tox = load("ci/jenkins/scripts/tox.groovy")
        mac = load("ci/jenkins/scripts/mac.groovy")
        devpi = load("ci/jenkins/scripts/devpi.groovy")
    }
    parallel(
        [
            failFast: true,
            'Checking sonarqube Settings': {
                node(){
                    try{
                        withCredentials([string(credentialsId: SONARQUBE_CREDENTIAL_ID, variable: 'dddd')]) {
                            echo 'Found credentials for sonarqube'
                        }
                        defaultParameterValues.USE_SONARQUBE = true
                    } catch(e){
                        echo "Setting defaultValue for USE_SONARQUBE to false. Reason: ${e}"
                        defaultParameterValues.USE_SONARQUBE = false
                    }
                }
            },
            'Getting Distribution Info': {
                node('linux && docker') {
                    timeout(2){
                        ws{
                            checkout scm
                            try{
                                docker.image('python:3.8').inside {
                                    sh(
                                       label: "Running setup.py with dist_info",
                                       script: """python --version
                                                  python setup.py dist_info
                                               """
                                    )
                                    stash includes: "*.dist-info/**", name: 'DIST-INFO'
                                    archiveArtifacts artifacts: "*.dist-info/**"
                                }
                            } finally{
                                cleanWs(
                                    patterns: [
                                            [pattern: '*.dist-info/**', type: 'INCLUDE'],
                                            [pattern: '.eggs/', type: 'INCLUDE'],
                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                        ],
                                    notFailBuild: true,
                                    deleteDirs: true
                                    )
                            }
                        }
                    }
                }
            }
        ]
    )
}
startup()
props = get_props()
pipeline {
    agent none
    options {
        timeout(time: 1, unit: 'DAYS')
    }
    parameters {
        booleanParam(name: "RUN_CHECKS", defaultValue: true, description: "Run checks on code")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "USE_SONARQUBE", defaultValue: defaultParameterValues.USE_SONARQUBE, description: "Send data test data to SonarQube")
        booleanParam(name: "BUILD_PACKAGES", defaultValue: false, description: "Build Python packages")
        booleanParam(name: "BUILD_MAC_PACKAGES", defaultValue: false, description: "Test Python packages on Mac")
        booleanParam(name: "TEST_PACKAGES", defaultValue: true, description: "Test Python packages by installing them and running tests on the installed package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
    }
    stages {
        stage("Building") {
            agent {
                dockerfile {
                    filename 'ci/docker/linux/build/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                }
            }
            stages{
                stage("Building Python Package"){
                    steps {
                        timeout(20){
                            tee("logs/python_build.log"){
                                sh(
                                    label: "Build python package",
                                    script: 'CFLAGS="--coverage -fprofile-arcs -ftest-coverage" LFLAGS="-lgcov --coverage" python setup.py build -b build --build-lib build/lib/ build_ext -j $(grep -c ^processor /proc/cpuinfo) --inplace'
                                )
                            }
                        }
                    }
                    post{
                        always{
                            stash includes: 'uiucprescon/**/*.dll,uiucprescon/**/*.pyd,uiucprescon/**/*.exe,uiucprescon/**/*.so,build/**', name: "COMPILED_BINARIES"
                            recordIssues(filters: [excludeFile('build/*'), excludeFile('conan/*'), ], tools: [gcc(pattern: 'logs/python_build.log')])
                        }
                    }
                }
                stage("Building Documentation"){
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

                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                echo "props = ${props}"
                                def DOC_ZIP_FILENAME = "${props.Name}-${props.Version}.doc.zip"
                                zip archive: true, dir: "build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                                stash includes: "dist/${DOC_ZIP_FILENAME},build/docs/html/**", name: 'DOCS_ARCHIVE'
                            }
                        }
                    }
                }
            }
            post{
                cleanup{
                    cleanWs(
                        patterns: [
                                [pattern: 'build/', type: 'INCLUDE'],
                                [pattern: 'logs/', type: 'INCLUDE'],
                            ],
                        notFailBuild: true,
                        deleteDirs: true
                        )
                }
            }
        }
        stage("Checks"){
            when{
                equals expected: true, actual: params.RUN_CHECKS
            }
            stages{
                stage("Code Quality") {
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                            args '--mount source=sonar-cache-ocr,target=/opt/sonar/.sonar/cache'
                        }
                    }
                    stages{
                        stage("Setting up Tests"){
                            parallel{
                                stage('Setting Up C++ Tests'){
                                    steps{
                                        sh(
                                            label: "Running conan",
                                            script: 'conan install . -if build/cpp -g cmake_find_package'
                                        )
                                        sh(
                                            label: "Running Build wrapper",
                                            script: '''cmake -B ./build/cpp -S ./ -D CMAKE_C_FLAGS="-Wall -Wextra -fprofile-arcs -ftest-coverage" -D CMAKE_CXX_FLAGS="-Wall -Wextra -fprofile-arcs -ftest-coverage" -DBUILD_TESTING:BOOL=ON -D CMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_OUTPUT_EXTENSION_REPLACE:BOOL=ON -DCMAKE_MODULE_PATH=./build/cpp
                                                       make -C build/cpp clean tester
                                                       '''
                                        )
                                    }
                                }
                                stage('Setting Up Python Tests'){
                                    steps{
                                        timeout(3){
                                            sh(
                                                label: "Build python package",
                                                script: '''mkdir -p build/python
                                                           CFLAGS="--coverage -fprofile-arcs -ftest-coverage" LFLAGS="-lgcov --coverage" build-wrapper-linux-x86-64 --out-dir build/build_wrapper_output_directory  python setup.py build -b build/python --build-lib build/python/lib/ build_ext -j $(grep -c ^processor /proc/cpuinfo) --inplace --debug
                                                           '''
                                            )
                                            unstash "DOCS_ARCHIVE"
                                            sh '''mkdir -p logs
                                                  mkdir -p reports
                                                  '''
                                        }
                                    }
                                }
                            }
                        }
                        stage("Running Tests"){
                            parallel {
                                stage("Run Pytest Unit Tests"){
                                    steps{
                                        timeout(10){
                                            sh(
                                                label: "Running pytest",
                                                script: '''mkdir -p reports/pytestcoverage
                                                           coverage run --parallel-mode --source=uiucprescon -m pytest --junitxml=./reports/pytest/junit-pytest.xml --basetemp=/tmp/pytest
                                                           '''
                                            )
                                        }
                                    }
                                    post {
                                        always {
                                            junit "reports/pytest/junit-pytest.xml"
                                            stash includes: "reports/pytest/junit-pytest.xml", name: 'PYTEST_REPORT'

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
                                stage("C++ Tests") {
                                    steps{
                                        sh(
                                            label: "Running CTest",
                                            script: "cd build/cpp && ctest --output-on-failure --no-compress-output -T Test",
                                            returnStatus: true
                                        )

                                        sh(
                                            label: "Running cpp tests",
                                            script: "build/cpp/tests/tester -r sonarqube -o reports/test-cpp.xml"
                                        )
                                    }
                                    post{
                                        always{
                                            xunit(
                                                testTimeMargin: '3000',
                                                thresholdMode: 1,
                                                thresholds: [
                                                    failed(),
                                                    skipped()
                                                ],
                                                tools: [
                                                    CTest(
                                                        deleteOutputFiles: true,
                                                        failIfNotNew: true,
                                                        pattern: "build/cpp/Testing/**/*.xml",
                                                        skipNoTestFiles: true,
                                                        stopProcessingIfError: true
                                                    )
                                                ]
                                            )
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
                                            stash includes: "logs/flake8.log", name: 'FLAKE8_REPORT'
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
                                    }
                                }
                                stage("Run Pylint Static Analysis") {
                                    steps{
                                        catchError(buildResult: 'SUCCESS', message: 'Pylint found issues', stageResult: 'UNSTABLE') {
                                            sh(label: "Running pylint",
                                                script: '''mkdir -p logs
                                                           mkdir -p reports
                                                           pylint uiucprescon -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --persistent=no > reports/pylint.txt
                                                           '''

                                            )
                                        }
                                        sh(
                                            script: 'pylint   -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --persistent=no > reports/pylint_issues.txt',
                                            label: "Running pylint for sonarqube",
                                            returnStatus: true
                                        )
                                    }
                                    post{
                                        always{
                                            recordIssues(tools: [pyLint(pattern: 'reports/pylint.txt')])
                                            stash includes: "reports/pylint_issues.txt,reports/pylint.txt", name: 'PYLINT_REPORT'
                                        }
                                    }
                                }
                            }
                            post{
                                always{
                                    sh "mkdir -p build/coverage"
                                    sh "find ./build -name '*.gcno' -exec gcov {} -p --source-prefix=${WORKSPACE}/ \\;"
                                    sh "mv *.gcov build/coverage/"
                                    sh(script:'''coverage combine
                                                 coverage xml -o ./reports/coverage-python.xml
                                                 gcovr --filter uiucprescon/ocr --print-summary --keep --xml -o reports/coverage_cpp.xml
                                                 gcovr --filter uiucprescon/ocr --print-summary --keep
                                                 '''
                                        )
                                    archiveArtifacts artifacts: '**/*.gcov'
                                    stash includes: "reports/coverage*.xml", name: 'COVERAGE_REPORT'
                                    publishCoverage(
                                        adapters: [
                                            coberturaAdapter(mergeToOneReport: true, path: 'reports/coverage*.xml')
                                        ],
                                        sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                                    )
                                }
                            }
                        }
                        stage("Sonarcloud Analysis"){
                            options{
                                lock("uiucprescon.ocr-sonarcloud")
                            }
                            when{
                                equals expected: true, actual: params.USE_SONARQUBE
                                beforeAgent true
                                beforeOptions true
                            }
                            steps{
                                unstash "COVERAGE_REPORT"
                                unstash "PYTEST_REPORT"
                // //                 unstash "BANDIT_REPORT"
                                unstash "PYLINT_REPORT"
                                unstash "FLAKE8_REPORT"
                                unstash "DIST-INFO"
                                sonarcloudSubmit("uiucprescon.ocr.dist-info/METADATA", "reports/sonar-report.json", 'sonarcloud-uiucprescon.ocr')
                            }
                            post {
                                always{
                                   recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                                }
                                failure{
                                    sh "ls -R"
                                }
                            }
                        }
                    }

                }
                stage("Run Tox test") {
                    when {
                       equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    steps {
                        script{
                            def tox
                            node(){
                                checkout scm
                                tox = load("ci/jenkins/scripts/tox.groovy")
                            }
                            def windowsJobs = [:]
                            def linuxJobs = [:]
                            stage("Scanning Tox Environments"){
                                parallel(
                                    "Linux":{
                                        linuxJobs = tox.getToxTestsParallel(
                                                envNamePrefix: "Tox Linux",
                                                label: "linux && docker",
                                                dockerfile: 'ci/docker/linux/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            )
                                    },
                                    "Windows":{
                                        windowsJobs = tox.getToxTestsParallel(
                                                envNamePrefix: "Tox Windows",
                                                label: "windows && docker",
                                                dockerfile: 'ci/docker/windows/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                         )
                                    },
                                    failFast: true
                                )
                            }
                            parallel(windowsJobs + linuxJobs)
                        }
                    }
                }

            }
        }
        stage("Python Packaging"){
            when{
                anyOf{
                    equals expected: true, actual: params.BUILD_PACKAGES
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                }
                beforeAgent true
            }
            stages{
                stage('Building'){
                    steps{
                        script{
                            def packages
                            node(){
                                checkout scm
                                packages = load 'ci/jenkins/scripts/packaging.groovy'
                            }
                            def macBuildStages = [:]
                            SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
                                macBuildStages["MacOS - Python ${pythonVersion}: wheel"] = {
                                    packages.buildPkg(
                                        agent: [
                                            label: "mac && python${pythonVersion}",
                                        ],
                                        buildCmd: {
                                            sh "python${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                stash includes: 'dist/*.whl', name: "python${pythonVersion} mac wheel"
                                                wheelStashes << "python${pythonVersion} mac wheel"
                                            }
                                        ]
                                    )
                                }
                            }
                            def windowsBuildStages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
                                windowsBuildStages["Windows - Python ${pythonVersion}: wheel"] = {
                                    packages.buildPkg(
                                        agent: [
                                            dockerfile: [
                                                label: 'windows && docker',
                                                filename: 'ci/docker/windows/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                            ]
                                        ],
                                        buildCmd: {
                                            bat "py -${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                stash includes: 'dist/*.whl', name: "python${pythonVersion} windows wheel"
                                                wheelStashes << "python${pythonVersion} windows wheel"
                                            }
                                        ]
                                    )
                                }
                            }
                            def buildStages =  [
                               failFast: true,
                                'Source Distribution': {
                                    packages.buildPkg(
                                        agent: [
                                            dockerfile: [
                                                label: 'linux && docker',
                                                filename: 'ci/docker/linux/package/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            ]
                                        ],
                                        buildCmd: {
                                            sh "python3 -m pep517.build --source --out-dir dist/ ."
                                        },
                                        post:[
                                            success: {
                                                stash includes: 'dist/*.tar.gz,dist/*.zip', name: 'python sdist'
                                                wheelStashes << 'python sdist'
                                                archiveArtifacts artifacts: 'dist/*.tar.gz,dist/*.zip'
                                            },
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            failure: {
                                                sh "python3 -m pip list"
                                            }
                                        ]
                                    )
                                }
                            ]
                            def linuxBuildStages = [:]
                            SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
                                linuxBuildStages["Linux - Python ${pythonVersion}: wheel"] = {
                                    packages.buildPkg(
                                        agent: [
                                            dockerfile: [
                                                label: 'linux && docker',
                                                filename: 'ci/docker/linux/package/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            ]
                                        ],
                                        buildCmd: {
                                            sh(label: "Building python wheel",
                                               script:"""python${pythonVersion} -m pip wheel --no-deps -w ./dist .
                                                         auditwheel repair ./dist/*.whl -w ./dist
                                                         """
                                               )
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                stash includes: 'dist/*manylinux*.*whl', name: "python${pythonVersion} linux wheel"
                                                wheelStashes << "python${pythonVersion} linux wheel"
                                            }
                                        ]
                                    )
                                }
                            }
                            buildStages = buildStages + windowsBuildStages + linuxBuildStages
                            if(params.BUILD_MAC_PACKAGES == true){
                                buildStages = buildStages + macBuildStages
                            }
                            parallel(buildStages)
                        }

                    }
                }
                stage("Testing"){
                    when{
                        equals expected: true, actual: params.TEST_PACKAGES
                    }
                    steps{
                        script{
                            def packages
                            node(){
                                checkout scm
                                packages = load 'ci/jenkins/scripts/packaging.groovy'
                            }
                            def macTestStages = [:]
                            SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
                                macTestStages["MacOS - Python ${pythonVersion}: wheel"] = {
                                    packages.testPkg2(
                                        agent: [
                                            label: "mac && python${pythonVersion}",
                                        ],
                                        testSetup: {
                                            checkout scm
                                            unstash "python${pythonVersion} mac wheel"
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.whl').each{
                                                sh(label: "Running Tox",
                                                   script: """python${pythonVersion} -m venv venv
                                                   ./venv/bin/python -m pip install --upgrade pip
                                                   ./venv/bin/pip install tox
                                                   ./venv/bin/tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"""
                                                )
                                            }

                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '.tox/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                 archiveArtifacts artifacts: 'dist/*.whl'
                                            }
                                        ]
                                    )
                                }
                                macTestStages["MacOS - Python ${pythonVersion}: sdist"] = {
                                    packages.testPkg2(
                                        agent: [
                                            label: "mac && python${pythonVersion}",
                                        ],
                                        testSetup: {
                                            checkout scm
                                            unstash 'python sdist'
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.tar.gz').each{
                                                sh(label: "Running Tox",
                                                   script: """python${pythonVersion} -m venv venv
                                                   ./venv/bin/python -m pip install --upgrade pip
                                                   ./venv/bin/pip install tox
                                                   ./venv/bin/tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"""
                                                )
                                            }

                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '.tox/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                        ]
                                    )
                                }
                            }
                            def windowsTestStages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
                                windowsTestStages["Windows - Python ${pythonVersion}: wheel"] = {
                                    packages.testPkg2(
                                        agent: [
                                            dockerfile: [
                                                label: 'windows && docker',
                                                filename: 'ci/docker/windows/tox_no_vs/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                            ]
                                        ],
                                        dockerImageName: "${currentBuild.fullProjectName}_test_no_msvc".replaceAll("-", "_").replaceAll('/', "_").replaceAll(' ', "").toLowerCase(),
                                        testSetup: {
                                             checkout scm
                                             unstash "python${pythonVersion} windows wheel"
                                        },
                                        testCommand: {
                                             findFiles(glob: 'dist/*.whl').each{
                                                 powershell(label: "Running Tox", script: "tox --installpkg ${it.path} --workdir \$env:TEMP\\tox  -e py${pythonVersion.replace('.', '')}")
                                             }

                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                archiveArtifacts artifacts: 'dist/*.whl'
                                            }
                                        ]
                                    )
                                }
                                windowsTestStages["Windows - Python ${pythonVersion}: sdist"] = {
                                    packages.testPkg2(
                                        agent: [
                                            dockerfile: [
                                                label: 'windows && docker',
                                                filename: 'ci/docker/windows/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                            ]
                                        ],
                                        dockerImageName: "${currentBuild.fullProjectName}_test_with_msvc".replaceAll("-", "_").replaceAll('/', "_").replaceAll(' ', "").toLowerCase(),
                                        testSetup: {
                                            checkout scm
                                            unstash 'python sdist'
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.tar.gz').each{
                                                bat(label: "Running Tox", script: "tox --workdir %TEMP%\\tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}")
                                            }
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                        ]
                                    )
                                }
                            }
                            def linuxTestStages = [:]
                            SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
                                linuxTestStages["Linux - Python ${pythonVersion}: wheel"] = {
                                    packages.testPkg2(
                                        agent: [
                                            dockerfile: [
                                                label: 'linux && docker',
                                                filename: 'ci/docker/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            ]
                                        ],
                                        testSetup: {
                                            checkout scm
                                            unstash "python${pythonVersion} linux wheel"
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.whl').each{
                                                timeout(5){
                                                    sh(
                                                        label: 'Running Tox',
                                                        script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')}"
                                                        )
                                                }
                                            }
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                archiveArtifacts artifacts: 'dist/*.whl'
                                            },
                                        ]
                                    )
                                }
                                linuxTestStages["Linux - Python ${pythonVersion}: sdist"] = {
                                    packages.testPkg2(
                                        agent: [
                                            dockerfile: [
                                                label: 'linux && docker',
                                                filename: 'ci/docker/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            ]
                                        ],
                                        testSetup: {
                                            checkout scm
                                            unstash "python sdist"
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.tar.gz').each{
                                                sh(
                                                    label: 'Running Tox',
                                                    script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')}"
                                                    )
                                            }
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                        ]
                                    )
                                }

                            }

                            def testingStages = windowsTestStages + linuxTestStages
                            if(params.BUILD_MAC_PACKAGES == true){
                                testingStages = testingStages + macTestStages
                            }
                            parallel(testingStages)
                        }
                    }
                }
            }
        }
        stage("Deploy to DevPi") {
            agent none
            options{
                lock("uiucprescon.ocr-devpi")
            }
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                        tag "*"
                    }
                }
                beforeAgent true
                beforeOptions true
            }
            environment{
                devpiStagingIndex = getDevPiStagingIndex()
            }
            stages{
                stage("Upload to DevPi Staging"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/tox/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                          }
                    }
                    options{
                        retry(3)
                    }
                    steps {
                        script{
                            unstash "DOCS_ARCHIVE"
                            wheelStashes.each{
                                unstash it
                            }
                            devpi.upload(
                                server: "https://devpi.library.illinois.edu",
                                credentialsId: "DS_devpi",
                                index: getDevPiStagingIndex(),
                                clientDir: "./devpi"
                            )
                        }
                    }
                    post{
                        cleanup{
                            cleanWs(
                                notFailBuild: true
                            )
                        }
                    }
                }
                stage('Test DevPi packages') {
                    steps{
                        script{
                            def macPackages = [:]
                            SUPPORTED_MAC_VERSIONS.each{pythonVersion ->
                                macPackages["MacOS - Python ${pythonVersion}: wheel"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            label: "mac && python${pythonVersion}"
                                        ],
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                            devpiExec: 'venv/bin/devpi'
                                        ],
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: getMacDevpiName(pythonVersion, 'wheel'),
                                        ],
                                        test:[
                                            setup: {
                                                sh(
                                                    label:'Installing Devpi client',
                                                    script: '''python3 -m venv venv
                                                                venv/bin/python -m pip install pip --upgrade
                                                                venv/bin/python -m pip install devpi_client
                                                                '''
                                                )
                                            },
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                            teardown: {
                                                sh( label: 'Remove Devpi client', script: 'rm -r venv')
                                            }
                                        ]
                                    )
                                }
                                macPackages["MacOS - Python ${pythonVersion}: sdist"]= {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            label: "mac && python${pythonVersion}"
                                        ],
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                            devpiExec: 'venv/bin/devpi'
                                        ],
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'tar.gz'
                                        ],
                                        test:[
                                            setup: {
                                                sh(
                                                    label:'Installing Devpi client',
                                                    script: '''python3 -m venv venv
                                                                venv/bin/python -m pip install pip --upgrade
                                                                venv/bin/python -m pip install devpi_client
                                                                '''
                                                )
                                            },
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                            teardown: {
                                                sh( label: 'Remove Devpi client', script: 'rm -r venv')
                                            }
                                        ]
                                    )
                                }
                            }

                            def windowsPackages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{pythonVersion ->
                                windowsPackages["Windows - Python ${pythonVersion}: sdist"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/windows/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE',
                                                label: 'windows && docker'
                                            ]
                                        ],
                                        dockerImageName:  "${currentBuild.fullProjectName}_devpi_with_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', '').toLowerCase(),
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                        ],
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'tar.gz'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                                windowsPackages["Test Python ${pythonVersion}: wheel Windows"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/windows/tox_no_vs/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                                                label: 'windows && docker'
                                            ]
                                        ],
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                        ],
                                        dockerImageName:  "${currentBuild.fullProjectName}_devpi_without_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', '').toLowerCase(),
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: "(${pythonVersion.replace('.','')}).*(win_amd64\\.whl)"
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                            }
                            def linuxPackages = [:]
                            SUPPORTED_LINUX_VERSIONS.each{pythonVersion ->
                                linuxPackages["Linux - Python ${pythonVersion}: sdist"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                                                label: 'linux && docker'
                                            ]
                                        ],
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                        ],
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'tar.gz'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                                linuxPackages["Linux - Python ${pythonVersion}: wheel"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                                                label: 'linux && docker'
                                            ]
                                        ],
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                        ],
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: "(${pythonVersion.replace('.','')}).*(manylinux).*(\\.whl)"
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                            }
                            def devpiPackagesTesting = windowsPackages + linuxPackages
                            if (params.BUILD_MAC_PACKAGES){
                                 devpiPackagesTesting = devpiPackagesTesting + macPackages
                            }

                            parallel(devpiPackagesTesting)
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
                            filename 'ci/docker/linux/tox/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                        }
                    }
                    steps {
                        script{
                            echo "Pushing to production/release index"
                            devpi.pushPackageToIndex(
                                pkgName: props.Name,
                                pkgVersion: props.Version,
                                server: "https://devpi.library.illinois.edu",
                                indexSource: "DS_Jenkins/${getDevPiStagingIndex()}",
                                indexDestination: "production/release",
                                credentialsId: 'DS_devpi'
                            )
                        }
                    }
                }
            }
            post {
                success{
                    node('linux && docker') {
                        script{
                            if (!env.TAG_NAME?.trim()){
                                checkout scm
                                docker.build("ocr:devpi",'-f ./ci/docker/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                    devpi.pushPackageToIndex(
                                        pkgName: props.Name,
                                        pkgVersion: props.Version,
                                        server: "https://devpi.library.illinois.edu",
                                        indexSource: "DS_Jenkins/${getDevPiStagingIndex()}",
                                        indexDestination: "DS_Jenkins/${env.BRANCH_NAME}",
                                        credentialsId: 'DS_devpi'
                                    )
                                }
                            }
                        }
                    }
                }
                cleanup{
                    node('linux && docker') {
                        script{
                            checkout scm
                            docker.build("ocr:devpi",'-f ./ci/docker/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                devpi.removePackage(
                                    pkgName: props.Name,
                                    pkgVersion: props.Version,
                                    index: "DS_Jenkins/${getDevPiStagingIndex()}",
                                    server: "https://devpi.library.illinois.edu",
                                    credentialsId: 'DS_devpi',

                                )
                            }
                        }
                    }
                }
            }
        }
        stage("Deploy"){
            parallel{
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                        beforeAgent true
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    steps{
                        unstash "DOCS_ARCHIVE"
                        deploy_docs(props.Name, "build/docs/html")
                    }
                }
            }
        }
    }
}
