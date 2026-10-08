"""倪师断法论文成稿 v2（由 v1 改来，只多认补充材料的「S图N」「表SN」编号；其余与 v1 相同）：Markdown → Word（pandoc，套用此前论文的 reference.docx）＋ PDF（pandoc 出 HTML，套样式表，Chrome 打印）。
只做呈现，不改任何文字与数字。版式沿用此前论文（倪海厦紫微研究_Claude接续_20260925 的 scripts/build_manuscript.py 与 04_论文/build/manuscript.css）：
- 正文宋体、标题与加粗黑体；表格只有横线，表头浅灰米色底；
- 图片单独居中，图题另起一段「**图 N**　……」左对齐；表题「**表 N　……**」在表上方；
- 正文里的「图N」「表N」排成「图 N」「表 N」（图片路径不动）。
另加：条目紧跟段落时补空行，使 pandoc 认出列表；以及三处防空白：长表可在行与行之间分页（每页重复表头），表题与表同页，图与图题不拆开。
验收：PDF 里 Type 3 字体为 0；列出嵌入字体与页数。
用法：python3 build_paper_v1.py --md <论文.md> --out <新目录> [--name <输出文件名>]"""
import argparse, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
REF = os.path.join(HERE, 'build', 'reference.docx')
CSS = os.path.join(HERE, 'build', 'paper.css')


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit('失败：' + ' '.join(map(str, cmd[:3])))
    return r


def transform(md):
    """只改版式：图题、表题、正文里的图号表号空格、标题块。"""
    out, lines, i = [], md.split('\n'), 0
    title_done = False
    while i < len(lines):
        ln = lines[i]
        m = re.match(r'^!\[(S?图)(\d+)　(.*)\]\((.+)\)\s*$', ln)
        if m:
            out += ['::: fig', f'![]({m.group(4)})', '', f'**{m.group(1)} {m.group(2)}**　{m.group(3)}', ':::']
            i += 1
            continue
        if not title_done and ln.startswith('# '):
            sub = lines[i + 2] if i + 2 < len(lines) and lines[i + 2].startswith('——') else None
            out += ['::: titleblock', ln, '']
            if sub:
                out += [sub, '']
                i += 2
            out += [':::']
            title_done = True
            i += 1
            continue
        mt = re.match(r'^\*\*表(S?)(\d+)　(.*)\*\*\s*$', ln)
        if mt:
            out += ['::: tabtitle', f'**表 {mt.group(1)}{mt.group(2)}　{mt.group(3)}**', ':::']
            i += 1
            continue
        if not ln.startswith('![') and '](' not in ln:
            ln = re.sub(r'(图|表)(\d+)', r'\1 \2', ln)
        out.append(ln)
        i += 1
    # pandoc 要求列表前空一行：条目紧跟在段落后时补一个空行（只补空行，不改文字）
    LIST = re.compile(r'^\s*([-*]|\d+\.)\s')
    fixed = []
    for k, ln in enumerate(out):
        if LIST.match(ln) and fixed and fixed[-1].strip() and not LIST.match(fixed[-1]) and not fixed[-1].lstrip().startswith('|'):
            fixed.append('')
        fixed.append(ln)
    return '\n'.join(fixed)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--md', required=True); ap.add_argument('--out', required=True); ap.add_argument('--name')
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    os.makedirs(a.out)
    src = os.path.abspath(a.md)
    base = os.path.dirname(src)
    name = a.name or os.path.splitext(os.path.basename(src))[0]
    work = os.path.join(a.out, '_build')
    os.makedirs(work)
    md = transform(open(src, encoding='utf-8').read())
    for rel in sorted(set(re.findall(r'!\[\]\(([^)]+)\)', md))):
        os.makedirs(os.path.join(work, os.path.dirname(rel)), exist_ok=True)
        shutil.copyfile(os.path.join(base, rel), os.path.join(work, rel))
    open(os.path.join(work, 'paper.md'), 'w', encoding='utf-8').write(md)
    shutil.copyfile(CSS, os.path.join(work, 'paper.css'))
    docx = os.path.join(a.out, name + '.docx')
    run(['pandoc', os.path.join(work, 'paper.md'), '-o', docx, '--resource-path', work, '--reference-doc', REF])
    html = os.path.join(work, 'paper.html')
    run(['pandoc', os.path.join(work, 'paper.md'), '-s', '-o', html, '-c', 'paper.css', '--metadata', f'pagetitle={name}',
         '--resource-path', work, '-V', 'lang=zh-CN'])
    pdf = os.path.join(a.out, name + '.pdf')
    run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={pdf}', '--virtual-time-budget=20000',
         'file://' + html])
    fonts = run(['pdffonts', pdf]).stdout.splitlines()[2:]
    t3 = sum(1 for l in fonts if 'Type 3' in l)
    names = sorted({re.sub(r'^[A-Z]{6}\+', '', l.split()[0]) for l in fonts if l.strip()})
    pages = re.search(r'Pages:\s+(\d+)', run(['pdfinfo', pdf]).stdout).group(1)
    print({'docx': docx, 'pdf': pdf, 'pages': pages, 'type3': t3, 'fonts': names})
    if t3:
        sys.exit(1)


if __name__ == '__main__':
    main()
