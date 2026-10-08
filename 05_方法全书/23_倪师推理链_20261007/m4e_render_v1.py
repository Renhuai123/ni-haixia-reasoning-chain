"""M4e 认本人检验：三组论断的成稿（依据《00h_三项补充研究方案_v2.md》甲、三「论断里给审者看什么」）。只做呈现，不改推理。
- 链组 render_chain_m4e：第四版推理结果，每个判断写「由盘面得出」或「由『前提』推出」；命宫另列最长的几条主线。
- 平铺组 render_flat_m4e：同一份推理结果，每宫每层把判断平铺列出，不写由什么推出。
- 第三版先天组 v3_natal：第三版成稿（cite=False）只取「一、命宫」「二、身宫」「三、三方四正」「五、六亲与诸宫」四节，
  「五、」改编为「四、」，删去写明「女命」「男命」的括注。
字段白名单（两个第四版组）：宫名、身宫标注、层名、判断名、前提判断名、「由盘面得出」、〔两说〕、主线（只链组）。
不写：盘面条件、附加条件、空宫借对宫、算子注记、另有几种推法、T 编号、原话摘录、命例标记、方向与强度。
涉及生死的判断（DEATH_LAYER 的层，或判断名合 DEATH_RE）一律不写原判断，改写成第三版同样的提醒句：
「要特别注意{对象}的健康与安全（原断涉及生死，按研究方案只作提醒）」，对象沿用第三版 ni_engine_v1.WHO；
作为前提出现时写「（涉生死，只作提醒）」。
用法：作为模块调用。"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, HERE); sys.path.insert(0, E_DIR)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E

DEATH_LAYER = '寿元'
DEATH_RE = re.compile(r'死|夭|致命|自杀|寿|活到|走了|就走|想走|过不了|不保|养不活|丧|亡|剋|克夫|克妻|刑克')
DEATH_MASK = '（涉生死，只作提醒）'
CHAIN_HEAD = '推理链（照倪海厦看盘的顺序：命宫 → 定性 → 长相、个性 → 行为 → 路线 → 成败；后一个判断由前一个判断推出）'
FLAT_HEAD = '先天论断（按宫、按层列出判断）'
V3_KEEP = ('一、', '二、', '三、', '五、')
V3_SECTION = re.compile(r'^[〇一二三四五六七八九]、')
GENDER_NOTE = re.compile(r'（[^（）]*(?:女命|男命)[^（）]*）')


def death_nodes(nodes):
    return sorted(n for n, v in nodes.items() if v['层'] == DEATH_LAYER or DEATH_RE.search(v['名']))


def reminder(palace):
    return f'要特别注意{E.WHO[palace]}的健康与安全（原断涉及生死，按研究方案只作提醒）'


def palace_order(shen):
    order = ['命宫'] + ([shen] if shen and shen != '命宫' else []) + ['财帛', '官禄', '迁移']
    order += [p for p in C.PALACES if p not in order]
    out = []
    for p in order:
        if p not in out:
            out.append(p)
    return out


def head(k, name, shen):
    if shen and name == shen:
        return f'{k}、{name}（身宫{"也" if name == "命宫" else ""}在此）'
    return f'{k}、{name}'


def _name(n, nodes, dead):
    return DEATH_MASK if n in dead else nodes[n]['名']


def _layer_lines(dp, nodes, dead, name, chain):
    two = C.two_sayings(dp, nodes)
    out = []
    for lay in C.LAYER_ORDER:
        ns = sorted((n for n in dp if nodes[n]['层'] == lay), key=lambda n: (dp[n][0]['depth'], nodes[n]['名']))
        if not ns:
            continue
        tags = set(two[lay][0] + two[lay][1]) if lay in two else set()
        live = [n for n in ns if n not in dead]
        items = []
        for n in live:
            tag = '〔两说〕' if n in tags else ''
            if chain:
                x = dp[n][0]
                frm = (f"由「{'＋'.join(_name(p, nodes, dead) for p in x['premises'])}」推出" if x['premises'] else '由盘面得出')
                items.append(f'  {lay}：{nodes[n]["名"]} ← {frm}{tag}')
            else:
                items.append(nodes[n]['名'] + tag)
        if chain:
            out += items
            if len(live) < len(ns):
                out.append(f'  {lay}：{reminder(name)}')
        else:
            if len(live) < len(ns):
                items.append(reminder(name))
            out.append(f'  {lay}：' + '；'.join(items))
    return out


def render_chain_m4e(der, nodes, steps_by_id, shen, dead):
    L = [CHAIN_HEAD]
    k = 0
    for name in palace_order(shen):
        dp = der.get(name, {})
        if not dp:
            continue
        k += 1
        L.append(head(k, name, shen))
        if name == '命宫':
            for path in C.main_chains(dp, nodes, steps_by_id):
                ids = _path_ids(dp, path, nodes)
                L.append('  主线：' + ' → '.join(['盘面'] + [_name(n, nodes, dead) for n in ids]))
        L += _layer_lines(dp, nodes, dead, name, chain=True)
    return '\n'.join(L) + '\n'


def _path_ids(dp, path, nodes):
    """C.main_chains 返回结点名；这里按同样的走法取回结点号（与 C.chain_path 相同的走法）。"""
    used = {p for xs in dp.values() for p in xs[0]['premises']}
    ends = sorted((n for n in dp if n not in used and dp[n][0]['premises']), key=lambda n: (-dp[n][0]['depth'], nodes[n]['名']))
    for n in ends:
        seq = [n]
        while dp[seq[-1]][0]['premises']:
            x = dp[seq[-1]][0]
            seq.append(max(x['premises'], key=lambda p: (dp[p][0]['depth'], p)))
        ids = list(reversed(seq))
        if [nodes[m]['名'] for m in ids] == path[1:]:
            return ids
    raise AssertionError('主线对不回结点')


def render_flat_m4e(der, nodes, shen, dead):
    L = [FLAT_HEAD]
    k = 0
    for name in palace_order(shen):
        dp = der.get(name, {})
        if not dp:
            continue
        k += 1
        L.append(head(k, name, shen))
        L += _layer_lines(dp, nodes, dead, name, chain=False)
    return '\n'.join(L) + '\n'


def v3_natal(text):
    keep, out = False, []
    for ln in text.split('\n'):
        if V3_SECTION.match(ln):
            keep = ln.startswith(V3_KEEP)
        if keep:
            ln = GENDER_NOTE.sub('', ln)
            out.append('四、' + ln[2:] if ln.startswith('五、') else ln)
    assert out and out[0].startswith('一、'), '第三版成稿里找不到「一、命宫」'
    return '\n'.join(out).rstrip('\n') + '\n'


def judgment_set_v4(der, dead):
    """区分度用：(宫, 结点) 的集合；涉生死的结点按 (宫, 层, 提醒) 计。"""
    out = set()
    for name, dp in der.items():
        for n in dp:
            out.add((name, n) if n not in dead else (name, 'DEATH'))
    return out
