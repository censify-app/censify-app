# How to host using Cloudflare Tunnel
1) Install [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)

2) Login to cloudflare
```bash
cloudflared tunnel login
```

3) Create tunnel
```bash
cloudflared tunnel create censify
```

4) Create config
Change `config.yml` in `<user_path>/.cloudflared/`
(change `<tunnel-id>` to your tunnel id and `<user_path>` to your user path like `C:\Users\<username>\`)
```yml
tunnel: <tunnel-id>
credentials-file: <user_path>/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: censify.<your_domain>
    service: http://localhost:5000
  - service: http_status:404
```

5) Route DNS
```bash
cloudflared tunnel route dns censify.<your_domain>
```

6) Start tunnel
```bash
cloudflared tunnel run censify
```