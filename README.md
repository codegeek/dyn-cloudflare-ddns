# Cloudflare DNS updater from DDNS services

Dyn-Cloudflare-DDNS is a simple Python 3.9.x script that retrieves an IP address from a Dynamic DNS provider (Dyn, No-IP, etc)
and uses that to update Cloudflare's DNS. The reason for this script is that many routers have the capability to update DDNS 
services, but usually Cloudflare isn't supported.

In order for this script to work, you need to have an account with a Dynamic DNS provider *and* an account with Cloudflare.