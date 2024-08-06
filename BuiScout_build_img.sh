#! /bin/zsh 

SUBJECT=$1
DIR="$( cd "$( dirname "$0" )" && pwd )"

cd $DIR
cd ..

docker image rm -f buiscout
docker build . -t buiscout -f $DIR/Dockerfile

mkdir -p ./BuiScout_docker_mountpoint/data
mkdir -p ./BuiScout_docker_mountpoint/subject

cp $DIR/config.json ./BuiScout_docker_mountpoint/.
cp -rn ./subject/$SUBJECT ./BuiScout_docker_mountpoint/subject/.

docker run --rm -v "$(pwd)/BuiScout_docker_mountpoint":/mountpoint/ buiscout:latest