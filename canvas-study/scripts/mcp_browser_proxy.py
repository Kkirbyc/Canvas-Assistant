"""Filter Playwright stdio tools. Click/navigation still require task-level restraint."""
import asyncio,json,sys,threading,re
ALLOWED={'browser_navigate','browser_navigate_back','browser_snapshot','browser_take_screenshot','browser_find','browser_click','browser_hover','browser_select_option','browser_tabs','browser_resize','browser_wait_for','browser_press_key','browser_close'}
def filter_response(message):
    result=message.get('result')
    if isinstance(result,dict) and isinstance(result.get('tools'),list):
        result['tools']=[tool for tool in result['tools'] if tool.get('name') in ALLOWED]
    return message
def permitted(message):
    return message.get('method')!='tools/call' or message.get('params',{}).get('name') in ALLOWED
async def main():
    if len(sys.argv)<3:raise ValueError('Expected Node executable and Playwright CLI arguments')
    child=await asyncio.create_subprocess_exec(*sys.argv[1:],stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,limit=16*1024*1024)
    def emit(message):
        sys.stdout.buffer.write((json.dumps(message,ensure_ascii=False)+'\n').encode());sys.stdout.buffer.flush()
    queue=asyncio.Queue();loop=asyncio.get_running_loop()
    def read_input():
        while True:
            line=sys.stdin.buffer.readline()
            try:loop.call_soon_threadsafe(queue.put_nowait,line)
            except RuntimeError:return
            if not line:return
    threading.Thread(target=read_input,daemon=True).start()
    async def incoming():
        while line:=await queue.get():
            try:message=json.loads(line)
            except (ValueError,UnicodeError):continue
            if not permitted(message):
                if 'id' in message:emit({'jsonrpc':'2.0','id':message['id'],'error':{'code':-32601,'message':'Tool not enabled by Canvas Study browser filter'}})
                continue
            child.stdin.write(line);await child.stdin.drain()
        child.stdin.close()
    async def outgoing():
        while True:
            try:line=await child.stdout.readline()
            except ValueError:
                sys.stderr.write('Canvas Study: MCP response exceeded 16 MiB. Request a scoped snapshot or a smaller screenshot.\n');return
            if not line:return
            try:emit(filter_response(json.loads(line)))
            except (ValueError,UnicodeError):continue
    async def diagnostics():
        while line:=await child.stderr.readline():
            message=line.decode('utf-8',errors='replace')
            if re.search(r'ENOENT|Cannot find module|Executable doesn.t exist|browserType.launch|Error:',message):
                message=re.sub(r'https?://\S+','[URL omitted]',message)
                message=re.sub(r'(?i)(bearer|token|password|cookie|authorization)[^\r\n]*','[credential-related detail omitted]',message)
                sys.stderr.write('Playwright startup: '+message[:1000]+'\n');sys.stderr.flush()
    try:
        diagnostic_task=asyncio.create_task(diagnostics())
        tasks=[asyncio.create_task(incoming()),asyncio.create_task(outgoing())]
        done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
        for t in pending:t.cancel()
        for t in done:t.result()
    finally:
        diagnostic_task.cancel()
        if child.returncode is None:
            child.terminate()
            try:await asyncio.wait_for(child.wait(),5)
            except asyncio.TimeoutError:child.kill();await child.wait()
if __name__=='__main__':asyncio.run(main())
