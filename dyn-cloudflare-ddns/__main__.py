import os
import dns.resolver
from cloudflare import APIError, Cloudflare
import logging
# import logging.config

logger = logging.getLogger('dyn-cloudflare-ddns')

def getExternalIPFromDDNS(host, rtype):
    try:
        result = dns.resolver.resolve(host, rtype)
    except Exception as e:
        exit('DNS resolve Error: %s' % e)    
    return result

def cloudflare_credentials():
    token = os.getenv("CF_API_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN")
    key = os.getenv("CF_API_KEY") or os.getenv("CLOUDFLARE_API_KEY")
    email = os.getenv("CF_API_EMAIL") or os.getenv("CLOUDFLARE_EMAIL")
    if token:
        return {"api_token": token}
    if key and email:
        return {"api_key": key, "api_email": email}
    if key:
        # Legacy CF_API_KEY deployments used a token without an email.
        return {"api_token": key}
    raise SystemExit("CF_API_TOKEN (or CF_API_KEY) is required")


def updateCloudflare(ip_address, ip_type, zone_name):
    if ip_type not in ("A", "AAAA"):
        raise SystemExit("DDNS_RTYPE must be A or AAAA")
    try:
        with Cloudflare(**cloudflare_credentials()) as cf:
            zone = next(iter(cf.zones.list(name=zone_name)), None)
            if zone is None:
                raise SystemExit("Zone not found: %s" % zone_name)

            dns_records = cf.dns.records.list(
                zone_id=zone.id,
                name={"exact": zone_name},
                type=ip_type,
                match="all",
            )
            found = False
            for record in dns_records:
                if record.type != ip_type:
                    continue
                found = True
                if ip_address == record.content:
                    logger.info('IP unchanged for zone "%s": %s', zone_name, ip_address)
                    continue

                # Retain required fields; leave proxy state and metadata untouched.
                cf.dns.records.edit(
                    record.id, zone_id=zone.id, name=record.name,
                    type=record.type, ttl=record.ttl, content=ip_address,
                )
                logger.info(
                    'DNS zone "%s" updated: %s -> %s',
                    zone_name, record.content, ip_address,
                )

            if not found:
                cf.dns.records.create(
                    zone_id=zone.id, name=zone_name, type=ip_type, ttl=1,
                    content=ip_address,
                )
                logger.info("Record created for zone %s: %s", zone_name, ip_address)
    except APIError as e:
        raise SystemExit("Cloudflare API error %s - %s" % (zone_name, e)) from e
    except Exception as e:
        raise SystemExit("Cloudflare error %s - %s" % (zone_name, e)) from e

def setupLogging():
    # logging.config.fileConfig('logging.conf')
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def main():
    setupLogging()
    cfZone = os.getenv('CF_ZONE')

    ddnsHost = os.getenv('DDNS_HOST')
    ddnsRtype = os.getenv('DDNS_RTYPE', 'A')

    if ddnsHost == None:
        exit("DDNS_HOST is required")
    if cfZone == None:
        exit("CF_ZONE is required")
    if ddnsRtype not in ("A", "AAAA"):
        raise SystemExit("DDNS_RTYPE must be A or AAAA")
    cloudflare_credentials()

    external_ips = getExternalIPFromDDNS(ddnsHost, ddnsRtype)
    if external_ips != None:
        ip = external_ips.rrset[0].to_text()
        logger.debug('Trying to update CloudFlare Zone "%s" with IP: %s' % (cfZone, ip))
        updateCloudflare(ip, ddnsRtype, cfZone)
    else:
        logger.error('No external IPs found for host "%s"' % ddnsHost)

if __name__ == "__main__":
    main()