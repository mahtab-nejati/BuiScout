# For more information, please refer to https://aka.ms/vscode-docker-python
FROM ubuntu:22.04
SHELL ["/bin/bash", "-l", "-c"]

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# OS update
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y openjdk-11-jre python3 pip graphviz graphviz-dev

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

# Set up BuiScout
COPY BuiScout /BuiScout
RUN pip install -r /BuiScout/requirements.txt

ENV HOME=/root
WORKDIR $HOME
RUN echo 'export PS1="\e[1m[\e[34mBuiScout\e[37m] \e[32m\W \e[37m# \e[0m"' >> $HOME/.bashrc
RUN echo 'alias scout="python3 /BuiScout/scout.py"' >> $HOME/.bashrc
