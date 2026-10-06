from pathlib import Path
import hashlib,urllib.request
path=Path(__file__).resolve().parents[1]/'data/source.mp3';path.parent.mkdir(exist_ok=True)
url='https://archive.org/download/JFK_Inaugural_Address_19610120/JFK_Inaugural_Address_19610120.mp3'
with urllib.request.urlopen(url,timeout=60) as response:data=response.read(25_000_000)
if hashlib.sha256(data).hexdigest()!='7a931ad726a9b732d8db01af6eaff55b9a34d42ee78f7ea73eba8533c3aa0e4d':raise RuntimeError('Source integrity check failed')
path.write_bytes(data);print('Downloaded verified public-domain speech recording.')
