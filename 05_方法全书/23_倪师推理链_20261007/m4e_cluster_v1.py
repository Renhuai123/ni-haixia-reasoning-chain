"""第一次认本人检验（M4e）按题组成团重算（事后补算，只作描述；回应第十四稿内审 R2 第 4 条）。
28 题里有 10 题分成 3 组，组内四位当事人相同、用的是同一组四份论断（按 key_m4e_v1 的 letters 求得），题目不完全独立。
做法：每组只取一题，与其余 18 题合成 21 个互不共用论断的单位，做单尾精确二项检验（瞎猜 1/4）。
组内取哪一题有 4×2×4 = 32 种取法，全部算出，报最小、最大的 p，以及每组取编号最小一题时的 p。
逐题对错的判法与 m4e_analyze_v1 相同（只认格式合格的答案，「最符合」与真论断字母相同算对）。
用法：python3 m4e_cluster_v1.py --root m4e_v1 --out chain_results_v1/m4e_cluster_v1.json"""
import argparse, itertools, json, os
from collections import defaultdict
from m4e_analyze_v1 import valid, binom_tail, ARMS


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    key = json.load(open(os.path.join(a.root, 'key_m4e_v1.json'), encoding='utf-8'))
    man = json.load(open(os.path.join(a.root, 'manifest.json'), encoding='utf-8'))
    summ = json.load(open(os.path.join(a.root, 'audit_summary_v1.json'), encoding='utf-8'))
    assert not summ['待重跑']
    items = {i: v['true'] for i, v in key['items'].items()}
    groups = defaultdict(list)
    for i, v in key['items'].items():
        groups[frozenset(v['letters'].values())].append(i)
    shared = [sorted(g) for g in groups.values() if len(g) > 1]
    single = sorted(i for g in groups.values() if len(g) == 1 for i in g)
    assert sum(len(g) for g in shared) == 10 and len(shared) == 3 and len(single) == 18
    out = {'schema': 'm4e-cluster-v1', '说明': __doc__.split('\n')[0], '共用论断的题组': shared, '单独的题数': len(single), '单位数': len(single) + len(shared), 'arms': {}}
    for arm in ARMS:
        pack_of = {pk['items'][0]: pk['pack'] for pk in man['arms'][arm]}
        hit = {}
        for i in sorted(items):
            st = summ['arms'][arm][pack_of[i]]
            ans = None
            if st['status'] == '合格':
                obj = json.load(open(os.path.join(a.root, f'judge_returns_{arm}', st['accepted'] + '.json'), encoding='utf-8'))
                ans = next((x for x in obj['答案'] if x.get('题') == i), None)
            hit[i] = ans is not None and valid(ans) and ans['最符合'] == items[i]
        base = sum(hit[i] for i in single)
        n = len(single) + len(shared)
        res = []
        for pick in itertools.product(*shared):
            k = base + sum(hit[i] for i in pick)
            res.append({'取法': list(pick), '认对': k, '单侧p': binom_tail(n, k)})
        first = next(r for r in res if r['取法'] == [g[0] for g in shared])
        out['arms'][arm] = {'28题认对': sum(hit.values()), '题组内各题对错': {'、'.join(g): [hit[i] for i in g] for g in shared},
                            '21单位认对·最少': min(r['认对'] for r in res), '21单位认对·最多': max(r['认对'] for r in res),
                            '单侧p·最大': max(r['单侧p'] for r in res), '单侧p·最小': min(r['单侧p'] for r in res),
                            '每组取编号最小一题': first, '取法数': len(res)}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({arm: {k: v for k, v in r.items() if k != '题组内各题对错'} for arm, r in out['arms'].items()}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
