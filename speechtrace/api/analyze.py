from http.server import BaseHTTPRequestHandler
import base64,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import analyze
class handler(BaseHTTPRequestHandler):
 def do_POST(self):
  try:
   headers={key.lower():value for key,value in self.headers.items()}
   supplied=headers.get('content-length')
   length=int(supplied) if supplied is not None else None
   if length is not None and (length<1 or length>3_200_000):raise ValueError('Upload request must be below 3.2 MB.')
   raw=self.rfile.read(length if length is not None else 3_200_001)
   if not raw or len(raw)>3_200_000:raise ValueError('Upload request must be below 3.2 MB.')
   body=json.loads(raw);transcript=body.get('transcript','')
   if not isinstance(transcript,str) or len(transcript)>1500:raise ValueError('Use a transcript up to 1500 characters.')
   baseline=base64.b64decode(body['baseline'],validate=True);participant=base64.b64decode(body['participant'],validate=True)
   result=analyze(baseline,participant,transcript);self.respond(200,result)
  except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:self.respond(400,{'error':str(e)})
  except Exception:self.respond(503,{'error':'The alignment model is temporarily unavailable. Bundled examples remain usable; try again shortly.'})
 def respond(self,status,data):
  result=json.dumps(data,allow_nan=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(result)
 def log_message(self,*args):pass
