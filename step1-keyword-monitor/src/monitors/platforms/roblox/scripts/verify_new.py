import urllib.request
import json
import time

def get_universe_id(place_id):
    url = f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("universeId")
    except:
        return None

def get_game_info(universe_id):
    url = f"https://games.roblox.com/v1/games?universeIds={universe_id}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data['data']:
                return data['data'][0]
    except:
        pass
    return None

def verify(ids):
    for pid in ids:
        uid = get_universe_id(pid)
        if uid:
            info = get_game_info(uid)
            if info:
                print(f"ID: {pid}")
                # print(f"Name: {info['name']}") # Skip printing name to avoid encoding issues
                print(f"  Created: {info['created']}")
                print(f"  Updated: {info['updated']}")
                print(f"  UniverseId: {uid}")
        time.sleep(0.5)

if __name__ == "__main__":
    # The IDs mentioned in the report
    verify(["89917661348537", "127080713564152", "125579556815131", "114998660298420", "78335169704561"])
