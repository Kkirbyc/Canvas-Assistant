"""Validate public skill sources and build a credential-free distributable ZIP."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import ast,hashlib,json,re,shutil,xml.etree.ElementTree as ET,zipfile
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'canvas-study'
class Links(HTMLParser):
    def __init__(self,source):super().__init__();self.urls=[];self.feed(source)
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('href','src') and value:self.urls.append(value)
def files():
    return sorted(p for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
def main():
    version=json.loads((PACKAGE/'package-version.json').read_text(encoding='utf-8'))['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z0-9.]+)?',version):raise ValueError('Invalid version')
    for name in ('LICENSE','NOTICE','THIRD_PARTY_NOTICES.md'):shutil.copy2(ROOT/name,PACKAGE/name)
    for p in files():
        if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'))
        if p.suffix=='.svg':ET.parse(p)
        if p.suffix in ('.md','.html','.py','.js','.json','.txt','.ps1','.css'):
            s=p.read_text(encoding='utf-8')
            if re.search(r'(?:[A-Z]:[/\\]Users[/\\](?!Public\b)[\w.-]+)|(?:gh[pousr]_[A-Za-z0-9]{20,})|(?:github_pat_[A-Za-z0-9_]{20,})',s):raise ValueError('Possible private path/credential: '+str(p.relative_to(ROOT)))
            if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',s):raise ValueError('Private key detected')
    skill=(PACKAGE/'SKILL.md').read_text(encoding='utf-8')
    front=re.match(r'^---\n(.*?)\n---\n',skill,re.S)
    if not front:raise ValueError('Missing skill frontmatter')
    fields=dict(line.split(': ',1) for line in front[1].splitlines())
    if fields.get('name')!='canvas-study' or not fields.get('description'):raise ValueError('Invalid skill metadata')
    checked=0
    for p in files():
        if p.suffix=='.html':
            for url in Links(p.read_text(encoding='utf-8')).urls:
                parsed=urlsplit(url)
                if parsed.scheme or parsed.netloc or not parsed.path:continue
                target=(p.parent/unquote(parsed.path)).resolve()
                if not target.is_relative_to(PACKAGE.resolve()) or not target.is_file():raise ValueError(f'Broken/outside local link: {p.name} -> {url}')
                checked+=1
        if p.suffix=='.md' and p.name!='example.md':
            for dest in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if dest.startswith(('https://','http://','#')):continue
                if not (p.parent/dest).is_file():raise ValueError(f'Broken reference: {p.name} -> {dest}')
    content=[p.relative_to(PACKAGE).as_posix() for p in files() if p.name not in ('PACKAGE-CONTENTS.txt','SHA256SUMS.txt')]+['PACKAGE-CONTENTS.txt','SHA256SUMS.txt']
    (PACKAGE/'PACKAGE-CONTENTS.txt').write_text('\n'.join(sorted(content))+'\n',encoding='utf-8',newline='\n')
    sums=['  '.join((hashlib.sha256(p.read_bytes()).hexdigest(),p.relative_to(PACKAGE).as_posix())) for p in files() if p.name!='SHA256SUMS.txt']
    (PACKAGE/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8',newline='\n')
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    archive=dist/f'canvas-assistant-windows-{version}.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files():
            # Stable ZIP metadata: repeated builds of identical content have identical hashes.
            info=zipfile.ZipInfo('canvas-study/'+p.relative_to(PACKAGE).as_posix(),date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise ValueError('ZIP integrity failure')
        for line in sums:
            digest,name=line.split('  ',1)
            if hashlib.sha256(z.read('canvas-study/'+name)).hexdigest()!=digest:raise ValueError('ZIP checksum mismatch')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii',newline='\n')
    report={'version':version,'archive':archive.name,'bytes':archive.stat().st_size,'files':len(files()),'local_links':checked,'sha256':digest,'checks':'PASS'}
    (dist/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report))
if __name__=='__main__':main()
