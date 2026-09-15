FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    coreutils \
    gawk \
    grep \
    sed \
    findutils \
    procps \
    iproute2 \
    sysstat \
    util-linux \
    jq \
    tree \
    less \
    file \
    diffutils \
    bc \
    ca-certificates \
    curl \
    lsof \
    python3 \
    man-db \
    manpages \
    && rm -rf /var/lib/apt/lists/*

RUN if [ -f /usr/share/man/man1/gawk.1.gz ]; then \
      ln -sf /usr/share/man/man1/gawk.1.gz /usr/share/man/man1/awk.1.gz; \
    fi

RUN useradd \
    --create-home \
    --uid 1000 \
    --shell /bin/bash \
    student

RUN mkdir -p \
    /opt/console-chaos \
    /workspace/play \
    /workspace/grade \
    /shared \
    && chown -R student:student \
        /opt/console-chaos \
        /workspace \
        /shared

COPY --chown=student:student agent.py /opt/console-chaos/agent.py

WORKDIR /opt/console-chaos

USER student

CMD ["python3", "/opt/console-chaos/agent.py"]
