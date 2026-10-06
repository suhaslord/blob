"""Reference-relative speech delivery analysis. No absolute speaker-quality claims."""
import base64, hashlib, io, json, math, re, threading, urllib.request, wave, zipfile
from pathlib import Path
import numpy as np
from vosk import Model, KaldiRecognizer, SetLogLevel
SetLogLevel(-1)
MODEL_URL='https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip'
MODEL_ROOT=Path('/tmp/speechtrace-model');_model=None;_lock=threading.Lock()

def get_model():
 global _model
 with _lock:
  if _model is None:
   local=Path(__file__).parent/'models/vosk-model-small-en-us-0.15'
   model_path=local if local.exists() else MODEL_ROOT/'vosk-model-small-en-us-0.15'
   if not model_path.exists():
    MODEL_ROOT.mkdir(exist_ok=True)
    with urllib.request.urlopen(MODEL_URL,timeout=45) as response: data=response.read(60_000_000)
    if hashlib.sha256(data).hexdigest()!='30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498':raise ValueError('Model archive integrity check failed')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
     for name in archive.namelist():
      if not (MODEL_ROOT/name).resolve().is_relative_to(MODEL_ROOT.resolve()): raise ValueError('Invalid model archive')
     archive.extractall(MODEL_ROOT)
   _model=Model(str(model_path))
 return _model

def read_wav(data):
 if len(data)>1_100_000:raise ValueError('Each WAV must be at most 1.1 MB; use a clip up to 32 seconds.')
 try:
  with wave.open(io.BytesIO(data),'rb') as f:
   if f.getnchannels()!=1 or f.getsampwidth()!=2 or f.getframerate()!=16000:raise ValueError('Use mono PCM16 WAV at 16 kHz.')
   x=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float64)/32768
 except (wave.Error,EOFError) as e:raise ValueError('Upload a valid PCM WAV file.') from e
 if len(x)<16000 or len(x)>512000:raise ValueError('Use a 1–32 second recording.')
 if np.max(np.abs(x))<0.0002:raise ValueError('The recording is silent or too quiet to analyze.')
 return x

def align_words(x,transcript):
 text=' '.join(re.findall(r"[a-z]+(?:'[a-z]+)?",transcript.lower()))
 if not text or len(text.split())>120:raise ValueError('Provide a transcript of 1–120 English words.')
 # Sentence grammar constrains decoding to the supplied word sequence. Acoustic
 # boundaries come from Vosk's Kaldi decoder, rather than uniform word spacing.
 rec=KaldiRecognizer(get_model(),16000,json.dumps([text,'[unk]']));rec.SetWords(True)
 pcm=(np.clip(x,-1,1)*32767).astype('<i2').tobytes();words=[]
 for start in range(0,len(pcm),8000):
  if rec.AcceptWaveform(pcm[start:start+8000]):words.extend(json.loads(rec.Result()).get('result',[]))
 words.extend(json.loads(rec.FinalResult()).get('result',[]))
 aligned=[{'word':w['word'],'start':w['start'],'end':w['end'],'confidence':round(w['conf'],3)} for w in words if w['word']!='[unk]']
 expected=text.split();actual=[w['word'] for w in aligned]
 # Ordered longest common subsequence measures transcript coverage, without
 # pretending ASR errors prove a speaking mistake.
 previous=[0]*(len(actual)+1)
 for word in expected:
  row=[0]
  for j,a in enumerate(actual):row.append(previous[j]+1 if word==a else max(row[-1],previous[j+1]))
  previous=row
 coverage=previous[-1]/len(expected)
 return {'words':aligned,'coverage':round(coverage,3),'method':'Vosk constrained sentence grammar / Kaldi word boundaries','warning':None if coverage>=.85 else 'Low transcript coverage. Alignment is uncertain; check the transcript and recording. This is not evidence of a speaking error.'}

def features(x):
 size=400;hop=320
 frames=np.lib.stride_tricks.sliding_window_view(np.pad(x,(0,max(0,size-len(x)))),size)[::hop]
 rms=np.sqrt(np.mean(frames*frames,axis=1)+1e-12);db=20*np.log10(rms+1e-9)
 windowed=frames*np.hanning(size);power=np.abs(np.fft.rfft(windowed,n=512))**2
 hz=np.linspace(0,8000,257);mel=lambda h:2595*np.log10(1+h/700);points=700*(10**(np.linspace(mel(80),mel(7600),28)/2595)-1)
 filters=np.maximum(0,np.minimum((hz[None,:]-points[:-2,None])/(points[1:-1,None]-points[:-2,None]),(points[2:,None]-hz[None,:])/(points[2:,None]-points[1:-1,None])))
 logmel=np.log(power@filters.T+1e-9);basis=np.cos(np.pi/26*(np.arange(26)[None,:]+.5)*np.arange(1,13)[:,None]);mfcc=logmel@basis.T
 mfcc=(mfcc-np.mean(mfcc,axis=0))/(np.std(mfcc,axis=0)+1e-6)
 pitch=[];confidence=[]
 for f in frames:
  f=f-f.mean();corr=np.correlate(f,f,'full')[size-1:];lo=45;hi=250;k=int(np.argmax(corr[lo:hi]))+lo;c=float(corr[k]/(corr[0]+1e-12));pitch.append(16000/k if c>.35 else 0);confidence.append(c)
 pitch=np.array(pitch);voiced=pitch>0;median=np.median(pitch[voiced]) if voiced.any() else 1
 semitones=np.where(voiced,12*np.log2(np.maximum(pitch,1)/median),0)
 normalized_db=db-np.median(db[db>np.percentile(db,35)])
 # Keep silence information but normalize utterance-wide energy and pitch.
 vectors=np.column_stack([mfcc,normalized_db/12])
 return {'vectors':vectors,'db':normalized_db,'pitch':semitones,'voiced':voiced,'seconds':np.arange(len(frames))*hop/16000,'duration':len(x)/16000}

def dtw(a,b):
 # Downsample to 100 ms; use a monotone full path for duration-varying mirrors.
 aa=a['vectors'][::5];bb=b['vectors'][::5];n,m=len(aa),len(bb)
 local=np.mean((aa[:,None,:]-bb[None,:,:])**2,axis=2);cost=np.full((n+1,m+1),np.inf);cost[0,0]=0;back=np.zeros((n,m),dtype=np.uint8)
 for i in range(n):
  for j in range(m):
   options=(cost[i,j],cost[i,j+1]+.04,cost[i+1,j]+.04);k=int(np.argmin(options));cost[i+1,j+1]=local[i,j]+options[k];back[i,j]=k
 i=n-1;j=m-1;path=[]
 while i>=0 and j>=0:
  path.append((i,j));k=back[i,j]
  if k==0:i-=1;j-=1
  elif k==1:i-=1
  else:j-=1
 path.reverse();mapping=np.zeros(m)
 for j in range(m):mapping[j]=np.median([i for i,jj in path if jj==j])
 return mapping,local,n,m

def runs(mask,minimum=3):
 out=[];start=None
 for i,on in enumerate(list(mask)+[False]):
  if on and start is None:start=i
  if not on and start is not None:
   if i-start>=minimum:out.append((start,i))
   start=None
 return out

def analyze(baseline_bytes,participant_bytes,transcript,include_alignment=True):
 x=read_wav(baseline_bytes);y=read_wav(participant_bytes);a=features(x);b=features(y);mapping,local,n,m=dtw(a,b)
 ai=np.clip(np.rint(mapping*5).astype(int),0,len(a['db'])-1);bi=np.arange(m)*5
 energy=b['db'][bi]-a['db'][ai]
 pitch=b['pitch'][bi]-a['pitch'][ai];voiced=b['voiced'][bi]&a['voiced'][ai]
 # Smooth to prevent single-frame flags.
 energy=np.convolve(energy,np.ones(3)/3,'same');pitch=np.convolve(pitch,np.ones(3)/3,'same')
 regions=[]
 for start,end in runs(np.abs(energy)>7,minimum=4):
  delta=float(np.median(energy[start:end]));regions.append({'start':round(start*.1,2),'end':round(min(end*.1,b['duration']),2),'kind':'energy','baseline_start':round(float(mapping[start])*.1,2),'delta':round(delta,2),'unit':'dB','explanation':f'Local energy is {abs(delta):.1f} dB {"lower" if delta<0 else "higher"} than the aligned baseline after median normalization. Try a steadier volume in this passage.'})
 for start,end in runs((np.abs(pitch)>5)&voiced,minimum=7):
  delta=float(np.median(pitch[start:end]));regions.append({'start':round(start*.1,2),'end':round(min(end*.1,b['duration']),2),'kind':'contour','baseline_start':round(float(mapping[start])*.1,2),'delta':round(delta,2),'unit':'semitones','explanation':f'Pitch movement differs by about {abs(delta):.1f} semitones relative to each recording’s median pitch. Compare the emphasis here; a difference is not automatically a flaw.'})
 # At matched acoustic anchors, cumulative time lag reveals local pacing shifts.
 lag=np.arange(m)*.1-mapping*.1
 slope=np.zeros(m)
 for j in range(5,m-5):slope[j]=(mapping[j+5]-mapping[j-5])
 for start,end in runs((slope<5)&(b['db'][bi]>-22),minimum=10):
  regions.append({'start':round(start*.1,2),'end':round(min(end*.1,b['duration']),2),'kind':'pacing','baseline_start':round(float(mapping[start])*.1,2),'delta':round(float(np.median(slope[start:end]))/10,2),'unit':'relative advance','explanation':'The recording advances through the baseline at less than half the reference pace over this region. Review elongated delivery or an extra pause.'})
 for start,end in runs((slope>16)&(b['db'][bi]>-22),minimum=7):
  regions.append({'start':round(start*.1,2),'end':round(min(end*.1,b['duration']),2),'kind':'pacing','baseline_start':round(float(mapping[start])*.1,2),'delta':round(float(np.median(slope[start:end]))/10,2),'unit':'relative advance','explanation':'The recording advances through the baseline at over 1.6 times the reference pace here. Review whether the rushed passage leaves enough time for the audience.'})
 for start,end in runs((b['db'][bi]<-28)&(a['db'][ai]>-22),minimum=7):
  regions.append({'start':round(start*.1,2),'end':round(min(end*.1,b['duration']),2),'kind':'pause','baseline_start':round(float(mapping[start])*.1,2),'delta':round((end-start)*.1,2),'unit':'seconds','explanation':f'A low-energy interval lasts {(end-start)*.1:.1f} s where the aligned reference is more active. Review whether this pause is intentional.'})
 components={}
 for name,types in [('energy',{'energy'}),('pacing',{'pacing','pause'}),('contour',{'contour'})]:
  duration=sum(r['end']-r['start'] for r in regions if r['kind'] in types);components[name]=round(max(0,100-400*duration/b['duration']),1)
 score=round(.4*components['energy']+.4*components['pacing']+.2*components['contour'],1)
 alignment=align_words(y,transcript) if include_alignment else {'words':[],'coverage':None,'method':'not requested','warning':None}
 baseline_alignment=align_words(x,transcript) if include_alignment else {'words':[],'coverage':None}
 if include_alignment and alignment['coverage']>=.85 and baseline_alignment['coverage']>=.85:
  aw=baseline_alignment['words'];bw=alignment['words']
  # Compare ordered matched word boundaries as an independent pacing check.
  dp=np.zeros((len(aw)+1,len(bw)+1),dtype=int)
  for i in range(len(aw)):
   for j in range(len(bw)):dp[i+1,j+1]=dp[i,j]+1 if aw[i]['word']==bw[j]['word'] else max(dp[i,j+1],dp[i+1,j])
  pairs=[];i=len(aw);j=len(bw)
  while i and j:
   if aw[i-1]['word']==bw[j-1]['word']:pairs.append((aw[i-1],bw[j-1]));i-=1;j-=1
   elif dp[i-1,j]>=dp[i,j-1]:i-=1
   else:j-=1
  pairs.reverse()
  if len(pairs)>=5:
   base_span=pairs[-1][0]['end']-pairs[0][0]['start'];part_span=pairs[-1][1]['end']-pairs[0][1]['start'];rate=base_span/max(part_span,.1)
   if rate>1.6:
    regions.append({'start':pairs[0][1]['start'],'end':pairs[-1][1]['end'],'kind':'pacing','baseline_start':pairs[0][0]['start'],'delta':round(rate,2),'unit':'speech span ratio','explanation':f'The matched spoken passage takes {part_span:.1f} s versus {base_span:.1f} s in the reference ({rate:.2f}× reference pace). Review whether the faster delivery is intentional.'})
   for (prev_a,prev_b),(next_a,next_b) in zip(pairs,pairs[1:]):
    base_gap=next_a['start']-prev_a['end'];part_gap=next_b['start']-prev_b['end']
    if part_gap-base_gap>.7 and min(prev_a['confidence'],prev_b['confidence'],next_a['confidence'],next_b['confidence'])>=.8:
     regions.append({'start':prev_b['end'],'end':next_b['start'],'kind':'pause','baseline_start':prev_a['end'],'delta':round(part_gap-base_gap,2),'unit':'extra seconds','explanation':f'The gap between “{prev_b["word"]}” and “{next_b["word"]}” is {part_gap:.2f} s, compared with {base_gap:.2f} s in the reference. Review this added pause.'})
 # Remove nested flags of the same kind; preserve the widest causal region.
 regions=[r for k,r in enumerate(regions) if not any(j!=k and other['kind']==r['kind'] and other['start']<=r['start'] and other['end']>=r['end'] and (other['end']-other['start']>r['end']-r['start'] or j<k) for j,other in enumerate(regions))]
 # Union overlapping intervals within each rubric component.
 for name,types in [('energy',{'energy'}),('pacing',{'pacing','pause'}),('contour',{'contour'})]:
  intervals=sorted((r['start'],r['end']) for r in regions if r['kind'] in types);merged=[]
  for start,end in intervals:
   if merged and start<=merged[-1][1]:merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
   else:merged.append((start,end))
  duration=sum(end-start for start,end in merged);components[name]=round(max(0,100-400*duration/b['duration']),1)
 score=round(.4*components['energy']+.4*components['pacing']+.2*components['contour'],1)
 for r in regions:
  r['words']=' '.join(w['word'] for w in alignment['words'] if w['end']>=r['start'] and w['start']<=r['end'])
 timeline=[{'time':round(j*.1,2),'baseline_time':round(float(mapping[j])*.1,2),'baseline_energy':round(float(a['db'][ai[j]]),2),'participant_energy':round(float(b['db'][bi[j]]),2),'energy_delta':round(float(energy[j]),2),'lag':round(float(lag[j]),2)} for j in range(m)]
 return {'score':score,'components':components,'weights':{'energy':.4,'pacing':.4,'contour':.2},'regions':sorted(regions,key=lambda r:r['start']),'timeline':timeline,'alignment':alignment,'baseline_alignment':baseline_alignment,'baseline_duration':a['duration'],'participant_duration':b['duration'],'disclaimer':'Scores measure deviations from this reference, not absolute quality or fairness across speakers. Alignment and detected regions are estimates; review them by listening. Content quality is not scored.'}
