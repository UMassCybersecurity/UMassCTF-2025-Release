FROM docker.io/debian:bookworm

WORKDIR /home/ctf

RUN useradd -d /home/ctf -u 1001 ctf
RUN echo "root:dsalfkjoei09820938aefdkjsdf" | chpasswd
RUN echo "ctf:dsfsd09f78a7efiafhsdif9asd8f790" | chpasswd

COPY --chown=root:root assets ./

ENTRYPOINT [ "./ynetd", "-p", "4444", "-u", "ctf", "/home/ctf/calc" ]