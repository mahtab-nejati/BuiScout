#! /bin/zsh 

# Check if the first argument is empty
if [ -z "$1" ]; then
    echo '\n\e[1m\e[32m*** Usage: [tag] builds docker image buiscout:tag (with the tag). Default tag is "latest" ***\n\e[0m'
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

cp $DIR/config.json ./_BuiScout_mountpoint/.

docker run --rm -it -v "$(pwd)/_BuiScout_mountpoint":/_BuiScout_mountpoint/ $DOCKER bash