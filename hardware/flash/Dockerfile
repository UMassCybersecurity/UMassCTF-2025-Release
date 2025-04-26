FROM gcc:bookworm as builder

RUN apt update && apt install cmake -y

WORKDIR /usr/src/sim

COPY sim .
RUN mkdir build && cd build && cmake .. && make

FROM debian:bookworm

RUN apt update 
RUN apt install libelf1 -y

WORKDIR /home/ctf

RUN useradd -d /home/ctf -u 1001 ctf
RUN chown ctf:ctf /home/ctf
RUN echo "root:dsalfkjoei0938aefdkjsdf" | chpasswd
RUN echo "ctf:dsfsd09f78a7eisdif9asd8f790" | chpasswd

COPY --from=builder --chown=root:root /usr/src/sim/build/libsimavr.so.1 /usr/lib
COPY --from=builder --chown=root:root /usr/src/sim/build/ctfavrsim .
COPY --chown=root:root ./assets .

RUN chmod +x ./ynetd
RUN chmod +x ./ctfavrsim
RUN chmod +x ./entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]