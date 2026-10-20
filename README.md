# Cloudflare DNS updater from DDNS services

[![Docker Images](https://github.com/codegeek/dyn-cloudflare-ddns/actions/workflows/publish.yml/badge.svg)](https://github.com/codegeek/dyn-cloudflare-ddns/actions/workflows/publish.yml)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/codegeek/dyn-cloudflare-ddns/github-actions.yml)
![GitHub Release](https://img.shields.io/github/v/release/codegeek/dyn-cloudflare-ddns)
![GitHub License](https://img.shields.io/github/license/codegeek/dyn-cloudflare-ddns)


Dyn-Cloudflare-DDNS is a simple Python 3.10+ script that retrieves an IP address from a Dynamic DNS provider (Dyn, No-IP, etc)
and uses that to update Cloudflare's DNS. The reason for this script is that many routers have the capability to update DDNS 
services, but usually Cloudflare isn't supported.

In order for this script to work, you need to have an account with a Dynamic DNS provider *and* an account with Cloudflare.

This script uses [Poetry](https://python-poetry.org/) and depends on [Cloudflare](https://github.com/cloudflare/cloudflare-python) and [DNSPython](https://www.dnspython.org/).

## Installation

```shell
$ python -m pip install poetry==2.5.1
$ poetry sync
```

## Environment Variables

This script uses environment variables for its configuration

Variable | Required  | Description
--- | --- | ---
CF_ZONE | Yes | Cloudflare zone name; its apex A/AAAA record is updated
DDNS_HOST | Yes | Dynamic Hostname where the IP will be retrieved from
CF_API_TOKEN | Yes* | Cloudflare API token with Zone Read and DNS Edit permissions for the target zone
CF_API_KEY | No | Legacy token alias; with CF_API_EMAIL, a global API key
CF_API_EMAIL | No | Account email when using a global API key
DDNS_RTYPE | No | DNS Record Type (Only A or AAAA)

*Provide `CF_API_TOKEN` (recommended), a token in the legacy `CF_API_KEY`, or
`CF_API_KEY` plus `CF_API_EMAIL` for global API key authentication.
The SDK environment names `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_API_KEY`, and
`CLOUDFLARE_EMAIL` are also accepted. An explicit API token takes precedence.
Legacy SDK configuration files are no longer read.

## Validation

```shell
poetry check --lock
poetry run python -m unittest discover -s tests -v
poetry run python -m pip check
poetry build
```

Tests simulate Cloudflare HTTP responses and do not change live DNS records.

## Running

### Standalone

```shell
$ poetry run python3 dyn-cloudflare-ddns
```

### Inside Docker

```shell
docker run -e CF_API_TOKEN='<CF_TOKEN>' -e DDNS_HOST='<DDNS_HOST>' -e CF_ZONE='<CF_ZONE>' -d --name dyn-cloudflare-ddns ghcr.io/codegeek/dyn-cloudflare-ddns
```
