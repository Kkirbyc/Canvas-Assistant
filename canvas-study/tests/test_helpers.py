import importlib.util,io,json,sys,tempfile,unittest,zipfile,subprocess,threading,queue
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import canvas_api,render,mcp_browser_proxy
spec=importlib.util.spec_from_file_location('installer',ROOT/'scripts/setup.py');setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
class Response(io.BytesIO):
    def __init__(self,data,link=''):super().__init__(json.dumps(data).encode());self.headers={'Link':link}
class Fake:
    def __init__(self,responses):self.responses=iter(responses);self.requests=[]
    def open(self,req,timeout):self.requests.append(req);return next(self.responses)
class Checks(unittest.TestCase):
    def test_api_pagination_and_header(self):
        fake=Fake([Response([1],'<https://school.instructure.com/api/v1/courses?page=2>; rel="next"'),Response([2])]);reader=canvas_api.Reader('https://school.instructure.com','test-token',fake)
        self.assertEqual(reader.read('/api/v1/courses'),[1,2]);self.assertEqual(len(fake.requests),2);self.assertTrue(all(r.method=='GET' for r in fake.requests));self.assertEqual(fake.requests[0].get_header('Authorization'),'Bearer test-token')
    def test_cross_origin_pagination_blocked(self):
        fake=Fake([Response([1],'<https://attacker.example/api/v1/courses>; rel="next"')])
        with self.assertRaises(ValueError):canvas_api.Reader('https://school.instructure.com','test-token',fake).read('/api/v1/courses')
        self.assertEqual(len(fake.requests),1)
    def test_pagination_cycle(self):
        fake=Fake([Response([1],'<https://school.instructure.com/api/v1/courses>; rel="next"')])
        with self.assertRaises(ValueError):canvas_api.Reader('https://school.instructure.com','t',fake).read('/api/v1/courses')
    def test_invalid_origins(self):
        for url in ['http://school.edu','https://user:pass@school.edu','https://school.edu/path','https://school.edu?token=x']:
            with self.assertRaises(ValueError):canvas_api.origin(url)
    def test_redirect_disabled(self):self.assertIsNone(canvas_api.NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere.test'))
    def test_no_mutation_endpoint(self):
        with self.assertRaises(ValueError):canvas_api.endpoint('submit',123,'456')
        with self.assertRaises(ValueError):canvas_api.endpoint('page',123,'../../users')
        self.assertIn('start_date=1970-01-01',canvas_api.endpoint('announcements',123))
    def test_tool_filter(self):
        msg={'result':{'tools':[{'name':'browser_snapshot'},{'name':'browser_evaluate'},{'name':'browser_file_upload'}]}}
        self.assertEqual(len(mcp_browser_proxy.filter_response(msg)['result']['tools']),1)
        self.assertFalse(mcp_browser_proxy.permitted({'method':'tools/call','params':{'name':'browser_evaluate'}}))
        self.assertTrue(mcp_browser_proxy.permitted({'method':'tools/call','params':{'name':'browser_snapshot'}}))
    def test_zip_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);z=p/'bad.zip'
            with zipfile.ZipFile(z,'w') as f:f.writestr('../escape','bad')
            with self.assertRaises(ValueError):setup.safe_extract(z,p/'out')
            self.assertFalse((p/'escape').exists())
    def test_host_args_preserve_spaces(self):
        args=setup.host_command('claude',Path('C:/My Tools/node.exe'),Path('C:/My Tools/cli.js'),Path('C:/My Tools/config.json'))
        self.assertIn('C:\\My Tools\\node.exe' if sys.platform=='win32' else 'C:/My Tools/node.exe',args)
        self.assertIn('--scope',args);self.assertEqual(args[args.index('--scope')+1],'user')
    def test_renderer_security_and_answers(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);src=p/'input';src.mkdir();(src/'notes.md').write_text('# Notes\n\n## RDD\n\n<script>alert(1)</script>\n\n```\na < b\n```\n\n[PDF](source.pdf)',encoding='utf-8');(src/'answer-key.md').write_text('# SECRETANSWER\nResult42',encoding='utf-8');(src/'source.pdf').write_bytes(b'%PDF-test')
            m=render.build(src,p/'site');body=(p/'site/notes.html').read_text(encoding='utf-8');search=(p/'site/search.js').read_text(encoding='utf-8')
            self.assertNotIn('<script>alert',body);self.assertIn('a &lt; b',body);self.assertNotIn('SECRETANSWER',search);self.assertNotIn('answer-key.html',body);self.assertIn('source.pdf',m['copied_dependencies'])
            with self.assertRaises(ValueError):render.build(src,p/'site')
    def test_renderer_unsafe_dependencies(self):
        for content in ['[outside](../private.txt)','![remote](https://remote.test/a.png)','[active](javascript:alert)','<img src=x onerror=alert(1)>']:
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);src=p/'input';src.mkdir();(p/'private.txt').write_text('PRIVATE');(src/'notes.md').write_text('# Notes\n'+content)
                if content.startswith('<'):
                    render.build(src,p/'site');self.assertNotIn('<img src=x',(p/'site/notes.html').read_text())
                else:
                    with self.assertRaises(ValueError):render.build(src,p/'site')
    def test_reference_links_and_missing_nested_page(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);src=p/'in';src.mkdir();(src/'notes.md').write_text('# Notes\n[Plan][p]\n\n[p]: plan.md\n\n[Home](index.html)');(src/'plan.md').write_text('# Plan')
            render.build(src,p/'out');self.assertIn('href="plan.html"',(p/'out/notes.html').read_text())
            (src/'notes.md').write_text('# Notes\n[Broken](nested/plan.html)')
            with self.assertRaises(ValueError):render.build(src,p/'out2')
    def test_cli_shim_avoids_shell(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'A&B';p.mkdir();shim=p/'codex.cmd';shim.write_text('do not execute')
            self.assertIsNone(setup.native_host_prefix('codex',shim,Path('node.exe')))
            entry=p/'node_modules/@openai/codex/bin/codex.js';entry.parent.mkdir(parents=True);entry.write_text('// fixture')
            self.assertEqual(setup.native_host_prefix('codex',shim,Path('node.exe')),['node.exe',str(entry)])
    def test_proxy_large_response_and_denied_tool(self):
        with tempfile.TemporaryDirectory() as d:
            child=Path(d)/'fake_server.py';child.write_text('import sys,json\nfor line in sys.stdin:\n m=json.loads(line);print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"content":[{"type":"text","text":"x"*100000}]}}),flush=True)\n')
            proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/mcp_browser_proxy.py'),sys.executable,str(child)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                def exchange(message):
                    proc.stdin.write((json.dumps(message)+'\n').encode());proc.stdin.flush();q=queue.Queue()
                    threading.Thread(target=lambda:q.put(proc.stdout.readline()),daemon=True).start()
                    return json.loads(q.get(timeout=10))
                result=exchange({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'browser_snapshot'}})
                self.assertEqual(len(result['result']['content'][0]['text']),100000)
                result=exchange({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'browser_evaluate'}})
                self.assertEqual(result['error']['code'],-32601)
            finally:
                proc.stdin.close()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
                proc.stdout.close();proc.stderr.close()
if __name__=='__main__':unittest.main(verbosity=2)
