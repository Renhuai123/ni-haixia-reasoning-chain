"""倪师推理链论文（第十二稿）的全部插图 v5（只做呈现；数字全部取自已登记的结果文件）。v4 原样保留，v5 只按第四轮内审改图18、图19：
- 图18 左栏「其他」只画区间横线、不画柱、不标条数（事先的解读规则：特定一致率 < 0.5 的类只报区间）；右栏两种分法之间留空、各加小标题，
  条内标出 10% 以上各段的百分比，不画「其他」一段（条末空白）；
- 图19 加事先定的判定线 0.8（灰虚线）。
图1–图17 与 v4 完全相同（直接调用 v3、v4 的函数）。另写 图中数字_chain_v5.json。用法：python3 make_chain_figures_v5.py --out <新目录>"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_chain_figures_v3 as F
import make_chain_figures_v4 as G
from make_chain_figures_v3 import plt, W, INK, INK2, MUTED, GRID, GRAY, RED, save, jl, CH, E
from make_chain_figures_v4 import TYPES, TCOL, RS

MAIN5 = [t for t in TYPES if t != '其他']


def fig_types(out, t):
    d = t['类型分布·全部']
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 3.7), dpi=220, gridspec_kw={'width_ratios': [1.2, 1]})
    ys = list(range(len(TYPES)))[::-1]
    for ty, y in zip(TYPES, ys):
        v = d[ty]; lo, hi = v['95%（按T成团重抽）']
        if ty == '其他':
            a1.plot([lo, hi], [y, y], color=GRAY, lw=1.6, zorder=3)
            for x in (lo, hi):
                a1.plot([x, x], [y - .14, y + .14], color=GRAY, lw=1.2, zorder=3)
            a1.text(hi + .012, y, f'只报区间（{lo * 100:.1f}%–{hi * 100:.1f}%）', va='center', fontsize=7.8, color=MUTED)
            continue
        a1.barh(y, v['条数'] / d['n'], height=.58, color=TCOL[ty], zorder=2)
        a1.plot([lo, hi], [y, y], color=INK, lw=1.0, zorder=3)
        a1.text(hi + .012, y, f"{v['条数']}（{v['条数'] / d['n'] * 100:.0f}%）", va='center', fontsize=8, color=INK2)
    a1.set_yticks(ys); a1.set_yticklabels(TYPES, fontsize=8.6)
    a1.set_xlim(0, max(d[ty]['95%（按T成团重抽）'][1] for ty in TYPES) + .16)
    a1.set_xlabel(f"占 {d['n']} 条推理步的比例（横线为按出处成团重抽的 95% 区间）", fontsize=8)
    a1.set_title('全部推理步', loc='left', fontsize=9.4)
    for s in ('top', 'right', 'left'):
        a1.spines[s].set_visible(False)
    a1.tick_params(axis='y', length=0); a1.grid(axis='x', color=GRID, lw=.6); a1.set_axisbelow(True)
    groups = [('先天', '类型分布·先天', 4.0), ('运限', '类型分布·运限', 3.0), ('通则', '类型分布·通则', 1.0), ('命例特指', '类型分布·命例特指', 0.0)]
    for name, k, y in groups:
        g = t[k]; left = 0.0
        for ty in MAIN5:
            v = g[ty]['条数'] / g['n']
            a2.barh(y, v, left=left, height=.62, color=TCOL[ty], edgecolor='white', lw=.6)
            if v >= .10:
                a2.text(left + v / 2, y, f'{v * 100:.0f}', ha='center', va='center', fontsize=7.2, color='white')
            left += v
    a2.set_yticks([g[2] for g in groups]); a2.set_yticklabels([f"{g[0]}（{t[g[1]]['n']}）" for g in groups], fontsize=8.4)
    a2.text(-.02, 4.62, '按适用分', fontsize=7.8, color=MUTED, transform=a2.get_yaxis_transform(), ha='right')
    a2.text(-.02, 1.62, '按命例特指分', fontsize=7.8, color=MUTED, transform=a2.get_yaxis_transform(), ha='right')
    a2.axhline(2.0, color=GRID, lw=.8)
    a2.set_xlim(0, 1); a2.set_ylim(-.6, 5.0); a2.set_xlabel('各类所占比例（条内数字为百分比；条末空白为「其他」）', fontsize=8)
    a2.set_title('分开看', loc='left', fontsize=9.4)
    for s in ('top', 'right', 'left'):
        a2.spines[s].set_visible(False)
    a2.tick_params(axis='y', length=0)
    from matplotlib.patches import Patch
    a2.legend(handles=[Patch(color=TCOL[ty], label=ty) for ty in MAIN5], loc='upper center', bbox_to_anchor=(.45, -.2), ncol=3, fontsize=7.6)
    fig.tight_layout()
    save(fig, out, '图18_推理类型.png')
    return {ty: {'条数': d[ty]['条数'], '区间': d[ty]['95%（按T成团重抽）']} for ty in TYPES}


def fig_recall(out, r):
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
        ax.text(hi + .01, y, f"{v['召回率']:.2f}（区间 {lo:.2f} 至 {hi:.2f}；至少 {v['单侧95%下界']:.2f}）", va='center', fontsize=8, color=INK2, clip_on=False, zorder=4,
                bbox=dict(facecolor=F.SURFACE, edgecolor='none', pad=1.2))
    ax.axvline(.8, color=GRAY, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.text(.8, ys[0] + .55, '判定线 0.8', color=MUTED, fontsize=7.6, ha='center', va='bottom')
    ax.set_yticks(ys); ax.set_yticklabels([i[1] for i in items], fontsize=8.4)
    lo_all = min(r['召回率'][k]['95%区间（Gamma后验合成）'][0] for k, _, _ in items)
    x0 = max(0, round(lo_all - .1, 1))
    ax.set_xlim(x0, 1.0); ax.set_ylim(ys[-1] - .6, ys[0] + .95)
    ax.set_xticks([t_ / 10 for t_ in range(int(x0 * 10), 11)])
    ax.set_xlabel('召回率（黑点＝点估计；色条＝95% 区间；红竖线＝单侧 95% 下界）', fontsize=8)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0); ax.grid(axis='x', color=GRID, lw=.6); ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, out, '图19_召回率.png')
    return {k: {kk: r['召回率'][k][kk] for kk in ('召回率', '95%区间（Gamma后验合成）', '单侧95%下界')} for k, _, _ in items}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out)
    M = os.path.join(CH, 'chain_merged_v1')
    adj, chk, norm = jl(M, 'adjudicated_v1.json'), jl(M, 'check_v1.json'), jl(M, 'normalized_v1.json')
    labels_all = jl(CH, 'chain_norm_packets_v1', 'labels_all.json')
    kb = jl(CH, 'chain_kb_v1.json')
    cov, rep, diag, ex, post, post2 = (jl(RS, f) for f in ('coverage_v1.json', 'reproduce_v1.json', 'reproduce_diag_v1.json', 'example_r30_v1.json', 'posthoc_v1.json', 'posthoc2_v1.json'))
    chart = next(r for r in jl(E, 'freeze_check_v1', 'rand_charts.json')['rows'] if r['id'] == 'r30')
    rec = {}
    rec['图1'] = F.fig_pipeline(a.out, adj, chk, norm, kb)
    rec['图2'] = F.fig_layers(a.out, kb)
    rec['图3'] = F.fig_anatomy(a.out, kb)
    rec['图4'] = F.fig_extract_check(a.out, adj, chk)
    rec['图5'] = F.fig_normalize(a.out, norm, labels_all)
    rec['图6'] = F.fig_layer_matrix(a.out, kb)
    rec['图7'] = F.fig_hubs(a.out, kb)
    F.fig_algorithm(a.out)
    rec['图9'] = F.fig_example_chart(a.out, chart)
    rec['图10'] = F.fig_r30_chain(a.out, ex, kb)
    rec['图11'] = F.fig_v3_v4(a.out, ex)
    rec['图12'] = F.fig_coverage(a.out, cov, os.path.join(CH, 'chain_kb_v1.json'), os.path.join(CH, 'v4_holdout_v1', 'holdout_charts.json'), ex, post)
    F.fig_test_design(a.out)
    rec['图14'] = F.fig_test_result(a.out, rep, diag)
    rec['图15'] = F.fig_diag(a.out, diag)
    rec['图16'] = F.fig_posthoc(a.out, post, post2, rep)
    rec['图17'] = G.fig_m4e(a.out, jl(RS, 'm4e_analysis_v1.json'))
    rec['图18'] = fig_types(a.out, jl(RS, 'types_final_v1.json'))
    rec['图19'] = fig_recall(a.out, jl(RS, 'recall_v1.json'))
    open(os.path.join(a.out, '图中数字_chain_v5.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'out': sorted(os.listdir(a.out))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
