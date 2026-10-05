"""Extract selected original PDF page images plus full text; no course code runs."""
import argparse,json
from pathlib import Path
import pymupdf
def main():
    p=argparse.ArgumentParser();p.add_argument('pdf',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--pages',default='',help='Comma-separated 1-based pages; empty means text only');a=p.parse_args()
    if a.out.exists() and any(a.out.iterdir()):raise ValueError('Choose an empty output directory')
    pages=sorted(set(int(x) for x in a.pages.split(',') if x.strip()))
    with pymupdf.open(a.pdf) as doc:
        if doc.needs_pass:raise ValueError('Encrypted PDF requires authorized local unlocking')
        if any(n<1 or n>len(doc) for n in pages):raise ValueError('Page out of range')
        a.out.mkdir(parents=True,exist_ok=True)
        text='\n\n'.join(f'--- PDF page {i+1} ---\n'+page.get_text() for i,page in enumerate(doc))
        (a.out/'text.txt').write_text(text,encoding='utf-8')
        for n in pages:
            page=doc[n-1];page.get_pixmap(matrix=pymupdf.Matrix(1600/page.rect.width,1600/page.rect.width),alpha=False).save(a.out/f'page-{n}.png')
        (a.out/'extraction.json').write_text(json.dumps({'file':a.pdf.name,'pages':len(doc),'rendered':pages,'status':'extracted_not_yet_read'},indent=2),encoding='utf-8')
        print(f'Extracted {len(doc)} text pages and {len(pages)} images. Inspect them before marking read.')
if __name__=='__main__':main()
