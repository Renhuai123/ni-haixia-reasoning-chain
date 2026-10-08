"""倪师推理链论文第十七稿的插图 v9（只做呈现；数字全部取自已登记的结果文件）。v8 原样保留，v9 只改图04：
- 第十六稿内审第三轮（W1-5）：图04 里「先生不好」由「个性强」推出，但按列等距铺开时它离「佐才」更近，印刷稿上箭头起点容易看错。
  v9 只改纵向排法：从第 1 步起，每个判断尽量放在它的前提（第 1 步是盘面条件）的平均高度，按这个高度从上到下排，挤不下就依次往下错开；
  框、颜色、线型、图例、数据与 v3 的 fig_r30_chain 完全相同（函数照抄，只换排法一段）。
其余各图从 figures_chain_v8 原样复制。另写 图中数字_chain_v9.json。用法：python3 make_chain_figures_v9.py --out <新目录>"""
import argparse, collections, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_chain_figures_v3 as F
from make_chain_figures_v3 import plt, Patch, INK, INK2, GRID, GRAY, FILL2, LAYER_COL, C, lc, dcanvas, box, arrow, note, save, jl, CH

V8 = os.path.join(HERE, 'figures_chain_v8')
RS = os.path.join(CH, 'chain_results_v1')


def fig_r30_chain_v9(out, ex, kb):
    case = {s['step_id']: s['命例特指'] for s in kb['steps']}
    DASH = (0, (2.2, 1.6))
    nodes = ex['第四版·命宫结点']
    name2id = {}
    for n, v in nodes.items():
        assert v['名'] not in name2id, ('命宫里有同名结点', v['名'])
        name2id[v['名']] = n
    ends = [p[-1] for p in ex['第四版·命宫主线']]
    keep, stack = set(), [name2id[e] for e in ends]
    while stack:
        n = stack.pop()
        if n in keep:
            continue
        keep.add(n)
        stack += nodes[n]['推法'][0]['premises']
    first = {n: nodes[n]['推法'][0] for n in keep}
    depth = {n: first[n]['depth'] for n in keep}
    maxd = max(depth.values())
    kids = collections.defaultdict(set)
    for n in keep:
        for p in first[n]['premises']:
            kids[p].add(n)
    def subtree(n, seen=None):
        seen = set() if seen is None else seen
        for k in kids[n]:
            if k not in seen:
                seen.add(k); subtree(k, seen)
        return seen
    def cond_label(x):
        t = '、'.join(c.replace('本宫有:', '有').replace('本宫化:', '化').replace('三方四正有:', '三方四正有').replace(',', '、') for c in (x['条件'] or []))
        return ('命宫' if not t.startswith('三方') else '') + t + ('（借对宫）' if '借' in x['via'] else '')
    conds = []
    for n in keep:
        if depth[n] == 1 and cond_label(first[n]) not in conds:
            conds.append(cond_label(first[n]))
    pref = ['命宫有武曲、贪狼（借对宫）', '命宫有贪狼（借对宫）', '命宫化权（借对宫）', '三方四正有天府、天相']
    conds = [c for c in pref if c in conds] + sorted(c for c in conds if c not in pref)
    pos_idx = {('c', c): i for i, c in enumerate(conds)}
    cols = {0: [('c', c) for c in conds]}
    for d in range(1, maxd + 1):
        def key(n):
            x = first[n]
            ps = [pos_idx[('c', cond_label(x))]] if d == 1 else [pos_idx[('n', p)] for p in x['premises']]
            return (sum(ps) / len(ps), -len(subtree(n)), nodes[n]['名'])
        ns = sorted((n for n in keep if depth[n] == d), key=key)
        for i, n in enumerate(ns):
            pos_idx[('n', n)] = i
        cols[d] = [('n', n) for n in ns]
    nmax = max(len(v) for v in cols.values())
    bh, gap = 4.6, 1.4
    H = nmax * (bh + gap) + 11.0
    fig, ax = dcanvas(H / 10)
    colw = 66.0 / (maxd + 1)
    w = colw - 3.4
    pos = {}
    step = bh + gap
    c_top = (H - 3.4 + 6.0) / 2 + (nmax * step - gap) / 2 - bh / 2      # 最高一格的框中心
    c_bot = c_top - (nmax - 1) * step                                   # 最低一格的框中心
    center = {}
    for d, items in cols.items():
        if d == 0:
            tot = len(items) * step - gap
            y_top = (H - 3.4 + 6.0) / 2 + tot / 2
            for i, it in enumerate(items):
                center[it] = y_top - i * step - bh / 2
            continue
        # v9：每个判断尽量放在前提（或盘面条件）的平均高度，按这个高度从上到下排，挤不下就依次往下错开
        def want(it):
            x0 = first[it[1]]
            ps = [('c', cond_label(x0))] if d == 1 else [('n', p) for p in x0['premises']]
            return sum(center[p] for p in ps) / len(ps)
        order = sorted(items, key=lambda it: (-want(it), items.index(it)))
        cs = []
        for k, it in enumerate(order):
            c = min(want(it), c_top) if k == 0 else min(want(it), cs[-1] - step)
            cs.append(c)
        if cs[-1] < c_bot:                       # 整列往上挪，保证不出画面
            sh = c_bot - cs[-1]
            cs = [c + sh for c in cs]
        for it, c in zip(order, cs):
            center[it] = c
    for d, items in cols.items():
        for it in items:
            x = d * colw + (colw - w) / 2 + .8
            y = center[it] - bh / 2
            if it[0] == 'c':
                txt = '三方四正有\n天府、天相' if it[1].startswith('三方') else it[1].replace('（借对宫）', '\n（借对宫）')
                box(ax, x, y, w, bh, txt, fc='white', ec=GRID, fs=7.2)
            else:
                v, x0 = nodes[it[1]], first[it[1]]
                fem = '性别:女' in (x0['附加条件'] or []) + (x0['条件'] or [])
                fc, ec = lc(v['层'])
                box(ax, x, y, w, bh, f"{v['名']}\n{v['层']}｜{x0['T']}" + ('·女命' if fem else ''), fc=fc, ec=ec, fs=7.6)
            pos[it] = (x, y)
    for n in keep:
        x = first[n]
        xb, yb = pos[('n', n)]
        cs = case[x['step']]
        col, lw_, ls_ = (INK2, .9, DASH) if cs else (GRAY, .8, '-')
        if depth[n] == 1:
            xa, ya = pos[('c', cond_label(x))]
            arrow(ax, xa + w, ya + bh / 2, xb, yb + bh / 2, color=col, lw=lw_, ls=ls_)
        elif len(x['premises']) == 1:
            xa, ya = pos[('n', x['premises'][0])]
            arrow(ax, xa + w, ya + bh / 2, xb, yb + bh / 2, color=col, lw=lw_, ls=ls_)
        else:   # 几个前提要同时成立：先汇到一点，标「且」，再进结论
            jx, jy = xb - 1.5, yb + bh / 2
            for p in x['premises']:
                xa, ya = pos[('n', p)]
                ax.plot([xa + w, jx], [ya + bh / 2, jy], color=col, lw=lw_, ls=ls_)
            ax.plot([jx], [jy], 'o', color=INK2, ms=3.2)
            ax.text(jx - .3, jy + 1.1, '且', fontsize=7.2, color=INK, ha='right', va='center', fontweight='bold')
            arrow(ax, jx, jy, xb, jy, color=col, lw=lw_, ls=ls_)
    for d in range(maxd + 1):
        note(ax, d * colw + colw / 2 + .8, H - 1.4, '盘面' if d == 0 else f'第 {d} 步', fs=8.2, ha='center', color=INK2)
    present = sorted({nodes[n]['层'] for n in keep}, key=C.LAYER_ORDER.index)
    hs = [Patch(fc=lc(l)[0], ec=lc(l)[1], lw=.9, label=l) for l in present if l in LAYER_COL]
    if any(l not in LAYER_COL for l in present):
        hs.append(Patch(fc=FILL2, ec=GRAY, lw=.9, label='其余领域（此处为婚姻）' if set(l for l in present if l not in LAYER_COL) == {'婚姻'} else '其余领域'))
    hs.append(plt.Line2D([], [], color=INK2, lw=.9, ls=DASH, label='虚线：命例特指的步'))
    ax.legend(handles=hs, loc='lower center', bbox_to_anchor=(.5, 0.0), ncol=4, fontsize=7.4, frameon=False, handlelength=1.6)
    save(fig, out, '图04_示例盘的推理链.png')
    return {'结点': sorted(nodes[n]['名'] for n in keep), '最大深度': maxd, '盘面条件': conds, '命例特指的步': sorted({first[n]['step'] for n in keep if case[first[n]['step']]})}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out)
    os.makedirs(os.path.join(a.out, '补充'))
    for f in sorted(os.listdir(V8)):
        if f.endswith('.png') and f != '图04_示例盘的推理链.png':
            shutil.copy2(os.path.join(V8, f), os.path.join(a.out, f))
    for f in sorted(os.listdir(os.path.join(V8, '补充'))):
        shutil.copy2(os.path.join(V8, '补充', f), os.path.join(a.out, '补充', f))
    rec = json.load(open(os.path.join(V8, '图中数字_chain_v8.json'), encoding='utf-8'))
    rec['图04（v9 重画，只改纵向排法）'] = fig_r30_chain_v9(a.out, jl(RS, 'example_r30_v1.json'), jl(CH, 'chain_kb_v1.json'))
    open(os.path.join(a.out, '图中数字_chain_v9.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'正文图': len([f for f in os.listdir(a.out) if f.endswith('.png')]), '补充图': len(os.listdir(os.path.join(a.out, '补充')))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
