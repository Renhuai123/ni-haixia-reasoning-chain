"""倪师推理链论文（第七稿）的全部插图 v1（只做呈现；数字全部取自已登记的文件，不新做统计）。
样式沿用第六稿（make_paper_figures_v6.py）：冠宋黑体（Hiragino Sans GB）、米白底、蓝为主色、示意图框第一行加粗其余灰字、300 dpi。
读（23_倪师推理链_20261007 下）：
- chain_merged_v1/adjudicated_v1.json（抽取一致程度、定稿步数）、chain_merged_v1/check_v1.json（逐步核查）、
  chain_merged_v1/normalized_v1.json 与 chain_norm_packets_v1/labels_all.json（归一）、chain_kb_v1.json（推理链知识库）；
- chain_results_v1/：coverage_v1.json、reproduce_v1.json、reproduce_diag_v1.json、trace_check_v1.json、example_r30_v1.json；
- v4_holdout_v1/holdout_charts.json（覆盖图要逐盘的最长链分布：用第四版引擎重推，并核对与 coverage_v1.json 的分位数、各层盘数完全相同）；
- 21_倪师断法引擎_20261005/freeze_check_v1/rand_charts.json（示例盘 r30 的盘面）。
图内不写图号，图号与图题写在正文。另写 图中数字_chain_v1.json，供正文核数。
用法：python3 make_chain_figures_v1.py --out <新目录>"""
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
LGRAY, GRAY, RED, AMBER, ORANGE, TEAL = '#d4d3ce', '#b9b8b3', '#e34948', '#eda100', '#eb6834', '#1baf7a'
FILL, FILL2, FILL3, FILL4, FILL5, FILL6 = '#dbe9fa', '#eeeeeb', '#fdf0cc', '#fbe1d6', '#d6f1e6', '#f9dcdc'
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
# 各层的配色（底色, 边色）；其余领域一律灰
LAYER_COL = {'定性': (FILL, BLUE), '长相': (FILL5, TEAL), '个性': (FILL5, TEAL), '行为': (FILL3, AMBER), '路线': (FILL4, ORANGE), '成败': (FILL6, RED)}
MAIN6 = ['定性', '长相', '个性', '行为', '路线', '成败']


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
    """估算文字所占的宽高（单位 0.1 英寸）：汉字与全角符号按 1 个字宽，西文与数字按 0.55 个字宽，行距 1.45。"""
    def cw(ch):
        return 1.0 if (ord(ch) > 0x2E80 or ch in '…—→×') else 0.55
    ls = text.split('\n')
    return max(sum(cw(ch) for ch in l) for l in ls) * fs / 7.2, len(ls) * fs * 1.45 / 7.2


def box(ax, x, y, w, h, text, fc=FILL, ec=BLUE, fs=9, bold=False, color=INK, lw=.9, ha='center', r=0.8):
    """圆角框：多行时第一行加粗、深色，其余行灰字；bold=True 时整框加粗。文字放不下就报错。"""
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


def arrow(ax, x1, y1, x2, y2, color=MUTED, lw=1.1, rad=0):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color=color, lw=lw, shrinkA=0, shrinkB=0, mutation_scale=9,
                                                                 connectionstyle=f'arc3,rad={rad}'))


def elabel(ax, x, y, text, fs=6.6, color=INK2):
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, color=color, bbox=dict(boxstyle='round,pad=0.12', fc=SURFACE, ec='none'))


def save(fig, out, name, tight=True):
    fig.savefig(os.path.join(out, name), bbox_inches='tight' if tight else None, pad_inches=0.08, dpi=300)
    plt.close(fig)


def wrap(s, n):
    """按字数硬折行（汉字按 1、西文数字按 0.55 计宽）。"""
    out, cur, w = [], '', 0.0
    for ch in s:
        cw = 1.0 if ord(ch) > 0x2E80 else .55
        if w + cw > n and cur:
            out.append(cur); cur, w = '', 0.0
        cur += ch; w += cw
    if cur:
        out.append(cur)
    return out


# ---------------- 图1 总流程 ----------------
def fig_pipeline(out, adj, chk, norm, kb):
    a = adj['一致程度']['按步·甲乙各自']
    jia, yi = a['甲·收'] + a['甲·不收'], a['乙·收'] + a['乙·不收']
    c = chk['counts']
    ok, bad = c['定性步成立'] + c['推理步成立'], c['定性步不成立'] + c['推理步不成立']
    kc = kb['counts']
    n_q = adj['一致程度']['按条']['条目']
    left = [f'① 讲稿原话\n《天纪》倪海厦原话 {n_q} 条，分 35 批',
            f'② 抽取（甲、乙各自独立）\n甲抽出 {jia} 步，乙抽出 {yi} 步',
            f"③ 裁定（第三人逐步定稿）\n定稿 {adj['counts']['定稿步']} 步：定性步 {adj['counts']['定性步']}、推理步 {adj['counts']['推理步']}",
            f'④ 逐步核查（第四人逐步判）\n判成立 {ok} 步，不成立 {bad} 步']
    right = [f"⑤ 判断归一（两人归类，第三人裁定）\n{norm['counts']['判断名']} 个判断名归成 {norm['counts']['结点']} 个结点",
             f"⑥ 推理链知识库\n{kc['收下的步']} 步、{kc['结点']} 个结点；引擎可用 {kc['引擎可用（可操作且先天）']} 步",
             '⑦ 引擎第四版\n每一宫从盘面起，一轮一轮往后推',
             '⑧ 四项检验\n忠实、覆盖、复现命例、可追溯']
    bw, bh, gap = 29.6, 7.0, 3.0
    H = 4 * bh + 3 * gap + 1.2
    fig, ax = dcanvas(H / 10)
    xs = (1.6, 34.8)
    tops = [H - .6 - bh - k * (bh + gap) for k in range(4)]
    for col, items in enumerate((left, right)):
        for k, t in enumerate(items):
            fc, ec = ((FILL, BLUE) if col == 0 else (FILL5, TEAL)) if k < 3 or col == 0 else (FILL3, AMBER)
            box(ax, xs[col], tops[k], bw, bh, t, fc=fc, ec=ec, fs=8.6, ha='left')
            if k:
                arrow(ax, xs[col] + bw / 2, tops[k - 1], xs[col] + bw / 2, tops[k] + bh)
    arrow(ax, xs[0] + bw, tops[3] + bh / 2, xs[1], tops[0] + bh / 2, color=GRAY)
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
        s = by[sid]
        assert [(nd[n]['层'], nd[n]['名']) for n in s['conclusions']] == [(lay, name)], sid
    assert [nd[n]['名'] for n in by['T213-c2']['premises']] == ['佐才'] and [nd[n]['名'] for n in by['T214-c3']['premises']] == ['佐才']
    assert [nd[n]['名'] for n in by['T247-c3']['premises']] == ['刚强']
    assert by['T213-c1']['条件'] == ['本宫有:天相'] and by['T239-c5']['条件'] == ['本宫有:杀破狼']
    H = 55.0
    fig, ax = dcanvas(H / 10)
    q = '「介绍命宫的时候，我们可以看到这个人的长相，这个人的个性。从个性上面可以知道这个人的行为模式。其实开始从命宫一看就已经知道成败」（T409）'
    for i, ln in enumerate(wrap(q, 52)):
        note(ax, 1.4, H - 2.0 - i * 2.3, ln, fs=8.4, color=INK2)
    rows = [('盘面', '星、亮度、四化、会照'), ('定性', '属于哪一类星、哪一类人'), ('长相·个性', '外貌、性情'), ('行为', '做事的方式'),
            ('路线', '走哪条路、做哪一行'), ('成败', '成就高低、得失贵贱')]
    rh, bh = 7.0, 5.4
    y0 = H - 12.2
    ys = {name: y0 - k * rh for k, (name, _) in enumerate(rows)}
    for k, (name, desc) in enumerate(rows):
        fc, ec = (('white', GRID) if name == '盘面' else lc(name.split('·')[-1]))
        box(ax, 1.4, ys[name], 15.2, bh, f'{name}\n{desc}', fc=fc, ec=ec, fs=8.2)
        if k:
            arrow(ax, 9.0, ys[rows[k - 1][0]], 9.0, ys[name] + bh, color=GRAY)
        ax.plot([17.4, 64.6], [ys[name] - .8, ys[name] - .8], color=GRID, lw=.6, zorder=0)
    def node(x, row, text, lay, w=12.4):
        fc, ec = ('white', GRID) if lay == '盘面' else lc(lay)
        box(ax, x - w / 2, ys[row], w, bh, text, fc=fc, ec=ec, fs=8.4)
        return (x, ys[row], ys[row] + bh)
    a0 = node(29.0, '盘面', '命宫有天相', '盘面')
    a1 = node(29.0, '定性', '佐才', '定性')
    a2 = node(24.6, '路线', '当助理秘书', '路线')
    a3 = node(36.4, '成败', '位高无权', '成败')
    b0 = node(54.0, '盘面', '命宫有七杀、\n破军或贪狼', '盘面', w=13.6)
    b1 = node(54.0, '长相·个性', '刚强', '个性')
    b2 = node(54.0, '行为', '大怒之下犯大错', '行为', w=15.4)
    arrow(ax, 29.0, a0[1], 29.0, a1[2]); elabel(ax, 33.0, (a0[1] + a1[2]) / 2, 'T213 定性步')
    arrow(ax, 26.0, a1[1], 24.6, a2[2]); elabel(ax, 19.9, ys['行为'] + 2.6, 'T213 推理步\n「你适合去当」')
    arrow(ax, 33.0, a1[1], 36.4, a3[2]); elabel(ax, 40.6, ys['行为'] + 2.6, 'T214 推理步\n「所以」')
    arrow(ax, 54.0, b0[1], 54.0, b1[2]); elabel(ax, 58.6, ys['定性'] + 2.7, 'T239 定性步')
    arrow(ax, 54.0, b1[1], 54.0, b2[2]); elabel(ax, 58.8, (b1[1] + b2[2]) / 2, 'T247 推理步')
    note(ax, 17.6, 1.6, '框的颜色表示层，箭头上是出处。两条链都取自推理链知识库。', fs=7.6, width=47)
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
        quote = wrap(f"「{s['原话摘录']}」", 19)
        return common + mid + tail, quote
    need = []
    for s_ in (q, r):
        fs_, quote = fields(s_)
        need.append(5.6 + sum(1.9 * len(wrap(v, 20)) + .5 for _, v in fs_) + 1.9 * len(quote) + 1.6)
    H = max(need) + .8
    fig, ax = dcanvas(H / 10)
    for k, (s, title, fc, ec) in enumerate(((q, '定性步（起步）：盘面 → 判断', FILL, BLUE), (r, '推理步（承接）：判断 → 判断', FILL5, TEAL))):
        x0 = 1.2 + k * 32.6
        ax.add_patch(FancyBboxPatch((x0, .8), 31.2, H - 1.6, boxstyle='round,pad=0,rounding_size=0.8', fc=fc, ec=ec, lw=.9))
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
        assert y - len(quote) * 1.9 > 1.2, ('卡片放不下', s['step_id'])
    save(fig, out, '图03_两种步.png')
    return {'定性步': q['step_id'], '推理步': r['step_id']}


# ---------------- 图4 抽取一致与核查 ----------------
def fig_extract_check(out, adj, chk):
    g = adj['一致程度']
    t = g['按条']
    both_no = t['推理步有无一致'] - t['两人都有推理步']
    src = g['按步·定稿来源']
    c = chk['counts']
    rows = [(f"{t['条目']} 条原话：\n两人对「有没有推理步」", [('两人都说有', t['两人都有推理步'], BLUE), ('两人都说没有', both_no, LBLUE), ('只一人说有', t['只一人有推理步'], AMBER)]),
            (f"定稿 {adj['counts']['定稿步']} 步的来源", [('甲乙都抽到', src['甲乙'], BLUE), ('只甲抽到', src['只甲'], AMBER), ('只乙抽到', src['只乙'], ORANGE), ('裁定者补入', src['补入'], GRAY)]),
            (f"定性步 {adj['counts']['定性步']} 步的核查", [('成立', c['定性步成立'], TEAL), ('不成立', c['定性步不成立'], RED)]),
            (f"推理步 {adj['counts']['推理步']} 步的核查", [('成立', c['推理步成立'], TEAL), ('不成立', c['推理步不成立'], RED)])]
    fig, ax = plt.subplots(figsize=(W, 3.3), dpi=220)
    for k, (name, segs) in enumerate(rows):
        y = len(rows) - 1 - k
        tot = sum(v for _, v, _ in segs); x = 0
        small = [(lab, v, col) for lab, v, col in segs if v / tot <= .07]
        for j, (lab, v, col) in enumerate(segs):
            ax.barh(y, v / tot, left=x, color=col, height=.56, edgecolor=SURFACE, lw=1.5)
            if v / tot > .07:
                ax.text(x + v / tot / 2, y, f'{lab} {v}', ha='center', va='center', fontsize=7.8, color='white' if col in (BLUE, TEAL, RED, ORANGE) else INK)
            x += v / tot
        for i, (lab, v, col) in enumerate(small):   # 窄段的标注放到条形右边，上下错开
            yy = y + (len(small) - 1) * .13 - i * .26
            ax.plot([1.02], [yy], 's', color=col, ms=5, clip_on=False)
            ax.text(1.035, yy, f'{lab} {v}', ha='left', va='center', fontsize=7.2, color=INK2, clip_on=False)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=8.4)
    ax.set_xlim(0, 1); ax.set_ylim(-.5, len(rows) - .2)
    ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(['0', '25%', '50%', '75%', '100%'], fontsize=7.6, color=MUTED)
    for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.set_title('抽取两人的一致程度与逐步核查的结果', loc='left')
    fig.tight_layout(); fig.subplots_adjust(right=.84)
    save(fig, out, '图04_抽取与核查.png')
    return {'按条一致': t['推理步有无一致'], '两人都有': t['两人都有推理步'], '两人都没有': both_no, '只一人': t['只一人有推理步'],
            '来源': src, '核查': {k: c[k] for k in ('定性步成立', '定性步不成立', '推理步成立', '推理步不成立')}}


# ---------------- 图5 判断归一 ----------------
def fig_normalize(out, norm, labels_all):
    lab = {l['编号']: l for l in labels_all['labels']}
    nid = next(k for k, v in norm['nodes'].items() if v['名'] == '武官星' and v['层'] == '定性')
    mem = sorted(norm['nodes'][nid]['成员'], key=lambda m: -lab[m]['次数'])
    groups = [('G1', '定性'), ('G2', '长相、个性、行为'), ('G3', '路线、成败'), ('G4', '财、祖业田宅、福德'), ('G5', '婚姻、子女、父母、\n兄弟、朋友合伙'), ('G6', '健康、意外、官非、\n寿元、其他')]
    ag = norm['agreement']
    fig = plt.figure(figsize=(W, 3.5), dpi=220)
    ax = fig.add_axes([0.0, 0.0, 0.47, 1.0]); ax.axis('off')
    Wd, Hd = 38.5, 35.0
    ax.set_xlim(0, Wd); ax.set_ylim(0, Hd)
    ax.text(.6, Hd - 1.6, '例：六种说法归成一个结点', fontsize=9.6, fontweight='bold', color=INK, va='center')
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
        ax2.text(v + .015, y, f'{v:.0%}', va='center', fontsize=7.8, color=INK)
    ax2.set_yticks(ys); ax2.set_yticklabels([n for _, n in groups], fontsize=7.4)
    ax2.set_xlim(0, 1.12); ax2.set_xticks([0, .5, 1]); ax2.set_xticklabels(['0', '50%', '100%'], fontsize=7.4, color=MUTED)
    for s in ('top', 'right', 'left'): ax2.spines[s].set_visible(False)
    ax2.tick_params(axis='y', length=0)
    ax2.set_title('两名归类者的合并一致率（按组）', loc='left', fontsize=9.2)
    ax2.text(0, -1.25, '合并一致率＝两人都放进同一结点的判断名对数\n÷ 至少一人放进同一结点的对数', fontsize=7.0, color=MUTED, va='top', transform=ax2.transData)
    save(fig, out, '图05_判断归一.png')
    return {'例': [(lab[m]['判断'], lab[m]['次数']) for m in mem], '合并一致率': {g: ag[g]['合并一致率'] for g, _ in groups}}


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
    vcap = 50   # 颜色到 50 条封顶，免得「其余领域」一格把其他格都压淡；数字照实写
    ax.imshow([[min(v, vcap) for v in r] for r in M], cmap=cmap, vmin=0, vmax=vcap)
    for i in range(len(cats)):
        for j in range(len(cats)):
            v = M[i][j]
            if v:
                ax.text(j, i, str(v), ha='center', va='center', fontsize=8.4, color='white' if v > vcap * .55 else INK)
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
    for s in R:
        for p in s['premises']:
            for c in s['conclusions']:
                outl[p][c].add(s['T'])
    def hub(name):
        n = next(k for k, v in nd.items() if v['名'] == name and v['层'] == '定性')
        tg = sorted(outl[n].items(), key=lambda kv: (C.LAYER_ORDER.index(nd[kv[0]]['层']), min(int(t[1:]) for t in kv[1]), nd[kv[0]]['名']))
        return [(nd[c]['层'], nd[c]['名'], '、'.join(sorted(ts, key=lambda t: int(t[1:])))) for c, ts in tg]
    hubs = {h: hub(h) for h in ('武官星', '佐才', '文官带', '财星')}
    bh, gap = 2.5, .45
    nL = len(hubs['武官星'])
    H = nL * (bh + gap) + 5.0
    fig, ax = dcanvas(H / 10)
    def draw(name, x0, ytop, tw=17.2):
        ts = hubs[name]
        hgt = len(ts) * (bh + gap) - gap
        yc = ytop - hgt / 2
        box(ax, x0, yc - 2.6, 9.6, 5.2, f'{name}\n定性层', fc=FILL, ec=BLUE, fs=8.6)
        for i, (lay, nm, T) in enumerate(ts):
            y = ytop - i * (bh + gap) - bh
            fc, ec = lc(lay)
            box(ax, x0 + 12.4, y, tw, bh, f'{lay}｜{nm}　{T}', fc=fc, ec=ec, fs=7.0, ha='left', r=.5)
            ax.plot([x0 + 9.6, x0 + 12.4], [yc, y + bh / 2], color=GRAY, lw=.6, zorder=0)
        return hgt
    top = H - 2.4
    draw('武官星', .8, top)
    y = top
    for name in ('佐才', '文官带', '财星'):
        hgt = draw(name, 33.6, y, tw=19.4)
        y -= hgt + 2.6
    assert y > 0, '右栏放不下'
    save(fig, out, '图07_枢纽判断.png')
    return {h: [list(x) for x in v] for h, v in hubs.items()}


# ---------------- 图8 引擎怎样往后推 ----------------
def fig_algorithm(out):
    H = 31.0
    fig, ax = dcanvas(H / 10)
    box(ax, 1.0, 22.4, 18.0, 7.0, '盘面\n这一宫的星、亮度、四化，\n三方四正、身宫、性别', fc='white', ec=GRID, fs=8.2)
    box(ax, 23.4, 22.4, 19.6, 7.0, '第一步：定性步\n条件在这一宫都成立\n→ 得出判断（深度 1）', fc=FILL, ec=BLUE, fs=8.2)
    box(ax, 47.4, 22.4, 17.6, 7.0, '第二步起：推理步\n前提都已得出、附加条件成立\n→ 得出后一个判断', fc=FILL5, ec=TEAL, fs=7.8)
    arrow(ax, 19.0, 25.9, 23.4, 25.9); arrow(ax, 43.0, 25.9, 47.4, 25.9)
    ax.annotate('', xy=(60.6, 29.4), xytext=(52.0, 29.4), arrowprops=dict(arrowstyle='-|>', color=TEAL, lw=1.0, mutation_scale=9, connectionstyle='arc3,rad=-0.9'))
    note(ax, 50.8, 31.4, '再来一轮，直到推不出新判断（最多 8 轮）', fs=7.2, ha='right', color=TEAL)
    box(ax, 23.4, 11.6, 41.6, 7.4, '输出：这一宫的全部判断\n每个判断记下全部推法，成稿显示最短的一条（深度＝前提里最深的＋1）；\n同一层里有吉有凶，标「两说」，都列出，不投票', fc=FILL3, ec=AMBER, fs=8.0)
    arrow(ax, 56.2, 22.4, 56.2, 19.0)
    box(ax, 1.0, 1.0, 64.0, 8.6, '一步用在哪一宫\n写某宫的只用在那一宫；写身宫的用在身宫所在之宫；写任一宫的：人宫（命、兄弟、夫妻、子女、\n仆役、父母）都用，事宫只在结论合宫性时用（路线、成败 → 官禄；路线、意外 → 迁移；财 → 财帛……）。\n条件求值、空宫借对宫、五种修正都沿用第一版', fc=FILL2, ec=GRAY, fs=7.6, ha='left')
    box(ax, 1.0, 11.6, 18.0, 7.4, '十二宫各推一遍\n命宫在前；有几张候选盘\n时，只留都推出的判断', fc='white', ec=GRID, fs=8.0)
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
    """同第六稿图10（示例盘），只改中心说明文字。"""
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
        ax.text(x + cw - 1, y + chh - 1, STEMS[p['stem']] + BR[b], fontsize=8, color=MUTED, va='top', ha='right')
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
            ax.text(x + 1, y + chh - 9.6, '　'.join(aux[:3]) + ('\n' + '　'.join(aux[3:6]) if len(aux) > 3 else ''), fontsize=7.6, color=MUTED, va='top', linespacing=1.4)
    li = c['lunarInfo']
    center = (f"开发用随机盘 r30（不对应真人）\n女命　{li['fourPillars'][0]}年生　{c['wuxingJuName']}\n命宫在{BR[ming]}（空宫，借对宫{BR[(ming + 6) % 12]}：武曲、贪狼）\n身宫在{BR[shen]}（{pal[shen]['name']}）\n"
              f"绿框＝命宫的三方四正\n星名后的字表示亮度与四化")
    chart_grid(ax, 0, 0, cw, chh, label, style, center=center)
    save(fig, out, '图09_示例盘.png')
    return {'命宫': BR[ming], '身宫': BR[shen]}


# ---------------- 图10 示例盘命宫的推理链 ----------------
def fig_r30_chain(out, ex):
    """r30 命宫「主线」（main_chains）上的结点，连同它们最短推法里的全部前提；按深度分栏。
    每个框写：判断名；层｜得出它的那一步的 T 编号（该步要求女命的注「女命」）。排列次序只为少交叉，数据不动。"""
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
    H = nmax * (bh + gap) + 5.0
    fig, ax = dcanvas(H / 10)
    colw = 66.0 / (maxd + 1)
    w = colw - 3.0
    pos = {}
    for d, items in cols.items():
        tot = len(items) * (bh + gap) - gap
        y_top = (H - 3.4) / 2 + tot / 2
        for i, it in enumerate(items):
            x = d * colw + (colw - w) / 2
            y = y_top - i * (bh + gap) - bh
            if it[0] == 'c':
                txt = '三方四正有\n天府、天相' if it[1].startswith('三方') else it[1].replace('（借对宫）', '\n（借对宫）')
                box(ax, x, y, w, bh, txt, fc='white', ec=GRID, fs=7.4)
            else:
                v, x0 = nodes[it[1]], first[it[1]]
                fem = '性别:女' in (x0['附加条件'] or []) + (x0['条件'] or [])
                fc, ec = lc(v['层'])
                box(ax, x, y, w, bh, f"{v['名']}\n{v['层']}｜{x0['T']}" + ('·女命' if fem else ''), fc=fc, ec=ec, fs=7.8)
            pos[it] = (x, y)
    def edge(a, b):
        (xa, ya), (xb, yb) = pos[a], pos[b]
        arrow(ax, xa + w, ya + bh / 2, xb, yb + bh / 2, color=GRAY, lw=.8)
    for n in keep:
        x = first[n]
        if depth[n] == 1:
            edge(('c', cond_label(x)), ('n', n))
        else:
            for p in x['premises']:
                edge(('n', p), ('n', n))
    for d in range(maxd + 1):
        note(ax, d * colw + colw / 2, H - 1.4, '盘面' if d == 0 else f'深度 {d}', fs=8.2, ha='center', color=INK2)
    save(fig, out, '图10_示例盘的推理链.png')
    return {'结点': sorted(nodes[n]['名'] for n in keep), '最大深度': maxd, '盘面条件': conds}


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
    pick = ['T97', 'T176', 'T923', 'T934', 'T928', 'T213']
    pick = [t for t in pick if t in items][:6]
    left = [f"{items[t][0]}：{items[t][1]}（{t}）" for t in pick]
    nodes = ex['第四版·命宫结点']
    name2id = {v['名']: n for n, v in nodes.items()}
    def chain_line(path):
        names = path[1:]
        s = path[0].replace('本宫有:', '命宫有').replace('本宫化:', '命宫化').replace('三方四正有:', '三方四正有').replace(',', '、')
        parts = [s]
        for nm in names:
            x = nodes[name2id[nm]]['推法'][0]
            parts.append(f"→〔{x['T']}〕{nm}")
        return ''.join(parts)
    lines = [chain_line(p) for p in ex['第四版·命宫主线'][:5]]
    b1 = '第三版：命宫里各条规则各自命中，彼此之间没有推导关系（节选）\n' + '\n'.join('· ' + x for x in left)
    b2 = '第四版：后一个判断由前一个判断推出，〔 〕里是出处（命宫主线，节选）\n' + '\n'.join('· ' + x for x in lines)
    h1 = text_size(b1, 7.8)[1] + 2.0
    h2 = text_size(b2, 7.8)[1] + 2.0
    H = h1 + h2 + 3.2
    fig, ax = dcanvas(H / 10)
    box(ax, 1.0, H - 1.0 - h1, 64.0, h1, b1, fc=FILL2, ec=GRAY, fs=7.8, ha='left')
    box(ax, 1.0, 1.0, 64.0, h2, b2, fc=FILL5, ec=TEAL, fs=7.8, ha='left')
    save(fig, out, '图11_第三版与第四版.png')
    return {'第三版': left, '第四版': lines}


# ---------------- 图12 覆盖 ----------------
def fig_coverage(out, cov, kb_path, holdout_path, ex):
    nodes, steps = C.load_kb(kb_path)
    rows = [r for r in jl(holdout_path)['rows'] if 'error' not in r]
    depths, nr, reach = [], [], collections.Counter()
    for r in rows:
        ch = ENG.Chart(r)
        dp = C.infer(ch, nodes, steps)['命宫']
        depths.append(max((xs[0]['depth'] for xs in dp.values()), default=0))
        nr.append(len({x['step'] for xs in dp.values() for x in xs if x['premises']}))
        for lay in {nodes[n]['层'] for n, xs in dp.items() if any(x['premises'] for x in xs)}:
            reach[lay] += 1
    m = cov['命宫']
    assert statistics.median(depths) == m['最长链步数']['中位数'] and max(depths) == m['最长链步数']['最大']
    assert statistics.median(nr) == m['用上的推理步条数']['中位数'] and max(nr) == m['用上的推理步条数']['最大']
    assert {k: reach[k] for k in reach} == m['推理步走到各层的盘数'], '与覆盖检验结果不一致'
    n = cov['charts']
    fig, axs = plt.subplots(1, 2, figsize=(W, 3.1), dpi=220, gridspec_kw={'width_ratios': [1.15, 1]})
    ax = axs[0]
    vals = [reach[l] / n for l in MAIN6]
    ax.bar(range(6), vals, color=[lc(l)[1] for l in MAIN6], width=.62)
    for i, v in enumerate(vals):
        ax.text(i, v + .02, f'{v:.0%}' if v >= .1 else f'{v:.1%}', ha='center', fontsize=7.8, color=INK)
    ax.set_xticks(range(6)); ax.set_xticklabels(MAIN6, fontsize=8.2)
    ax.set_ylim(0, 1.1); ax.set_yticks([0, .5, 1]); ax.set_yticklabels(['0', '50%', '100%'], fontsize=7.6, color=MUTED)
    ax.set_title('命宫里经推理步推到这一层的盘', loc='left', fontsize=9.2)
    ax2 = axs[1]
    cnt = collections.Counter(depths)
    ks = list(range(1, max(depths) + 1))
    ax2.bar(ks, [cnt[k] / n for k in ks], color=BLUE, width=.62)
    for k in ks:
        ax2.text(k, cnt[k] / n + .015, f'{cnt[k] / n:.0%}' if cnt[k] / n >= .01 else f'{cnt[k] / n:.1%}', ha='center', fontsize=7.8, color=INK)
    r30 = ex['第四版·命宫覆盖口径']['最长链步数']
    ax2.annotate('示例盘 r30', xy=(r30, cnt[r30] / n + .07), xytext=(r30 + .2, cnt[r30] / n + .2), fontsize=7.6, color=RED,
                 arrowprops=dict(arrowstyle='-|>', color=RED, lw=.8, mutation_scale=7))
    ax2.set_xticks(ks); ax2.set_xlabel('命宫最长一条链的步数', fontsize=8.2)
    ax2.set_ylim(0, max(cnt.values()) / n + .3); ax2.set_yticks([0, .25, .5]); ax2.set_yticklabels(['0', '25%', '50%'], fontsize=7.6, color=MUTED)
    ax2.set_title('最长一条链有几步', loc='left', fontsize=9.2)
    for a in axs:
        for s in ('top', 'right'): a.spines[s].set_visible(False)
        a.grid(axis='y', color=GRID, lw=.6); a.set_axisbelow(True)
    fig.tight_layout()
    save(fig, out, '图12_覆盖.png')
    return {'各层盘数': {l: reach[l] for l in MAIN6}, '盘数': n, '最长链分布': {k: cnt[k] for k in ks}, 'r30最长链': r30,
            '推理步条数分位': m['用上的推理步条数'], 'r30推理步条数': ex['第四版·命宫覆盖口径']['用上的推理步条数']}


# ---------------- 图13 主检验的设计 ----------------
def fig_test_design(out):
    H = 33.0
    fig, ax = dcanvas(H / 10)
    box(ax, 15.0, 26.0, 36.0, 6.0, '倪海厦讲这位命主的时段\n（分 P 与起止时间，前后各加 2 分钟）', fc='white', ec=GRID, fs=8.2)
    box(ax, 1.0, 15.4, 30.4, 8.2, '倪师判断集 G\n时段内、命例特指、先天、宫为命宫或身宫的\n步，它们的结论（归一后的结点）', fc=FILL6, ec=RED, fs=7.8)
    box(ax, 34.6, 15.4, 30.4, 8.2, '剔除时段内的全部步\n（不论是否命例特指）\n引擎只用其余的步推', fc=FILL, ec=BLUE, fs=7.8)
    arrow(ax, 25.0, 26.0, 16.2, 23.6); arrow(ax, 41.0, 26.0, 49.8, 23.6)
    box(ax, 34.6, 5.2, 14.6, 7.8, '本人盘 X\n命宫（加身宫）推出\n的结点 N(X)', fc='white', ec=GRID, fs=7.6)
    box(ax, 50.4, 5.2, 14.6, 7.8, '600 张留出随机盘\n每张同样推\nN(H)', fc='white', ec=GRID, fs=7.6)
    arrow(ax, 45.0, 15.4, 41.9, 13.0); arrow(ax, 55.0, 15.4, 57.7, 13.0)
    box(ax, 1.0, 1.0, 30.4, 12.0, '得分与排位\ns(X)＝|G ∩ N(X)| ÷ |G|\nu＝（得分高于本人盘的张数＋0.5×相等的张数）÷ 600\n0 最好；0.5＝和随机盘一样\n平均 u；p：随机抽一张当本人盘，重复 1 万次', fc=FILL3, ec=AMBER, fs=7.4, ha='left')
    arrow(ax, 34.6, 9.1, 31.4, 7.6); arrow(ax, 16.2, 15.4, 16.2, 13.0)
    save(fig, out, '图13_主检验设计.png')


# ---------------- 图14 主检验结果 ----------------
def fig_test_result(out, rep, diag):
    reach0 = {r['person_id'] for r in diag['各人'] if r['实际可达'] == 0}
    ps = [p for p in rep['各人'] if p['计入']]
    ps.sort(key=lambda p: (p['u'], p['person_id']))
    fig, ax = plt.subplots(figsize=(W, 5.2), dpi=220)
    for i, p in enumerate(ps):
        y = len(ps) - 1 - i
        col = GRAY if p['person_id'] in reach0 else BLUE
        ax.plot([p['只用定性步·u']], [y], 'o', ms=7.5, mfc='none', mec=MUTED, mew=1.0, zorder=2)
        ax.plot([p['u']], [y], 'o', ms=6.2, color=col, zorder=3)
    ax.axvline(.5, color=RED, lw=1.0, ls=(0, (3, 3)))
    mu = rep['主检验']['平均u']; pv = rep['主检验']['p_单侧']
    ax.axvline(mu, color=BLUE, lw=1.0)
    ax.text(.505, len(ps) - .2, '0.5＝和随机盘一样', color=RED, fontsize=7.8, va='bottom')
    ax.text(.985, len(ps) - 2.2, f'平均 u＝{mu:.3f}（蓝竖线）\np＝{pv:.3f}：未通过\n（事先定 p＜0.05 才算通过）', color=BLUE, fontsize=8.4, ha='right', va='top', linespacing=1.5)
    ax.set_yticks(range(len(ps))); ax.set_yticklabels([p['person_id'] for p in reversed(ps)], fontsize=7.4)
    ax.set_xlim(0, 1); ax.set_ylim(-.8, len(ps) + .6)
    ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(['0\n比所有随机盘都好', '0.25', '0.5', '0.75', '1\n比所有随机盘都差'], fontsize=7.4, color=MUTED)
    for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', color=GRID, lw=.6); ax.set_axisbelow(True)
    ax.legend(handles=[plt.Line2D([], [], marker='o', ls='', color=BLUE, ms=6, label='全部步'),
                       plt.Line2D([], [], marker='o', ls='', mfc='none', mec=MUTED, ms=7, label='只用定性步'),
                       plt.Line2D([], [], marker='o', ls='', color=GRAY, ms=6, label='剔除后一个判断也推不出（事后诊断）')],
              loc='upper left', bbox_to_anchor=(0, -.1), ncol=3, fontsize=7.6)
    ax.set_title(f"主检验：{rep['人数']['计入']} 位命主的本人盘在 600 张随机盘里排第几（u）", loc='left')
    fig.tight_layout()
    save(fig, out, '图14_主检验结果.png')
    return {'计入': rep['人数']['计入'], '平均u': mu, 'p': pv, '只用定性步平均u': rep['另报·只用定性步']['平均u'],
            '只用定性步p': rep['另报·只用定性步']['p_单侧'], 'u小于0.5': rep['主检验']['u小于0.5的人数'], '推不出的人': sorted(reach0)}


# ---------------- 图15 事后诊断 ----------------
def fig_diag(out, diag):
    d1, d3, d4 = diag['D1可达性'], diag['D3不剔除'], diag['D4构成']['步']
    tot = d1['倪师判断集结点合计']
    reach, struct = d1['实际可达的结点'], d1['结构上可达的结点']
    ok_steps = d4.get('定性步·可操作·无格无其他', 0) + d4.get('推理步·可操作·无格无其他', 0)
    ge = sum(v for k, v in d4.items() if '含格' in k)
    other = sum(v for k, v in d4.items() if '含其他' in k)
    nst = sum(d4.values())
    rows = [(f'倪师判断集 {tot} 个结点\n（剔除此人时段内的步之后）', [('随机盘上推出过', reach, BLUE), ('有步可推，但\n600 张盘都没推出', struct - reach, LBLUE), ('没有任何步能推出', tot - struct, GRAY)]),
            (f'倪师判断集的 {nst} 步', [('条件都能求值', ok_steps, TEAL), ('含「格」', ge, AMBER), ('原话没说出盘面', other, GRAY)])]
    fig, axs = plt.subplots(1, 2, figsize=(W, 2.9), dpi=220, gridspec_kw={'width_ratios': [2.3, 1]})
    ax = axs[0]
    for k, (name, segs) in enumerate(rows):
        y = len(rows) - 1 - k
        s = sum(v for _, v, _ in segs); x = 0
        for lab, v, col in segs:
            ax.barh(y, v / s, left=x, color=col, height=.56, edgecolor=SURFACE, lw=1.5)
            if v / s > .14:
                ax.text(x + v / s / 2, y, f'{lab}\n{v}', ha='center', va='center', fontsize=7.2, color='white' if col in (BLUE, TEAL) else INK, linespacing=1.2)
            else:   # 窄段的标注放到条形下面
                ax.text(x + v / s / 2, y - .32, f"{lab.replace(chr(10), ' ')} {v}", ha='center', va='top', fontsize=6.8, color=INK2)
            x += v / s
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=7.8)
    ax.set_xlim(0, 1); ax.set_xticks([])
    for s_ in ('top', 'right', 'left', 'bottom'): ax.spines[s_].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.set_title('判断集里的结点与步', loc='left', fontsize=9.2)
    ax2 = axs[1]
    v = [d3['本人盘得分平均'], d3['留出盘得分平均']]
    ax2.bar([0, 1], v, color=[BLUE, GRAY], width=.58)
    for i, x in enumerate(v):
        ax2.text(i, x + .01, f'{x:.1%}', ha='center', fontsize=7.8)
    ax2.set_xticks([0, 1]); ax2.set_xticklabels(['本人盘', '随机盘'], fontsize=8)
    ax2.set_ylim(0, .4); ax2.set_yticks([0, .2, .4]); ax2.set_yticklabels(['0', '20%', '40%'], fontsize=7.4, color=MUTED)
    ax2.set_title('不剔除时推出的比例', loc='left', fontsize=9.2)
    for s_ in ('top', 'right'): ax2.spines[s_].set_visible(False)
    fig.text(.01, -.02, '事后诊断，只作描述，不改主检验「未通过」的结论。右图不剔除此人时段内的步，命例步本来就是照这张盘说的，只用来看管道通不通。',
             fontsize=7.2, color=MUTED, ha='left')
    fig.tight_layout()
    save(fig, out, '图15_事后诊断.png')
    return {'结点': tot, '实际可达': reach, '结构上可达': struct, '步': nst, '可求值': ok_steps, '含格': ge, '没说出盘面': other,
            '不剔除·本人盘': d3['本人盘得分平均'], '不剔除·随机盘': d3['留出盘得分平均'], '不剔除·平均u': d3['平均u']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out)
    M = os.path.join(CH, 'chain_merged_v1'); RS = os.path.join(CH, 'chain_results_v1')
    adj, chk, norm = jl(M, 'adjudicated_v1.json'), jl(M, 'check_v1.json'), jl(M, 'normalized_v1.json')
    labels_all = jl(CH, 'chain_norm_packets_v1', 'labels_all.json')
    kb = jl(CH, 'chain_kb_v1.json')
    cov, rep, diag, ex = jl(RS, 'coverage_v1.json'), jl(RS, 'reproduce_v1.json'), jl(RS, 'reproduce_diag_v1.json'), jl(RS, 'example_r30_v1.json')
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
    rec['图10'] = fig_r30_chain(a.out, ex)
    rec['图11'] = fig_v3_v4(a.out, ex)
    rec['图12'] = fig_coverage(a.out, cov, os.path.join(CH, 'chain_kb_v1.json'), os.path.join(CH, 'v4_holdout_v1', 'holdout_charts.json'), ex)
    fig_test_design(a.out)
    rec['图14'] = fig_test_result(a.out, rep, diag)
    rec['图15'] = fig_diag(a.out, diag)
    open(os.path.join(a.out, '图中数字_chain_v1.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'out': sorted(os.listdir(a.out))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
