import urllib.request
import gzip
from io import BytesIO
from lxml import etree

def fetch_sitemap(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            # Handle gzipped sitemaps
            if url.endswith(".gz") or resp.info().get("Content-Encoding") == "gzip":
                content = gzip.decompress(content)
            return content.decode('utf-8')
    except Exception as e:
        print(f"Error fetching sitemap {url}: {e}")
        return None

def parse_sitemap(xml_content):
    if not xml_content:
        return []
    
    urls = []
    try:
        # Use lxml etree for better performance and resilience
        parser = etree.XMLParser(recover=True, no_network=True)
        root = etree.fromstring(xml_content.encode('utf-8'), parser=parser)
        
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Check if it's a sitemapindex or a urlset
        if root.tag.endswith('sitemapindex'):
            for sitemap in root.xpath('//ns:sitemap', namespaces=ns):
                loc = sitemap.xpath('ns:loc', namespaces=ns)
                if loc:
                    urls.append({'type': 'sitemap', 'loc': loc[0].text})
        else:
            for url in root.xpath('//ns:url', namespaces=ns):
                loc = url.xpath('ns:loc', namespaces=ns)
                lastmod = url.xpath('ns:lastmod', namespaces=ns)
                if loc:
                    urls.append({
                        'type': 'url',
                        'loc': loc[0].text,
                        'lastmod': lastmod[0].text if lastmod else None
                    })
    except Exception as e:
        print(f"Error parsing sitemap with lxml: {e}")
        
    return urls
