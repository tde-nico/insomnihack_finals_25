FROM ubuntu:24.04 AS builder

RUN useradd -u 1001 ctf

FROM pwn.red/jail
COPY --from=builder / /srv

COPY parser /srv/app/run
RUN chmod 755 /srv/app/run

COPY jail-hook.sh /jail/hook.sh
