FROM sagemath/sagemath:latest

USER root
RUN useradd -U -M -d /app -c 'default user' ctf
# Some permissions to allow sage to run as ctf
RUN mkdir -p /home/sage/.sage
RUN chmod 777 /home/sage && chown -R sage:ctf /home/sage/sage/sage /home/sage/.sage
RUN chmod 777 /home/sage/.sage
USER ctf
WORKDIR /app
USER root
COPY ynetd chall.sage flag.txt ./
RUN chmod +777 ynetd chall.sage flag.txt

EXPOSE 40444
CMD ["./ynetd", "-p", "40444", "-u", "ctf", "./chall.sage"]