@Library(["devpi", "PythonHelpers"]) _


def remove_files(artifacts){
    script{
        def files = findFiles glob: "${artifacts}"
        files.each { file_name ->
            bat "del ${file_name}"
        }
    }
}


def remove_from_devpi(devpiExecutable, pkgName, pkgVersion, devpiIndex, devpiUsername, devpiPassword){
    script {
            try {
                bat "${devpiExecutable} login ${devpiUsername} --password ${devpiPassword}"
                bat "${devpiExecutable} use ${devpiIndex}"
                bat "${devpiExecutable} remove -y ${pkgName}==${pkgVersion}"
            } catch (Exception ex) {
                echo "Failed to remove ${pkgName}==${pkgVersion} from ${devpiIndex}"
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
def runtox(){
    // TODO: Make more generic
    script{
        try{
            bat "tox --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox -vv"
        } catch (exc) {
            bat "tox --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox --recreate -vv"
        }
    }

}


def test_wheel(pkgRegex, python_version){
    script{

        bat "python -m venv venv\\${NODE_NAME}\\${python_version} && venv\\${NODE_NAME}\\${python_version}\\Scripts\\python.exe -m pip install pip --upgrade && venv\\${NODE_NAME}\\${python_version}\\Scripts\\pip.exe install tox --upgrade"

        def python_wheel = findFiles glob: "**/${pkgRegex}"
        dir("source"){
            python_wheel.each{
                echo "Testing ${it}"
                bat "${WORKSPACE}\\venv\\${NODE_NAME}\\${python_version}\\Scripts\\tox.exe --installpkg=${WORKSPACE}\\${it} -e py${python_version}"
            }

        }


    }
}

pipeline {
    agent {
        label "Windows && VS2015 && Python3 && longfilenames"
    }

    triggers {
        cron('@daily')
    }

    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
        timeout(90)  // Timeout after 90 minutes. This shouldn't take this long but it hangs for some reason
        checkoutToSubdirectory("source")
        preserveStashes()
    }
    environment {
        PKG_NAME = pythonPackageName(toolName: "CPython-3.6")
        PKG_VERSION = pythonPackageVersion(toolName: "CPython-3.6")
        DOC_ZIP_FILENAME = "${env.PKG_NAME}-${env.PKG_VERSION}.doc.zip"
        DEVPI = credentials("DS_devpi")
        build_number = VersionNumber(projectStartDate: '2018-7-30', versionNumberString: '${BUILD_DATE_FORMATTED, "yy"}${BUILD_MONTH, XX}${BUILDS_THIS_MONTH, XX}', versionPrefix: '', worstResultForIncrement: 'SUCCESS')
        WORKON_HOME ="${WORKSPACE}\\pipenv\\"

    }
    parameters {
        booleanParam(name: "FRESH_WORKSPACE", defaultValue: false, description: "Purge workspace before staring and checking out source")
//        booleanParam(name: "BUILD_DOCS", defaultValue: true, description: "Build documentation")
        booleanParam(name: "TEST_RUN_DOCTEST", defaultValue: true, description: "Test documentation")
        booleanParam(name: "TEST_RUN_PYTEST", defaultValue: true, description: "Run PyTest unit tests")
        booleanParam(name: "TEST_RUN_FLAKE8", defaultValue: true, description: "Run Flake8 static analysis")
        booleanParam(name: "TEST_RUN_MYPY", defaultValue: true, description: "Run MyPy static analysis")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")

        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "ocr", description: 'The directory that the docs should be saved under')
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
    }
    stages {
        stage("Configure") {
            environment {
                PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
            }
            stages{
                stage("Purge all existing data in workspace"){
                    when{
                        equals expected: true, actual: params.FRESH_WORKSPACE
                    }
                    steps{
                        deleteDir()
                        dir("source"){
                            checkout scm
                        }
                    }
                }
                stage("Installing Required System Level Dependencies"){
                    steps{
                        lock("system_python_${NODE_NAME}"){
                            bat "python -m pip install pip --upgrade --quiet && python -m pip install --upgrade pipenv --quiet"
                        }
                    }
                    post{
                        success{
                            bat "(if not exist logs mkdir logs) && python.exe -m pip list > logs/pippackages_system_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }
                    }

                }
                stage("Installing Pipfile"){
                    options{
                        timeout(5)
                    }
                    steps {
                        dir("source"){
                            bat "python.exe -m pipenv install --dev --deploy && python.exe -m pipenv check && python.exe -m pipenv run pip list > ${WORKSPACE}/logs/pippackages_pipenv_${NODE_NAME}.log"
                        }
                    }
                    post{
                        success{
                            archiveArtifacts artifacts: "logs/pippackages_pipenv_${NODE_NAME}.log"
                        }
                    }
                }
                stage("Creating Virtualenv for Building"){
                    steps {
                        create_venv("python.exe", "venv\\36")
                    }
                    post{
                        success{
                            bat "venv\\36\\Scripts\\pip.exe list > logs/pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }

                    }
                }
            }
            post{
                success{
                    echo "Configured ${env.PKG_NAME}, version ${env.PKG_VERSION}, for testing."
                }
                failure {
                    deleteDir()
                }
            }

        }
        stage("Building") {

            stages{
                stage("Building Python Package"){
                    environment {
                        PATH = "${WORKSPACE}\\venv\\36\\Scripts;${tool 'cmake3.13'};${tool name: 'nasm_2_x64', type: 'com.cloudbees.jenkins.plugins.customtools.CustomTool'};$PATH"
                    }
                    steps {

                        dir("source"){

                            powershell "& python setup.py build -b ${WORKSPACE}\\build\\36 -j${env.NUMBER_OF_PROCESSORS} --build-lib ../build/36/lib build_ext --inplace | tee ${WORKSPACE}\\logs\\build.log"

                        }

//                        dir("build\\36\\lib\\tests"){
//                            bat "copy ${WORKSPACE}\\source\\tests\\*.py"
//
//                        }
//                        dir("build\\36\\lib\\tests\\feature"){
//                                bat "copy ${WORKSPACE}\\source\\tests\\feature\\*.py"
//                                bat "copy ${WORKSPACE}\\source\\tests\\feature\\*.feature"
//                        }
                    }
                    post{
                        always{
                            recordIssues(tools: [
                                    pyLint(name: 'Setuptools Build: PyLint', pattern: 'logs/build.log'),
                                    msBuild(name: 'Setuptools Build: MSBuild', pattern: 'logs/build.log')
                                ]
                                )
                            // dir("source"){
                            //     bat "tree /F /A > ${WORKSPACE}\\logs\\built_package.log"
                            // }
                            // archiveArtifacts "logs/built_package.log"
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
                        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                    }
                    steps{
                        // echo "Building docs on ${env.NODE_NAME}"
                        dir("source"){
                            bat "python -m pipenv run sphinx-build docs/source ${WORKSPACE}\\build\\docs\\html -d ${WORKSPACE}\\build\\docs\\.doctrees -w ${WORKSPACE}\\logs\\build_sphinx.log"
                        }
                    }
                    post{
                        always {
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log', id: 'sphinx_build')])
                            archiveArtifacts artifacts: 'logs/build_sphinx.log', allowEmptyArchive: true

                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${env.DOC_ZIP_FILENAME}"
                            stash includes: 'build/docs/html/**', name: 'DOCS_ARCHIVE'
                        }
                        // failure{
                        //     echo "Failed to build Python package"
                        // }
                    }
                }
            }
        }

        stage("Testing") {
            failFast true
            stages{
                stage("Installing Package Testing Tools"){
                    steps{
                        bat "venv\\36\\Scripts\\pip.exe install mypy lxml sphinx pytest flake8 pytest-cov pytest-bdd --upgrade-strategy only-if-needed && venv\\36\\Scripts\\pip.exe install \"tox>=3.7\""

                    }
                }
                stage("Running Tests"){
                    environment{
                        PYTHON_VENV_SCRIPTS_PATH = "${WORKSPACE}\\venv\\36\\Scripts"
                        PYTHON_SYSTEM_SCRIPTS_PATH = "${tool 'CPython-3.6'}\\Scripts"
                        PATH = "${env.PYTHON_VENV_SCRIPTS_PATH};${env.PYTHON_SYSTEM_SCRIPTS_PATH};${tool 'cmake3.13'};$PATH"
                    }
                    parallel {
                        stage("Run Tox test") {
                            when {
                               equals expected: true, actual: params.TEST_RUN_TOX
                            }
                            stages{
                                stage("Removing Previous Tox Environment"){
                                    when{
                                        equals expected: true, actual: params.FRESH_WORKSPACE
                                    }
                                    steps{
                                        dir(".tox"){
                                            deleteDir()
                                        }
                                    }

                                }
                                stage("Run Tox"){
                                    environment {
                                        PYTHON_VENV_SCRIPTS_PATH = "${WORKSPACE}\\venv\\venv36\\Scripts"
                                        NASM_PATH = "${tool name: 'nasm_2_x64', type: 'com.cloudbees.jenkins.plugins.customtools.CustomTool'}"
                                        PATH = "${env.PYTHON_VENV_SCRIPTS_PATH};${tool 'CPython-3.6'};${tool 'CPython-3.7'};${tool 'cmake3.13'};${env.NASM_PATH};$PATH"
                                        CL = "/MP"
                                    }

                                    steps {
                                        dir("source"){
                                            runtox()
                                        }
                                    }
                                }

                            }
                        }
                        stage("Run Pytest Unit Tests"){
                            when {
                               equals expected: true, actual: params.TEST_RUN_PYTEST
                            }
                            environment{
                                junit_filename = "junit-${env.NODE_NAME}-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                            }
                            steps{
                                dir("source"){
                                    bat "python.exe -m pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/pytestcoverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --integration --cov-config=${WORKSPACE}/source/setup.cfg"
//                                    bat "${WORKSPACE}\\venv\\36\\Scripts\\python.exe -m pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/pytestcoverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --integration --cov-config=${WORKSPACE}/source/setup.cfg"
                                }
                            }
                            post {
                                always {
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/pytestcoverage", reportFiles: 'index.html', reportName: 'Coverage.py', reportTitles: ''])
                                    junit "reports/pytest/${env.junit_filename}"
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
                            when {
                                equals expected: true, actual: params.TEST_RUN_DOCTEST
                            }
                            steps {
                                dir("source"){
                                    bat "pipenv run sphinx-build -b doctest docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees -w ${WORKSPACE}/logs/doctest_warnings.log"
                                }
                            }
                            post{
                                always {
                                    
                                    recordIssues(tools: [sphinxBuild(name: 'Doctest', pattern: 'logs/doctest_warnings.log', id: 'doctest')])
                                }
                            }
                        }
                        stage("Run Flake8 Static Analysis") {
                            when {
                                equals expected: true, actual: params.TEST_RUN_FLAKE8
                            }
                            steps{
                                dir("source"){
                                    bat returnStatus: true, script: "flake8 uiucprescon --tee --output-file ${WORKSPACE}\\logs\\flake8.log"
                                }
                            }
                            post {
                                always {
                                    // archiveArtifacts allowEmptyArchive: true, artifacts: "logs/flake8.log"
                                    recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                }
                            }
                        }
                        stage("Run MyPy Static Analysis") {
                            when {
                                equals expected: true, actual: params.TEST_RUN_MYPY
                            }
                            stages{
                                stage("Generate Stubs") {
                                    steps{
                                        dir("source"){
                                          bat "stubgen -p uiucprescon -o ${WORKSPACE}\\mypy_stubs"
                                        }
                                    }

                                }
                                stage("Running MyPy"){
                                    environment{
                                        MYPYPATH = "${WORKSPACE}\\mypy_stubs"
                                    }

                                    steps{
                                        bat "if not exist reports\\mypy\\html mkdir reports\\mypy\\html"
                                        dir("source"){
                                            bat returnStatus: true, script: "mypy -p uiucprescon --cache-dir=nul --html-report ${WORKSPACE}\\reports\\mypy\\html > ${WORKSPACE}\\logs\\mypy.log"
                                        }
                                    }
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/mypy/html/", reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                }
                            }
                        }
                    }
                }
            }

        }
        stage("Packaging") {
            environment {
                CMAKE_PATH = "${tool 'cmake3.13'}"
                PATH = "${env.CMAKE_PATH};$PATH"
                CL = "/MP"
            }
            parallel{
                stage("Python 3.6 whl"){
                    stages{
                        stage("Create venv for 3.6"){
                            environment {
                                PATH = "${tool 'CPython-3.6'};$PATH"
                            }

                            steps {
                                bat "python -m venv venv\\36 && venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install wheel setuptools --upgrade"
                            }
                        }
                        stage("Creating bdist wheel for 3.6"){
                            environment {
                                NASM_PATH = "${tool name: 'nasm_2_x64', type: 'com.cloudbees.jenkins.plugins.customtools.CustomTool'}"
                                PYTHON36_VENV_SCRIPTS_PATH = "${WORKSPACE}\\venv\\36\\scripts"
                                PATH = "${env.PYTHON36_VENV_SCRIPTS_PATH};${env.NASM_PATH};${tool 'CPython-3.6'};$PATH"
                            }
                            steps {

                                dir("source"){
                                    bat "python setup.py build -b ../build/36/ -j${env.NUMBER_OF_PROCESSORS} --build-lib ../build/36/lib --build-temp ../build/36/temp build_ext --inplace --cmake-exec=${env.CMAKE_PATH}\\cmake.exe bdist_wheel -d ${WORKSPACE}\\dist"
                                }
                            }
                            post{
                               success{
                                    stash includes: 'dist/*.whl', name: "whl 3.6"
                                }
                            }
                        }
                        stage("Testing 3.6 wheel on a computer without Visual Studio"){
                            agent { label 'Windows && !VS2015' }
                            environment {
                                PATH = "${tool 'CPython-3.6'};$PATH"
                            }
                            steps{
                                unstash "whl 3.6"
                                test_wheel("*cp36*.whl", "36")

                            }
                            post{
                                cleanup{
                                    deleteDir()
                                }
                            }
                        }
                    }
                }
                stage("Python sdist"){
                    environment {
                        PATH = "${tool 'CPython-3.6'};$PATH"
                    }
                    steps {
                        dir("source"){
                            bat "python setup.py sdist -d ${WORKSPACE}\\dist --format zip"
                        }
                    }
                    post{
                        success{
                            stash includes: 'dist/*.zip,dist/*.tar.gz', name: "sdist"
                        }
                    }
                }
                stage("Python 3.7 whl"){
                    agent {
                        label "Windows && Python3 && VS2015"
                    }
                    environment {
                        CMAKE_PATH = "${tool 'cmake3.13'}"
                        NASM_PATH = "${tool name: 'nasm_2_x64', type: 'com.cloudbees.jenkins.plugins.customtools.CustomTool'}"
                        PATH = "${env.CMAKE_PATH};${env.NASM_PATH};${tool 'CPython-3.7'};$PATH"
                        // CL = "/MP"
                    }
                    stages{
                        stage("create venv for 3.7"){
                            steps {
                                bat "python -m venv venv\\37 && venv\\37\\Scripts\\python.exe -m pip install pip --upgrade && venv\\37\\Scripts\\pip.exe install wheel setuptools --upgrade"
                            }
                        }

                        stage("Creating bdist wheel for 3.7"){
                            environment {
                                PYTHON37_VENV_SCRIPTS_PATH = "${WORKSPACE}\\venv\\37\\scripts"
                                PATH = "${env.PYTHON37_VENV_SCRIPTS_PATH};$PATH"
                            }
                            steps {
                                dir("source"){
                                    bat "python setup.py build -b ../build/37/ -j${env.NUMBER_OF_PROCESSORS} --build-lib ../build/37/lib/ --build-temp ../build/37/temp build_ext --cmake-exec=${env.CMAKE_PATH}\\cmake.exe bdist_wheel -d ${WORKSPACE}\\dist"
                                }
                            }
                            post{
                                success{
                                    stash includes: 'dist/*.whl', name: "whl 3.7"
                                }

                            }
                        }
                        stage("Testing 3.7 wheel on a computer without Visual Studio"){
                            agent { label 'Windows && !VS2015' }
                            environment {
                                PATH = "${tool 'CPython-3.7'};$PATH"
                            }
                            steps{
                                unstash "whl 3.7"
                                test_wheel("*cp37*.whl", "37")

                            }
                            post{
                                cleanup{
                                    deleteDir()
                                }
                            }
                        }
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                disableDeferredWipeout: true,
                                patterns: [
                                    [pattern: 'dist', type: 'INCLUDE'],
                                    [pattern: 'source', type: 'INCLUDE'],
                                    [pattern: '*tmp', type: 'INCLUDE'],
                                    ]
                                )
                        }
                    }
                }
            }
            post{
                success{
                    unstash "whl 3.7"
                    unstash "whl 3.6"
                    unstash "sdist"
                    archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                }
            }
        }
        stage("Deploy to DevPi") {
            when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                        triggeredBy "TimerTriggerCause"
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }

            environment{
                PYTHON36_VENV_SCRIPTS_PATH = "${WORKSPACE}\\venv\\36\\Scripts"
                PATH = "${env.PYTHON36_VENV_SCRIPTS_PATH};$PATH"
            }
            stages{
                stage("Upload to DevPi Staging"){
                    steps {
                        unstash "DOCS_ARCHIVE"
                        unstash "whl 3.6"
                        unstash "whl 3.7"
                        unstash "sdist"
                        bat "pip install devpi-client && devpi use https://devpi.library.illinois.edu && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && devpi upload --from-dir dist"
                    }
                }
                stage("Test DevPi packages") {
                    options{
                        timestamps()
                    }
                    parallel {
                        stage("Testing DevPi .zip Package with Python 3.6 and 3.7"){
                            environment {
                                PATH = "${tool 'CPython-3.7'};${tool 'CPython-3.6'};$PATH"
                            }
                            agent {
                                node {
                                    label "Windows && Python3 && VS2015"
                                }
                            }
                            options {
                                skipDefaultCheckout(true)

                            }
                            stages{
                                stage("Creating venv to test sdist"){
                                        steps {
                                            lock("system_python_${NODE_NAME}"){
                                                bat "python -m venv venv\\venv36 && venv\\venv36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\venv36\\Scripts\\pip.exe install setuptools --upgrade && venv\\venv36\\Scripts\\pip.exe install devpi-client \"tox<3.7\""
                                            }

                                        }

                                }
                                stage("Testing DevPi zip Package"){

                                    environment {
                                        CMAKE_PATH = "${tool 'cmake3.13'}"
                                        NASM_PATH = "${tool name: 'nasm_2_x64', type: 'com.cloudbees.jenkins.plugins.customtools.CustomTool'}"
                                        PYTHON_SCRIPTS_PATH = "${WORKSPACE}\\venv\\venv36\\Scripts"
                                        PATH = "${env.CMAKE_PATH};${env.NASM_PATH};${env.PYTHON_SCRIPTS_PATH};${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps {
                                        // echo "Testing Source zip package in devpi"

                                        timeout(40){
                                            devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${env.PKG_NAME}",
                                                pkgVersion: "${env.PKG_VERSION}",
                                                pkgRegex: "zip",
                                                detox: false
                                            )
                                        }
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
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
                                }
                                failure{
                                    deleteDir()
                                }
                            }

                        }

                        stage("Testing DevPi .whl Package with Python 3.6"){
                            agent {
                                node {
                                    label "Windows && Python3 && !VS2015"
                                }
                            }

                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Creating venv to Test py36 .whl"){
                                    environment {
                                        PATH = "${tool 'CPython-3.6'};$PATH"
                                    }
                                    steps {
                                        create_venv("python.exe", "venv\\36")

                                        bat "venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
                                    }

                                }
                                stage("Testing DevPi .whl Package with Python 3.6"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${WORKSPACE}\\venv\\36\\Scripts;$PATH"
                                    }

                                    steps {

                                        devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${env.PKG_NAME}",
                                                pkgVersion: "${env.PKG_VERSION}",
                                                pkgRegex: "36.*whl",
                                                detox: false,
                                                toxEnvironment: "py36"
                                            )

                                    }
                                }
                            }
                            post {
                                failure {
                                    // archiveArtifacts allowEmptyArchive: true, artifacts: "**/MSBuild_*.failure.txt"
                                    deleteDir()
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
                                }
                            }
                        }
                        stage("Testing DevPi .whl Package with Python 3.7"){
                            agent {
                                node {
                                    label "Windows && Python3 && !VS2015"
                                }
                            }

                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Creating venv to Test py37 .whl"){
                                    environment {
                                        PATH = "${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps {
                                       create_venv("python.exe", "venv\\37")
                                       bat "venv\\37\\Scripts\\pip.exe install setuptools --upgrade && venv\\37\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
                                    }

                                }
                                stage("Testing DevPi .whl Package with Python 3.7"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${WORKSPACE}\\venv\\37\\Scripts;$PATH"
                                    }

                                    steps {

                                        devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${env.PKG_NAME}",
                                                pkgVersion: "${env.PKG_VERSION}",
                                                pkgRegex: "37.*whl",
                                                detox: false,
                                                toxEnvironment: "py37"
                                            )

                                    }
                                }
                            }
                            post {
                                failure {
                                    deleteDir()
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
                                }
                            }
                        }
                    }
                }
                stage("Deploy to DevPi Production") {
                        when {
                            allOf{
                                equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                                branch "master"
                            }
                        }
                        steps {
                            script {
                                try{
                                    timeout(30) {
                                        input "Release ${env.PKG_NAME} ${env.PKG_VERSION} (https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging/${env.PKG_NAME}/${env.PKG_VERSION}) to DevPi Production? "
                                    }
                                    bat "venv\\36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && venv\\36\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging && venv\\36\\Scripts\\devpi.exe push --index ${env.DEVPI_USR}/${env.BRANCH_NAME}_staging ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
                                } catch(err){
                                    echo "User response timed out. Packages not deployed to DevPi Production."
                                }
                            }
                        }
                }
            }
            post {
                success {
                    // echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    bat "venv\\36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && venv\\36\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && venv\\36\\Scripts\\devpi.exe push --index ${env.DEVPI_USR}/${env.BRANCH_NAME}_staging ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME}"

                }
                cleanup{
                    remove_from_devpi("venv\\36\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
                }
            }
        }
        stage("Deploy Online Documentation") {
            when{
                equals expected: true, actual: params.DEPLOY_DOCS
            }
            steps{
                dir("build/docs/html/"){
                    script{
                        try{
                            timeout(30) {
                                input 'Update project documentation?'
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
                                        remoteDirectory: "${params.DEPLOY_DOCS_URL_SUBFOLDER}",
                                        remoteDirectorySDF: false,
                                        removePrefix: '',
                                        sourceFiles: '**')],
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
            }
        }
    }
    post {
        cleanup{
            cleanWs(
                deleteDirs: true,
                disableDeferredWipeout: true,
                patterns: [
                    [pattern: 'dist', type: 'INCLUDE'],
                    [pattern: 'reports', type: 'INCLUDE'],
                    [pattern: 'logs', type: 'INCLUDE'],
                    [pattern: 'certs', type: 'INCLUDE'],
                    [pattern: '*tmp', type: 'INCLUDE'],
                    [pattern: 'source', type: 'INCLUDE'],
                    [pattern: 'mypy_stubs', type: 'INCLUDE'],
                    [pattern: "source", type: 'INCLUDE'],
//                    [pattern: "source/**/*.pyd", type: 'INCLUDE'],
//                    [pattern: "source/**/*.exe", type: 'INCLUDE'],
//                    [pattern: "source/**/*.exe", type: 'INCLUDE']
                    ]
                )
        }
    }
}
