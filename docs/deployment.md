# Deployment Guide — BMAD v6 Template Architect

## 1. Deployment Options

| Option | Use Case |
|---|---|
| Local (venv) | Development and personal use on a single machine |
| Podman container | Production-ready single-host deployment |
| Podman Compose / Quadlet | Multi-service production deployment |

---

## 2. Local Deployment (Virtual Environment)

```bash
# 1. Clone repository
git clone https://github.com/DXCSithlordPadawan/BMAD6.git
cd BMAD6

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure secrets
cp .env.example .env
# Edit .env — set SECRET_KEY to a 64-char random hex string

# 5. Start the application
python app.py
```

> **Security note:** `python app.py` uses Flask's built-in development server. For anything beyond localhost use, deploy behind a production WSGI server and reverse proxy (see Section 4).

---

## 3. Production WSGI Server

Flask's built-in server is not suitable for production. Use **Gunicorn** or **Waitress**:

### Gunicorn (Linux)

```bash
pip install gunicorn
gunicorn --workers 2 --bind 0.0.0.0:8000 'app:app'
```

### Waitress (cross-platform)

```bash
pip install waitress
waitress-serve --port=8000 app:app
```

---

## 4. Reverse Proxy (nginx)

Terminating TLS at the proxy and forwarding to Flask on `127.0.0.1:8000` is the recommended production pattern.

```nginx
server {
    listen 80;
    server_name bmad.internal.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bmad.internal.example.com;

    ssl_certificate     /etc/ssl/certs/bmad.crt;
    ssl_certificate_key /etc/ssl/private/bmad.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Restrict to internal network
    allow 10.0.0.0/8;
    deny all;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        client_max_body_size 1M;
    }
}
```

---

## 5. Container Deployment (Podman)

### Quick Start

```bash
# Build the image
podman build -t bmad6-architect:latest .

# Run the container
podman run -d \
  --name bmad6 \
  -p 8000:8000 \
  --env-file .env \
  -v ./bmad_output:/app/bmad_output:Z \
  bmad6-architect:latest
```

> The `-v` flag persists generated output outside the container. The `:Z` label sets the correct SELinux context.

### Check the container is running

```bash
podman ps
podman logs bmad6
```

### Stop and remove

```bash
podman stop bmad6
podman rm bmad6
```

For detailed container build instructions, see [`container_build.md`](container_build.md).

---

## 6. Systemd / Podman Quadlet (Auto-start on Boot)

Create `/etc/containers/systemd/bmad6.container`:

```ini
[Unit]
Description=BMAD v6 Template Architect
After=network.target

[Container]
Image=bmad6-architect:latest
PublishPort=8000:8000
EnvironmentFile=/opt/bmad6/.env
Volume=/opt/bmad6/bmad_output:/app/bmad_output:Z

[Service]
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now bmad6
```

---

## 7. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | **Yes** | Flask session signing key. Min 32 chars. Generate with `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `FLASK_DEBUG` | No | Set to `1` for development only. Default: `0`. |

---

## 8. Production Checklist

- [ ] `SECRET_KEY` set to ≥64-character random hex value
- [ ] `FLASK_DEBUG=0`
- [ ] Running behind TLS-terminating reverse proxy
- [ ] Network access restricted to authorised users / VPN
- [ ] Container running as non-root (`USER bmad`)
- [ ] `bmad_output/` volume mounted outside container for persistence
- [ ] Logs being collected (Podman journald or log forwarding)
- [ ] Health check passing: `curl http://localhost:8000/` returns 200
