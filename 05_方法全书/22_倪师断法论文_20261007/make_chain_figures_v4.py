"""倪师推理链论文（第十一稿）的全部插图 v4（只做呈现；数字全部取自已登记的结果文件，不新做统计）。
图1–图16 与 v3 完全相同（直接调用 make_chain_figures_v3 的各函数）；新增三张，对应《00h_三项补充研究方案_v2.md》的三项补充研究：
- 图17 认本人检验 M4e：三组的认对率与 Clopper–Pearson 95% 区间、瞎猜线、事先定的通过线；前作 M4d 两组作参照（只作描述）；
- 图18 推理类型：最终类型的分布与按 T 成团重抽的 95% 区间；右图分先天与运限；
- 图19 召回率：推理步与起步的召回率点估计、95% 区间与单侧下界（主口径与加两可）。
读（23_倪师推理链_20261007/chain_results_v1 下）：m4e_analysis_v1.json、types_final_v1.json、recall_v1.json，以及 v3 所读的全部文件。
另写 图中数字_chain_v4.json，供正文核数。用法：python3 make_chain_figures_v4.py --out <新目录>"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_chain_figures_v3 as F
from make_chain_figures_v3 import plt, W, BLUE, LBLUE, DBLUE, GRAY, LGRAY, RED, INK, INK2, MUTED, GRID, TEAL, AMBER, ORANGE, VIOLET, save, jl, CH, E

RS = os.path.join(CH, 'chain_results_v1')


# ---------------- 图17 认本人检验 ----------------
def fig_m4e(out, m):
    rows = [('链组（推理链）', m['arms']['链'], BLUE), ('平铺组（同一推理结果，平铺列出）', m['arms']['平'], LBLUE), ('第三版先天组', m['arms']['三'], TEAL)]
    ref = [('前作 M4d 全文组（含大限流年）', m['M4d认对题数']['full']), ('前作 M4d 综合论断组', m['M4d认对题数']['syn'])]
    n = m['n_items']
    fig, ax = plt.subplots(figsize=(W, 3.6), dpi=220)
    ys = list(range(len(rows) + len(ref)))[::-1]
    for (lab, a, col), y in zip(rows, ys):
        r = a['hits'] / n
        lo, hi = a['rate_CP95']
        ax.barh(y, r, height=.56, color=col, zorder=2)
        ax.plot([lo, hi], [y, y], color=INK, lw=1.1, zorder=3)
        for x in (lo, hi):
            ax.plot([x, x], [y - .12, y + .12], color=INK, lw=1.1, zorder=3)
        pv = a['p_binomial_one_sided']
        ax.text(hi + .015, y, f"{a['hits']}/{n}　p{'＜0.001' if pv < 0.001 else f'＝{pv:.3f}'}", va='center', fontsize=8, color=INK2)
    for (lab, k), y in zip(ref, ys[len(rows):]):
        ax.barh(y, k / n, height=.56, color='none', edgecolor=GRAY, hatch='////', lw=.8, zorder=2)
        ax.text(k / n + .015, y, f'{k}/{n}（只作参照）', va='center', fontsize=8, color=MUTED)
    ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows] + [r[0] for r in ref], fontsize=8.2)
    ax.axvline(.25, color=RED, lw=1.0, ls=(0, (3, 3)), zorder=1)
    ax.axvline(12 / n, color=MUTED, lw=.9, ls=(0, (1, 2)), zorder=1)
    ax.text(.25 - .008, ys[0] + .55, '瞎猜 1/4', color=RED, fontsize=7.6, ha='right', va='bottom')
    ax.text(12 / n + .008, ys[0] + .55, '通过线 12/28', color=MUTED, fontsize=7.6, ha='left', va='bottom')
    ax.set_xlim(0, 1.08); ax.set_ylim(ys[-1] - .6, ys[0] + .9)
    ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(['0', '0.25', '0.5', '0.75', '1'])
    ax.set_xlabel('认对率（横线为 Clopper–Pearson 95% 区间）')
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, lw=.6); ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, out, '图17_认本人检验.png')
    return {arm: {'k': m['arms'][arm]['hits'], 'p': m['arms'][arm]['p_binomial_one_sided'], 'CP95': m['arms'][arm]['rate_CP95'],
                  '名次和': m['arms'][arm]['rank_sum'], '名次p': m['arms'][arm]['p_rank_sum_one_sided']} for arm in ('链', '平', '三')} | {'M4d': m['M4d认对题数']}


# ---------------- 图18 推理类型 ----------------
TYPES = ['取象', '术数机理', '类属展开', '性情因果', '处境常理', '其他']
TCOL = {'取象': VIOLET, '术数机理': BLUE, '类属展开': TEAL, '性情因果': AMBER, '处境常理': ORANGE, '其他': GRAY}


def fig_types(out, t):
    d = t['类型分布·全部']
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 3.5), dpi=220, gridspec_kw={'width_ratios': [1.25, 1]})
    ys = list(range(len(TYPES)))[::-1]
    for ty, y in zip(TYPES, ys):
        v = d[ty]; lo, hi = v['95%（按T成团重抽）'] or (None, None)
        a1.barh(y, v['比例'], height=.58, color=TCOL[ty], zorder=2)
        if lo is not None:
            a1.plot([lo, hi], [y, y], color=INK, lw=1.0, zorder=3)
        a1.text((hi or v['比例']) + .012, y, f"{v['条数']}（{v['比例'] * 100:.0f}%）", va='center', fontsize=8, color=INK2)
    a1.set_yticks(ys); a1.set_yticklabels(TYPES, fontsize=8.6)
    a1.set_xlim(0, max(d[ty]['95%（按T成团重抽）'][1] if d[ty]['95%（按T成团重抽）'] else d[ty]['比例'] for ty in TYPES) + .14)
    a1.set_xlabel(f"占 {d['n']} 条推理步的比例（横线为按出处成团重抽的 95% 区间）", fontsize=8)
    a1.set_title('全部推理步', loc='left', fontsize=9.4)
    for s in ('top', 'right', 'left'):
        a1.spines[s].set_visible(False)
    a1.tick_params(axis='y', length=0); a1.grid(axis='x', color=GRID, lw=.6); a1.set_axisbelow(True)
    groups = [('先天', t['类型分布·先天']), ('运限', t['类型分布·运限']), ('通则', t['类型分布·通则']), ('命例特指', t['类型分布·命例特指'])]
    left = [0] * len(groups)
    for ty in TYPES:
        vals = [g[1][ty]['比例'] for g in groups]
        a2.barh(range(len(groups))[::-1], vals, left=left, height=.58, color=TCOL[ty], edgecolor='white', lw=.6, label=ty)
        left = [l + v for l, v in zip(left, vals)]
    a2.set_yticks(range(len(groups))[::-1]); a2.set_yticklabels([f"{g[0]}（{g[1]['n']}）" for g in groups], fontsize=8.4)
    a2.set_xlim(0, 1); a2.set_xlabel('各类所占比例', fontsize=8)
    a2.set_title('分开看', loc='left', fontsize=9.4)
    for s in ('top', 'right', 'left'):
        a2.spines[s].set_visible(False)
    a2.tick_params(axis='y', length=0)
    a2.legend(loc='upper center', bbox_to_anchor=(.45, -.2), ncol=3, fontsize=7.6)
    fig.tight_layout()
    save(fig, out, '图18_推理类型.png')
    return {ty: {'条数': d[ty]['条数'], '比例': d[ty]['比例'], '区间': d[ty]['95%（按T成团重抽）']} for ty in TYPES} | \
           {'alpha': t['一致程度·全部']['类型']['alpha'], 'alpha区间': t['一致程度·全部']['类型']['alpha_95%（按T成团重抽）']}


# ---------------- 图19 召回率 ----------------
def fig_recall(out, r):
    items = [('推理步·明确漏', '推理步（主口径：只算明确漏）', BLUE), ('推理步·明确漏加两可', '推理步（明确漏加两可）', LBLUE),
             ('定性步·明确漏', '起步（只算明确漏）', TEAL), ('定性步·明确漏加两可', '起步（明确漏加两可）', '#9fdcc5')]
    fig, ax = plt.subplots(figsize=(W, 2.9), dpi=220)
    ys = list(range(len(items)))[::-1]
    for (k, lab, col), y in zip(items, ys):
        v = r['召回率'][k]
        lo, hi = v['95%区间（Gamma后验合成）']
        ax.plot([lo, hi], [y, y], color=col, lw=6, solid_capstyle='butt', zorder=2)
        ax.plot([v['召回率']], [y], 'o', color=INK, ms=5, zorder=3)
        ax.plot([v['单侧95%下界']] * 2, [y - .25, y + .25], color=RED, lw=1.2, zorder=3)
        ax.text(hi + .01, y, f"{v['召回率']:.2f}（区间 {lo:.2f} 至 {hi:.2f}；至少 {v['单侧95%下界']:.2f}）", va='center', fontsize=8, color=INK2, clip_on=False)
    ax.set_yticks(ys); ax.set_yticklabels([i[1] for i in items], fontsize=8.4)
    lo_all = min(r['召回率'][k]['95%区间（Gamma后验合成）'][0] for k, _, _ in items)
    ax.set_xlim(max(0, round(lo_all - .1, 1)), 1.0)
    ax.set_xticks([t / 10 for t in range(int(round(max(0, lo_all - .1), 1) * 10), 11)])
    ax.set_xlabel('召回率（黑点＝点估计；色条＝95% 区间；红竖线＝单侧 95% 下界）', fontsize=8)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0); ax.grid(axis='x', color=GRID, lw=.6); ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, out, '图19_召回率.png')
    return {k: {kk: r['召回率'][k][kk] for kk in ('召回率', '95%区间（Gamma后验合成）', '单侧95%下界', 'M估计')} for k, _, _ in items}


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
    rec['图17'] = fig_m4e(a.out, jl(RS, 'm4e_analysis_v1.json'))
    rec['图18'] = fig_types(a.out, jl(RS, 'types_final_v1.json'))
    rec['图19'] = fig_recall(a.out, jl(RS, 'recall_v1.json'))
    open(os.path.join(a.out, '图中数字_chain_v4.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'out': sorted(os.listdir(a.out))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
