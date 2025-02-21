# Start with Debian 12 base image
FROM debian:12

# Set noninteractive mode
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variables
ENV TOKEN=pat_Sw5zEF8CS5Apeu8zKEeGithV

# Update and install necessary dependencies
RUN apt-get update && apt-get install -y \
    gnupg2 \
    wget \
    lsb-release && \
    apt-get clean

# Add SignalWire repository and import GPG key
RUN wget --http-user=signalwire --http-password=$TOKEN \
    -O /usr/share/keyrings/signalwire-freeswitch-repo.gpg \
    https://freeswitch.signalwire.com/repo/deb/debian-release/signalwire-freeswitch-repo.gpg && \
    echo "machine freeswitch.signalwire.com login signalwire password $TOKEN" > /etc/apt/auth.conf && \
    chmod 600 /etc/apt/auth.conf && \
    echo "deb [signed-by=/usr/share/keyrings/signalwire-freeswitch-repo.gpg] https://freeswitch.signalwire.com/repo/deb/debian-release/ $(lsb_release -sc) main" > /etc/apt/sources.list.d/freeswitch.list && \
    echo "deb-src [signed-by=/usr/share/keyrings/signalwire-freeswitch-repo.gpg] https://freeswitch.signalwire.com/repo/deb/debian-release/ $(lsb_release -sc) main" >> /etc/apt/sources.list.d/freeswitch.list

# Update the package list again
RUN apt-get update

# Install odbcinst1debian2 separately to handle its configuration
RUN echo 'odbcinst odbcinst/missing_file note' | debconf-set-selections
RUN echo 'odbcinst1debian2 odbcinst1debian2/missing_file note' | debconf-set-selections
RUN apt-get -y install odbcinst1debian2

# Update and install FreeSWITCH
RUN apt-get update && \
    apt-get install -y freeswitch-meta-all odbc-postgresql lua-json sngrep unixodbc vim python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the existing /etc/freeswitch folder into the image
COPY ./freeswitch /etc/freeswitch

# Create required directories and remove unnecessary directory
RUN mkdir -p /var/spool/freeswitch/rnr && \
    mkdir -p /var/spool/freeswitch/amd && \
    mkdir -p /var/spool/freeswitch/default && \
    mkdir -p /usr/share/freeswitch/sounds/custom_sounds && \
    rm -rf /usr/share/freeswitch/sounds/en && \
    rm -rf /usr/share/freeswitch/sounds/es && \
    rm -rf /usr/share/freeswitch/sounds/fr && \
    rm -rf /usr/share/freeswitch/sounds/pt && \
    rm -rf /usr/share/freeswitch/sounds/ru



# Set up Python virtual environment and install packages
RUN python3 -m venv /usr/share/freeswitch/scripts/amdenv && \
    /usr/share/freeswitch/scripts/amdenv/bin/pip3 install --no-cache-dir --upgrade pip && \
    /usr/share/freeswitch/scripts/amdenv/bin/pip3 install librosa numpy

# Activate virtual environment (for interactive use)
ENV PATH="/usr/share/freeswitch/scripts/amdenv/bin:$PATH"

# Start FreeSWITCH
CMD ["freeswitch", "-nonat"]
