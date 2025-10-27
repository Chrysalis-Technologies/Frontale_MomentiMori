# Cloudflare tunnel setup

The `cloudflared` folder is bind-mounted into the `cloudflared` service that now
ships with `docker compose`. Follow the steps below to expose the gallery at
`https://frontale.marzocchi.tech` (or any hostname on your Cloudflare zone).

1. **Authenticate**  
   ```powershell
   .\bin\cloudflared.exe login
   ```  
   Pick the `marzocchi.tech` zone when the browser prompt opens.

2. **Create the tunnel** (re-use the existing name if you already have one).  
   ```powershell
   .\bin\cloudflared.exe tunnel create frontale-momentimori
   ```  
   This stores a credentials JSON inside `%USERPROFILE%\.cloudflared\`.

3. **Copy the credentials**  
   Copy the generated `<tunnel-id>.json` from `%USERPROFILE%\.cloudflared\` into
   this repository’s `cloudflared/` folder and rename it to
   `frontale-momentimori.json` (or adjust the filename inside
   `config.yml` to match whatever you call it).

4. **Create your config**  
   Copy `cloudflared/config.template.yml` to `cloudflared/config.yml`. If you
   stick with the provided tunnel name and hostname, no edits are required.
   Otherwise, update the `tunnel`, `credentials-file`, and `hostname` fields.

5. **Map the hostname to the tunnel**  
   ```powershell
   .\bin\cloudflared.exe tunnel route dns frontale-momentimori frontale.marzocchi.tech
   ```

6. **Start the stack (gallery + tunnel)**  
   ```powershell
   docker compose --profile cloudflare up -d --build
   ```

The `cloudflared` service will now read `cloudflared/config.yml`, connect using
the credentials JSON you dropped into the same folder, and keep the hostname
alive. Update the config or restart the service whenever you change tunnel
settings.
