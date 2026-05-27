import urllib.request
import re

sites = [
    "https://y8.com/robots.txt",
    "https://poki.com/robots.txt",
    "https://www.twoplayergames.org/robots.txt",
    "https://html5games.com/robots.txt",
    "https://www.kongregate.com/robots.txt",
    "https://www.crazygames.com/robots.txt",
    "https://www.addictinggames.com/robots.txt",
    "https://www.onlinegames.io/robots.txt",
    "https://www.1001games.com/robots.txt",
    "https://armorgames.com/robots.txt",
    "https://www.coolmathgames.com/robots.txt",
    "https://itch.io/robots.txt",
    "https://gamejolt.com/robots.txt",
    "https://scratch.mit.edu/robots.txt",
    "https://www.game-game.com/robots.txt"
]

def check_robots(url):
    print(f"Checking {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            sitemaps = re.findall(r'^Sitemap:\s*(.*)$', content, re.MULTILINE | re.IGNORECASE)
            for sm in sitemaps:
                print(f"  Found sitemap: {sm.strip()}")
            if not sitemaps:
                print("  No sitemap found in robots.txt")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    for site in sites:
        check_robots(site)
