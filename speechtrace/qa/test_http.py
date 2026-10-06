"""Regression checks for hosted header casing and bounded validation."""
import io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from api.analyze import handler
class HTTPTests(unittest.TestCase):
 def invoke(self,headers,body):
  instance=object.__new__(handler);instance.headers=headers;instance.rfile=io.BytesIO(body);result=[];instance.respond=lambda status,data:result.append((status,data))
  with patch('api.analyze.analyze',return_value={'score':100}):instance.do_POST()
  return result[0]
 def test_runtime_header_casing_and_missing_length(self):
  body=json.dumps({'baseline':'YXVkaW8=','participant':'YXVkaW8=','transcript':'the same words'}).encode()
  for headers in [{'content-length':str(len(body))},{'Content-Length':str(len(body))},{}]:
   self.assertEqual(self.invoke(headers,body),(200,{'score':100}))
 def test_chunked_runtime_upload(self):
  body=json.dumps({'baseline':'YXVkaW8=','participant':'YXVkaW8=','transcript':'the same words'}).encode()
  framed=hex(len(body))[2:].encode()+b'\r\n'+body+b'\r\n0\r\n\r\n'
  self.assertEqual(self.invoke({'transfer-encoding':'chunked'},framed),(200,{'score':100}))
  self.assertEqual(self.invoke({'transfer-encoding':'chunked'},b'400000\r\n')[0],400)
 def test_oversize_request_rejected_before_decoding(self):
  self.assertEqual(self.invoke({'content-length':'3200001'},b'')[0],400)
  self.assertEqual(self.invoke({},b'a'*3_200_001)[0],400)
 def test_invalid_json_and_base64_are_validation_errors(self):
  for body in [b'not json',b'{"baseline":"!!","participant":"YQ==","transcript":"words"}',b'{}']:
   self.assertEqual(self.invoke({'content-length':str(len(body))},body)[0],400)
if __name__=='__main__':unittest.main()
