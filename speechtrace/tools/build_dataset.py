from pathlib import Path
import sys,json,subprocess,io,wave,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import analyze,align_words,read_wav
OUT=ROOT/'public/data';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'data/source.mp3'
if not SOURCE.exists():raise SystemExit('Run python tools/download_source.py or pass the full speech MP3 path.')
clips=[('power',57,12,'For man holds in his mortal hands the power to abolish all forms of human poverty and all forms of human life.'),('beliefs',70.2,10.8,'And yet the same revolutionary beliefs for which our forebears fought are still at issue around the globe.')]
def wav(x):
 b=io.BytesIO()
 with wave.open(b,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes((np.clip(x,-1,1)*32767).astype('<i2').tobytes())
 return b.getvalue()
entries=[]
for key,offset,duration,text in clips:
 baseline=OUT/(key+'-baseline.wav');subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(offset),'-t',str(duration),'-i',str(SOURCE),'-ar','16000','-ac','1',str(baseline)],check=True)
 raw=baseline.read_bytes();x=read_wav(raw);words=align_words(x,text);(OUT/(key+'-transcript.txt')).write_text(text+'\n')
 variants=[('unchanged',x.copy(),[]),('global-gain-control',x*10**(-10/20),[])]
 for name,db,start,end in [('near-perfect',-5,3,5),('moderate-volume',-14,3,5),('severe-volume',-24,3,6)]:
  y=x.copy();y[int(start*16000):int(end*16000)]*=10**(db/20);variants.append((name,y,[{'kind':'energy','start':start,'end':end,'delta_db':db}]))
 y=np.concatenate([x[:6*16000],np.zeros(2*16000),x[6*16000:]]);variants.append(('extra-pause',y,[{'kind':'pause','start':6,'end':8,'inserted_seconds':2}]))
 rushed=OUT/(key+'-rushed.wav');subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(baseline),'-af','atempo=1.8',str(rushed)],check=True);variants.append(('rushed',read_wav(rushed.read_bytes()),[{'kind':'pacing','start':0,'end':len(read_wav(rushed.read_bytes()))/16000,'speed_factor':1.8}]))
 for name,y,gold in variants:
  path=OUT/(key+'-'+name+'.wav');path.write_bytes(wav(y));result=analyze(raw,path.read_bytes(),text)
  entry={'id':key+'-'+name,'clip':key,'label':name.replace('-',' '),'baseline':'/data/'+baseline.name,'participant':'/data/'+path.name,'transcript':text,'source_offset':offset,'gold_regions':gold,'baseline_alignment':words,'result':result,'audio_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  entries.append(entry);print(entry['id'],result['score'],'regions',[(r['kind'],r['start'],r['end']) for r in result['regions']],'coverage',result['alignment']['coverage'],flush=True)
manifest={'version':1,'created':'2026-10-06','speaker':'John F. Kennedy','speech':'1961 inaugural address','source_url':'https://archive.org/download/JFK_Inaugural_Address_19610120/JFK_Inaugural_Address_19610120.mp3','rights_evidence':['https://commons.wikimedia.org/wiki/File:JFK_inaugural_address.ogg','https://archive.org/details/JohnF.KennedyInauguralAddress'],'rights':'Public-domain US government speech recording; credited to John F. Kennedy Presidential Library & Museum. Mirrors are deterministic digital modifications, not recordings of new speakers.','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'alignment_label_method':'Vosk constrained decoding on baseline; machine-estimated boundaries, not hand-validated word ground truth. Injected flaw intervals are exact construction labels.','cases':entries}
(OUT/'dataset.json').write_text(json.dumps(manifest,indent=2))
