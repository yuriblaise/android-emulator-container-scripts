default_image="us-docker.pkg.dev/android-emulator-268719/images/30-google-x64:30.1.2"

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
        # You can add a timeout here if you want
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
    
    echo "DOCKER ID: ${docker_id}"
    echo "waiting on container health..."
    echo ```wait_docker_health ${docker_id}``` 
    echo "Connect with docker exec -it $docker_id /bin/bash"

    $(culebraContainerInstall ${docker_id})

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

    #Launch script and print out logs
    docker exec $cont_id sh /culebra_container_install.sh
    echo $(docker logs -f $cont_id | grep -ve 'logcat' -ve 'kernel' -ve 'pulse' -ve 'install 3.7.3' -ve '7.3')
    
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