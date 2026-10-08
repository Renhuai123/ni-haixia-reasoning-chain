"""倪师推理链主检验：复现倪海厦自己读过的命例（依据《00_推理链方案_v1.md》七、3；运行前登记，结果不论好坏都报）。
1. 人：M4 的 28 位命例（m3_statements_merged_v1.json 里 eligible 的人），用同一批候选出生资料排盘（m4_build_v2.run_charts）。
2. 倪师判断集 G_A：推理链知识库里出处落在此人讲述时段内、命例特指、适用先天、宫为命宫或身宫的步，它们的结论结点之并。
   时段判定与逐例留一相同（分P 相同、时间在 start_s 与 end_s 之间，时段已含前后各 2 分钟）。G_A 为空的人不计入，人数照报。
3. 引擎：剔除出处落在此人讲述时段内的全部步（不论是否命例特指），用其余的步推（ni_chain_engine_v1.infer 的 allowed）。
4. 本人结点：命宫推出的结点，加上身宫所在之宫里经「身宫」途径推出的结点；有几张候选盘时，取各候选都推出的结点。
5. 得分 s(A, X) = |G_A ∩ 本人结点(X)| / |G_A|。
6. 对照：同一套剔除后的步，在 600 张第四版留出盘上各算 s(A, H)。本人盘的位置
   u_A = （s(A,H) > s(A,本人盘) 的张数 ＋ 0.5 × 相等的张数）÷ 600；0 表示比所有随机盘都好，0.5 表示和随机盘一样。
7. 主统计量：计入各人 u_A 的平均数。p 值：每人改从 600 张留出盘里随机抽一张 j 当作「本人盘」，
   u = （其余 599 张里得分高于 j 的张数 ＋ 0.5 × 与 j 相等的张数）÷ 599，取各人平均；重复 10000 次（种子 METIS-V4-复现检验-20261007），
   平均 u 不大于实测值的比例即为 p（单侧）。p < 0.05 算通过。
8. 另报（只作描述）：
   - 只用定性步（不用推理步）时同样的得分、u 与 p；
   - 倪师判断集里推理步的连线（前提结点 → 结论结点）：引擎在本人盘上有没有一种推法是由这个前提推出这个结论（几张候选都要有），报复现条数与比例；
     同样在 600 张留出盘上算「复现连线的平均比例」作参照。
写出 <out>；文件已存在就停。用法：python3 chain_reproduce_v1.py --kb <chain_kb> --persons <m3_statements_merged_v1.json> --holdout <v4 留出盘> --out <新文件>"""
import argparse, json, os, random, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, HERE)
sys.path.insert(0, E_DIR)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E
from m4_build_v2 import run_charts

SEED = 'METIS-V4-复现检验-20261007'
N_MC = 10000


def in_segs(s, segs):
    m = re.match(r'P(\d+)', str(s.get('分P', '')))
    if not m or not s.get('时间'):
        return False
    t = E.secs(s['时间'])
    return any(int(g['分P']) == int(m.group(1)) and g['start_s'] <= t <= g['end_s'] for g in segs)


def person_nodes(der, chart):
    out = set(der['命宫'])
    if chart.shen != '命宫':
        out |= {n for n, xs in der[chart.shen].items() if any(x['via'].startswith('身宫') for x in xs)}
    return out


def person_links(der, chart):
    """本人结点的每一种推法里的（前提, 结论）连线。"""
    out = set()
    for pal in {'命宫', chart.shen}:
        for n, xs in der[pal].items():
            if pal != '命宫' and not any(x['via'].startswith('身宫') for x in xs):
                continue
            for x in xs:
                for p in x['premises']:
                    out.add((p, n))
    return out


def u_of(own, others):
    g = sum(1 for v in others if v > own); e = sum(1 for v in others if v == own)
    return (g + 0.5 * e) / len(others)


def null_us(scores):
    """每张留出盘 j 当「本人盘」时的 u（与其余 599 张比）。"""
    out = []
    for j, sj in enumerate(scores):
        g = sum(1 for k, v in enumerate(scores) if k != j and v > sj)
        e = sum(1 for k, v in enumerate(scores) if k != j and v == sj)
        out.append((g + 0.5 * e) / (len(scores) - 1))
    return out


def mc_p(obs_mean, per_person_null, seed):
    rng = random.Random(seed)
    n = len(per_person_null)
    hit = 0
    for _ in range(N_MC):
        m = sum(rng.choice(us) for us in per_person_null) / n
        hit += m <= obs_mean
    return hit / N_MC


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('kb', 'persons', 'holdout', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    kb = json.load(open(a.kb, encoding='utf-8'))
    nodes, steps = C.load_kb(a.kb)                 # 引擎可用的步（可操作、先天）
    eng_ids = {s['step_id'] for s in steps}
    q_ids = {s['step_id'] for s in steps if s['类型'] == '定性步'}
    persons = [p for p in json.load(open(a.persons, encoding='utf-8'))['persons'] if p.get('eligible')]
    hold = [r for r in json.load(open(a.holdout, encoding='utf-8'))['rows'] if 'error' not in r]
    hcharts = [E.Chart(r) for r in hold]
    hprep = [C.prepare(c, nodes, steps) for c in hcharts]
    rows = run_charts({f"{p['person_id']}#{i}": c['form'] for p in persons for i, c in enumerate(p['candidates'])})
    out_people, us, us1, null_all, null_all1 = [], [], [], [], []
    link_tot = link_hit = 0
    link_hold = []
    for p in persons:
        pid = p['person_id']
        segs = p['segments']
        gold_steps = [s for s in kb['steps'] if in_segs(s, segs) and s.get('命例特指') and s['适用'] == '先天' and s['宫'] in ('命宫', '身宫')]
        gold = sorted({n for s in gold_steps for n in s['conclusions']})
        removed = {s['step_id'] for s in kb['steps'] if in_segs(s, segs)}
        allowed = eng_ids - removed
        allowed1 = q_ids - removed
        rec = {'person_id': pid, '候选盘数': len(p['candidates']), '剔除的步': len(removed & eng_ids), '倪师判断集步数': len(gold_steps), '倪师判断集结点数': len(gold),
               '倪师判断集': [{'结点': n, '层': nodes.get(n, kb['nodes'].get(n, {})).get('层'), '名': nodes.get(n, kb['nodes'].get(n, {})).get('名')} for n in gold]}
        if not gold:
            rec['计入'] = False
            out_people.append(rec); continue
        rec['计入'] = True
        crs = [rows[f'{pid}#{i}'] for i in range(len(p['candidates']))]
        assert all('error' not in r for r in crs), pid
        cch = [E.Chart(r) for r in crs]
        cprep = [C.prepare(c, nodes, steps) for c in cch]

        def own_nodes(allow):
            sets = [person_nodes(C.infer(c, nodes, steps, prep=pp, allowed=allow), c) for c, pp in zip(cch, cprep)]
            return set.intersection(*sets)
        G = set(gold)
        own = own_nodes(allowed); own1 = own_nodes(allowed1)
        s_own = len(G & own) / len(G); s_own1 = len(G & own1) / len(G)
        hs, hs1, hl = [], [], []
        gl = {(pp, c) for s in gold_steps if s['类型'] == '推理步' for pp in s['premises'] for c in s['conclusions']}
        for c, pp in zip(hcharts, hprep):
            der = C.infer(c, nodes, steps, prep=pp, allowed=allowed)
            hs.append(len(G & person_nodes(der, c)) / len(G))
            der1 = C.infer(c, nodes, steps, prep=pp, allowed=allowed1)
            hs1.append(len(G & person_nodes(der1, c)) / len(G))
            if gl:
                hl.append(len(gl & person_links(der, c)) / len(gl))
        u = u_of(s_own, hs); u1 = u_of(s_own1, hs1)
        us.append(u); us1.append(u1)
        null_all.append(null_us(hs)); null_all1.append(null_us(hs1))
        own_links = set.intersection(*[person_links(C.infer(c, nodes, steps, prep=pp, allowed=allowed), c) for c, pp in zip(cch, cprep)])
        link_tot += len(gl); link_hit += len(gl & own_links)
        if gl:
            link_hold.append(sum(hl) / len(hl))
        rec.update({'本人盘得分': round(s_own, 4), '留出盘平均得分': round(sum(hs) / len(hs), 4), 'u': round(u, 4),
                    '本人盘推出的倪师判断': sorted(G & own),
                    '只用定性步·本人盘得分': round(s_own1, 4), '只用定性步·留出盘平均得分': round(sum(hs1) / len(hs1), 4), '只用定性步·u': round(u1, 4),
                    '推理步连线': len(gl), '本人盘复现的连线': len(gl & own_links), '留出盘复现连线的平均比例': round(sum(hl) / len(hl), 4) if hl else None})
        out_people.append(rec)
    n = len(us)
    mean_u = sum(us) / n if n else None
    mean_u1 = sum(us1) / n if n else None
    res = {'schema': 'chain-reproduce-v1', 'seed': SEED, 'n_mc': N_MC, 'holdout_charts': len(hold), 'kb_engine_steps': len(steps),
           '人数': {'M4命例': len(persons), '计入': n, '不计入（倪师判断集为空）': len(persons) - n},
           '主检验': {'平均u': round(mean_u, 4) if n else None, 'p_单侧': mc_p(mean_u, null_all, SEED) if n else None,
                    'u中位数': round(statistics.median(us), 4) if n else None, 'u小于0.5的人数': sum(1 for x in us if x < 0.5),
                    'u不大于0.05的人数': sum(1 for x in us if x <= 0.05)},
           '另报·只用定性步': {'平均u': round(mean_u1, 4) if n else None, 'p_单侧': mc_p(mean_u1, null_all1, SEED + '-定性步') if n else None},
           '另报·推理步连线': {'连线合计': link_tot, '本人盘复现': link_hit, '比例': round(link_hit / link_tot, 4) if link_tot else None,
                         '留出盘复现比例的平均（各人平均再平均）': round(sum(link_hold) / len(link_hold), 4) if link_hold else None},
           '各人': out_people}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != '各人'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
