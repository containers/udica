FROM fedora:30

USER root

# Update image
RUN dnf update --disableplugin=subscription-manager -y && \
    rm -rf /var/cache/yum

# Install dependencies
RUN dnf install --disableplugin=subscription-manager -y \
            container-selinux \
            python3 \
            python3-setools \
            systemd-devel \
            policycoreutils \
            policycoreutils-python-utils \
    && rm -rf /var/cache/yum

# build udica
WORKDIR /tmp
COPY udica/ udica/udica/
COPY LICENSE udica/
COPY README.md udica/
COPY setup.py udica/
WORKDIR /tmp/udica
RUN python3 setup.py install
WORKDIR /

# Clean up
RUN rm -rf /tmp/udica/

ENTRYPOINT ["/usr/bin/udica"]
