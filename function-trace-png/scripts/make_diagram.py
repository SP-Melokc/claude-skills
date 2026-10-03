#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""function-trace-png —— 把带 [[X]] 标记的"调用链树"渲染成带注解的 PNG 调用图。

用法:
    python make_diagram.py tree.txt                 # 处理文件里所有 @@@ 段
    python make_diagram.py tree.txt --scale 2       # 2x 高清(默认)
    python make_diagram.py tree.txt --outdir imgs   # 指定输出目录

tree.txt 格式(可含多张图, 用 @@@ 分段):
    @@@ 输出文件名 | 图的标题 | 副标题(可空)
    khugepaged_do_scan()                 [[D]]// 注释[[/]]
      └─ [[B]]collapse_scan_mm_slot()[[/]]
           ...

颜色标记(必须用真标记, 不是 \\033):
    [[C]]青  [[B]]蓝  [[Y]]黄  [[P]]紫  [[G]]绿  [[W]]白  [[R]]红  [[D]]灰
    [[/]] 闭合。每行若没闭合, 脚本会自动补, 防止颜色漏到下一行。
    语义: C=框架/承接入口  B=核心入口(本图根)  Y=骨干函数  P=叶子子函数
          G=分配/创建  W=关键变量/锁  R=关键转折/失败★  D=注释与"为什么"

输出: 每个 @@@ 段生成 <输出文件名>.html 和 <输出文件名>.png。
"""
import sys, os, io, html, argparse, subprocess, tempfile, shutil

COLORS = {'C': 'c', 'B': 'b', 'Y': 'y', 'P': 'p', 'G': 'g', 'W': 'w', 'R': 'r', 'D': 'd'}

CSS = """
  html,body { margin:0; padding:0; background:#0d1117; }
  body { padding:34px 42px; }
  h1 { font: 700 26px Consolas,"Cascadia Mono","DejaVu Sans Mono",monospace; color:#e8edf2; margin:0 0 6px; }
  .sub { font: 15px Consolas,"Cascadia Mono","DejaVu Sans Mono",monospace; color:#7d8794; margin:0 0 20px; }
  pre { font: 15px/23px Consolas,"Cascadia Mono","DejaVu Sans Mono",monospace; color:#c9d1d9; white-space:pre; margin:0; }
  .c{color:#34d3eb;font-weight:700} .b{color:#4d9bff;font-weight:700}
  .y{color:#ffd23f;font-weight:700} .p{color:#c792ea}
  .g{color:#5ad07a;font-weight:700} .w{color:#ffffff;font-weight:700}
  .r{color:#ff6b6b;font-weight:700} .d{color:#7d8794}
  .lg { font: 14px Consolas,"Cascadia Mono","DejaVu Sans Mono",monospace; margin-top:22px; color:#7d8794; }
"""

DOC = """<!doctype html>
<html><head><meta charset="utf-8"><style>%s</style></head>
<body>
  <h1>%s</h1>
  <div class="sub">%s</div>
  <pre>%s</pre>
  <div class="lg">
    <span class="c">青=框架/承接</span> &nbsp; <span class="b">蓝=核心入口(本图根)</span> &nbsp;
    <span class="y">黄=骨干函数</span> &nbsp; <span class="p">紫=叶子子函数</span> &nbsp;
    <span class="g">绿=分配/创建</span> &nbsp; <span class="w">白=关键变量/锁</span> &nbsp;
    <span class="r">红=关键转折/失败&#9733;</span> &nbsp; <span class="d">灰=注释与"为什么"</span>
  </div>
</body></html>"""


def render_tree(tree):
    out_lines = []
    for line in tree.split('\n'):
        esc = html.escape(line, quote=False)
        for key, cls in COLORS.items():
            esc = esc.replace('[[%s]]' % key, '<span class="%s">' % cls)
        esc = esc.replace('[[/]]', '</span>')
        opens = esc.count('<span')
        closes = esc.count('</span>')
        if opens > closes:                      # 每行自动闭合, 防止漏色
            esc += '</span>' * (opens - closes)
        out_lines.append(esc)
    return '\n'.join(out_lines)


def parse_sections(text):
    secs, cur = [], None
    for line in text.split('\n'):
        if line.lstrip().startswith('@@@'):
            head = line.split('@@@', 1)[1].strip()
            parts = [p.strip() for p in head.split('|')]
            name = parts[0] or 'diagram'
            title = parts[1] if len(parts) > 1 and parts[1] else name
            sub = parts[2] if len(parts) > 2 else ''
            cur = {'name': name, 'title': title, 'sub': sub, 'body': []}
            secs.append(cur)
        elif cur is not None:
            cur['body'].append(line)
    for s in secs:
        s['tree'] = '\n'.join(s['body']).strip('\n')
    return [s for s in secs if s['tree']]


def find_browser():
    cands = [
        os.environ.get('EDGE_BIN'), os.environ.get('CHROME_BIN'),
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        shutil.which('msedge'), shutil.which('google-chrome'),
        shutil.which('chromium'), shutil.which('chrome'),
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def to_png(browser, html_path, png_path, w, h, scale, user_dir):
    url = 'file:///' + os.path.abspath(html_path).replace('\\', '/')
    cmd = [browser, '--headless=new', '--disable-gpu', '--hide-scrollbars',
           '--force-device-scale-factor=%d' % scale, '--no-first-run',
           '--no-default-browser-check', '--user-data-dir=%s' % user_dir,
           '--screenshot=%s' % os.path.abspath(png_path),
           '--window-size=%d,%d' % (w + 20, h + 20), url]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    return os.path.exists(png_path)


def main():
    ap = argparse.ArgumentParser(description='渲染带注解的调用图 PNG')
    ap.add_argument('tree', help='树文本文件(可含多个 @@@ 段)')
    ap.add_argument('--outdir', default=None, help='输出目录(默认=树文件所在目录)')
    ap.add_argument('--scale', type=int, default=2, help='设备像素比, 默认 2x')
    args = ap.parse_args()

    with io.open(args.tree, 'r', encoding='utf-8') as f:
        text = f.read()
    secs = parse_sections(text)
    if not secs:
        print('ERROR: 没找到任何 @@@ 段, 检查树文件格式', file=sys.stderr)
        return 1

    outdir = args.outdir or os.path.dirname(os.path.abspath(args.tree))
    os.makedirs(outdir, exist_ok=True)
    browser = find_browser()
    tmpdir = tempfile.mkdtemp(prefix='ftpng_')

    for s in secs:
        lines = s['tree'].split('\n')
        maxlen = max(len(l) for l in lines)
        w = int(maxlen * 8.6) + 120
        h = int(len(lines) * 23 + 250)
        body = render_tree(s['tree'])
        doc = DOC % (CSS, html.escape(s['title']), s['sub'], body)
        html_path = os.path.join(outdir, s['name'] + '.html')
        png_path = os.path.join(outdir, s['name'] + '.png')
        with io.open(html_path, 'w', encoding='utf-8') as f:
            f.write(doc)
        if browser:
            ok = to_png(browser, html_path, png_path, w, h, args.scale, tmpdir)
            print('%s  ->  %s' % (s['name'], png_path if ok else '(渲染失败, 只出了 HTML)'))
        else:
            print('%s  ->  %s  (没找到 Edge/Chrome, 只出了 HTML)' % (s['name'], html_path))

    shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
