# Version 0.2.0

- Migrated from the legacy Cloudflare 2.x SDK to Cloudflare 5.9.0.
- Added explicit API token and global API key authentication with standard SDK environment variable support.
- Preserved legacy tokens supplied through CF_API_KEY; global API keys require CF_API_EMAIL.
- Removed legacy SDK configuration-file support. Configure credentials with environment variables before upgrading.
- Preserved DNS TTL, proxy settings, and metadata during address updates and added automatic pagination.
- Rejected unsupported DNS record types before DNS resolution and fixed API error reporting.
- Added regression tests and refreshed dependencies, CI, and build tooling.
- Updated the Docker runtime to Python 3.15; standalone execution requires Python 3.10+.

# Version 0.1.0

- Initial Release

# Version 0.1.1

- Updated Cloudflare library to 2.19
- Updated Python to 3.12
- Modified logs
