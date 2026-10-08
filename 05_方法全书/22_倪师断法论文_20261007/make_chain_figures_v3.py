"""倪师推理链论文（第九稿）的全部插图 v3（只做呈现；数字全部取自已登记的文件，不新做统计）。
v3 替代说明：按第二轮两份内审意见改图，v2 原样保留：图2 的 T213 标注贴近箭头；图5 写「两名归类者」，合计线标签移开；
图6 在其余领域前加分隔线；图7、图10 把只在命例里说过的推导画成虚线；图8 措辞改白话；图15 注明按人累计、「条件写得出」；
图16 上图按补记三把判断集的步拆成七类，下图分「换算法」与「按人分组」，事后各项不报 p 值。
以下为 v2 的说明。
v2 替代说明：按第一轮两份内审意见改图，v1 原样保留。
- 全文把「定性步」改叫「起步」（数据文件里仍叫定性步），以免与「定性层」混淆；抽取、裁定、核查、归一一律写成 AI；
- 图1 加一处直角转折的连线，⑥ 写明进引擎的条件；图2 拆成七层，「会照」改「三方四正」，T213、T247 标「紧接承上」；
- 图3 加方向与强度的说明；图4 去掉图内标题、窄段换色、加横轴说明；图5 加六组合计参考线；图7 加层的图例，领域「其他」显示为「杂项」；
- 图8 加「对每一宫各做一遍」的总框；图9 中央说明加主星、辅煞、化忌、亮度的读法；图10 两个前提的步画「且」，列名改为「第 N 步」，加图例；
- 图11 链里写出另需的前提与女命限定；图12 左图加「任一层」一柱，右图加「只用通则步（事后）」对照；图13 补上随机盘到得分的箭头；
- 图14 空心圈错开半行；图15 只留事先登记的诊断（判断集的结点与步）；新增图16 事后补充分析（只作描述）。
读（23_倪师推理链_20261007 下）：chain_merged_v1/（adjudicated_v1、check_v1、normalized_v1）、chain_norm_packets_v1/labels_all.json、chain_kb_v1.json、
chain_results_v1/（coverage_v1、reproduce_v1、reproduce_diag_v1、posthoc_v1、example_r30_v1）、v4_holdout_v1/holdout_charts.json；
21_倪师断法引擎_20261005/freeze_check_v1/rand_charts.json（示例盘 r30 的盘面）。
图内不写图号，图号与图题写在正文。另写 图中数字_chain_v3.json，供正文核数（v3 另读 chain_results_v1/posthoc2_v1.json）。
用法：python3 make_chain_figures_v3.py --out <新目录>"""
import argparse, collections, json, os, statistics, sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
W5 = os.path.dirname(HERE)
E = os.path.join(W5, '21_倪师断法引擎_20261005')
CH = os.path.join(W5, '23_倪师推理链_20261007')
sys.path.insert(0, CH)
sys.path.insert(0, E)
import ni_chain_engine_v1 as C  # noqa: E402
import ni_engine_v1 as ENG  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#8a8984', '#e6e5e1'
BLUE, LBLUE, DBLUE = '#2a78d6', '#9ec5f4', '#184f95'
LGRAY, GRAY, RED, AMBER, ORANGE, TEAL, VIOLET = '#d4d3ce', '#b9b8b3', '#e34948', '#eda100', '#eb6834', '#1baf7a', '#7d55c7'
FILL, FILL2, FILL3, FILL4, FILL5, FILL6, FILL7 = '#dbe9fa', '#eeeeeb', '#fdf0cc', '#fbe1d6', '#d6f1e6', '#f9dcdc', '#ebe4f7'
plt.rcParams.update({'font.family': ['Hiragino Sans GB', 'Heiti TC'], 'axes.unicode_minus': False, 'font.size': 9,
    'axes.titlesize': 10, 'axes.titleweight': 'bold', 'axes.titlecolor': INK, 'axes.labelsize': 9, 'axes.edgecolor': GRID, 'axes.linewidth': .8,
    'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2, 'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'grid.color': GRID, 'grid.linewidth': .8, 'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE, 'savefig.facecolor': SURFACE,
    'legend.frameon': False, 'legend.fontsize': 8, 'text.color': INK})
W = 8.2
DW = 6.6   # 示意图宽 6.6 英寸；坐标单位＝0.1 英寸
BR = '子丑寅卯辰巳午未申酉戌亥'
STEMS = '甲乙丙丁戊己庚辛壬癸'
MAJOR = ['紫微', '天机', '太阳', '武曲', '天同', '廉贞', '天府', '太阴', '贪狼', '巨门', '天相', '天梁', '七杀', '破军']
JI6 = ['左辅', '右弼', '文昌', '文曲', '天魁', '天钺']
SHA6 = ['擎羊', '陀罗', '火星', '铃星', '地空', '地劫']
GRIDPOS = {5: (0, 0), 6: (0, 1), 7: (0, 2), 8: (0, 3), 4: (1, 0), 9: (1, 3), 3: (2, 0), 10: (2, 3), 2: (3, 0), 1: (3, 1), 0: (3, 2), 11: (3, 3)}
LAYER_COL = {'定性': (FILL, BLUE), '长相': (FILL7, VIOLET), '个性': (FILL5, TEAL), '行为': (FILL3, AMBER), '路线': (FILL4, ORANGE), '成败': (FILL6, RED)}
MAIN6 = ['定性', '长相', '个性', '行为', '路线', '成败']
SHOWNAME = {'其他': '杂项'}   # 领域「其他」在图里显示为「杂项」，免得与条件「其他:」混淆


def lc(layer):
    return LAYER_COL.get(layer, (FILL2, GRAY))


def jl(*p):
    return json.load(open(os.path.join(*p), encoding='utf-8'))


def dcanvas(h, w=DW):
    fig = plt.figure(figsize=(w, h), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w * 10); ax.set_ylim(0, h * 10); ax.axis('off')
    return fig, ax


def text_size(text, fs):
    def cw(ch):
        return 1.0 if (ord(ch) > 0x2E80 or ch in '…—→×') else 0.55
    ls = text.split('\n')
    return max(sum(cw(ch) for ch in l) for l in ls) * fs / 7.2, len(ls) * fs * 1.45 / 7.2


def box(ax, x, y, w, h, text, fc=FILL, ec=BLUE, fs=9, bold=False, color=INK, lw=.9, ha='center', r=0.8):
    tw, th = text_size(text, fs)
    assert tw <= w - 1.0 and th <= h - 0.6, ('文字放不下', text[:24], round(tw, 1), w, round(th, 1), h)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}', fc=fc, ec=ec, lw=lw))
    tx = x + w / 2 if ha == 'center' else x + 0.8
    ls = text.split('\n')
    lh = fs * 1.45 / 7.2
    top = y + h / 2 + (len(ls) - 1) * lh / 2
    for i, ln in enumerate(ls):
        head = bold or (i == 0 and len(ls) > 1)
        ax.text(tx, top - i * lh, ln, ha=ha, va='center', fontsize=fs if (head or len(ls) == 1) else fs - .4,
                color=color if (head or len(ls) == 1) else INK2, fontweight='bold' if head else 'normal')


def note(ax, x, y, text, fs=8, ha='left', color=MUTED, width=None, va='center'):
    tw, _ = text_size(text, fs)
    if width is not None:
        assert tw <= width, ('说明文字太宽', text[:24], round(tw, 1), width)
    ax.text(x, y, text, ha=ha, va=va, fontsize=fs, color=color, linespacing=1.45)


def arrow(ax, x1, y1, x2, y2, color=MUTED, lw=1.1, rad=0, ls='-'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color=color, lw=lw, shrinkA=0, shrinkB=0, mutation_scale=9,
                                                                 connectionstyle=f'arc3,rad={rad}', linestyle=ls))


def elabel(ax, x, y, text, fs=6.8, color=INK2, ha='center'):
    ax.text(x, y, text, ha=ha, va='center', fontsize=fs, color=color, linespacing=1.3, bbox=dict(boxstyle='round,pad=0.12', fc=SURFACE, ec='none'))


def save(fig, out, name, tight=True):
    fig.savefig(os.path.join(out, name), bbox_inches='tight' if tight else None, pad_inches=0.08, dpi=300)
    plt.close(fig)


def wrap(s, n):
    out, cur, w = [], '', 0.0
    for ch in s:
        cw = 1.0 if ord(ch) > 0x2E80 else .55
        if w + cw > n and cur:
            out.append(cur); cur, w = '', 0.0
        cur += ch; w += cw
    if cur:
        out.append(cur)
    return out


def layer_legend(ax, layers, loc='lower center', anchor=(.5, -.02), ncol=7, fs=7.6):
    hs = [Patch(fc=lc(l)[0], ec=lc(l)[1], lw=.9, label=l) for l in layers if l in LAYER_COL]
    if any(l not in LAYER_COL for l in layers):
        hs.append(Patch(fc=FILL2, ec=GRAY, lw=.9, label='其余领域'))
    ax.legend(handles=hs, loc=loc, bbox_to_anchor=anchor, ncol=ncol, fontsize=fs, frameon=False, handlelength=1.4, columnspacing=1.1)


# ---------------- 图1 总流程 ----------------
def fig_pipeline(out, adj, chk, norm, kb):
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
             '⑧ 四项检验\n忠实、覆盖、复现命例、可追溯']
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
    # ④ → ⑤：从④右边出来，沿两栏之间的空隙往上，再进⑤
    gx = (xs[0] + bw + xs[1]) / 2
    y4, y5 = tops[3] + bh / 2, tops[0] + bh / 2
    ax.plot([xs[0] + bw, gx, gx], [y4, y4, y5], color=MUTED, lw=1.1)
    arrow(ax, gx, y5, xs[1], y5)
    save(fig, out, '图01_总流程.png')
    return {'条目': n_q, '甲抽出': jia, '乙抽出': yi, '定稿': adj['counts']['定稿步'], '核查成立': ok, '核查不成立': bad,
            '判断名': norm['counts']['判断名'], '结点（归一表）': norm['counts']['结点'], '知识库步': kc['收下的步'], '知识库结点': kc['结点'],
            '引擎可用': kc['引擎可用（可操作且先天）']}


# ---------------- 图2 七层与两条真实的链 ----------------
def fig_layers(out, kb):
    by = {s['step_id']: s for s in kb['steps']}
    nd = kb['nodes']
    need = {'T213-c1': ('定性', '佐才'), 'T213-c2': ('路线', '当助理秘书'), 'T214-c3': ('成败', '位高无权'),
            'T239-c5': ('个性', '刚强'), 'T247-c3': ('行为', '大怒之下犯大错')}
    for sid, (lay, name) in need.items():
        assert [(nd[n]['层'], nd[n]['名']) for n in by[sid]['conclusions']] == [(lay, name)], sid
    assert [nd[n]['名'] for n in by['T213-c2']['premises']] == ['佐才'] and [nd[n]['名'] for n in by['T214-c3']['premises']] == ['佐才']
    assert [nd[n]['名'] for n in by['T247-c3']['premises']] == ['刚强']
    assert by['T213-c1']['条件'] == ['本宫有:天相'] and by['T239-c5']['条件'] == ['本宫有:杀破狼']
    assert by['T213-c2']['连接'] == '紧接承上' and by['T214-c3']['连接'] == '所以' and by['T247-c3']['连接'] == '紧接承上'
    rows = [('盘面', '星、亮度、四化、三方四正'), ('定性', '属于哪一类星、哪一类人'), ('长相', '外貌、体型'), ('个性', '性情'),
            ('行为', '做事的方式'), ('路线', '走哪条路、做哪一行'), ('成败', '成就高低、得失贵贱')]
    rh, bh = 6.4, 5.0
    H = 7.0 + len(rows) * rh + .6
    fig, ax = dcanvas(H / 10)
    q = '「介绍命宫的时候，我们可以看到这个人的长相，这个人的个性。从个性上面可以知道这个人的行为模式。其实开始从命宫一看就已经知道成败」（T409）'
    for i, ln in enumerate(wrap(q, 52)):
        note(ax, 1.4, H - 2.0 - i * 2.3, ln, fs=8.4, color=INK2)
    y0 = H - 6.6 - bh
    ys = {name: y0 - k * rh for k, (name, _) in enumerate(rows)}
    for k, (name, desc) in enumerate(rows):
        fc, ec = (('white', GRID) if name == '盘面' else lc(name))
        box(ax, 1.4, ys[name], 15.4, bh, f'{name}\n{desc}', fc=fc, ec=ec, fs=8.0)
        if k:
            arrow(ax, 9.1, ys[rows[k - 1][0]], 9.1, ys[name] + bh, color=GRAY)
        ax.plot([17.6, 64.6], [ys[name] - .7, ys[name] - .7], color=GRID, lw=.6, zorder=0)
    def node(x, row, text, lay, w=12.4):
        fc, ec = ('white', GRID) if lay == '盘面' else lc(lay)
        box(ax, x - w / 2, ys[row], w, bh, text, fc=fc, ec=ec, fs=8.4)
        return (x, ys[row], ys[row] + bh)
    a0 = node(29.0, '盘面', '命宫有天相', '盘面')
    a1 = node(29.0, '定性', '佐才', '定性')
    a2 = node(24.0, '路线', '当助理秘书', '路线')
    a3 = node(37.0, '成败', '位高无权', '成败')
    b0 = node(54.0, '盘面', '命宫有七杀、\n破军或贪狼', '盘面', w=13.6)
    b1 = node(54.0, '个性', '刚强', '个性')
    b2 = node(54.0, '行为', '大怒之下犯大错', '行为', w=15.4)
    arrow(ax, 29.0, a0[1], 29.0, a1[2]); elabel(ax, 30.0, (a0[1] + a1[2]) / 2, 'T213 起步', ha='left')
    arrow(ax, 26.0, a1[1], 24.0, a2[2]); elabel(ax, 25.8, ys['行为'] + 2.6, 'T213 推理步\n紧接承上', ha='left')
    arrow(ax, 33.0, a1[1], 37.0, a3[2]); elabel(ax, 36.2, ys['个性'] + 1.6, 'T214 推理步\n「所以」', ha='left')
    arrow(ax, 54.0, b0[1], 54.0, b1[2]); elabel(ax, 55.0, (b0[1] + b1[2]) / 2, 'T239 起步', ha='left')
    arrow(ax, 54.0, b1[1], 54.0, b2[2]); elabel(ax, 55.0, (b1[1] + b2[2]) / 2, 'T247 推理步，紧接承上', ha='left')
    save(fig, out, '图02_七层与真实的链.png')
    return {'步': sorted(need)}


# ---------------- 图3 两种步的解剖 ----------------
def fig_anatomy(out, kb):
    by = {s['step_id']: s for s in kb['steps']}
    nd = kb['nodes']
    q, r = by['T218-c1'], by['T214-c3']
    assert q['类型'] == '定性步' and r['类型'] == '推理步'
    def fields(s):
        con = s['结论']
        common = [('出处', f"{s['T']}（{'讲命例时说的' if s['命例特指'] else '讲星时说的，不是命例特指'}）"), ('宫、适用', f"{s['宫']}；{s['适用']}")]
        if s['类型'] == '定性步':
            mid = [('条件', '、'.join(c.replace('本宫有:', '本宫有').replace('三方四正有:', '三方四正有').replace(',', '、') for c in s['条件']))]
        else:
            mid = [('前提', '、'.join(f"{p['层']}层「{p['判断']}」" for p in s['前提']) + '（须已推出）'),
                   ('附加条件', '、'.join(s['附加条件']) if s['附加条件'] else '无'), ('连接', f"「{s['连接']}」")]
        tail = [('结论', f"{con['层']}层「{nd[s['conclusions'][0]]['名']}」"), ('原话说法', f"「{con['原话说法']}」"),
                ('方向、强度', f"{s['方向']}；{s['强度']}")]
        return common + mid + tail, wrap(f"「{s['原话摘录']}」", 19)
    need = []
    for s_ in (q, r):
        fs_, quote = fields(s_)
        need.append(5.6 + sum(1.9 * len(wrap(v, 20)) + .5 for _, v in fs_) + 1.9 * len(quote) + 1.6)
    H = max(need) + .8 + 4.6
    fig, ax = dcanvas(H / 10)
    for k, (s, title, fc, ec) in enumerate(((q, '起步：盘面 → 判断', FILL, BLUE), (r, '推理步：判断 → 判断', FILL5, TEAL))):
        x0 = 1.2 + k * 32.6
        ax.add_patch(FancyBboxPatch((x0, 4.6), 31.2, H - 5.4, boxstyle='round,pad=0,rounding_size=0.8', fc=fc, ec=ec, lw=.9))
        ax.text(x0 + 1.0, H - 2.6, title, fontsize=9.2, fontweight='bold', color=INK, va='center')
        fs_, quote = fields(s)
        y = H - 5.6
        for name, val in fs_:
            ax.text(x0 + 1.0, y, name, fontsize=8, color=DBLUE, fontweight='bold', va='center')
            for i, ln in enumerate(wrap(val, 20)):
                ax.text(x0 + 8.4, y - i * 1.9, ln, fontsize=8, color=INK, va='center')
            y -= 1.9 * len(wrap(val, 20)) + .5
        ax.text(x0 + 1.0, y, '原话摘录', fontsize=8, color=DBLUE, fontweight='bold', va='center')
        for i, ln in enumerate(quote):
            ax.text(x0 + 8.4, y - i * 1.9, ln, fontsize=7.8, color=INK2, va='center')
        assert y - len(quote) * 1.9 > 5.0, ('卡片放不下', s['step_id'])
    note(ax, 1.4, 2.6, '方向：吉、凶、中。强度：原话说「一定」「肯定」「势必」等写「断」，其余写「倾向」。两张卡片都是知识库里的原样记录。', fs=7.6, color=INK2, width=64)
    save(fig, out, '图03_两种步.png')
    return {'起步': q['step_id'], '推理步': r['step_id']}


# ---------------- 图4 抽取一致与核查 ----------------
def fig_extract_check(out, adj, chk):
    g = adj['一致程度']
    t = g['按条']
    both_no = t['推理步有无一致'] - t['两人都有推理步']
    src = g['按步·定稿来源']
    c = chk['counts']
    rows = [(f"{t['条目']} 条原话：\n甲乙对「有没有推理步」", [('甲乙都说有', t['两人都有推理步'], BLUE), ('甲乙都说没有', both_no, LBLUE), ('只一个说有', t['只一人有推理步'], GRAY)]),
            (f"定稿 {adj['counts']['定稿步']} 步的来源", [('甲乙都抽到', src['甲乙'], BLUE), ('只甲抽到', src['只甲'], AMBER), ('只乙抽到', src['只乙'], ORANGE), ('裁定者补入', src['补入'], LGRAY)]),
            (f"起步 {adj['counts']['定性步']} 步的核查", [('成立', c['定性步成立'], TEAL), ('不成立', c['定性步不成立'], RED)]),
            (f"推理步 {adj['counts']['推理步']} 步的核查", [('成立', c['推理步成立'], TEAL), ('不成立', c['推理步不成立'], RED)])]
    fig, ax = plt.subplots(figsize=(W, 3.1), dpi=220)
    for k, (name, segs) in enumerate(rows):
        y = len(rows) - 1 - k
        tot = sum(v for _, v, _ in segs); x = 0
        small = [(lab, v, col) for lab, v, col in segs if v / tot <= .07]
        for lab, v, col in segs:
            ax.barh(y, v / tot, left=x, color=col, height=.56, edgecolor=SURFACE, lw=1.5)
            if v / tot > .07:
                ax.text(x + v / tot / 2, y, f'{lab} {v}', ha='center', va='center', fontsize=7.8, color='white' if col in (BLUE, TEAL, RED, ORANGE) else INK)
            x += v / tot
        for i, (lab, v, col) in enumerate(small):
            yy = y + (len(small) - 1) * .13 - i * .26
            ax.plot([1.02], [yy], 's', color=col, ms=5, clip_on=False)
            ax.text(1.035, yy, f'{lab} {v}', ha='left', va='center', fontsize=7.2, color=INK2, clip_on=False)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=8.4)
    ax.set_xlim(0, 1); ax.set_ylim(-.5, len(rows) - .4)
    ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(['0', '25%', '50%', '75%', '100%'], fontsize=7.6, color=MUTED)
    ax.set_xlabel('占这一行总数的比例', fontsize=8, color=MUTED)
    for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    fig.tight_layout(); fig.subplots_adjust(right=.84)
    save(fig, out, '图04_抽取与核查.png')
    return {'按条一致': t['推理步有无一致'], '两人都有': t['两人都有推理步'], '两人都没有': both_no, '只一人': t['只一人有推理步'],
            '来源': src, '核查': {k: c[k] for k in ('定性步成立', '定性步不成立', '推理步成立', '推理步不成立')}}


# ---------------- 图5 判断归一 ----------------
def fig_normalize(out, norm, labels_all):
    lab = {l['编号']: l for l in labels_all['labels']}
    nid = next(k for k, v in norm['nodes'].items() if v['名'] == '武官星' and v['层'] == '定性')
    mem = sorted(norm['nodes'][nid]['成员'], key=lambda m: -lab[m]['次数'])
    groups = [('G1', '定性'), ('G2', '长相、个性、行为'), ('G3', '路线、成败'), ('G4', '财、祖业田宅、福德'), ('G5', '婚姻、子女、父母、\n兄弟、朋友合伙'), ('G6', '健康、意外、官非、\n寿元、杂项')]
    ag = norm['agreement']
    both = sum(v['两人都合的对数'] for v in ag.values()); either = sum(v['任一人合的对数'] for v in ag.values())
    fig = plt.figure(figsize=(W, 3.5), dpi=220)
    ax = fig.add_axes([0.0, 0.0, 0.47, 1.0]); ax.axis('off')
    Wd, Hd = 38.5, 35.0
    ax.set_xlim(0, Wd); ax.set_ylim(0, Hd)
    ax.text(.6, Hd - 1.6, f'例：{len(mem)} 种说法归成一个结点', fontsize=9.6, fontweight='bold', color=INK, va='center')
    bh, gap = 3.6, 1.0
    top = Hd - 5.0
    for i, m in enumerate(mem):
        y = top - i * (bh + gap)
        box(ax, .8, y - bh, 17.0, bh, f"「{lab[m]['判断']}」　出现 {lab[m]['次数']} 次", fc='white', ec=GRID, fs=8.0)
        ax.plot([17.8, 21.6], [y - bh / 2, Hd / 2 - 2.6], color=GRAY, lw=.8)
    arrow(ax, 21.6, Hd / 2 - 2.6, 24.2, Hd / 2 - 2.6, color=GRAY, lw=.8)
    box(ax, 24.2, Hd / 2 - 6.2, 13.2, 7.2, '结点「武官星」\n定性层', fc=FILL, ec=BLUE, fs=9)
    ax2 = fig.add_axes([0.6, 0.16, 0.37, 0.72])
    vals = [ag[g]['合并一致率'] for g, _ in groups]
    ys = list(range(len(groups)))[::-1]
    ax2.barh(ys, vals, color=BLUE, height=.56)
    for y, v in zip(ys, vals):
        ax2.text(v + .015, y, f'{v:.1%}', va='center', fontsize=7.6, color=INK)
    ax2.axvline(both / either, color=RED, lw=1.0, ls=(0, (3, 3)))
    ax2.text(both / either + .02, -.55, f'六组合计 {both / either:.1%}', color=RED, fontsize=7.4, ha='left', va='bottom')
    ax2.set_yticks(ys); ax2.set_yticklabels([n for _, n in groups], fontsize=7.4)
    ax2.set_xlim(0, 1.12); ax2.set_ylim(-.6, len(groups) - .1); ax2.set_xticks([0, .5, 1]); ax2.set_xticklabels(['0', '50%', '100%'], fontsize=7.4, color=MUTED)
    for s in ('top', 'right', 'left'): ax2.spines[s].set_visible(False)
    ax2.tick_params(axis='y', length=0)
    ax2.set_title('两名归类者的合并一致率（按组）', loc='left', fontsize=9.2, pad=14)
    ax2.text(0, -1.3, '合并一致率＝两名归类者都放进同一结点的判断名对数\n÷ 至少一名放进同一结点的对数', fontsize=7.0, color=MUTED, va='top', transform=ax2.transData)
    save(fig, out, '图05_判断归一.png')
    return {'例': [(lab[m]['判断'], lab[m]['次数']) for m in mem], '合并一致率': {g: ag[g]['合并一致率'] for g, _ in groups}, '六组合计': round(both / either, 4)}


# ---------------- 图6 层与层之间的连线 ----------------
def fig_layer_matrix(out, kb):
    nd = kb['nodes']
    R = [s for s in kb['steps'] if s['类型'] == '推理步']
    cats = MAIN6 + ['其余领域']
    cat = lambda n: nd[n]['层'] if nd[n]['层'] in MAIN6 else '其余领域'
    M = [[0] * len(cats) for _ in cats]
    for s in R:
        for p in s['premises']:
            for c in s['conclusions']:
                M[cats.index(cat(p))][cats.index(cat(c))] += 1
    tot = sum(map(sum, M))
    fig, ax = plt.subplots(figsize=(W * .72, 4.4), dpi=220)
    cmap = LinearSegmentedColormap.from_list('b', [SURFACE, FILL, LBLUE, BLUE, DBLUE])
    vcap = 50
    ax.imshow([[min(v, vcap) for v in r] for r in M], cmap=cmap, vmin=0, vmax=vcap)
    for i in range(len(cats)):
        for j in range(len(cats)):
            v = M[i][j]
            if v:
                ax.text(j, i, str(v), ha='center', va='center', fontsize=8.4, color='white' if v > vcap * .55 else INK)
    ax.axhline(len(cats) - 1.5, color=INK2, lw=1.0); ax.axvline(len(cats) - 1.5, color=INK2, lw=1.0)
    ax.set_xticks(range(len(cats))); ax.set_xticklabels(cats, fontsize=8.2)
    ax.set_yticks(range(len(cats))); ax.set_yticklabels(cats, fontsize=8.2)
    ax.set_xlabel('结论在哪一层', fontsize=8.6); ax.set_ylabel('前提在哪一层', fontsize=8.6)
    ax.xaxis.set_label_position('top'); ax.xaxis.tick_top()
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(f'推理步的连线：{len(R)} 步、{tot} 条（前提 → 结论）', loc='left', pad=34)
    fig.tight_layout()
    save(fig, out, '图06_层间连线.png')
    return {'推理步': len(R), '连线': tot, '矩阵': {cats[i]: {cats[j]: M[i][j] for j in range(len(cats)) if M[i][j]} for i in range(len(cats))}}


# ---------------- 图7 几个枢纽判断 ----------------
def fig_hubs(out, kb):
    nd = kb['nodes']
    R = [s for s in kb['steps'] if s['类型'] == '推理步']
    outl = collections.defaultdict(lambda: collections.defaultdict(set))
    gen = collections.defaultdict(lambda: collections.defaultdict(bool))   # 这条连线有没有通则步（不是命例特指）
    for s in R:
        for p in s['premises']:
            for c in s['conclusions']:
                outl[p][c].add(s['T'])
                gen[p][c] |= not s['命例特指']
    def hub(name):
        n = next(k for k, v in nd.items() if v['名'] == name and v['层'] == '定性')
        tg = sorted(outl[n].items(), key=lambda kv: (C.LAYER_ORDER.index(nd[kv[0]]['层']), min(int(t[1:]) for t in kv[1]), nd[kv[0]]['名']))
        return [(nd[c]['层'], nd[c]['名'], '、'.join(sorted(ts, key=lambda t: int(t[1:]))), gen[n][c]) for c, ts in tg]
    hubs = {h: hub(h) for h in ('武官星', '佐才', '文官带', '财星')}
    bh, gap = 2.5, .45
    nL = len(hubs['武官星'])
    H = nL * (bh + gap) + 8.0
    fig, ax = dcanvas(H / 10)
    def draw(name, x0, ytop, tw=17.2):
        ts = hubs[name]
        hgt = len(ts) * (bh + gap) - gap
        yc = ytop - hgt / 2
        box(ax, x0, yc - 2.6, 9.6, 5.2, f'{name}\n定性层', fc=FILL, ec=BLUE, fs=8.6)
        for i, (lay, nm, T, g) in enumerate(ts):
            y = ytop - i * (bh + gap) - bh
            fc, ec = lc(lay)
            box(ax, x0 + 12.4, y, tw, bh, f'{SHOWNAME.get(lay, lay)}｜{nm}　{T}', fc=fc, ec=ec, fs=7.0, ha='left', r=.5)
            ax.plot([x0 + 9.6, x0 + 12.4], [yc, y + bh / 2], color=GRAY if g else INK2, lw=.6 if g else .8, ls='-' if g else (0, (2, 1.5)), zorder=0)
        return hgt
    top = H - 2.4
    draw('武官星', .8, top)
    y = top
    for name in ('佐才', '文官带', '财星'):
        hgt = draw(name, 33.6, y, tw=19.4)
        y -= hgt + 2.6
    assert y > 3.0, '右栏放不下'
    present = sorted({x[0] for v in hubs.values() for x in v} | {'定性'}, key=C.LAYER_ORDER.index)
    hs = [Patch(fc=lc(l)[0], ec=lc(l)[1], lw=.9, label=l) for l in present if l in LAYER_COL] + [Patch(fc=FILL2, ec=GRAY, lw=.9, label='其余领域'),
          plt.Line2D([], [], color=INK2, lw=.8, ls=(0, (2, 1.5)), label='虚线：只在命例里说过')]
    ax.legend(handles=hs, loc='lower center', bbox_to_anchor=(.5, 0.0), ncol=len(hs), fontsize=7.6, frameon=False, handlelength=1.4)
    save(fig, out, '图07_枢纽判断.png')
    return {h: [list(x) for x in v] for h, v in hubs.items()}  # 每项：层、名、出处、有没有通则步


# ---------------- 图8 引擎怎样往后推 ----------------
def fig_algorithm(out):
    H = 37.0
    fig, ax = dcanvas(H / 10)
    ax.add_patch(FancyBboxPatch((.6, 10.6), 64.8, 25.6, boxstyle='round,pad=0,rounding_size=0.8', fc='none', ec=GRAY, lw=.9, ls=(0, (4, 3))))
    note(ax, 1.6, 34.6, '以下对十二宫的每一宫各做一遍（命宫在前）', fs=8.2, color=INK2)
    box(ax, 1.6, 22.4, 17.6, 7.4, '盘面\n这一宫的星、亮度、四化，\n三方四正、身宫、性别', fc='white', ec=GRID, fs=8.0)
    box(ax, 23.4, 22.4, 19.6, 7.4, '第一步：起步\n条件在这一宫都成立\n→ 得出判断（深度 1）', fc=FILL, ec=BLUE, fs=8.2)
    box(ax, 47.4, 22.4, 17.4, 7.4, '第二步起：推理步\n前提都已得出、附加条件成立\n→ 得出后一个判断', fc=FILL5, ec=TEAL, fs=7.6)
    arrow(ax, 19.2, 26.1, 23.4, 26.1); arrow(ax, 43.0, 26.1, 47.4, 26.1)
    ax.annotate('', xy=(60.6, 29.8), xytext=(52.0, 29.8), arrowprops=dict(arrowstyle='-|>', color=TEAL, lw=1.0, mutation_scale=9, connectionstyle='arc3,rad=-0.9'))
    note(ax, 50.8, 32.4, '再来一轮，直到推不出新判断（最多 8 轮）', fs=7.2, ha='right', color=TEAL)
    box(ax, 23.4, 11.6, 41.4, 7.4, '输出：这一宫的全部判断\n每个判断记下全部推导路径，输出最短的一条（深度＝前提里最深的＋1）；\n同一层里有吉有凶，标「两说」，都列出，不投票', fc=FILL3, ec=AMBER, fs=7.8)
    arrow(ax, 56.1, 22.4, 56.1, 19.0)
    box(ax, 1.6, 11.6, 17.6, 7.4, '候选盘\n出生时辰不定时，每张\n各推一次，只留都推出的', fc='white', ec=GRID, fs=8.0)
    box(ax, .6, .6, 64.8, 8.6, '一步用在哪一宫\n写某宫的只用在那一宫；写身宫的用在身宫所在之宫；写任一宫的：人宫（命、兄弟、夫妻、子女、\n仆役、父母）都用，事宫只收与该宫所管之事相符的结论（官禄收路线、成败；迁移收路线、意外；财帛收财……）。\n条件判断、空宫借对宫沿用第一版；五种修正只用于起步，只改方向与强度', fc=FILL2, ec=GRAY, fs=7.6, ha='left')
    save(fig, out, '图08_引擎怎样推.png')


# ---------------- 图9 示例盘 ----------------
def chart_grid(ax, x0, y0, cw, chh, label, style, center=None, cfs=8.6):
    for b, (r, c) in GRIDPOS.items():
        fc, ec, lw = style(b)
        ax.add_patch(Rectangle((x0 + c * cw, y0 + (3 - r) * chh), cw, chh, fc=fc, ec=ec, lw=lw))
        label(b, x0 + c * cw, y0 + (3 - r) * chh)
    if center:
        ax.text(x0 + 2 * cw, y0 + 2 * chh, center, ha='center', va='center', fontsize=cfs, color=INK, linespacing=1.55)


def fig_example_chart(out, chart):
    c = chart['chart']
    pal = {p['branch']: p for p in c['palaces']}
    ming, shen = c['mingGongBranch'], c['shenGongBranch']
    sfsz = {ming, (ming + 6) % 12, (ming + 4) % 12, (ming + 8) % 12}
    fig, ax = plt.subplots(figsize=(W, 6.2), dpi=220)
    ax.set_xlim(0, 100); ax.set_ylim(0, 75.6); ax.axis('off')
    cw, chh = 25, 18.9
    def style(b):
        if b == ming: return (FILL5, TEAL, 2.0)
        if b in sfsz: return (FILL5, TEAL, 1.0)
        return ('white', GRID, .8)
    def label(b, x, y):
        p = pal[b]
        tag = ('（命）' if b == ming else '') + ('（身）' if b == shen else '')
        ax.text(x + 1, y + chh - 1, f"{p['name']}{tag}", fontsize=8.6, fontweight='bold', color='#0d7a54' if b in sfsz else INK, va='top')
        ax.text(x + cw - 1, y + chh - 1, BR[b], fontsize=8, color=MUTED, va='top', ha='right')
        mn = []
        for s in p['stars']:
            nm = s['name']
            if nm in MAJOR:
                lv = s.get('brightnessRaw') or ''
                hua = s.get('siHua') or ''
                mn.append(nm + (lv[:1] if lv else '') + ('化' + hua if hua else ''))
        if not mn:
            mn = ['（空宫）']
        aux = [s['name'] for s in p['stars'] if s['name'] in JI6 + SHA6 + ['禄存', '天马']]
        cx = x + 1
        for m in mn:
            ax.text(cx, y + chh - 5.2, m, fontsize=8.4, color=RED if '化忌' in m else INK, va='top')
            cx += sum(1.0 if ord(ch) > 0x2E80 else .55 for ch in m) * 1.5 + 3.0
        if aux:
            ax.text(x + 1, y + chh - 9.6, '　'.join(aux[:3]) + ('\n' + '　'.join(aux[3:6]) if len(aux) > 3 else ''), fontsize=7.6, color=INK2, va='top', linespacing=1.4)
    li = c['lunarInfo']
    center = (f"开发用随机盘 r30（不对应真人）\n女命　{li['fourPillars'][0]}年生　{c['wuxingJuName']}\n命宫在{BR[ming]}（空宫，借对宫{BR[(ming + 6) % 12]}：武曲、贪狼）\n身宫在{BR[shen]}（{pal[shen]['name']}）\n"
              f"绿框＝命宫的三方四正\n黑字＝主星，灰字＝辅星与煞星，红字＝化忌\n星名后一字是亮度：庙＞旺＞平＞闲＞陷")
    chart_grid(ax, 0, 0, cw, chh, label, style, center=center, cfs=8.2)
    save(fig, out, '图09_示例盘.png')
    return {'命宫': BR[ming], '身宫': BR[shen]}


# ---------------- 图10 示例盘命宫的推理链 ----------------
def fig_r30_chain(out, ex, kb):
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
    for d, items in cols.items():
        tot = len(items) * (bh + gap) - gap
        y_top = (H - 3.4 + 6.0) / 2 + tot / 2
        for i, it in enumerate(items):
            x = d * colw + (colw - w) / 2 + .8
            y = y_top - i * (bh + gap) - bh
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
    save(fig, out, '图10_示例盘的推理链.png')
    return {'结点': sorted(nodes[n]['名'] for n in keep), '最大深度': maxd, '盘面条件': conds, '命例特指的步': sorted({first[n]['step'] for n in keep if case[first[n]['step']]})}


# ---------------- 图11 第三版与第四版 ----------------
def fig_v3_v4(out, ex):
    t3 = ex['第三版成稿']
    sec = t3.split('一、命宫')[1].split('二、身宫')[0]
    items = {}
    for ln in sec.split('\n'):
        ln = ln.strip()
        if '：' not in ln:
            continue
        lay, body = ln.split('：', 1)
        for it in body.split('；'):
            m = it.rsplit('（', 1)
            if len(m) == 2 and m[1].startswith('T'):
                items.setdefault(m[1].split('，')[0].rstrip('）'), (lay, m[0]))
    pick = [t for t in ['T97', 'T176', 'T923', 'T934', 'T928'] if t in items]
    left = [f"{items[t][0]}：{items[t][1]}（{t}）" for t in pick]
    nodes = ex['第四版·命宫结点']
    name2id = {v['名']: n for n, v in nodes.items()}
    def chain_line(path):
        s = path[0].replace('本宫有:', '命宫有').replace('本宫化:', '命宫化').replace('三方四正有:', '三方四正有').replace(',', '、')
        parts, prev = [s], None
        for nm in path[1:]:
            x = nodes[name2id[nm]]['推法'][0]
            extra = [nodes[p]['名'] for p in x['premises'] if nodes[p]['名'] != prev]
            note_ = ('，另需' + '、'.join(extra) if extra else '') + ('，限女命' if '性别:女' in (x['附加条件'] or []) + (x['条件'] or []) else '')
            parts.append(f"{nm}（{x['T']}{note_}）")
            prev = nm
        return ' → '.join(parts)
    lines = [chain_line(p) for p in ex['第四版·命宫主线'][:5]]
    b1 = '第三版：命宫里各条规则各自命中，彼此之间没有推导关系（节选；类别名是前作自己的）\n' + '\n'.join('· ' + x for x in left)
    b2 = '第四版：后一个判断由前一个判断推出，括号里是出处（命宫主线，节选；命宫是空宫，星借自对宫）\n' + '\n'.join('· ' + x for x in lines)
    h1 = text_size(b1, 7.8)[1] + 2.0
    h2 = text_size(b2, 7.8)[1] + 2.0
    H = h1 + h2 + 3.2
    fig, ax = dcanvas(H / 10)
    box(ax, 1.0, H - 1.0 - h1, 64.0, h1, b1, fc=FILL2, ec=GRAY, fs=7.8, ha='left')
    box(ax, 1.0, 1.0, 64.0, h2, b2, fc=FILL5, ec=TEAL, fs=7.8, ha='left')
    save(fig, out, '图11_第三版与第四版.png')
    return {'第三版': left, '第四版': lines}


# ---------------- 图12 覆盖 ----------------
def fig_coverage(out, cov, kb_path, holdout_path, ex, post):
    nodes, steps = C.load_kb(kb_path)
    rows = [r for r in jl(holdout_path)['rows'] if 'error' not in r]
    depths, nr, reach, any3 = [], [], collections.Counter(), 0
    for r in rows:
        ch = ENG.Chart(r)
        dp = C.infer(ch, nodes, steps)['命宫']
        depths.append(max((xs[0]['depth'] for xs in dp.values()), default=0))
        nr.append(len({x['step'] for xs in dp.values() for x in xs if x['premises']}))
        lays = {nodes[n]['层'] for n, xs in dp.items() if any(x['premises'] for x in xs)}
        for lay in lays:
            reach[lay] += 1
        any3 += bool(lays & {'行为', '路线', '成败'})
    m = cov['命宫']
    assert statistics.median(depths) == m['最长链步数']['中位数'] and max(depths) == m['最长链步数']['最大']
    assert statistics.median(nr) == m['用上的推理步条数']['中位数'] and max(nr) == m['用上的推理步条数']['最大']
    assert {k: reach[k] for k in reach} == m['推理步走到各层的盘数'] and any3 == m['推理步走到行为路线成败任一层的盘'], '与覆盖检验结果不一致'
    n = cov['charts']
    g = post['P1a·只用通则步的覆盖']
    fig, axs = plt.subplots(1, 2, figsize=(W, 3.2), dpi=220, gridspec_kw={'width_ratios': [1.3, 1]})
    ax = axs[0]
    labels = MAIN6 + ['行为、路线、\n成败任一']
    vals = [reach[l] / n for l in MAIN6] + [any3 / n]
    cols = [lc(l)[1] for l in MAIN6] + [DBLUE]
    ax.bar(range(7), vals, color=cols, width=.62)
    for i, v in enumerate(vals):
        ax.text(i, v + .02, f'{v:.0%}' if v >= .1 else f'{v:.1%}', ha='center', fontsize=7.8, color=INK)
    ax.set_xticks(range(7)); ax.set_xticklabels(labels, fontsize=7.8)
    ax.set_ylim(0, 1.12); ax.set_yticks([0, .5, 1]); ax.set_yticklabels(['0', '50%', '100%'], fontsize=7.6, color=MUTED)
    ax.set_title('命宫里经推理步推到这一层的盘', loc='left', fontsize=9.2)
    ax2 = axs[1]
    cnt = collections.Counter(depths)
    gc = {int(k): v for k, v in g['最长链分布'].items()}
    ks = list(range(1, max(max(depths), max(gc)) + 1))
    wdt = .38
    ax2.bar([k - wdt / 2 for k in ks], [cnt[k] / n for k in ks], color=BLUE, width=wdt, label='全部步')
    ax2.bar([k + wdt / 2 for k in ks], [gc.get(k, 0) / g['盘数'] for k in ks], color=GRAY, width=wdt, label='只用通则步（事后）')
    for k in ks:
        v = cnt[k] / n
        ax2.text(k - wdt / 2, v + .015, f'{v:.0%}' if v >= .01 else f'{v:.1%}', ha='center', fontsize=7.0, color=INK)
        v2 = gc.get(k, 0) / g['盘数']
        if v2:
            ax2.text(k + wdt / 2, v2 + .015, f'{v2:.0%}' if v2 >= .01 else f'{v2:.1%}', ha='center', fontsize=7.0, color=INK2)
    r30 = ex['第四版·命宫覆盖口径']['最长链步数']
    ax2.annotate('示例盘 r30', xy=(r30 - wdt / 2, cnt[r30] / n + .06), xytext=(r30 - .9, cnt[r30] / n + .3), fontsize=7.6, color=RED,
                 arrowprops=dict(arrowstyle='-|>', color=RED, lw=.8, mutation_scale=7))
    ax2.set_xticks(ks); ax2.set_xlabel('命宫最长一条链的步数（含第一步起步）', fontsize=8.0)
    ax2.set_ylim(0, 1.0); ax2.set_yticks([0, .25, .5, .75]); ax2.set_yticklabels(['0', '25%', '50%', '75%'], fontsize=7.6, color=MUTED)
    ax2.legend(loc='upper right', fontsize=7.4)
    ax2.set_title('最长一条链有几步', loc='left', fontsize=9.2)
    for a in axs:
        for s in ('top', 'right'): a.spines[s].set_visible(False)
        a.grid(axis='y', color=GRID, lw=.6); a.set_axisbelow(True)
    fig.tight_layout()
    save(fig, out, '图12_覆盖.png')
    return {'各层盘数': {l: reach[l] for l in MAIN6}, '任一层': any3, '盘数': n, '最长链分布': {k: cnt[k] for k in ks}, 'r30最长链': r30,
            '只用通则步最长链分布': gc, '推理步条数分位': m['用上的推理步条数'], 'r30推理步条数': ex['第四版·命宫覆盖口径']['用上的推理步条数']}


# ---------------- 图13 主检验的设计 ----------------
def fig_test_design(out):
    H = 33.0
    fig, ax = dcanvas(H / 10)
    box(ax, 15.0, 26.0, 36.0, 6.0, '倪海厦讲这位命主的时段\n（视频分集与起止时间，前后各加 2 分钟）', fc='white', ec=GRID, fs=8.2)
    box(ax, 1.0, 15.4, 30.4, 8.2, '判断集 G\n时段内、命例特指、先天、宫为命宫或身宫的\n那些步的结论（归一后的结点）', fc=FILL6, ec=RED, fs=7.8)
    box(ax, 34.6, 15.4, 30.4, 8.2, '剔除时段内的全部步\n（不论是不是命例特指）\n引擎只用其余的步推', fc=FILL, ec=BLUE, fs=7.8)
    arrow(ax, 25.0, 26.0, 16.2, 23.6); arrow(ax, 41.0, 26.0, 49.8, 23.6)
    box(ax, 34.6, 5.2, 14.6, 7.8, '本人盘\n命宫（加身宫）\n推出的结点', fc='white', ec=GRID, fs=7.6)
    box(ax, 50.4, 5.2, 14.6, 7.8, '600 张随机盘\n每张同样推\n（开发时没用过）', fc='white', ec=GRID, fs=7.6)
    arrow(ax, 45.0, 15.4, 41.9, 13.0); arrow(ax, 55.0, 15.4, 57.7, 13.0)
    box(ax, 1.0, 1.0, 30.4, 12.0, '得分与排位\n得分＝G 里在这张盘上推出来的比例\nu＝随机盘里得分比本人盘高的比例（相等的算一半）\nu 越小，本人盘越突出；0.5＝和随机盘一样\n24 人取平均；p 由随机抽盘重复 1 万次算出', fc=FILL3, ec=AMBER, fs=7.4, ha='left')
    arrow(ax, 34.6, 9.1, 31.4, 7.6); arrow(ax, 16.2, 15.4, 16.2, 13.0)
    ax.plot([57.7, 57.7], [5.2, 3.0], color=MUTED, lw=1.1)
    arrow(ax, 57.7, 3.0, 31.4, 3.0)
    save(fig, out, '图13_主检验设计.png')


# ---------------- 图14 主检验结果 ----------------
def fig_test_result(out, rep, diag):
    reach0 = {r['person_id'] for r in diag['各人'] if r['实际可达'] == 0}
    ps = [p for p in rep['各人'] if p['计入']]
    ps.sort(key=lambda p: (p['u'], p['person_id']))
    fig, ax = plt.subplots(figsize=(W, 5.4), dpi=220)
    for i, p in enumerate(ps):
        y = len(ps) - 1 - i
        col = GRAY if p['person_id'] in reach0 else BLUE
        ax.plot([p['只用定性步·u']], [y - .24], 'o', ms=6.4, mfc='none', mec=MUTED, mew=1.0, zorder=2)
        ax.plot([p['u']], [y + .12], 'o', ms=6.2, color=col, zorder=3)
    ax.axvline(.5, color=RED, lw=1.0, ls=(0, (3, 3)))
    mu = rep['主检验']['平均u']; pv = rep['主检验']['p_单侧']; mu1 = rep['另报·只用定性步']['平均u']
    ax.axvline(mu, color=BLUE, lw=1.0)
    ax.text(.505, len(ps) - .2, '0.5＝和随机盘一样', color=RED, fontsize=7.8, va='bottom')
    ax.text(.985, len(ps) - 2.2, f'平均 u＝{mu:.3f}（蓝竖线）\np＝{pv:.3f}：未通过\n（事先定 p＜0.05 才算通过）\n只用起步：平均 u＝{mu1:.3f}', color=BLUE, fontsize=8.4, ha='right', va='top', linespacing=1.5)
    ax.set_yticks(range(len(ps))); ax.set_yticklabels([p['person_id'] for p in reversed(ps)], fontsize=7.4)
    ax.set_xlim(0, 1); ax.set_ylim(-.8, len(ps) + .6)
    ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(['0\n比所有随机盘都好', '0.25', '0.5', '0.75', '1\n比所有随机盘都差'], fontsize=7.4, color=MUTED)
    for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, lw=.6); ax.set_axisbelow(True)
    ax.legend(handles=[plt.Line2D([], [], marker='o', ls='', color=BLUE, ms=6, label='全部步'),
                       plt.Line2D([], [], marker='o', ls='', mfc='none', mec=MUTED, ms=7, label='只用起步（下移半行）'),
                       plt.Line2D([], [], marker='o', ls='', color=GRAY, ms=6, label='剔除后一个判断也推不出')],
              loc='upper left', bbox_to_anchor=(0, -.1), ncol=3, fontsize=7.6)
    ax.set_title(f"主检验：{rep['人数']['计入']} 位命主的 u（本人盘在 600 张随机盘里的位置）", loc='left')
    fig.tight_layout()
    save(fig, out, '图14_主检验结果.png')
    return {'计入': rep['人数']['计入'], '平均u': mu, 'p': pv, '只用定性步平均u': mu1,
            '只用定性步p': rep['另报·只用定性步']['p_单侧'], 'u小于0.5': rep['主检验']['u小于0.5的人数'], '推不出的人': sorted(reach0)}


# ---------------- 图15 事后诊断（事先登记的 D1、D4） ----------------
def fig_diag(out, diag):
    d1, d4 = diag['D1可达性'], diag['D4构成']['步']
    tot = d1['倪师判断集结点合计']
    reach, struct = d1['实际可达的结点'], d1['结构上可达的结点']
    ok_steps = d4.get('定性步·可操作·无格无其他', 0) + d4.get('推理步·可操作·无格无其他', 0)
    ge = sum(v for k, v in d4.items() if '含格' in k)
    other = sum(v for k, v in d4.items() if '含其他' in k)
    nst = sum(d4.values())
    rows = [(f'判断集 {tot} 个结点（按人累计）\n剔除本人时段的步之后', [('随机盘上推出过', reach, BLUE), ('有步可推，但 600 张盘都没推出', struct - reach, LBLUE), ('引擎能用的步都推不出', tot - struct, GRAY)]),
            (f'判断集的 {nst} 步（按人累计）\n条件写不写得出', [('条件写得出', ok_steps, TEAL), ('含「格」', ge, AMBER), ('原话没说出盘面', other, '#e8a0a0')])]
    fig, ax = plt.subplots(figsize=(W, 2.6), dpi=220)
    for k, (name, segs) in enumerate(rows):
        y = len(rows) - 1 - k
        s = sum(v for _, v, _ in segs); x = 0
        for lab, v, col in segs:
            ax.barh(y, v / s, left=x, color=col, height=.5, edgecolor=SURFACE, lw=1.5)
            if v / s > .14:
                ax.text(x + v / s / 2, y, f'{lab}\n{v}', ha='center', va='center', fontsize=7.2, color='white' if col in (BLUE, TEAL) else INK, linespacing=1.2)
            else:
                ax.text(x + v / s / 2, y - .31, f'{lab} {v}', ha='center', va='top', fontsize=6.8, color=INK2)
            x += v / s
        if k == 0:
            ax.annotate('', xy=(0, y + .34), xytext=(struct / tot, y + .34), arrowprops=dict(arrowstyle='<->', color=INK2, lw=.8, shrinkA=0, shrinkB=0))
            ax.text(struct / tot / 2, y + .38, f'有步可推 {struct}', ha='center', va='bottom', fontsize=7.2, color=INK2)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=7.8)
    ax.set_xlim(0, 1); ax.set_ylim(-.7, len(rows) - .3); ax.set_xticks([])
    for s_ in ('top', 'right', 'left', 'bottom'): ax.spines[s_].set_visible(False)
    ax.tick_params(axis='y', length=0)
    fig.tight_layout()
    save(fig, out, '图15_事后诊断.png')
    return {'结点': tot, '实际可达': reach, '结构上可达': struct, '步': nst, '可求值': ok_steps, '含格': ge, '没说出盘面': other}


# ---------------- 图16 事后补充分析 ----------------
def fig_posthoc(out, post, post2, rep_):
    q1 = post2['Q1·判断集的步在本人盘上（拆开）']
    seg = [('起步：条件成立', q1.get('起步·各候选都成立', 0) + q1.get('起步·部分候选成立', 0), TEAL),
           ('起步：条件不成立', q1.get('起步·条件都不成立', 0), RED),
           ('推理步：都成立', q1.get('推理步·各候选都成立', 0) + q1.get('推理步·部分候选成立', 0), '#4fc79b'),
           ('推理步：前提没推出', q1.get('推理步·附加条件成立但前提没推出', 0), ORANGE),
           ('推理步：附加条件不成立', q1.get('推理步·附加条件不成立', 0), '#f4a58a'),
           ('含「格」', q1.get('含格', 0), AMBER), ('原话没说出盘面', q1.get('原话没说出盘面', 0), '#e8a0a0')]
    tot = sum(v for _, v, _ in seg)
    fig = plt.figure(figsize=(W, 5.4), dpi=220)
    ax = fig.add_axes([0.24, 0.70, 0.72, 0.21])
    x = 0
    for i, (lab, v, col) in enumerate(seg):
        ax.barh(0, v / tot, left=x, color=col, height=.9, edgecolor=SURFACE, lw=1.5)
        if v / tot > .1:
            ax.text(x + v / tot / 2, 0, f'{lab}\n{v}', ha='center', va='center', fontsize=6.9, color='white' if col in (TEAL, RED, ORANGE) else INK, linespacing=1.2)
        else:
            ax.text(x + v / tot / 2, -.55 - (i % 2) * .42, f'{lab} {v}', ha='center', va='top', fontsize=6.6, color=INK2)
        x += v / tot
    ax.set_xlim(0, 1); ax.set_ylim(-1.5, .55); ax.set_yticks([0]); ax.set_yticklabels([f'判断集的 {tot} 步（按人累计）\n不剔除，看本人盘'], fontsize=7.8)
    ax.set_xticks([])
    for s_ in ('top', 'right', 'left', 'bottom'): ax.spines[s_].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.set_title('一、判断集的步，在本人盘上推不推得出', loc='left', fontsize=9.2)
    ax2 = fig.add_axes([0.24, 0.09, 0.72, 0.47])
    p7 = post['P7·分布']; p1 = post['P1b·只用通则步的主检验（事后）']; p2 = post['P2·候选盘']; p3 = post['P3·同性别对照']
    q6 = post2['Q6·不加前后2分钟']; q7 = post2['Q7·候选盘性别不一']
    rows = [('主检验（登记口径，24 人）', rep_['主检验']['平均u'], p7['平均u的自助法95%区间'], 'main'),
            ('换算法：只用通则步（24 人）', p1['平均u'], None, 'alg'),
            ('换算法：每张候选盘各算再平均（24 人）', p2['每张候选各算再平均的平均u'], None, 'alg'),
            (f"换算法：只和同性别随机盘比（{p3['人数']} 人）", p3['平均u'], None, 'alg'),
            (f"换算法：不加前后 2 分钟（{q6['计入人数']} 人）", q6['平均u'], None, 'alg'),
            (f"按人分组：只有一张候选盘（{p2['单候选人数']} 人）", p2['单候选平均u'], None, 'grp'),
            (f"按人分组：有几张候选盘（{p2['多候选人数']} 人）", p2['多候选原平均u'], None, 'grp'),
            (f"按人分组：候选盘男女都有（{q7['人数']} 人）", q7['平均u'], None, 'grp')]
    for i, (name, v, ci, kind) in enumerate(rows):
        y = len(rows) - 1 - i
        if ci:
            ax2.plot(ci, [y, y], color=LBLUE, lw=6, solid_capstyle='butt', zorder=1)
        ax2.plot([v], [y], 'o' if kind != 'grp' else 'D', color=BLUE if kind == 'main' else INK2, ms=7 if kind != 'grp' else 6, zorder=3)
        ax2.text(v + .008, y + .22, f'{v:.3f}' + (f"　p＝{rep_['主检验']['p_单侧']:.3f}" if kind == 'main' else ''), fontsize=7.4, color=INK, va='bottom')
    ax2.axhline(len(rows) - 1.5, color=GRID, lw=.8); ax2.axhline(len(rows) - 5.5, color=GRID, lw=.8)
    ax2.axvline(.5, color=RED, lw=1.0, ls=(0, (3, 3)))
    ax2.set_yticks(range(len(rows))); ax2.set_yticklabels([r[0] for r in reversed(rows)], fontsize=7.6)
    ax2.set_xlim(.3, .7); ax2.set_ylim(-.6, len(rows) - .2)
    ax2.set_xlabel('平均 u（越小越好；0.5＝和随机盘一样）。浅蓝带：主检验的 95% 区间（假定各人独立）。各行人数不同，不宜直接比大小', fontsize=7.2, color=MUTED)
    for s_ in ('top', 'right', 'left'): ax2.spines[s_].set_visible(False)
    ax2.tick_params(axis='y', length=0)
    ax2.set_title('二、换几种算法、按人分组看平均 u（事后，只作描述，不报 p 值）', loc='left', fontsize=9.2)
    save(fig, out, '图16_事后补充分析.png')
    return {'Q1': dict(q1), '各行平均u': [(r[0], r[1]) for r in rows], '主检验区间': p7['平均u的自助法95%区间']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out)
    M = os.path.join(CH, 'chain_merged_v1'); RS = os.path.join(CH, 'chain_results_v1')
    adj, chk, norm = jl(M, 'adjudicated_v1.json'), jl(M, 'check_v1.json'), jl(M, 'normalized_v1.json')
    labels_all = jl(CH, 'chain_norm_packets_v1', 'labels_all.json')
    kb = jl(CH, 'chain_kb_v1.json')
    cov, rep, diag, ex, post, post2 = (jl(RS, f) for f in ('coverage_v1.json', 'reproduce_v1.json', 'reproduce_diag_v1.json', 'example_r30_v1.json', 'posthoc_v1.json', 'posthoc2_v1.json'))
    chart = next(r for r in jl(E, 'freeze_check_v1', 'rand_charts.json')['rows'] if r['id'] == 'r30')
    rec = {}
    rec['图1'] = fig_pipeline(a.out, adj, chk, norm, kb)
    rec['图2'] = fig_layers(a.out, kb)
    rec['图3'] = fig_anatomy(a.out, kb)
    rec['图4'] = fig_extract_check(a.out, adj, chk)
    rec['图5'] = fig_normalize(a.out, norm, labels_all)
    rec['图6'] = fig_layer_matrix(a.out, kb)
    rec['图7'] = fig_hubs(a.out, kb)
    fig_algorithm(a.out)
    rec['图9'] = fig_example_chart(a.out, chart)
    rec['图10'] = fig_r30_chain(a.out, ex, kb)
    rec['图11'] = fig_v3_v4(a.out, ex)
    rec['图12'] = fig_coverage(a.out, cov, os.path.join(CH, 'chain_kb_v1.json'), os.path.join(CH, 'v4_holdout_v1', 'holdout_charts.json'), ex, post)
    fig_test_design(a.out)
    rec['图14'] = fig_test_result(a.out, rep, diag)
    rec['图15'] = fig_diag(a.out, diag)
    rec['图16'] = fig_posthoc(a.out, post, post2, rep)
    open(os.path.join(a.out, '图中数字_chain_v3.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'out': sorted(os.listdir(a.out))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
