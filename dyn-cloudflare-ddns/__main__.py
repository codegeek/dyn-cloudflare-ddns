import os
import dns.resolver
import CloudFlare
import logging
# import logging.config

logger = logging.getLogger('dyn-cloudflare-ddns')

def getExternalIPFromDDNS(host, rtype):
    try:
        result = dns.resolver.resolve(host, rtype)
    except Exception as e:
        exit('DNS resolve Error: %s' % e)    
    return result

def updateCloudflare(ip_address, ip_type, zone_name):
    try:
        cf = CloudFlare.CloudFlare()
        r_zones = cf.zones.get(params={'name': zone_name})
        if len(r_zones) == 0:
            exit("Zone not found: %s" % zone_name)

        logger.debug('Zone: %s' % r_zones)
        zone_id = r_zones[0]['id']
        logger.debug('Zone ID: %s' % zone_id)

        dns_records = cf.zones.dns_records.get(zone_id, params={'name':zone_name, 'match':'all', 'type':ip_type})
        logger.debug('DNS Records: %s' % dns_records)

        updated = False

        for dns_record in dns_records:
            old_ip_address = dns_record['content']
            old_ip_address_type = dns_record['type']
            if ip_type not in ['A','AAAA']:
                continue
            if ip_type != old_ip_address_type:
                logger.debug('Record "%s" ignored, wrong address family. Zone: %s' % (old_ip_address, zone_name))
                continue
            if ip_address == old_ip_address:
                logger.info('IP unchanged for zone "%s": %s' % (zone_name, ip_address))
                updated = True
                continue

            proxied_state = dns_record['proxied']
            dns_record_id = dns_record['id']
            dns_record = {
                'name':zone_name,
                'type':ip_type,
                'content':ip_address,
                'proxied':proxied_state
            }
            logger.debug('Updating DNS record: %s' % dns_record)

            dns_record = cf.zones.dns_records.put(zone_id, dns_record_id, data=dns_record)
            logger.info('DNS zone "%s" updated: %s -> %s' %(zone_name, old_ip_address, ip_address))
            updated = True
        
        if updated:
            return

        # No record found, create
        dns_record = {
            'name':zone_name,
            'type':ip_type,
            'content':ip_address
        }
        dns_record = cf.zones.dns_records.post(zone_id, data=dns_record)
        logger.info("Record created for zone %s: %s" % (zone_name, ip_address))
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit('CloudFlare API error %s - %d %s' % (zone_name, e, e))
    except Exception as e:
        exit('CloudFlare error %s - %s' % (zone_name, e))

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
    if os.getenv('CF_API_KEY') == None:
        exit("CF_API_KEY is required")

    external_ips = getExternalIPFromDDNS(ddnsHost, ddnsRtype)
    if external_ips != None:
        ip = external_ips.rrset[0].to_text()
        logger.debug('Trying to update CloudFlare Zone "%s" with IP: %s' % (cfZone, ip))
        updateCloudflare(ip, ddnsRtype, cfZone)
    else:
        logger.error('No external IPs found for host "%s"' % ddnsHost)

if __name__ == "__main__":
    main()