"""倪师推理链论文第十五稿的插图 v7（只做呈现；数字全部取自已登记的结果文件）。v6 原样保留，v7 只改图01：
- 第十四稿内审（R1-18、R5-9、R6-13）指出图01 ⑧ 框只写「四项检验」，与表3 的检验加补充研究对不上；
  v7 把 ⑧ 框改为「⑧ 检验：忠实、覆盖、可追溯、主检验（复现命例）」，下加一行「补充研究：认本人（两次）、推理方式、召回率」。
  框的位置、大小、配色与其余七框完全照 v3 的 fig_pipeline，数字照旧从同一批结果文件读。
其余正文 8 张、补充材料 12 张从 figures_chain_v6 原样复制。另写 图中数字_chain_v7.json（图01 的数字与 v6 相同时照抄 v6 的其余各图）。
用法：python3 make_chain_figures_v7.py --out <新目录>"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_chain_figures_v3 as F
from make_chain_figures_v3 import jl, CH, dcanvas, box, arrow, save, FILL, FILL3, FILL5, BLUE, TEAL, AMBER, MUTED

V6 = os.path.join(HERE, 'figures_chain_v6')


def fig_pipeline_v7(out, adj, chk, norm, kb):
    a = adj['一致程度']['按步·甲乙各自']
    jia, yi = a['甲·收'] + a['甲·不收'], a['乙·收'] + a['乙·不收']
    c = chk['counts']
    ok, bad = c['定性步成立'] + c['推理步成立'], c['定性步不成立'] + c['推理步不成立']
    kc = kb['counts']
    n_q = adj['一致程度']['按条']['条目']
    left = [f'① 讲稿原话\n《天纪》倪海厦原话 {n_q} 条，分 35 批',
            f'② 抽取（AI 甲、乙各自独立）\n甲抽出 {jia} 步，乙抽出 {yi} 步',
            f"③ 裁定（第三个 AI）\n定稿 {adj['counts']['定稿步']} 步：起步 {adj['counts']['定性步']}、推理步 {adj['counts']['推理步']}",
            f'④ 逐步核查（第四个 AI）\n判成立 {ok} 步；不成立的 {bad} 步不进库']
    right = [f"⑤ 判断归一（两个 AI 归类，一个裁定）\n{norm['counts']['判断名']} 个判断名归成 {norm['counts']['结点']} 个结点",
             f"⑥ 推理链知识库\n{kc['收下的步']} 步、{kc['结点']} 个结点\n先天且可操作的 {kc['引擎可用（可操作且先天）']} 步进引擎",
             '⑦ 引擎第四版\n每一宫从盘面起，一轮一轮往后推',
             '⑧ 检验：忠实、覆盖、可追溯、主检验（复现命例）\n补充研究：认本人（两次）、推理方式、召回率']
    bw, bh, gap = 29.6, 7.4, 2.8
    H = 4 * bh + 3 * gap + 1.2
    fig, ax = dcanvas(H / 10)
    xs = (1.2, 35.2)
    tops = [H - .6 - bh - k * (bh + gap) for k in range(4)]
    for col, items in enumerate((left, right)):
        for k, t in enumerate(items):
            fc, ec = (FILL, BLUE) if col == 0 else ((FILL5, TEAL) if k < 3 else (FILL3, AMBER))
            box(ax, xs[col], tops[k], bw, bh, t, fc=fc, ec=ec, fs=8.6, ha='left')
            if k:
                arrow(ax, xs[col] + bw / 2, tops[k - 1], xs[col] + bw / 2, tops[k] + bh)
    gx = (xs[0] + bw + xs[1]) / 2
    y4, y5 = tops[3] + bh / 2, tops[0] + bh / 2
    ax.plot([xs[0] + bw, gx, gx], [y4, y4, y5], color=MUTED, lw=1.1)
    arrow(ax, gx, y5, xs[1], y5)
    save(fig, out, '图01_总流程.png')
    return {'条目': n_q, '甲抽出': jia, '乙抽出': yi, '定稿': adj['counts']['定稿步'], '核查成立': ok, '核查不成立': bad,
            '判断名': norm['counts']['判断名'], '结点（归一表）': norm['counts']['结点'], '知识库步': kc['收下的步'], '知识库结点': kc['结点'],
            '引擎可用': kc['引擎可用（可操作且先天）']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out)
    os.makedirs(os.path.join(a.out, '补充'))
    for f in sorted(os.listdir(V6)):
        if f.endswith('.png') and f != '图01_总流程.png':
            shutil.copy2(os.path.join(V6, f), os.path.join(a.out, f))
    for f in sorted(os.listdir(os.path.join(V6, '补充'))):
        shutil.copy2(os.path.join(V6, '补充', f), os.path.join(a.out, '补充', f))
    M = os.path.join(CH, 'chain_merged_v1')
    adj, chk, norm = jl(M, 'adjudicated_v1.json'), jl(M, 'check_v1.json'), jl(M, 'normalized_v1.json')
    kb = jl(CH, 'chain_kb_v1.json')
    rec = json.load(open(os.path.join(V6, '图中数字_chain_v6.json'), encoding='utf-8'))
    new1 = fig_pipeline_v7(a.out, adj, chk, norm, kb)
    rec['图01（v7 重画，只改 ⑧ 框文字）'] = new1
    open(os.path.join(a.out, '图中数字_chain_v7.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'图01': new1, '复制正文图': len([f for f in os.listdir(a.out) if f.endswith('.png')]), '复制补充图': len(os.listdir(os.path.join(a.out, '补充')))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
