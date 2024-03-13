FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt-get upgrade -y
RUN apt install -y valgrind gcc make
RUN apt install -y libpng-dev libjpeg-dev libgtk-3-dev
RUN export LD_LIBRARY_PATH=/usr/include/gtk-3.0/
RUN apt install -y python3
RUN apt install -y time htop

# Id de usuairo y grupo correspondiente al host
ARG gid=1000
ARG uid=1000
RUN groupadd --gid ${gid} runner
RUN adduser runner --disabled-password --uid ${uid} --gid ${gid}

WORKDIR /home/runner
RUN chown -R runner /home/runner
USER runner
