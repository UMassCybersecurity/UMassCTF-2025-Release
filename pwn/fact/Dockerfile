FROM ubuntu:24.04
WORKDIR /home/ctf

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install gcc -y
RUN useradd -d /home/ctf -u 1001 ctf
RUN echo "root:3j5rWAxD8huRbk7bRs1rtisWl7cmWKOWzd3sM8FPaa4HjhnJTlQ4WiDRKEbPw5Iq" | chpasswd
RUN echo "ctf:3yCsBtRfsmvpWhG21QGW7O9cS7JTwvAUG1xbwE24cmC3i0q1yKSOIOoSoYABE0tg" | chpasswd
COPY --chown=root:root assets ./

RUN chmod +x ynetd 
RUN chmod +x fact
ENTRYPOINT [ "./ynetd", "-p", "4444", "-u", "ctf", "/home/ctf/fact" ]
