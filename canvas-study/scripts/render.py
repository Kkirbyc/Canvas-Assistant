"""Portable offline HTML renderer with dependency containment and answer separation."""
import argparse,html,json,re,shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,unquote
import markdown
ASSETS=Path(__file__).resolve().parents[1]/'assets'
class Text(HTMLParser):
    def __init__(self,s):super().__init__();self.parts=[];self.feed(s)
    def handle_data(self,d):self.parts.append(d)
def text(s):return ' '.join(Text(s).parts)
class Links(HTMLParser):
    def __init__(self,s):super().__init__();self.links=[];self.feed(s)
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('src','href') and v:self.links.append((tag,k,v))
def build(source,out):
    source=Path(source).resolve();out=Path(out).resolve()
    if source==out or source.is_relative_to(out) or out.is_relative_to(source):raise ValueError('Input and output must be separate, non-nested directories')
    if out.exists() and any(out.iterdir()):raise ValueError('Choose a new/empty output directory; no existing site will be overwritten')
    files=sorted(source.glob('*.md'))
    if not files:raise ValueError('No Markdown input')
    pages=[];dependencies=set();search=[];generated={p.with_suffix('.html') for p in files}|{source/'index.html'}
    for f in files:
        raw=f.read_text(encoding='utf-8')
        md=markdown.Markdown(extensions=['tables','fenced_code','toc'])
        md.preprocessors.deregister('html_block');md.inlinePatterns.deregister('html')
        body=md.convert(raw)
        def rewrite_link(match):
            value=html.unescape(match[1]);url=urlsplit(value)
            if not url.scheme and not url.netloc and url.path.endswith('.md'):
                target=(source/unquote(url.path)).resolve().with_suffix('.html')
                if target not in generated:raise ValueError('Markdown link has no generated page: '+url.path)
                value=urlunsplit(('', '', url.path[:-3]+'.html',url.query,url.fragment))
            return 'href="'+html.escape(value,quote=True)+'"'
        body=re.sub(r'href="([^"]*)"',rewrite_link,body)
        title=text(re.search(r'<h1[^>]*>(.*?)</h1>',body,re.S)[1]) if re.search(r'<h1[^>]*>',body) else f.stem
        answer=bool(re.search(r'answer|solution|答案|解析',f.stem,re.I))
        for tag,key,url in Links(body).links:
            parsed=urlsplit(url)
            if parsed.scheme or parsed.netloc:
                if key=='src' or parsed.scheme not in ('https','http','mailto'):raise ValueError('External assets/active URLs are not permitted: '+f.name)
                continue
            if not parsed.path:continue
            rel=unquote(parsed.path);target=(source/rel).resolve()
            if not target.is_relative_to(source):raise ValueError('Dependency outside input directory')
            if target in generated:continue
            if not target.is_file():raise ValueError('Missing local dependency: '+rel)
            if target.suffix.lower() not in ('.png','.jpg','.jpeg','.gif','.webp','.pdf','.txt'):raise ValueError('Unsupported local dependency: '+rel)
            dependencies.add(target)
        body=re.sub(r'<table>(.*?)</table>',r'<div class="table-scroll"><table>\1</table></div>',body,flags=re.S)
        for block in re.split(r'(?=<h2\b)',body):
            h=re.search(r'<h2 id="([^"]+)">(.*?)</h2>',block)
            if not answer:search.append({'title':text(h[2]) if h else title,'url':f.stem+'.html'+('#'+h[1] if h else ''),'text':text(block)})
        pages.append((f.stem+'.html',title,body,md.toc,answer))
    out.mkdir(parents=True,exist_ok=True)
    for dependency in dependencies:
        dest=out/dependency.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dependency,dest)
    shutil.copy2(ASSETS/'study.css',out/'study.css');shutil.copy2(ASSETS/'study.js',out/'study.js')
    (out/'search.js').write_text('window.SECTIONS='+json.dumps(search,ensure_ascii=False).replace('</','<\\/')+';',encoding='utf-8')
    nav=''.join(f'<a href="{html.escape(url)}">{html.escape(title)}</a>' for url,title,_,_,answer in pages if not answer)
    def shell(title,body,toc='',answer=False):
        return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><link rel="stylesheet" href="study.css">'+('' if answer else '<script src="search.js" defer></script>')+'<script src="study.js" defer></script><body><a class="skip" href="#main">跳到正文</a><header><a href="index.html">Canvas · 复习手册</a><button id="print">打印</button></header><div class="layout"><aside><details open><summary>目录</summary>'+nav+'</details><label for="search">搜索复习内容</label><input id="search" type="search"><div id="results" aria-live="polite"></div>'+toc+'</aside><main id="main">'+body+'</main></div><dialog id="zoom"><button id="close">关闭</button><a id="full" target="_blank" rel="noopener">原尺寸</a><img alt=""></dialog></body></html>'
    for filename,title,body,toc,answer in pages:(out/filename).write_text(shell(title,body,toc,answer),encoding='utf-8')
    if not (out/'index.html').exists():
        (out/'index.html').write_text(shell('复习资料','<h1>复习资料</h1><p>按目录阅读完整笔记、考试要求和计划。图片点击放大；正文与配图可离线使用。</p><nav class="cards">'+nav+'</nav>'),encoding='utf-8')
    manifest={'entry':'index.html','keep':[str(p.relative_to(out)).replace('\\','/') for p in out.rglob('*') if p.is_file()],'copied_dependencies':[str(p.relative_to(source)).replace('\\','/') for p in sorted(dependencies)]}
    (out/'site-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();m=build(a.input,a.output);print('Created offline HTML; retained files:',len(m['keep']))
