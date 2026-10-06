import io,json,sys,wave,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import analyze,read_wav
class EngineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cases=json.loads((ROOT/'public/data/dataset.json').read_text())['cases']
 def test_controls_and_severity_gradient(self):
  for clip in ['power','beliefs']:
   rows={c['id'].replace(clip+'-',''):c['result'] for c in self.cases if c['clip']==clip}
   for name in ['unchanged','global-gain-control','near-perfect']:
    self.assertEqual(rows[name]['score'],100);self.assertEqual(rows[name]['regions'],[])
   self.assertGreater(rows['moderate-volume']['score'],rows['severe-volume']['score']);self.assertLess(rows['severe-volume']['score'],80);self.assertLess(rows['rushed']['score'],80)
 def test_exact_injected_volume_intervals(self):
  for c in self.cases:
   if c['id'].endswith(('moderate-volume','severe-volume')):
    gold=c['gold_regions'][0];regions=[r for r in c['result']['regions'] if r['kind']=='energy'];self.assertTrue(regions)
    best=max(max(0,min(r['end'],gold['end'])-max(r['start'],gold['start']))/(max(r['end'],gold['end'])-min(r['start'],gold['start'])) for r in regions)
    self.assertGreaterEqual(best,.8)
 def test_pause_and_pace_have_grounded_regions(self):
  for c in self.cases:
   if c['id'].endswith('extra-pause'):
    self.assertTrue(any(r['kind']=='pause' and r['start']<=6.5 and r['end']>=7.5 for r in c['result']['regions']))
   if c['id'].endswith('rushed'):self.assertTrue(any(r['kind']=='pacing' for r in c['result']['regions']))
 def test_repeat_analysis_is_reproducible(self):
  c=next(c for c in self.cases if c['id']=='beliefs-moderate-volume');a=(ROOT/'public'/c['baseline'].lstrip('/')).read_bytes();b=(ROOT/'public'/c['participant'].lstrip('/')).read_bytes()
  first=analyze(a,b,c['transcript']);second=analyze(a,b,c['transcript']);self.assertEqual(first['score'],second['score']);self.assertEqual([(r['kind'],r['start'],r['end']) for r in first['regions']],[(r['kind'],r['start'],r['end']) for r in second['regions']])
 def test_rejects_silent_invalid_and_wrong_rate_audio(self):
  for data in [b'invalid',b'',b'a'*1_100_001]:
   with self.assertRaises(ValueError):read_wav(data)
  for rate in [16000,8000]:
   stream=io.BytesIO()
   with wave.open(stream,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(np.zeros(rate,dtype='<i2').tobytes())
   with self.assertRaises(ValueError):read_wav(stream.getvalue())
if __name__=='__main__':unittest.main()
