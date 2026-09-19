import os
import time
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET = os.environ["SUPABASE_SECRET"]

GAMES = [
    ("WinGo", "WinGo_30S"),
    ("WinGo", "WinGo_1M"),
]

def fetch_history(family, code):
    ts = int(time.time() * 1000)
    url = f"https://draw.ar-lottery01.com/{family}/{code}/GetHistoryIssuePage.json?ts={ts}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def parse_records(data):
    records = []
    try:
        items = data["data"]["list"]
    except (KeyError, TypeError):
        return records

    for node in items:
        period = str(node.get("issueNumber") or "").strip()
        if not period or not period.isdigit() or len(period) < 11:
            continue
        num_str = str(node.get("number") or node.get("premium") or "").strip()
        if not num_str.isdigit():
            continue
        num = int(num_str)
        if not (0 <= num <= 9):
            continue
        raw = str(node.get("color") or "").lower()
        if "violet" in raw and num == 0:
            c = "Red/Violet"
        elif "violet" in raw and num == 5:
            c = "Green/Violet"
        elif "green" in raw:
            c = "Green"
        elif "red" in raw:
            c = "Red"
        else:
            if num in [1, 3, 7, 9]:
                c = "Green"
            elif num == 0:
                c = "Red/Violet"
            elif num == 5:
                c = "Green/Violet"
            else:
                c = "Red"
        records.append({
            "period": period,
            "number": num,
            "size": "Big" if num >= 5 else "Small",
            "color": c,
            "ts": int(time.time() * 1000),
        })
    return records

def push_to_supabase(records):
    if not records:
        return
    url = f"{SUPABASE_URL}/rest/v1/wingo_results"
    headers = {
        "apikey": SUPABASE_SECRET,
        "Authorization": f"Bearer {SUPABASE_SECRET}",
        "Content-Type": "application/json",
        "Prefer": "resolution=ignore-duplicates,return=minimal",
    }
    r = requests.post(url, headers=headers, json=records, timeout=30)
    r.raise_for_status()
    print(f"  pushed {len(records)} records -> {r.status_code}")

def main():
    for family, code in GAMES:
        try:
            data = fetch_history(family, code)
            records = parse_records(data)
            print(f"{code}: fetched {len(records)} records")
            push_to_supabase(records)
        except Exception as e:
            print(f"{code} error: {e}")

if __name__ == "__main__":
    main()
