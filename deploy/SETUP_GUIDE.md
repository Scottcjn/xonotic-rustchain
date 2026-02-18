# Xonotic RustChain Server Setup Guide

This guide covers setting up a dedicated Xonotic RustChain Arena server on a Linux host (Ubuntu/Debian recommended).

## Prerequisites

- **OS**: Ubuntu 22.04 LTS or Debian 12
- **CPU**: 2+ Cores (4+ recommended for full AI features)
- **RAM**: 4GB+ (8GB+ if running local LLM/Ollama)
- **Storage**: 20GB+ SSD

## Option A: Docker Deployment (Recommended)

The easiest way to run the full stack (Game Server + AI + Economy).

1. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/Scottcjn/xonotic-rustchain.git
   cd xonotic-rustchain
   ```

3. **Configure**
   Create a `.env` file:
   ```bash
   DISCORD_TOKEN=your_token_here
   ENABLE_ML=true
   ```

4. **Run**
   ```bash
   cd deploy
   docker compose up -d --build
   ```

   The server will listen on UDP port 26000.

## Option B: Manual Installation (Bare Metal)

### 1. System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y wget unzip python3 python3-pip libcurl4 screen git
```

### 2. Install Xonotic

```bash
mkdir -p ~/xonotic
cd ~/xonotic
wget https://dl.xonotic.org/xonotic-0.8.6.zip
unzip xonotic-0.8.6.zip
mv Xonotic/* .
rm -rf Xonotic xonotic-0.8.6.zip
```

### 3. Install RustChain Mod

Clone the mod files into your Xonotic directory (overwriting where necessary):

```bash
# Assuming you are in ~/xonotic
git init
git remote add origin https://github.com/Scottcjn/xonotic-rustchain.git
git fetch
git checkout -t origin/main -f
```

### 4. Python Environment

Install dependencies for the bridge scripts:

```bash
pip3 install requests websockets --break-system-packages
# Or use a venv:
# python3 -m venv venv && source venv/bin/activate && pip install requests websockets
```

### 5. Configuration

Edit `server/server.cfg` to set your hostname, rcon password, and game settings.

```bash
nano server/server.cfg
```

### 6. Systemd Service (Auto-restart)

Create a service file to manage the server:

`sudo nano /etc/systemd/system/xonotic-rustchain.service`

```ini
[Unit]
Description=Xonotic RustChain Arena
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/xonotic
ExecStart=/root/xonotic/rustchain_arena_full.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now xonotic-rustchain
```

### 7. Firewall

Allow the game port:

```bash
sudo ufw allow 26000/udp
```

## Performance Tuning

- **Tickrate**: Default is usually 30. For competitive play, consider raising `sys_ticrate` in `server.cfg`.
- **Heap Size**: Use `-heapsize 512M` in launch arguments if running large maps.
- **LLM Offloading**: If running Ollama for bots, ensure you have a GPU or fast CPU. If lag occurs, disable `rustchain_bot_brain.py` or run Ollama on a separate machine.

## Updates

To update the RustChain mod:

```bash
cd ~/xonotic
git pull
sudo systemctl restart xonotic-rustchain
```
