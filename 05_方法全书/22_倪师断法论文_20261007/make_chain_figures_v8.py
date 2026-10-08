"""倪师推理链论文第十六稿的插图 v8（只做呈现；数字全部取自已登记的结果文件）。v7 原样保留，v8 只改图01 与图09：
- 图01：第十五稿内审第二轮（V1-3、V3-2）——表3 与 7.1 已把「忠实度」改称「核查」，⑧ 框的「忠实」随之改为「核查」。
  函数照抄 v7 的 fig_pipeline_v7，只改这一处文字；框的位置、大小、配色与数字来源都不变。
- 图09：第十四稿内审（R2-3）指出「至少 0.83」会被当成有保证的底线；正文已改为「单侧 95% 下界」，
  每条的标注随之从「至少 x」改为「单侧下界 x」，横轴说明加「只算抽样误差」。画法、配色、数据与 v5 的 fig_recall 相同。
其余正文 7 张、补充材料 12 张从 figures_chain_v7 原样复制。另写 图中数字_chain_v8.json。
用法：python3 make_chain_figures_v8.py --out <新目录>"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_chain_figures_v3 as F
import make_chain_figures_v4 as G
from make_chain_figures_v3 import plt, W, INK, INK2, MUTED, GRID, GRAY, RED, save, jl, CH, dcanvas, box, arrow, FILL, FILL3, FILL5, BLUE, TEAL, AMBER

V7 = os.path.join(HERE, 'figures_chain_v7')
RS = os.path.join(CH, 'chain_results_v1')


def fig_pipeline_v8(out, adj, chk, norm, kb):
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
             '⑧ 检验：核查、覆盖、可追溯、主检验（复现命例）\n补充研究：认本人（两次）、推理方式、召回率']
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


def fig_recall_v8(out, r):
    items = [('推理步·明确漏', '推理步（主口径：只算明确漏）', G.BLUE), ('推理步·明确漏加两可', '推理步（明确漏加两可）', G.LBLUE),
             ('定性步·明确漏', '起步（只算明确漏）', G.TEAL), ('定性步·明确漏加两可', '起步（明确漏加两可）', '#9fdcc5')]
    fig, ax = plt.subplots(figsize=(W, 3.0), dpi=220)
    ys = list(range(len(items)))[::-1]
    for (k, lab, col), y in zip(items, ys):
        v = r['召回率'][k]
        lo, hi = v['95%区间（Gamma后验合成）']
        ax.plot([lo, hi], [y, y], color=col, lw=6, solid_capstyle='butt', zorder=2)
        ax.plot([v['召回率']], [y], 'o', color=INK, ms=5, zorder=3)
        ax.plot([v['单侧95%下界']] * 2, [y - .25, y + .25], color=RED, lw=1.2, zorder=3)
        ax.text(hi + .01, y, f"{v['召回率']:.2f}（区间 {lo:.2f} 至 {hi:.2f}；单侧下界 {v['单侧95%下界']:.2f}）", va='center', fontsize=8, color=INK2, clip_on=False, zorder=4,
                bbox=dict(facecolor=F.SURFACE, edgecolor='none', pad=1.2))
    ax.axvline(.8, color=GRAY, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.text(.8, ys[0] + .55, '判定线 0.8', color=MUTED, fontsize=7.6, ha='center', va='bottom')
    ax.set_yticks(ys); ax.set_yticklabels([i[1] for i in items], fontsize=8.4)
    lo_all = min(r['召回率'][k]['95%区间（Gamma后验合成）'][0] for k, _, _ in items)
    x0 = max(0, round(lo_all - .1, 1))
    ax.set_xlim(x0, 1.0); ax.set_ylim(ys[-1] - .6, ys[0] + .95)
    ax.set_xticks([t_ / 10 for t_ in range(int(x0 * 10), 11)])
    ax.set_xlabel('召回率（黑点＝点估计；色条＝95% 区间；红竖线＝单侧 95% 下界，只算抽样误差）', fontsize=8)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0); ax.grid(axis='x', color=GRID, lw=.6); ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, out, '图09_召回率.png')
    return {k: {kk: r['召回率'][k][kk] for kk in ('召回率', '95%区间（Gamma后验合成）', '单侧95%下界')} for k, _, _ in items}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out)
    os.makedirs(os.path.join(a.out, '补充'))
    for f in sorted(os.listdir(V7)):
        if f.endswith('.png') and f not in ('图01_总流程.png', '图09_召回率.png'):
            shutil.copy2(os.path.join(V7, f), os.path.join(a.out, f))
    for f in sorted(os.listdir(os.path.join(V7, '补充'))):
        shutil.copy2(os.path.join(V7, '补充', f), os.path.join(a.out, '补充', f))
    rec = json.load(open(os.path.join(V7, '图中数字_chain_v7.json'), encoding='utf-8'))
    M = os.path.join(CH, 'chain_merged_v1')
    rec['图01（v8 重画，⑧ 框「忠实」改「核查」）'] = fig_pipeline_v8(a.out, jl(M, 'adjudicated_v1.json'), jl(M, 'check_v1.json'), jl(M, 'normalized_v1.json'), jl(CH, 'chain_kb_v1.json'))
    rec['图09（v8 重画，只改标注用词）'] = fig_recall_v8(a.out, jl(RS, 'recall_v1.json'))
    open(os.path.join(a.out, '图中数字_chain_v8.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'正文图': len([f for f in os.listdir(a.out) if f.endswith('.png')]), '补充图': len(os.listdir(os.path.join(a.out, '补充')))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
