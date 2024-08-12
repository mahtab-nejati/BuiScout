#! /bin/zsh 

# Check if the first argument is empty
if [ -z "$1" ]; then
    echo "\n\e[1m\e[32m*** Usage: [arg] where arg is the tag to be assigned to the image.***\n\e[0m"
    DOCKER="buiscout"
else
    DOCKER="buiscout:$1"
fi

DIR="$( cd "$( dirname "$0" )" && pwd )"

cd $DIR
cd ..

cp -f $DIR/.dockerignore ./

docker image rm -f $DOCKER
docker build . -t $DOCKER -f $DIR/Dockerfile 
rm .dockerignore

cp $DIR/config.json ./_BuiScout_docker_mountpoint/.

docker run --rm -it -v "$(pwd)/_BuiScout_docker_mountpoint":/mountpoint/ $DOCKER bash