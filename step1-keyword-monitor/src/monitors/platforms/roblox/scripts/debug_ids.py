import urllib.request
import json
import time

def check_id(pid):
    print(f"Checking PlaceID: {pid}")
    # Try universe lookup
    url = f"https://apis.roblox.com/universes/v1/places/{pid}/universe"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            uid = data.get("universeId")
            print(f"  UniverseID: {uid}")
            if uid:
                g_url = f"https://games.roblox.com/v1/games?universeIds={uid}"
                g_req = urllib.request.Request(g_url)
                with urllib.request.urlopen(g_req, timeout=10) as g_resp:
                    g_data = json.loads(g_resp.read())
                    if g_data['data']:
                        game = g_data['data'][0]
                        print(f"    Name: {game['name'].encode('ascii', 'ignore').decode()}")
                        print(f"    Created: {game['created']}")
                        print(f"    Updated: {game['updated']}")
                    else:
                        print("    No game data found for universe.")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    ids = ["89917661348537", "127080713564152", "114998660298420", "78335169704561"]
    for i in ids:
        check_id(i)
        time.sleep(1)
