"""倪师断法引擎第四版：推理链（依据《00_推理链方案_v1.md》六）。
第一至三版（21_倪师断法引擎_20261005/ni_engine_v1.py、v2、v3）都已定版，本文件只调用、不修改它们。
输入：推理链知识库（归一之后编译成的 chain_kb，结构见 load_kb）与命盘（chart_runner_v1.cjs 的输出行）。
做法（只做先天）：
1. 读盘与盘面条件求值沿用第一版：E.eval_rule（全部条件为真才成立；「格」「其他」无法求值，不成立）、空宫借对宫（E.try_rule 同样做法）、
   五个算子（E.operators，只用于定性步，只改方向与强度并加注，不删判断）。
2. 一步用在哪些宫：步的「宫」写某宫的只在那一宫；写「身宫」的在身宫所在之宫；写「任一宫」的按第一版任一宫的用法——
   人宫（命宫 兄弟 夫妻 子女 仆役 父母）都用；事宫只在结论的层与该宫宫性相符时用（路线→官禄、迁移；成败→官禄；财→财帛；
   祖业田宅→田宅；健康→疾厄；意外→迁移；福德→福德）。
3. 先用定性步：条件成立，就在该宫得出结论结点。再反复用推理步：前提结点在该宫都已得出、附加条件也成立，就得出结论结点；
   直到没有新的推导为止，最多 8 轮。
4. 每个结点记下全部推法（每条推法：哪一步、前提结点或盘面条件、推导途径、算子注记），按「深度」取最短的一条显示：
   定性步得出的深度为 1；推理步得出的深度为 1 ＋ 前提里最深的那个。
5. 同一宫、同一层里方向相反（一吉一凶）的结点，标「两说」，都列出，不取舍。
6. 并列候选（出生时辰不定等）：每张候选盘各推一次，只保留各候选在同一宫都推出来的结点。
用法：作为模块调用 load_kb / infer / infer_candidates / render_chain。"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, E_DIR)
import ni_engine_v1 as E

PALACES = E.PALACES
PERSON = E.PERSON
MAIN = ['定性', '长相', '个性', '行为', '路线', '成败']
OTHER = ['财', '婚姻', '子女', '父母', '兄弟', '朋友合伙', '健康', '祖业田宅', '福德', '官非', '意外', '寿元', '其他']
LAYER_ORDER = MAIN + OTHER
THEME = {'财帛': {'财'}, '官禄': {'路线', '成败'}, '田宅': {'祖业田宅'}, '疾厄': {'健康'}, '迁移': {'路线', '意外'}, '福德': {'福德'}}
MAX_ROUNDS = 8


def load_kb(path):
    """chain_kb：{'nodes': {结点号: {'层','名'}}, 'steps': [{'step_id','T','分P','时间','类型','宫','适用','parsed_conditions','parsed_extra',
    'premises': [结点号], 'conclusions': [结点号], '方向','强度','连接','原话摘录','命例特指','可操作', …}]}。只取可操作、适用先天的步。"""
    kb = json.load(open(path, encoding='utf-8'))
    steps = [s for s in kb['steps'] if s.get('可操作') and s.get('适用') == '先天']
    ids = [s['step_id'] for s in steps]
    assert len(ids) == len(set(ids)), '步编号重复'
    for s in steps:
        assert s['类型'] in ('定性步', '推理步') and s['conclusions'], s['step_id']
        assert (s['类型'] == '推理步') == bool(s['premises']), s['step_id']
        assert all(n in kb['nodes'] for n in s['premises'] + s['conclusions']), s['step_id']
    return kb['nodes'], steps


def applies(step, name, chart, nodes):
    """这一步能不能用在 name 这一宫，能用时返回推导途径。"""
    g = step['宫']
    if g == name:
        return '本宫'
    if g == '身宫' and chart.shen == name:
        return '身宫'
    if g == '任一宫':
        if name in PERSON:
            return '任一宫通义'
        if any(nodes[n]['层'] in THEME.get(name, set()) for n in step['conclusions']):
            return '任一宫通义'
    return None


def cond_ok(chart, conds, b):
    """全部条件在宫 b 成立（沿用 E.eval_rule；不成立且本宫空宫时借对宫主星再求一次）。返回 (成立, 是否借对宫)。"""
    if not conds:
        return True, False
    pseudo = {'parsed_conditions': conds, '适用': '先天'}
    ok, _ = E.eval_rule(chart, pseudo, b)
    if ok:
        return True, False
    borrowed = chart.majors_in(b + 6) if not chart.majors_in(b) else None
    if borrowed:
        ok, _ = E.eval_rule(chart, pseudo, b, borrowed=borrowed)
        if ok:
            return True, True
    return False, False


def prepare(chart, nodes, steps):
    """盘面一段：每一步在每一宫能不能用、盘面条件成不成立（定性步看条件，推理步看附加条件），只与盘有关，每张盘算一次。
    返回 {'q': {步号: {宫名: (途径, 方向, 强度, 算子注记)}}, 'r': {步号: {宫名: 途径}}}。"""
    q, r = {}, {}
    for s in steps:
        for name in PALACES:
            via = applies(s, name, chart, nodes)
            if not via:
                continue
            b = chart.by_name[name]['branch']
            if s['类型'] == '定性步':
                ok, borrowed = cond_ok(chart, s['parsed_conditions'], b)
                if ok:
                    pol, stg, notes = E.operators(chart, {'结论': {'方向': s['方向'], '强度': s['强度']}, 'parsed_conditions': s['parsed_conditions']}, b)
                    q.setdefault(s['step_id'], {})[name] = (via + ('（空宫借对宫）' if borrowed else ''), pol, stg, notes)
            else:
                ok, borrowed = cond_ok(chart, s['parsed_extra'], b)
                if ok:
                    r.setdefault(s['step_id'], {})[name] = via + ('（空宫借对宫）' if borrowed else '')
    return {'q': q, 'r': r}


def infer(chart, nodes, steps, prep=None, allowed=None):
    """对一张盘推理。返回 {宫名: {结点号: [推法…]}}，推法按深度从浅到深排列。
    prep：prepare() 的结果（不给就现算）；allowed：只用这些步号（不给就全用；逐例留一时用）。"""
    prep = prep if prep is not None else prepare(chart, nodes, steps)
    use = [s for s in steps if allowed is None or s['step_id'] in allowed]
    der = {name: collections.defaultdict(list) for name in PALACES}
    depth = {name: {} for name in PALACES}
    for s in use:
        if s['类型'] != '定性步':
            continue
        for name, (via, pol, stg, notes) in prep['q'].get(s['step_id'], {}).items():
            for n in s['conclusions']:
                der[name][n].append({'step': s['step_id'], 'premises': [], 'via': via, 'depth': 1, '方向': pol, '强度': stg, 'notes': list(notes)})
                depth[name][n] = 1
    rs = [s for s in use if s['类型'] == '推理步' and s['step_id'] in prep['r']]
    for rnd in range(MAX_ROUNDS):
        new = 0
        for s in rs:
            for name, via in prep['r'][s['step_id']].items():
                if not all(p in depth[name] for p in s['premises']):
                    continue
                d = 1 + max(depth[name][p] for p in s['premises'])
                for n in s['conclusions']:
                    if any(x['step'] == s['step_id'] for x in der[name][n]):
                        continue
                    der[name][n].append({'step': s['step_id'], 'premises': list(s['premises']), 'via': via,
                                         'depth': d, '方向': s['方向'], '强度': s['强度'], 'notes': []})
                    if n not in depth[name] or d < depth[name][n]:
                        depth[name][n] = d
                    new += 1
        if not new:
            break
    # 深度可能在后面几轮被更短的推法改小：按最终深度重算每条推法的深度后排序
    for name in PALACES:
        for _ in range(MAX_ROUNDS):
            changed = False
            for n, xs in der[name].items():
                for x in xs:
                    if x['premises']:
                        d = 1 + max(depth[name][p] for p in x['premises'])
                        if d != x['depth']:
                            x['depth'] = d; changed = True
                m = min(x['depth'] for x in xs)
                if m != depth[name][n]:
                    depth[name][n] = m; changed = True
            if not changed:
                break
        for xs in der[name].values():
            xs.sort(key=lambda x: (x['depth'], x['step']))
    return {name: dict(v) for name, v in der.items()}


def infer_candidates(rows, nodes, steps, preps=None, allowed=None):
    """并列候选：各候选在同一宫都推出来的结点才保留（推法取第一张候选的）。preps：各候选的 prepare() 结果，可不给。"""
    preps = preps or [None] * len(rows)
    res = [infer(E.Chart(r), nodes, steps, prep=p, allowed=allowed) for r, p in zip(rows, preps)]
    if len(res) == 1:
        return res[0]
    out = {}
    for name in PALACES:
        common = set.intersection(*(set(r[name]) for r in res))
        out[name] = {n: res[0][name][n] for n in res[0][name] if n in common}
    return out


def tree_steps(der_pal, n, seen=None):
    """结点 n 的最短推法用到的全部步（递归展开前提，各取最短推法）。"""
    seen = set() if seen is None else seen
    if n in seen:
        return []
    seen.add(n)
    x = der_pal[n][0]
    out = [x['step']]
    for p in x['premises']:
        out += tree_steps(der_pal, p, seen)
    return out


def two_sayings(der_pal, nodes):
    """同一层里有吉有凶的层：{层: ([吉结点], [凶结点])}。"""
    out = {}
    by = collections.defaultdict(lambda: ([], []))
    for n, xs in der_pal.items():
        pol = xs[0]['方向']
        if pol in ('吉', '凶'):
            by[nodes[n]['层']][0 if pol == '吉' else 1].append(n)
    for lay, (g, x) in by.items():
        if g and x:
            out[lay] = (sorted(g), sorted(x))
    return out


def stats(der, nodes, steps_by_id, palace='命宫'):
    """一宫的描述统计：结点数、经推理步得出的结点数、各层是否推到、最深的推法深度、最短推法里推理步最多的条数、两说处数。"""
    dp = der.get(palace, {})
    via_r = [n for n, xs in dp.items() if xs[0]['premises']]
    n_r = {n: sum(1 for st in tree_steps(dp, n) if steps_by_id[st]['类型'] == '推理步') for n in dp}
    layers = {nodes[n]['层'] for n in dp}
    layers_r = {nodes[n]['层'] for n in via_r}
    return {'结点': len(dp), '经推理步得出的结点': len(via_r), '最大深度': max((xs[0]['depth'] for xs in dp.values()), default=0),
            '单个结点最短推法里的推理步数最多': max(n_r.values(), default=0), '推理步总数（各结点最短推法去重）': len({st for n in dp for st in tree_steps(dp, n) if steps_by_id[st]['类型'] == '推理步'}),
            '推到的层': sorted(layers, key=LAYER_ORDER.index), '经推理步推到的层': sorted(layers_r, key=LAYER_ORDER.index),
            '两说': len(two_sayings(dp, nodes))}


def cond_text(conds):
    return '、'.join(conds) if conds else ''


def chain_path(dp, nodes, steps_by_id, n):
    """从盘面到结点 n 的一条主线：每次沿最短推法里最深的那个前提往回走，直到定性步。返回 [起步条件文字, 结点名…]。"""
    seq = [n]
    while dp[seq[-1]][0]['premises']:
        x = dp[seq[-1]][0]
        seq.append(max(x['premises'], key=lambda p: (dp[p][0]['depth'], p)))
    st = steps_by_id[dp[seq[-1]][0]['step']]
    return [cond_text(st.get('条件') or [])] + [nodes[m]['名'] for m in reversed(seq)]


def main_chains(dp, nodes, steps_by_id, k=5):
    """命宫里最长的几条主线（终点是没有再被当作前提用到的结点；按深度从深到浅，同深度按结点名）。"""
    used = {p for xs in dp.values() for p in xs[0]['premises']}
    ends = sorted((n for n in dp if n not in used and dp[n][0]['premises']), key=lambda n: (-dp[n][0]['depth'], nodes[n]['名']))
    return [chain_path(dp, nodes, steps_by_id, n) for n in ends[:k]]


def render_chain(der, nodes, steps_by_id, chart=None, cite=True, quote_len=40):
    """「推理链」一节的中文成稿：命宫一条主链在前，身宫与财帛、官禄、迁移随后，再其余各宫。"""
    L = ['推理链（照倪海厦看盘的顺序：命宫 → 定性 → 长相、个性 → 行为 → 路线 → 成败；后一个判断由前一个判断推出，每步注明原话出处）']
    order = ['命宫'] + ([chart.shen] if chart is not None and chart.shen != '命宫' else []) + ['财帛', '官禄', '迁移']
    order += [p for p in PALACES if p not in order]
    for k, name in enumerate(order, 1):
        dp = der.get(name, {})
        if not dp:
            continue
        head = f'{name}' + ('（身宫在此）' if chart is not None and chart.shen == name and name != '命宫' else '')
        L.append(f'{k}、{head}')
        if name == '命宫':
            for path in main_chains(dp, nodes, steps_by_id):
                L.append('  主线：' + ' → '.join([f'盘面「{path[0]}」'] + path[1:]))
        two = two_sayings(dp, nodes)
        for lay in LAYER_ORDER:
            ns = sorted((n for n in dp if nodes[n]['层'] == lay), key=lambda n: (dp[n][0]['depth'], nodes[n]['名']))
            for n in ns:
                x = dp[n][0]
                st = steps_by_id[x['step']]
                q = re.sub(r'\s+', '', st['原话摘录'])
                q = q if len(q) <= quote_len else q[:quote_len] + '……'
                src = f"〔{st['T']}「{q}」〕" if cite else ''
                if x['premises']:
                    pre = '＋'.join(nodes[p]['名'] for p in x['premises'])
                    extra = cond_text(st.get('附加条件') or [])
                    frm = f'由「{pre}」' + (f'，且{extra}' if extra else '') + f'推出{src}'
                else:
                    frm = f"由盘面「{cond_text(st.get('条件') or [])}」得出{src}" + ('（空宫借对宫）' if '借' in x['via'] else '')
                more = f'（另有 {len(dp[n]) - 1} 种推法）' if len(dp[n]) > 1 else ''
                notes = ''.join(f'〔{t}〕' for t in x['notes'])
                tag = '〔两说〕' if lay in two and n in two[lay][0] + two[lay][1] else ''
                L.append(f"  {lay}：{nodes[n]['名']} ← {frm}{notes}{more}{tag}")
    return '\n'.join(L)
