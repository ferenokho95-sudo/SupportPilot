import unittest,json,threading,os
from http.server import BaseHTTPRequestHandler,HTTPServer
from unittest.mock import patch
from common import llm
class ContractTests(unittest.TestCase):
 def test_http_request_usage_and_configured_cost(self):
    captured={}
    class Handler(BaseHTTPRequestHandler):
      def log_message(self,*args):pass
      def do_POST(self):
        captured['path']=self.path;captured['payload']=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        raw=json.dumps({'choices':[{'message':{'content':'test answer'}}],'usage':{'prompt_tokens':100,'completion_tokens':50}}).encode()
        self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
      with patch.dict(os.environ,{'LLM_API_KEY':'test-only','LLM_MODEL':'fixture','LLM_BASE_URL':f'http://127.0.0.1:{server.server_port}'},clear=True):
        result=llm([{'role':'user','content':'hello'}],prices={'input':2,'output':4})
      self.assertEqual(captured['path'],'/chat/completions');self.assertEqual(captured['payload']['model'],'fixture');self.assertEqual(result['input_tokens'],100);self.assertAlmostEqual(result['cost_usd'],.0004)
    finally:server.shutdown();server.server_close();thread.join()
 def test_different_model_no_wrong_global_price(self):
    from io import BytesIO
    payload=json.dumps({'choices':[{'message':{'content':'ok'}}],'usage':{'prompt_tokens':100,'completion_tokens':10}}).encode()
    with patch.dict(os.environ,{'LLM_API_KEY':'test','LLM_MODEL':'A','LLM_INPUT_USD_PER_MILLION':'10','LLM_OUTPUT_USD_PER_MILLION':'10'},clear=True),patch('urllib.request.urlopen',return_value=BytesIO(payload)):
      self.assertIsNone(llm([{'role':'user','content':'x'}],model='B')['cost_usd'])
if __name__=='__main__':unittest.main()
