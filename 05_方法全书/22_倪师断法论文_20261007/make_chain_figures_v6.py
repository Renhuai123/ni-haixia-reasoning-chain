"""倪师推理链论文第十四稿的插图 v6（只做呈现；数字全部取自已登记的结果文件）。
正文 9 张：
  图01 总流程、图02 七层与真实的链、图03 抽取与核查、图04 示例盘的推理链、图05 覆盖、图06 主检验结果、图09 召回率
    —— 直接复制第十三稿已定稿的 figures_chain_v5 里对应的图（内容不变，只改编号）；
  图07 认本人检验（第二次，M4f）—— 新画：三组的选中焦点比例与 95% 区间，第一次（M4e 链组）作参照；两种对比的平均差与 95% 区间；
  图08 推理方式 —— 新画：起步、推理步、《全书》断语的构成（定名·象名、定名·义名、断事各类），以及断事里五种依据与「明说道理」的比例。
    受事先写定的解读规则约束：某组类型 α < 0.4 不画该组构成；某项 α < 0.4 不画该项；特定一致率 < 0.5 的类只画斜线、不标数。
补充材料 12 张：figures_chain_v5 的其余各图按 S 编号复制到 <out>/补充/。
另写 图中数字_chain_v6.json。用法：python3 make_chain_figures_v6.py --m4f <m4f 结果.json> --trad <传统框架结果.json> --out <新目录>"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_chain_figures_v3 import SURFACE, plt, W, BLUE, LBLUE, DBLUE, GRAY, LGRAY, RED, INK, INK2, MUTED, GRID, TEAL, AMBER, ORANGE, VIOLET, save, jl, CH

V5 = os.path.join(HERE, 'figures_chain_v5')
COPY_MAIN = {'图01_总流程.png': '图01_总流程.png', '图02_七层与真实的链.png': '图02_七层与真实的链.png', '图04_抽取与核查.png': '图03_抽取与核查.png',
             '图10_示例盘的推理链.png': '图04_示例盘的推理链.png', '图12_覆盖.png': '图05_覆盖.png', '图14_主检验结果.png': '图06_主检验结果.png',
             '图19_召回率.png': '图09_召回率.png'}
COPY_SUPP = {'图03_两种步.png': 'S图01_两种步.png', '图05_判断归一.png': 'S图02_判断归一.png', '图06_层间连线.png': 'S图03_层间连线.png',
             '图07_枢纽判断.png': 'S图04_枢纽判断.png', '图08_引擎怎样推.png': 'S图05_引擎怎样推.png', '图09_示例盘.png': 'S图06_示例盘.png',
             '图11_第三版与第四版.png': 'S图07_第三版与第四版.png', '图13_主检验设计.png': 'S图08_主检验设计.png', '图15_事后诊断.png': 'S图09_事后诊断.png',
             '图16_事后补充分析.png': 'S图10_事后补充分析.png', '图17_认本人检验.png': 'S图11_第一次认本人检验.png', '图18_推理类型.png': 'S图12_旧五类推理类型.png'}


def pfmt(p):
    return 'p＜0.001' if p < 0.001 else f'p＝{p:.3f}'


def strip_axes(ax):
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, lw=.6); ax.set_axisbelow(True)


def fig_m4f(out, r, m4e):
    arms = [('正', '正题：本人陈述，本人盘对三张随机盘', BLUE), ('换陈述', '换陈述：别人的陈述，同四份论断', LGRAY), ('换论断', '换论断：本人陈述，他人真盘对三张随机盘', TEAL)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 3.5), dpi=220, gridspec_kw={'width_ratios': [1.55, 1]})
    ys = [3, 2, 1]
    rec = {}
    for (k, lab, col), y in zip(arms, ys):
        g = r['组'][k]
        rate = g['认对率']; lo, hi = g['认对率95%区间']
        a1.barh(y, rate, height=.56, color=col, zorder=2)
        a1.plot([lo, hi], [y, y], color=INK, lw=1.1, zorder=3)
        for x in (lo, hi):
            a1.plot([x, x], [y - .12, y + .12], color=INK, lw=1.1, zorder=3)
        a1.text(hi + .015, y, f"{g['选中焦点的卷数X']}/{g['有效卷数']}　上单尾{pfmt(g['P(X≥实测)'])}", va='center', fontsize=7.6, color=INK2)
        rec[k] = {'X': g['选中焦点的卷数X'], '有效卷': g['有效卷数'], '认对率': rate, '区间': [lo, hi], 'p上': g['P(X≥实测)'], 'p下': g['P(X≤实测)']}
    k1 = m4e['arms']['链']['hits']; n1 = m4e['n_items']
    a1.barh(0, k1 / n1, height=.56, color='none', edgecolor=GRAY, hatch='////', lw=.8, zorder=2)
    a1.text(k1 / n1 + .015, 0, f'{k1}/{n1}（只作参照）', va='center', fontsize=7.6, color=MUTED)
    a1.set_yticks(ys + [0]); a1.set_yticklabels([a[1] for a in arms] + ['第一次认本人（链组；陪衬为真人，审者模型不同）'], fontsize=7.4)
    a1.axvline(.25, color=RED, lw=1.0, ls=(0, (3, 3)), zorder=1)
    a1.text(.25 - .008, 3.62, '瞎猜 1/4', color=RED, fontsize=7.4, ha='right', va='bottom')
    a1.set_xlim(0, 1.1); a1.set_ylim(-.6, 3.95)
    a1.set_xticks([0, .25, .5, .75, 1]); a1.set_xticklabels(['0', '0.25', '0.5', '0.75', '1'])
    a1.set_xlabel('审者选中焦点论断的比例（横线为按题成团重抽的 95% 区间）', fontsize=7.8)
    a1.set_title('三组', loc='left', fontsize=9.2)
    strip_axes(a1)
    cons = [('对比甲：正题−换陈述', '对比甲：正题 − 换陈述\n（论断相同，陈述不同）'), ('对比乙：正题−换论断', '对比乙：正题 − 换论断\n（陈述相同，焦点论断不同）')]
    for (k, lab), y in zip(cons, (1, 0)):
        c = r['对比'][k]['按比例']
        lo, hi = c['平均差95%区间']
        a2.plot([lo, hi], [y, y], color=DBLUE, lw=5, solid_capstyle='butt', zorder=2)
        a2.plot([c['平均差']], [y], 'o', color=INK, ms=5, zorder=3)
        a2.text(lo, y + .3, f"{c['平均差']:+.2f}　{pfmt(c['符号翻转单尾p(正>对照)'])}", ha='left', fontsize=7.6, color=INK2,
                bbox=dict(facecolor=SURFACE, edgecolor='none', pad=1.0))
        rec[k] = {'平均差': c['平均差'], '区间': [lo, hi], 'p': c['符号翻转单尾p(正>对照)']}
    a2.axvline(0, color=RED, lw=1.0, ls=(0, (3, 3)), zorder=1)
    a2.set_yticks([1, 0]); a2.set_yticklabels([c[1] for c in cons], fontsize=7.4)
    lim = max(.5, max(abs(x) for k, _ in cons for x in r['对比'][k]['按比例']['平均差95%区间']) + .1)
    a2.set_xlim(-lim, lim); a2.set_ylim(-.6, 1.8)
    a2.set_xlabel('每题选中焦点比例之差的平均\n（色条为 95% 区间）', fontsize=7.8)
    a2.set_title('两种对比', loc='left', fontsize=9.2)
    strip_axes(a2)
    fig.tight_layout()
    save(fig, out, '图07_认本人检验.png')
    return rec


TCOMP = [('定名·象名', '定名·象名', VIOLET), ('定名·义名', '定名·义名', '#b7a0e6'), ('象', '断事·象', DBLUE), ('位', '断事·位', BLUE), ('时', '断事·时', LBLUE),
         ('义', '断事·义', TEAL), ('情', '断事·情', AMBER), ('直断', '断事·直断', LGRAY)]
GROUPS = [('起步', '起步'), ('推理步', '推理步'), ('全书', '《全书》断语')]
QC = [('C1', '象'), ('C2', '义'), ('C3', '位'), ('C4', '时'), ('C5', '情')]
GCOL = {'起步': BLUE, '推理步': AMBER, '全书': TEAL}


def fig_trad(out, t):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 3.9), dpi=220, gridspec_kw={'width_ratios': [1.25, 1]})
    rules = t['解读规则']
    rec = {}
    ys = [2, 1, 0]
    for (g, lab), y in zip(GROUPS, ys):
        d = t['分布'][g]
        n = d['n']
        if rules[g]['类型alpha<0.4']:
            a1.text(.02, y, '类型无法可靠区分，不报构成', va='center', fontsize=7.6, color=MUTED); continue
        nd = d['问A·定名比例']['条数']
        counts = {'定名·象名': d.get('定名里象名比例', {}).get('条数', 0)}
        counts['定名·义名'] = nd - counts['定名·象名']
        for t_ in ('象', '位', '时', '义', '情', '直断'):
            counts[t_] = d.get('断事里各类', {}).get(t_, {}).get('条数', 0)
        left = 0.0
        weak = set(rules[g]['特定一致率<0.5的类'])
        for key, _, col in TCOMP:
            v = counts[key] / n if n else 0
            hatch = '////' if (key in weak or key.replace('·', '·') in weak) else None
            a1.barh(y, v, left=left, height=.62, color=col if not hatch else 'white', edgecolor=col if hatch else 'white', hatch=hatch, lw=.6)
            if v >= .07 and not hatch:
                a1.text(left + v / 2, y, f'{v * 100:.0f}', ha='center', va='center', fontsize=7, color='white' if col not in (LBLUE, LGRAY, '#b7a0e6') else INK)
            left += v
        rec[g] = {'n': n, '构成': counts}
    a1.set_yticks(ys); a1.set_yticklabels([f"{lab}（{t['分布'][g]['n']}）" for g, lab in GROUPS], fontsize=8)
    a1.set_xlim(0, 1); a1.set_ylim(-.6, 2.6)
    a1.set_xticks([0, .25, .5, .75, 1]); a1.set_xticklabels(['0', '25%', '50%', '75%', '100%'], fontsize=7.4)
    a1.set_xlabel('各类所占比例（条内数字为百分比）', fontsize=7.8)
    a1.set_title('结论说的是什么、凭的是什么', loc='left', fontsize=9.2)
    for s in ('top', 'right', 'left'):
        a1.spines[s].set_visible(False)
    a1.tick_params(axis='y', length=0)
    from matplotlib.patches import Patch
    a1.legend(handles=[Patch(color=c, label=l) for _, l, c in TCOMP], loc='upper center', bbox_to_anchor=(.5, -.2), ncol=4, fontsize=7)
    items = QC + [('问D', '明说道理')]
    yb = list(range(len(items)))[::-1]
    off = {'起步': .26, '推理步': 0, '全书': -.26}
    for g, _ in GROUPS:
        d = t['分布'][g]
        bad = set(rules[g]['alpha<0.4的项'])
        for (q, nm), y in zip(items, yb):
            if q in bad:
                continue
            v = d['断事里问D明说道理'] if q == '问D' else d.get('断事里C1–C5答是', {}).get(nm)
            if not v:
                continue
            a2.barh(y + off[g], v['比例'], height=.24, color=GCOL[g], zorder=2)
            lo, hi = v['95%']
            a2.plot([lo, hi], [y + off[g]] * 2, color=INK, lw=.8, zorder=3)
            rec.setdefault(g, {}).setdefault('断事里答是', {})[nm] = {'比例': v['比例'], '区间': v['95%']}
    a2.set_yticks(yb); a2.set_yticklabels([nm for _, nm in items], fontsize=8)
    a2.set_xlim(0, 1); a2.set_xticks([0, .25, .5, .75, 1]); a2.set_xticklabels(['0', '25%', '50%', '75%', '100%'], fontsize=7.4)
    a2.set_xlabel('断事条目里答「是」的比例（横线为 95% 区间）', fontsize=7.8)
    a2.set_title('断事的依据（可多选）', loc='left', fontsize=9.2)
    a2.legend(handles=[Patch(color=GCOL[g], label=lab) for g, lab in GROUPS], loc='lower right', fontsize=7)
    strip_axes(a2)
    fig.tight_layout()
    save(fig, out, '图08_推理方式.png')
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('m4f', 'trad', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, '补充'))
    for src, dst in COPY_MAIN.items():
        shutil.copyfile(os.path.join(V5, src), os.path.join(a.out, dst))
    for src, dst in COPY_SUPP.items():
        shutil.copyfile(os.path.join(V5, src), os.path.join(a.out, '补充', dst))
    rec = {'复制自v5': {**COPY_MAIN, **{k: '补充/' + v for k, v in COPY_SUPP.items()}}}
    rec['图7'] = fig_m4f(a.out, jl(a.m4f), jl(CH, 'chain_results_v1', 'm4e_analysis_v1.json'))
    rec['图8'] = fig_trad(a.out, jl(a.trad))
    open(os.path.join(a.out, '图中数字_chain_v6.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'out': sorted(os.listdir(a.out))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
