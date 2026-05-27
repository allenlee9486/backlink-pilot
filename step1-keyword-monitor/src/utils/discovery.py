import re
from .sitemap_parser import fetch_sitemap, parse_sitemap

def discover_crazygames_new():
    """Finds new game URLs from CrazyGames sitemap."""
    index_url = "https://www.crazygames.com/sitemap-index.xml"
    index_content = fetch_sitemap(index_url)
    index_items = parse_sitemap(index_content)
    
    # Look for the 'en' sitemap
    en_sitemap_url = None
    for item in index_items:
        if "/en/sitemap" in item['loc']:
            en_sitemap_url = item['loc']
            break
            
    if not en_sitemap_url:
        return []
        
    en_content = fetch_sitemap(en_sitemap_url)
    en_items = parse_sitemap(en_content)
    
    # Games are usually https://www.crazygames.com/game/slug
    game_urls = []
    # Only process the last 100 entries to focus on newest
    for item in en_items[-100:]:
        loc = item['loc']
        if "/game/" in loc:
            slug = loc.split("/game/")[-1]
            game_urls.append({"name": slug, "slug": slug, "url": loc, "platform": "crazygames"})
            
    return game_urls

def discover_itch_new():
    """Finds new game URLs from itch.io sitemap."""
    url = "https://itch.io/sitemap.xml"
    content = fetch_sitemap(url)
    items = parse_sitemap(content)
    
    game_urls = []
    # Process last 100 entries
    for item in items[-100:]:
        loc = item['loc']
        # Games are usually https://username.itch.io/game-slug
        if ".itch.io/" in loc and loc.count("/") == 3:
            slug = loc.split("/")[-1]
            game_urls.append({"name": slug, "slug": slug, "url": loc, "platform": "itch"})
            
    return game_urls

def discover_steam_new():
    """Finds new game URLs from Steam sitemap."""
    index_url = "https://store.steampowered.com/sitemap/sitemap_index.xml"
    index_content = fetch_sitemap(index_url)
    index_items = parse_sitemap(index_content)
    
    # Look for the last apps sitemap (usually contains newer apps)
    apps_sitemaps = [item['loc'] for item in index_items if "sitemap_apps" in item['loc']]
    
    if not apps_sitemaps:
        return []
        
    apps_sitemap_url = apps_sitemaps[-1]
    apps_content = fetch_sitemap(apps_sitemap_url)
    apps_items = parse_sitemap(apps_content)
    
    game_urls = []
    # Process last 100 entries
    for item in apps_items[-100:]:
        loc = item['loc']
        match = re.search(r"/app/(\d+)/([^/]+)", loc)
        if match:
            app_id = match.group(1)
            name = match.group(2).replace("_", " ")
            game_urls.append({"name": name, "id": app_id, "url": loc, "platform": "steam"})
            
    return game_urls

CUSTOM_SITES = [
    "yoplay.io",
    "azgames.io",
    "block-blast.io",
    "chillguyclicker.io",
    "escaperoadcity2.io",
    "1games.io",
    "dinosaur-game.io",
    "spacewavesgame.io",
    "thatsnot-myneighbor.io",
    "crossy-road.io",
    "game-game.com",
    "curverush.com",
    "escaperoad2.io",
    "geometryvibes.io",
    "www.bestgames.com",
    "brain-lines.io",
    "elonplayground.io",
    "www.blipzi.com",
    "www.gamenora.com",
    "dashmetry.com",
    "melonplayground.io",
    "y8.com",
    "poki.com",
    "addictinggames.com",
    "html5games.com",
    "onlinegames.io",
    "twoplayergames.org",
    "crazygames.com",
    "itch.io",
    "kongregate.com",
    "gamedistribution.com",
    "armorgames.com",
    "gameflare.com"
]

# Mapping of domains to specific sitemap URLs if the default ones fail
SITEMAP_OVERRIDES = {
    "yoplay.io": ["https://yoplay.io/sitemap.xml"],
    "azgames.io": ["https://azgames.io/sitemap.xml"],
    "y8.com": ["https://www.y8.com/sitemaps/y8/en/sitemap.xml.gz", "https://zh.y8.com/sitemap.xml"],
    "poki.com": ["https://poki.com/sitemap.xml", "https://poki.com/en/sitemaps/index.xml"],
    "twoplayergames.org": ["https://www.twoplayergames.org/sitemap-games.xml"],
    "html5games.com": ["https://play.famobi.com/sitemap.xml"],
    "addictinggames.com": ["https://www.addictinggames.com/sitemap.xml"],
    "onlinegames.io": ["https://www.onlinegames.io/sitemap.xml"],
    "gamedistribution.com": ["https://gamedistribution.com/sitemap.xml"],
    "armorgames.com": ["https://armorgames.com/sitemap.xml"],
    "gameflare.com": ["https://www.gameflare.com/sitemap.xml"],
    "bestgames.com": ["https://www.bestgames.com/sitemap.xml"],
    "poki.com/en/new": ["https://poki.com/sitemap.xml"],
    "y8.com/new/games": ["https://www.y8.com/sitemaps/y8/en/sitemap.xml.gz"],
    "game-game.com": ["https://www.game-game.com/sitemap.xml"],
    "elonplayground.io": ["http://elonplayground.io/sitemap.xml"]
}

def discover_custom_sites():
    """Finds new game URLs from a list of custom domains' sitemaps."""
    all_game_urls = []
    
    for domain in CUSTOM_SITES:
        # Use overrides if available, otherwise try common locations
        sitemap_urls = SITEMAP_OVERRIDES.get(domain, [
            f"https://{domain}/sitemap.xml",
            f"https://{domain}/sitemap_index.xml",
            f"http://{domain}/sitemap.xml",
            f"http://{domain}/sitemap_index.xml"
        ])
        
        for sitemap_url in sitemap_urls:
            try:
                content = fetch_sitemap(sitemap_url)
                if not content:
                    continue
                    
                items = parse_sitemap(content)
                if not items:
                    continue
                
                # If it's a sitemap index (contains other sitemaps), try to follow the last one
                sub_sitemaps = [i['loc'] for i in items if 'sitemap' in i['loc'].lower() and i['loc'] != sitemap_url]
                if sub_sitemaps:
                    # Focus on the most recent sub-sitemap
                    last_sub = sub_sitemaps[-1]
                    sub_content = fetch_sitemap(last_sub)
                    if sub_content:
                        items = parse_sitemap(sub_content)

                # Filter for likely game URLs (this is heuristic)
                # We check the last 50 entries as they are usually the newest
                for item in items[-50:]: 
                    loc = item['loc']
                    # Basic heuristic: if it's not the homepage and has some path
                    if loc.strip("/") != f"https://{domain}".strip("/") and loc.strip("/") != f"http://{domain}".strip("/"):
                        # Extract a name from the URL
                        path = loc.rstrip("/").split("/")[-1]
                        if not path or path == domain: continue
                        
                        name = path.replace("-", " ").replace("_", " ").title()
                        all_game_urls.append({
                            "name": name,
                            "domain": domain,
                            "url": loc,
                            "platform": "general"
                        })
                break # If we successfully got items from one sitemap location, move to next domain
            except Exception as e:
                # print(f"⚠️ Failed to parse sitemap for {domain} at {sitemap_url}: {e}")
                pass
                
    return all_game_urls
