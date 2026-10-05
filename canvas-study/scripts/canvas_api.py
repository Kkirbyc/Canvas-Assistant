"""Scoped GET-only Canvas reader. Token is never a command argument or persisted."""
import argparse,getpass,json,os,re,sys,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def origin(value):
    p=urllib.parse.urlsplit(value)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ('','/'):
        raise ValueError('Canvas URL must be an HTTPS origin with no credentials, path, query or fragment')
    return value.rstrip('/')
def same_api(url,base):
    p=urllib.parse.urlsplit(url);b=urllib.parse.urlsplit(base)
    return p.scheme=='https' and p.netloc==b.netloc and p.username is None and p.password is None and p.path.startswith('/api/v1/') and not p.fragment
class Reader:
    def __init__(self,base,token,opener=None):
        self.base=origin(base)
        if not token or '\r' in token or '\n' in token:raise ValueError('Missing or invalid token')
        self.token=token;self.opener=opener or urllib.request.build_opener(NoRedirect())
    def read(self,path):
        if not path.startswith('/api/v1/'):raise ValueError('API path required')
        url=self.base+path;seen=set();items=[]
        for _ in range(1000):
            if not same_api(url,self.base) or url in seen:raise ValueError('Unsafe/cyclic pagination URL')
            seen.add(url)
            req=urllib.request.Request(url,headers={'Authorization':'Bearer '+self.token,'Accept':'application/json'},method='GET')
            try:
                with self.opener.open(req,timeout=45) as r:
                    data=json.load(r);link=r.headers.get('Link','')
            except urllib.error.HTTPError as e:raise RuntimeError(f'Canvas returned HTTP {e.code}; no response body or credentials logged') from None
            except urllib.error.URLError:raise RuntimeError('Canvas connection failed; check network and school origin') from None
            if not isinstance(data,list):
                if len(seen)>1:raise ValueError('Unexpected pagination shape')
                return data
            items.extend(data)
            candidates=re.findall(r'<([^>]+)>\s*;\s*rel="next"',link)
            if not candidates:return items
            if len(candidates)!=1:raise ValueError('Ambiguous pagination')
            url=urllib.parse.urljoin(url,candidates[0])
        raise RuntimeError('Pagination limit reached; result incomplete')
def endpoint(kind,course=None,resource=None):
    if kind=='profile':return '/api/v1/users/self/profile'
    if kind=='courses':return '/api/v1/courses?enrollment_state=active&per_page=100'
    if not course or not str(course).isdigit():raise ValueError('A numeric course ID is required')
    prefix=f'/api/v1/courses/{course}'
    if kind=='course':return prefix+'?include[]=syllabus_body'
    if kind=='announcements':return '/api/v1/announcements?'+urllib.parse.urlencode({'context_codes[]':f'course_{course}','per_page':100,'start_date':'1970-01-01','end_date':datetime.now(timezone.utc).isoformat()})
    plural={'modules':'modules','files':'files','assignments':'assignments','quizzes':'quizzes','pages':'pages'}
    if kind in plural:return prefix+'/'+plural[kind]+'?per_page=100'
    if resource is None:raise ValueError('Resource ID required')
    if kind=='page':
        if not re.fullmatch(r'[\w-]+',resource):raise ValueError('Unsafe page slug')
        return prefix+'/pages/'+urllib.parse.quote(resource)
    if not str(resource).isdigit():raise ValueError('Numeric resource ID required')
    if kind=='module-items':return prefix+f'/modules/{resource}/items?per_page=100'
    if kind=='assignment':return prefix+f'/assignments/{resource}'
    if kind=='file':return prefix+f'/files/{resource}'
    raise ValueError('Unsupported read operation')
def main():
    p=argparse.ArgumentParser();p.add_argument('--origin',required=True);p.add_argument('--kind',required=True,choices=['profile','courses','course','modules','module-items','files','file','pages','page','assignments','assignment','announcements','quizzes']);p.add_argument('--course');p.add_argument('--resource');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('Output already exists; choose a new snapshot filename')
    token=os.environ.get('CANVAS_TOKEN') or getpass.getpass('Canvas token (hidden; not saved): ')
    data=Reader(a.origin,token).read(endpoint(a.kind,a.course,a.resource))
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print('Saved private API response to requested output. Do not redistribute raw responses.')
if __name__=='__main__':
    try:main()
    except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(1)
