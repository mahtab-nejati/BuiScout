#! /bin/zsh 

# Check if the first argument is empty
if [ -z "$1" ]; then
    echo "Usage: You can specify a tag for the docker image 'buiscout'."
    DOCKER="buiscout"
else
    DOCKER="buiscout:$1"
fi

DIR="$( cd "$( dirname "$0" )" && pwd )"

cd $DIR
cd ..

cp $DIR/config.json ./_BuiScout_docker_mountpoint/.

docker run --rm -i -v "$(pwd)/_BuiScout_docker_mountpoint":/mountpoint/ $DOCKER