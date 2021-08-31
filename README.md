# Cloudflare DNS updater from DDNS services

[![Docker Images](https://github.com/codegeek/dyn-cloudflare-ddns/actions/workflows/publish.yml/badge.svg)](https://github.com/codegeek/dyn-cloudflare-ddns/actions/workflows/publish.yml)

Dyn-Cloudflare-DDNS is a simple Python 3.9.x script that retrieves an IP address from a Dynamic DNS provider (Dyn, No-IP, etc)
and uses that to update Cloudflare's DNS. The reason for this script is that many routers have the capability to update DDNS 
services, but usually Cloudflare isn't supported.

In order for this script to work, you need to have an account with a Dynamic DNS provider *and* an account with Cloudflare.

This script uses [Poetry](https://python-poetry.org/) and depends on [Cloudflare](https://github.com/cloudflare/python-cloudflare) and [DNSPython](https://www.dnspython.org/).

## Installation

```shell
$ poetry install
```

## Environment Variables

This script uses environment variables for its configuration

Variable | Required  | Description
--- | --- | ---
CF_ZONE | Yes | Cloudflare Zone to be updated
DDNS_HOST | Yes | Dynamic Hostname where the IP will be retrieved from
CF_API_KEY | Yes | Cloudflare API Key (v4)
DDNS_RTYPE | No | DNS Record Type (Only A or AAAA)

## Running

### Standalone

```shell
$ poetry run python3 dyn-cloudflare-ddns
```

### Inside Docker

```shell
docker run -e CF_API_KEY='<CF_KEY>' -e DDNS_HOST='<DDNS_HOST>' -e CF_ZONE='<CF_ZONE>' -d --name dyn-cloudflare-ddns ghcr.io/codegeek/dyn-cloudflare-ddns
```
