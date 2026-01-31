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

## 4. SSL/HTTPS (Automated) 🔒
We have included a script to automate Let's Encrypt certificate generation.

1.  **Make script executable**:
    ```bash
    chmod +x init-letsencrypt.sh
    ```
2.  **Run the initialization**:
    ```bash
    ./init-letsencrypt.sh
    ```
    *This will:*
    -   generate a placeholder certificate
    -   start nginx
    -   request the real certificate via Certbot
    -   reload nginx

3.  **Auto-Renewal**: The `certbot` service in `docker-compose.prod.yml` will automatically check for renewal every 12 hours.
