from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from api.analyze import handler as ApiHandler
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(Path(__file__).parent/'public'),**kwargs)
 def do_POST(self):
  if self.path=='/api/analyze':ApiHandler.do_POST(self)
  else:self.send_error(404)
 respond=ApiHandler.respond
 def log_message(self,*args):pass
ThreadingHTTPServer(('0.0.0.0',4181),Handler).serve_forever()
