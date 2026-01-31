# ZyraX Production Deployment Guide 🚀

## 1. Domain Setup (`<subdomain>.bipro.tech`)
1.  Log in to your DNS Provider (Cloudflare, Namecheap, etc.).
2.  Create an **A Record**:
    *   **Name/Host**: The subdomain part (e.g., `bot` if you want `bot.bipro.tech`).
    *   **Value/Target**: The Public IP Address of your server (VPS).
    *   **TTL**: Auto or 3600.

## 2. Configuration
1.  Open `deployment/nginx/conf.d/zyrax.conf`.
2.  Replace `server_name zyrax.bipro.tech;` with your actual domain (e.g., `bot.bipro.tech`).

## 3. Launching
Run the production composition which includes Nginx:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## 4. SSL/HTTPS (Optional but Recommended)
For key deployment, we recommend using **Certbot** on the host machine or adding a `certbot` container.
*Simplest method*: Use Cloudflare's "Flexible SSL" if your DNS is managed there. Nginx listens on Port 80, and Cloudflare handles the encryption to the user.
