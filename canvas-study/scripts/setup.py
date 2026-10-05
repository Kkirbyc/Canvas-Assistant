"""Windows per-user setup; plan by default. Never changes host permissions."""
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]
VERSION='1.0.0-preview.1'
NODE='24.16.0'
def run(args,**kwargs):
    subprocess.run([str(x) for x in args],check=True,**kwargs)
def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def safe_extract(archive,destination):
    destination=Path(destination).resolve()
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            target=(destination/entry.filename).resolve()
            if not target.is_relative_to(destination) or (entry.external_attr>>16)&0o170000==0o120000:
                raise ValueError('Unsafe archive entry')
        z.extractall(destination)
def node_runtime(runtime):
    node=shutil.which('node.exe')
    if node:
        version=subprocess.check_output([node,'--version'],text=True).strip()
        if int(version.lstrip('v').split('.')[0])>=20:
            npm=Path(node).parent/'node_modules/npm/bin/npm-cli.js'
            if npm.is_file():return Path(node),npm
    arch='arm64' if platform.machine().lower() in ('arm64','aarch64') else 'x64'
    name=f'node-v{NODE}-win-{arch}'
    destination=runtime/'node';node=destination/name/'node.exe'
    if not node.exists():
        destination.mkdir(parents=True,exist_ok=True)
        base=f'https://nodejs.org/dist/v{NODE}/'
        with urllib.request.urlopen(base+'SHASUMS256.txt',timeout=60) as r:checks=r.read().decode()
        filename=name+'.zip'
        expected=next(line.split()[0] for line in checks.splitlines() if line.split()[-1]==filename)
        archive=destination/filename
        with urllib.request.urlopen(base+filename,timeout=120) as r,archive.open('wb') as out:shutil.copyfileobj(r,out)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:raise ValueError('Node archive checksum mismatch')
        safe_extract(archive,destination)
    return node,node.parent/'node_modules/npm/bin/npm-cli.js'
def host_command(host,node,cli,config,python=None,proxy=None):
    args=([str(python),str(proxy)] if python and proxy else [])+[str(node),str(cli),'--config',str(config),'--no-webmcp']
    if host=='codex':return ['codex','mcp','add','canvas-study','--',*args]
    if host=='claude':return ['claude','mcp','add','--transport','stdio','--scope','user','canvas-study','--',*args]
    return None
def skill_destination(host,home):
    if host=='codex':return Path(os.environ.get('CODEX_HOME',home/'.codex'))/'skills/canvas-study'
    if host=='claude':return home/'.claude/skills/canvas-study'
    if host=='openclaw':return Path(os.environ.get('OPENCLAW_STATE_DIR',home/'.openclaw'))/'skills/canvas-study'
    return None
def native_host_prefix(host,executable,node):
    executable=Path(executable)
    if executable.suffix.lower()=='.exe':return [str(executable)]
    # Avoid implicit cmd.exe parsing of generated paths containing shell metacharacters.
    entry={'codex':'@openai/codex/bin/codex.js','claude':'@anthropic-ai/claude-code/cli.js'}.get(host)
    if entry:
        candidate=executable.parent/'node_modules'/entry
        if candidate.is_file():return [str(node),str(candidate)]
    return None
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['codex','claude','openclaw','generic'],required=True);parser.add_argument('--mode',choices=['auto','api','browser'],default='auto');parser.add_argument('--root',type=Path,default=Path.home()/'CanvasStudy');parser.add_argument('--apply',action='store_true');a=parser.parse_args()
    if sys.version_info<(3,11):raise RuntimeError('Python 3.11+ required')
    root=a.root.expanduser().resolve();runtime=root/'runtime';home=Path.home()
    mode=('api' if os.environ.get('CANVAS_TOKEN') else 'browser') if a.mode=='auto' else a.mode
    dest=skill_destination(a.host,home)
    print(json.dumps({'host':a.host,'mode':mode,'data_root':str(root),'skill_destination':str(dest) if dest else None,'actions':['copy skill if absent','create private local runtime','install document dependencies']+(['prepare Playwright MCP and host registration'] if mode=='browser' and a.host!='openclaw' else []),'openclaw':'Use host native browser; see references/hosts.md. Native Windows host not certified.','apply':a.apply},indent=2))
    if not a.apply:return
    if os.name!='nt':raise RuntimeError('This setup supports native Windows only; WSL setup is separate')
    if dest and dest.exists() and dest.resolve()!=PACKAGE:
        # Refuse replacement of a user's existing skill, even if it has the same name.
        if not (dest/'package-version.json').exists():raise RuntimeError('Existing skill found; review it before upgrading. Nothing overwritten.')
        if json.loads((dest/'package-version.json').read_text())!={'version':VERSION}:raise RuntimeError('Different installed version; explicit upgrade review required')
        for src in PACKAGE.rglob('*'):
            if src.is_file() and '__pycache__' not in src.parts:
                installed=dest/src.relative_to(PACKAGE)
                if not installed.is_file() or installed.read_bytes()!=src.read_bytes():raise RuntimeError('Existing skill differs; review before replacing')
    elif dest and dest.resolve()!=PACKAGE:
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(PACKAGE,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    runtime.mkdir(parents=True,exist_ok=True)
    (root/'.gitignore').write_text('*\n',encoding='utf-8') if not (root/'.gitignore').exists() else None
    envdir=runtime/'python';python=envdir/'Scripts/python.exe'
    if not python.exists():run([sys.executable,'-m','venv',envdir])
    run([python,'-m','pip','install','--disable-pip-version-check','--only-binary=:all:','-r',PACKAGE/'requirements.txt'])
    state={'version':VERSION,'host':a.host,'mode':mode,'course_root':str(root/'courses'),'python':str(python),'skill':str(dest or PACKAGE)}
    if mode=='browser' and a.host!='openclaw':
        node,npm=node_runtime(runtime);npmroot=runtime/'browser';npmroot.mkdir(exist_ok=True)
        for filename in ['package.json','package-lock.json']:
            src=PACKAGE/'assets/browser-runtime'/filename;target=npmroot/filename
            if target.exists() and target.read_bytes()!=src.read_bytes():raise RuntimeError('Existing browser dependency manifest differs; explicit upgrade review required')
            if not target.exists():shutil.copy2(src,target)
        env=os.environ.copy();env['PATH']=str(node.parent)+os.pathsep+env.get('PATH','')
        run([node,npm,'ci','--ignore-scripts','--no-audit','--no-fund'],cwd=npmroot,env=env)
        browser='msedge' if any((Path(os.environ.get(k,''))/'Microsoft/Edge/Application/msedge.exe').is_file() for k in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA') if os.environ.get(k)) else None
        launch={'headless':False,'chromiumSandbox':True}
        if browser:launch['channel']=browser
        else:
            env['PLAYWRIGHT_BROWSERS_PATH']=str(runtime/'browsers')
            run([node,npmroot/'node_modules/playwright/cli.js','install','chromium'],env=env)
            state['browser_env']={'PLAYWRIGHT_BROWSERS_PATH':env['PLAYWRIGHT_BROWSERS_PATH']}
            # Resolve executable through Playwright so the host needs no environment override.
            js="process.stdout.write(require('playwright').chromium.executablePath())"
            launch['executablePath']=subprocess.check_output([str(node),'-e',js],cwd=npmroot,env=env,text=True).strip()
        config=runtime/'playwright.json';write_json(config,{'browser':{'browserName':'chromium','isolated':True,'launchOptions':launch,'contextOptions':{'acceptDownloads':True}},'capabilities':[],'saveSession':False,'allowUnrestrictedFileAccess':False,'outputDir':str(root/'browser-output'),'console':{'level':'error'},'codegen':'none'})
        cli=npmroot/'node_modules/@playwright/mcp/cli.js'
        proxy=(dest or PACKAGE)/'scripts/mcp_browser_proxy.py'
        command=host_command(a.host,node,cli,config,python,proxy)
        write_json(runtime/'mcp-server.json',{'mcpServers':{'canvas-study':{'command':str(python),'args':[str(proxy),str(node),str(cli),'--config',str(config),'--no-webmcp']}}})
        state['mcp_command']=command
        if command:
            executable=shutil.which(command[0]+'.exe') or shutil.which(command[0]+'.cmd') or shutil.which(command[0])
            if not executable:print('Host CLI not found; use runtime/mcp-server.json and hosts.md. Registration pending.')
            else:
                prefix=native_host_prefix(a.host,executable,node)
                if not prefix:
                    print('Unsupported host CLI shim; import runtime/mcp-server.json through the host. Registration pending.')
                    write_json(root/'installation.json',state)
                    return
                # Never overwrite an existing server. Existing registration is a separate review.
                probe=subprocess.run([*prefix,'mcp','get','canvas-study'],capture_output=True)
                if probe.returncode==0:print('Existing canvas-study MCP entry retained; verify it against generated config.')
                else:run([*prefix,*command[1:]])
    write_json(root/'installation.json',state)
    print('Local setup completed. Restart/reload the host, verify tools, then log in personally. Authentication is not implied.')
if __name__=='__main__':
    try:main()
    except Exception as e:print('Setup stopped: '+str(e),file=sys.stderr);sys.exit(1)
