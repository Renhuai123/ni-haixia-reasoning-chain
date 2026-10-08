"""推理链成稿 v2：只修 ni_chain_engine_v1.render_chain 的两个排版毛病（依据《00f_内审后更正与事后补充分析_v1.md》一、3）：
1. 身宫恰好落在财帛、官禄、迁移之一时，那一宫只写一遍；
2. 没有判断的宫不占序号，序号连续。
其余文字、次序、引文写法与 v1 完全相同。引擎文件 ni_chain_engine_v1.py 不改。
用法：from ni_chain_render_v2 import render_chain"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_chain_engine_v1 as C


def render_chain(der, nodes, steps_by_id, chart=None, cite=True, quote_len=40):
    L = ['推理链（照倪海厦看盘的顺序：命宫 → 定性 → 长相、个性 → 行为 → 路线 → 成败；后一个判断由前一个判断推出，每步注明原话出处）']
    order = ['命宫'] + ([chart.shen] if chart is not None and chart.shen != '命宫' else []) + ['财帛', '官禄', '迁移']
    order += [p for p in C.PALACES if p not in order]
    dedup = []
    for p in order:
        if p not in dedup:
            dedup.append(p)
    k = 0
    for name in dedup:
        dp = der.get(name, {})
        if not dp:
            continue
        k += 1
        head = f'{name}' + ('（身宫在此）' if chart is not None and chart.shen == name and name != '命宫' else '')
        L.append(f'{k}、{head}')
        if name == '命宫':
            for path in C.main_chains(dp, nodes, steps_by_id):
                L.append('  主线：' + ' → '.join([f'盘面「{path[0]}」'] + path[1:]))
        two = C.two_sayings(dp, nodes)
        for lay in C.LAYER_ORDER:
            ns = sorted((n for n in dp if nodes[n]['层'] == lay), key=lambda n: (dp[n][0]['depth'], nodes[n]['名']))
            for n in ns:
                x = dp[n][0]
                st = steps_by_id[x['step']]
                q = re.sub(r'\s+', '', st['原话摘录'])
                q = q if len(q) <= quote_len else q[:quote_len] + '……'
                src = f"〔{st['T']}「{q}」〕" if cite else ''
                if x['premises']:
                    pre = '＋'.join(nodes[p]['名'] for p in x['premises'])
                    extra = C.cond_text(st.get('附加条件') or [])
                    frm = f'由「{pre}」' + (f'，且{extra}' if extra else '') + f'推出{src}'
                else:
                    frm = f"由盘面「{C.cond_text(st.get('条件') or [])}」得出{src}" + ('（空宫借对宫）' if '借' in x['via'] else '')
                more = f'（另有 {len(dp[n]) - 1} 种推法）' if len(dp[n]) > 1 else ''
                notes = ''.join(f'〔{t}〕' for t in x['notes'])
                tag = '〔两说〕' if lay in two and n in two[lay][0] + two[lay][1] else ''
                L.append(f"  {lay}：{nodes[n]['名']} ← {frm}{notes}{more}{tag}")
    return '\n'.join(L)
