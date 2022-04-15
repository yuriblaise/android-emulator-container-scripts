default_image="us-docker.pkg.dev/android-emulator-268719/images/30-google-x64:30.1.2"

DOCKER_PYTHON_PATH=/root/.pyenv/versions/3.7.3/bin/python3.7

DOCKER_PIP_PATH=/root/.pyenv/versions/3.7.3/bin/pip

# convienence function to spin up emulator
run () {
    local img="${1:-$default_image}"
    echo $img
    docker run \
    -e ADBKEY="$(cat ~/.android/adbkey)" \
    --device /dev/kvm \
    --publish 8554:8554/tcp \
    --publish 5555:5555/tcp  \
    $img
}


benchmark_help() {
    cat <<EOF
        usage: benchmark.sh run_benchmarks [DOCKER_ID] [SRC_PATH] [DEST_PATH]

        [DOCKER_ID] - id of the docker container

        [SRC_PATH] - where to copy content from locally, defaults to ./benchmarks

        [DEST_PATH] - where to copy SRC_PATH contents to in the container, defaults to root "/"
EOF
    exit 1
}

run_benchmarks () {

   while getopts 'h' flag; do
        case "${flag}" in
        h) benchmark_help ;;
        *) benchmark_help ;;
        esac
    done
    
    default_id=$(get_docker_id);
    cont_id="${1:-$default_id}";
    
    # Copy the local folder of python scripts to the docker container
    src_folder=${2:-$PWD/benchmarks}
    dest=${3:-/} #destination absolute path
    output_path=${3:-/benchmarks/results}
    docker cp $src_folder $cont_id:$dest

    docker exec $cont_id $DOCKER_PIP_PATH install -r ${dest}$(basename $src_folder)/requirements.txt
    
    docker exec $cont_id $DOCKER_PYTHON_PATH ${dest}$(basename $src_folder)/container_benchmark_script.py --adb_path /android/sdk/platform-tools/adb --adb_device 2 --apk_folder ${dest}$(basename $src_folder)/apks -culebra ${dest}$(basename $src_folder)/culebra.json -p 60 --silent_fail --python_path $DOCKER_PYTHON_PATH
    docker cp $cont_id:$output_path $src_folder

}

create_web_benchmark__container () {
    # Pass through any create web container arguments
    DOCKER_YAML=js/docker/docker-compose-build.yaml
    optargs=""
    while getopts 'hasip:' flag; do
        case "${flag}" in
        a) 
            optargs+=" -${flag} ${OPTARG}"
            DOCKER_YAML="${DOCKER_YAML} -f js/docker/development.yaml up" 
        ;;
        p) optargs+=" -${flag} ${OPTARG}";;
        h) optargs="-h" ;;
        s) optargs+=" -${flag} ${OPTARG}" ;;
        i) optargs+=" -${flag} ${OPTARG}" ;;
        *) optargs="-h" ;;
        esac
    done

    echo "Creating Web Container"
    x=$(./create_web_container.sh $optargs &)
    BACK_PID=$!
    while kill -0 $BACK_PID ; do
        echo "Process is still active..."
        sleep 1
    done
    echo "OUTPUT>>>>>>>>>>${x}"
    echo "Running Docker Comopose"
    $(docker-compose -f $DOCKER_YAML -d)
    echo "Waiting on Docker Container to start..."
    y=$(get_docker_id &)
    BACK_PID=$!
    while kill -0 $BACK_PID ; do
        echo "Waiting on docker...."
        sleep 1
    done
    docker_id=$(get_docker_id)
    
    # Wait for logcat health status
    echo "DOCKER ID: ${docker_id}"
    echo "waiting on container health..."
    echo ```wait_docker_health ${docker_id}``` 
    echo "Connect with docker exec -it $docker_id /bin/bash"

    # Install culebra and run the benchmark scripts
    culebraContainerInstall ${docker_id}
    run_benchmarks ${docker_id}

}

#gets docker id from name
get_docker_id() {
    local docker_name="${1:-emulator}"
    local id;
    until [ ${#id} -gt 0 ] ; do
        sleep 5
        id=$(docker ps -qf name=$docker_name)
        
    done;
    echo $id

}

wait_docker_health () {
    default_id=$(get_docker_id);
    containername="${1:-$default_id}" #get name if null provide id
    sleep 1;
    health_status=$(docker inspect -f {{.State.Health.Status}} $containername)
    echo $health_status
    until [ "`docker inspect -f {{.State.Health.Status}} $containername`"=="healthy" ]; do
        sleep 1;
        health_status=$(docker inspect -f {{.State.Health.Status}} $containername)
        echo $health_status
    done;
}

#Takes a container id and installs culebra and its dependencies to it
culebraContainerInstall() {
    default_id=$(get_docker_id);
    cont_id="${1:-$default_id}";
    docker cp ./culebra_container_install.sh $cont_id:/culebra_container_install.sh

    #Launch culebra install script inside of container
    docker exec $cont_id sh /culebra_container_install.sh
}


# Check if the function exists (bash specific)
if declare -f "$1" > /dev/null
then
  # call arguments verbatim
  "$@"
else
  # Show a helpful error
  echo "'$1' is not a known function name" >&2
  exit 1
fi





#   ./create_web_container.sh -p user1,passwd1