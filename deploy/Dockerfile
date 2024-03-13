FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt-get upgrade -y
RUN apt install -y valgrind gcc make
RUN apt install -y libpng-dev libjpeg-dev libgtk-3-dev
RUN export LD_LIBRARY_PATH=/usr/include/gtk-3.0/
RUN apt install -y python3
RUN apt install -y time htop

RUN groupadd --gid 10000 -r runner
RUN adduser runner --disabled-password --uid 10000 --gid 10000

WORKDIR /home/runner
RUN chown -R runner /home/runner
USER runner
