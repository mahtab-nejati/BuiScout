# For more information, please refer to https://aka.ms/vscode-docker-python
FROM ubuntu:22.04

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# OS update
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y openjdk-11-jre python3 pip graphviz graphviz-dev
# RUN apt install -y software-properties-common
# RUN add-apt-repository ppa:openjdk-r/ppa
# RUN apt update -y
# RUN apt upgrade -y

# Set up tree-sitter
RUN apt install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_16.x
RUN apt install -y nodejs
RUN apt install -y npm
# RUN npm install -g npm@10.8.1


# Set up GumTree and tree-sitter-parser
COPY gumtree/dist/build/distributions/gumtree-3.1.0-SNAPSHOT/ /GumTree/
ENV PATH=${PATH}:/GumTree/bin/
COPY tree-sitter-parser /tree-sitter-parser
ENV PATH=${PATH}:/tree-sitter-parser

# WORKDIR /tree-sitter-parser/tree-sitter-cmake
# RUN npm init --yes
# RUN npm install --save nan


# # Set up SWAP space
# RUN fallocate -l 16G /swapfile 
# RUN chmod 600 /swapfile 
# RUN mkswap /swapfile 
# RUN swapon /swapfile 
# RUN echo "/swapfile   swap   swap     defaults    0 0" >> /etc/fstab


# Set up BuiScout
COPY BuiScout /BuiScout
RUN pip install -r /BuiScout/requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /BuiScout folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
# RUN adduser -u 5678 --disabled-password --force-badname --gecos "" BuiScoutUser && chown -R BuiScoutUser /BuiScout
# USER BuiScoutUser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
WORKDIR /BuiScout
CMD ["python3", "scout.py"]
