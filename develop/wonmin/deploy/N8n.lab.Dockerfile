FROM alpine:3.24@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a AS python-runtime
RUN apk add --no-cache python3 \
    && mkdir -p /opt/python/bin /opt/python/lib \
    && cp -L /usr/bin/python3 /opt/python/bin/python3 \
    && cp -a /usr/lib/python3.* /opt/python/lib/ \
    && for lib in $(find /usr/lib/python3.* -name '*.so') /usr/bin/python3; do \
         ldd "$lib" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i ~ /^\//) print $i}'; \
       done | sort -u | while read lib; do \
         case "$lib" in *libc.musl*|*ld-musl*) ;; *) cp -L "$lib" /opt/python/lib/ ;; esac; \
       done

FROM n8nio/n8n@sha256:8602f5dfacbe2c931eeafd010de0e68182310e9f309921e780ab69182e92b3ae
USER root
COPY --from=python-runtime /opt/python /opt/python
COPY python3.lab.sh /usr/local/bin/python3
RUN chmod 755 /usr/local/bin/python3
USER node
