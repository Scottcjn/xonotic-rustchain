FROM debian:bookworm-slim

# Install system dependencies
# libcurl4 is needed for Xonotic's internal HTTP client (downloading maps etc)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    python3 \
    python3-pip \
    libcurl4 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/xonotic

# Download and extract Xonotic
# Using 0.8.6 stable release
ENV XONOTIC_VERSION=0.8.6
RUN wget -q --show-progress https://dl.xonotic.org/xonotic-${XONOTIC_VERSION}.zip \
    && unzip -q xonotic-${XONOTIC_VERSION}.zip \
    && mv Xonotic/* . \
    && rm -rf Xonotic xonotic-${XONOTIC_VERSION}.zip

# Copy RustChain integration files
# We copy everything from the build context (repo root) into the Xonotic folder
COPY . /opt/xonotic/

# Install Python dependencies for RustChain bridges
RUN pip3 install --no-cache-dir requests websockets --break-system-packages

# Create data directory for persistence
VOLUME ["/opt/xonotic/data"]

# Expose default Xonotic UDP port
EXPOSE 26000/udp

# Set up entrypoint
COPY deploy/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["+server.cfg"]
