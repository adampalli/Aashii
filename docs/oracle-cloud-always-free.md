# Host Aashii on Oracle Cloud (Always Free)

This guide deploys the bot with **long polling** on an Oracle Cloud Always Free VM. It avoids paid services and does not require a public HTTPS webhook.

## 1) Create an Always Free Ubuntu VM

1. Sign in to Oracle Cloud and open **Compute -> Instances**.
2. Click **Create instance**.
3. Choose:
   - Shape: `VM.Standard.E2.1.Micro` (Always Free eligible)
   - Image: Ubuntu 22.04 or 24.04
4. In **Add SSH keys**, paste your public key.
5. Create the instance.

## 2) Open SSH access in networking

In your VCN/security list (or NSG), allow inbound SSH:

- Source: `0.0.0.0/0` (or your IP range)
- Protocol: TCP
- Destination port: `22`

> No HTTP/HTTPS port is required for polling mode.

## 3) SSH into the VM

```bash
ssh ubuntu@<PUBLIC_IP>
```

## 4) Install system packages

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip postgresql postgresql-contrib
```

## 5) Create a PostgreSQL database for the bot

```bash
sudo -u postgres psql
```

In the `psql` shell:

```sql
CREATE USER aashii WITH PASSWORD 'replace_with_strong_password';
CREATE DATABASE aashii OWNER aashii;
\q
```

## 6) Clone the project and set up Python environment

The bot needs Python 3.10 or newer (`python3 --version`). Ubuntu 22.04 ships 3.10 and 24.04 ships 3.12, so the system Python works.

```bash
git clone <YOUR_REPO_URL> ~/Aashii
cd ~/Aashii
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 7) Initialize database schema

```bash
export PGPASSWORD='replace_with_strong_password'
psql "postgresql://aashii@localhost:5432/aashii" -f data/schema.sql
```

If your deployment needs the migration script too:

```bash
psql "postgresql://aashii@localhost:5432/aashii" -f data/migrate.sql
```

## 8) Configure bot content and environment variables

Create and customize setup config:

```bash
cp data/setup/bot-config.example.json data/setup/bot-config.json
# edit messages/images/command descriptions as needed
```

Create a runtime env file:

```bash
sudo tee /etc/aashii.env >/dev/null <<'ENV'
TOKEN=replace_with_telegram_bot_token
DATABASE_URL=postgresql://aashii:replace_with_strong_password@localhost:5432/aashii
POLL_INTERVAL=1
BOT_CONFIG_PATH=/home/ubuntu/Aashii/data/setup/bot-config.json
ENV
```

Set permissions:

```bash
sudo chmod 600 /etc/aashii.env
```

## 9) Create a systemd service

```bash
sudo tee /etc/systemd/system/aashii.service >/dev/null <<'UNIT'
[Unit]
Description=Aashii Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Aashii
EnvironmentFile=/etc/aashii.env
ExecStart=/home/ubuntu/Aashii/.venv/bin/python -m Aashii
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now aashii
```

## 10) Verify and monitor

```bash
systemctl status aashii --no-pager
journalctl -u aashii -f
```

Expected result: service stays `active (running)` and logs show the bot started polling.

## 11) Update workflow

When you push a new version:

```bash
cd ~/Aashii
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart aashii
```

## 12) Auto-deploy from GitHub (optional)

The workflow in `.github/workflows/deploy.yml` checks every pull request (Python compiles, JSON config is valid). On every push to `main` it also SSHes into the VM, runs `git pull --ff-only`, installs requirements, restarts `aashii` and fails if the service does not come back up. You can also run it by hand from **Actions -> Check and deploy -> Run workflow**.

One-time setup:

1. On the VM, create a key just for GitHub and authorize it:

   ```bash
   ssh-keygen -t ed25519 -N "" -C github-deploy -f ~/.ssh/github_deploy
   cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
   cat ~/.ssh/github_deploy        # private key, copy it for step 2
   ```

2. In GitHub open **Settings -> Secrets and variables -> Actions -> New repository secret** and add:
   - `ORACLE_HOST`: the VM's public IP.
   - `ORACLE_SSH_KEY`: the whole private key printed above, including the `BEGIN` and `END` lines.
   - `ORACLE_USER` (optional): defaults to `ubuntu`.
   - `ORACLE_KNOWN_HOSTS` (optional, recommended): output of `ssh-keyscan -H <PUBLIC_IP>` run from your own computer. Without it the workflow trusts whatever host key it sees at deploy time.

3. Then delete the private key from the VM: `rm ~/.ssh/github_deploy`.

Requirements on the VM: port 22 must accept connections from GitHub's runners (the guide's `0.0.0.0/0` rule does), the `ubuntu` user needs passwordless `sudo` (the default on Oracle Ubuntu images), and `~/Aashii` must have no local commits or edits to tracked files, otherwise `git pull --ff-only` stops the deploy.

## Optional hardening (recommended)

- Restrict SSH source CIDR to your own IP.
- Use Oracle Cloud Vault or another secret manager for token/password rotation.
- Add a simple uptime check (cron or external monitor) and alerting.

## Troubleshooting

- **`psycopg2.OperationalError`**: confirm PostgreSQL is running and `DATABASE_URL` credentials are correct.
- **Bot not responding**: check `TOKEN` value and whether bot was started in BotFather.
- **Service exits immediately**: inspect `journalctl -u aashii -n 200 --no-pager` for traceback.
