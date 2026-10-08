"""并列候选的闭合取交集 v1（依据《00l_三项深化方案》戊「候选盘」）。不改已登记的 ni_chain_engine_v1，只在它的逐盘推理结果上取交集。
ni_chain_engine_v1.infer_candidates 的做法：各候选在同一宫都推出来的结点才保留，推法取第一张候选的。
它的漏洞：保留的结点，第一张候选的推法可能用到一个没保留下来的前提（别的候选推不出它），成稿时「由『某某』推出」的某某在这一宫不出现，
画主线时还会因找不到前提而出错。前作 M4e 的 28 位本人与陪衬没有触发这一漏洞（本模块的 check 子命令可复核）；随机陪衬盘会触发。
闭合规则（「能接地」，最小不动点；回应方案独立审稿建9）：
1. 起点：保留集 = 各候选在同一宫都推出来的结点（同 infer_candidates）。
2. 每张候选各自从下往上重推一遍，只许用保留集里的结点：先收有定性步推法的结点，再反复收「有一条推法的前提全已收下」的结点，直到收不动；
   这张候选收下的结点叫它的接地集。新保留集 = 各候选接地集的交集。反复做 2，直到保留集不再变。
   这样，互相推出（A 由 B、B 由 A）而没有从盘面接地的结点不会留下。
3. 保留结点的推法：取第一张候选里前提全在保留集里的推法；深度在保留下来的推法上重算（定性步为 1，推理步为 1 + 前提深度的最大值），
   再按（深度，步号）排序。
用法：作为模块调用 infer_candidates_closed(rows, nodes, steps, allowed=None)；
      python3 cand_closure_v1.py check --kb chain_kb_v1.json --m4e <m4e_v1> --persons <m3_statements_merged_v1.json>：
      对 M4e 每题四份论断，比较 infer_candidates 与本函数的结果，打印不同的份数。"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, HERE); sys.path.insert(0, E_DIR)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E

MAX_ROUNDS = 64


def close(res):
    """res：各候选的 infer() 结果列表。返回闭合后的 {宫名: {结点: [推法…]}}。"""
    if len(res) == 1:
        return res[0]
    out = {}
    for name in C.PALACES:
        keep = set.intersection(*(set(r[name]) for r in res))
        while True:
            grounded = []
            for r in res:
                g = set()
                while True:
                    add = {n for n in keep - g if any(all(p in g for p in x['premises']) for x in r[name][n])}
                    if not add:
                        break
                    g |= add
                grounded.append(g)
            new = set.intersection(*grounded) if grounded else set()
            if new == keep:
                break
            keep = new
        dp = {n: [dict(x) for x in res[0][name][n] if all(p in keep for p in x['premises'])] for n in res[0][name] if n in keep}
        depth = {n: 1 for n, xs in dp.items() if any(not x['premises'] for x in xs)}
        for _ in range(MAX_ROUNDS):
            changed = False
            for n, xs in dp.items():
                for x in xs:
                    if x['premises'] and all(p in depth for p in x['premises']):
                        d = 1 + max(depth[p] for p in x['premises'])
                        if n not in depth or d < depth[n]:
                            depth[n] = d; changed = True
            if not changed:
                break
        assert set(depth) == set(dp), (name, '有结点算不出深度')
        for n, xs in dp.items():
            for x in xs:
                x['depth'] = 1 if not x['premises'] else 1 + max(depth[p] for p in x['premises'])
            xs.sort(key=lambda x: (x['depth'], x['step']))
        out[name] = dp
    return out


def infer_candidates_closed(rows, nodes, steps, allowed=None):
    return close([C.infer(E.Chart(r), nodes, steps, allowed=allowed) for r in rows])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('check',))
    for k in ('kb', 'm4e', 'persons'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    from m4_build_v2 import run_charts
    nodes, steps = C.load_kb(a.kb)
    persons = {p['person_id']: p for p in json.load(open(a.persons, encoding='utf-8'))['persons']}
    key = json.load(open(os.path.join(a.m4e, 'key_m4e_v1.json'), encoding='utf-8'))
    need = sorted({c for v in key['items'].values() for c in v['letters'].values()})
    rows = run_charts({f"{pid}#{i}": b['form'] for pid in need for i, b in enumerate(persons[pid]['candidates'])})
    cand = {pid: [rows[f'{pid}#{i}'] for i in range(len(persons[pid]['candidates']))] for pid in need}
    diff, total, multi = [], 0, 0
    for iid, v in sorted(key['items'].items()):
        R = set(v['R_T'])
        allowed = {s['step_id'] for s in steps if s['T'] not in R}
        for L, c in sorted(v['letters'].items()):
            total += 1
            if len(cand[c]) == 1:
                continue
            multi += 1
            res = [C.infer(E.Chart(r), nodes, steps, allowed=allowed) for r in cand[c]]
            old = C.infer_candidates(cand[c], nodes, steps, allowed=allowed)
            new = close(res)
            same = all(set(old[p]) == set(new[p]) and all([x['step'] for x in old[p][n]][:1] == [x['step'] for x in new[p][n]][:1] for n in new[p]) for p in C.PALACES)
            dangling = sum(1 for p in C.PALACES for n, xs in old[p].items() for x in xs if any(q not in old[p] for q in x['premises']))
            if not same or dangling:
                diff.append({'题': iid, '份': L, '命主': c, '结点数旧': sum(len(old[p]) for p in C.PALACES), '结点数新': sum(len(new[p]) for p in C.PALACES),
                             '旧结果里引用了未保留前提的推法数': dangling})
    print(json.dumps({'M4e论断份数': total, '多候选的份数': multi, '结果不同或有悬空前提的份数': len(diff), '明细': diff}, ensure_ascii=False))


if __name__ == '__main__':
    main()
