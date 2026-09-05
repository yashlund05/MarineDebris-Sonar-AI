import urllib.request
import json

url = "https://api.github.com/repos/mvaldenegro/marine-debris-fls-datasets/contents/md_fls_dataset/data/watertank-segmentation/Images"
req = urllib.request.Request(url, headers={"User-Agent": "MarineDebrisSonarAI-DatasetAuditor"})
with urllib.request.urlopen(req, timeout=10) as resp:
    items = json.loads(resp.read().decode("utf-8"))
    print(f"Total Images items: {len(items)}")
    for item in items[:15]:
        print(f" - {item['name']} ({item['size']} bytes)")
