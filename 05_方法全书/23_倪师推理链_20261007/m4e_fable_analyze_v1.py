"""M4e 用 Fable 5.1 重审：统计 v1（依据《00l_三项深化方案》v2 第五节决策点 3；只作描述）。
材料：m4e_v1 三组 84 个审者包逐字节原样，只把说明换成接口版（m4e_judge_instructions_{链,平,三}_api_v1.txt，只差材料与纪律几行），
  经 api_runner_v1.py 交给 claude-fable-5-1（effort high），每包一次独立调用。交卷名：链组 EC-Mxx、平铺组 EF-Mxx、第三版先天组 E3-Mxx。
有效卷：原卷合格取原卷，否则取第一份合格的重跑卷；三份都不合格，或「最符合」「排序」不合法，按答错计、名次记 4（与 M4e 相同）。
算：各组认对题数 k、单尾精确二项 p（p₀ = 1/4）、Clopper–Pearson 95% 区间、真论断名次和与单尾 p（同 m4e_analyze_v1）；
  各组与原 M4e（Claude Opus 5.5 审者）逐题配对：只 Fable 认出、只 Opus 认出的题数与配对差的条件精确 95% 区间（同 m4e_analyze_v1.paired）；
  Fable 三组之间的配对（链对平、平对三、链对三）。写出 <out>；文件已存在就停。
用法：python3 m4e_fable_analyze_v1.py --root m4e_v1 --returns <存档目录> --orig chain_results_v1/m4e_analysis_v1.json --out <新文件>"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m4e_analyze_v1 import binom_tail, clopper_pearson, ranksum_p, paired, valid

ARMS = {'链': 'EC', '平': 'EF', '三': 'E3'}


def accepted(rdir, name):
    for nm in (name, f'{name}_重跑1', f'{name}_重跑2'):
        au = os.path.join(rdir, nm + '.audit.json')
        if os.path.exists(au) and json.load(open(au, encoding='utf-8'))['ok']:
            return json.load(open(os.path.join(rdir, nm + '.json'), encoding='utf-8'))
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('root', 'returns', 'orig', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    key = json.load(open(os.path.join(a.root, 'key_m4e_v1.json'), encoding='utf-8'))
    man = json.load(open(os.path.join(a.root, 'manifest.json'), encoding='utf-8'))
    orig = json.load(open(a.orig, encoding='utf-8'))
    items = {i: v['true'] for i, v in key['items'].items()}
    res = {'schema': 'm4e-fable-v1', 'n_items': len(items), 'arms': {}, '与原M4e逐题配对': {}, 'Fable组间配对': {}}
    hits = {}
    for arm, pre in ARMS.items():
        per = {}
        for pk in man['arms'][arm]:
            (i,) = pk['items']
            obj = accepted(a.returns, f"{pre}-{pk['pack']}")
            ans = next((x for x in (obj or {}).get('答案', []) if x.get('题') == i), None)
            ok = ans is not None and valid(ans)
            per[i] = {'有合格卷': obj is not None, 'format_ok': ok, 'pick': ans['最符合'] if ok else None,
                      'hit': ok and ans['最符合'] == items[i], 'rank_of_true': ans['排序'].index(items[i]) + 1 if ok else 4}
        hit = {i: x['hit'] for i, x in per.items()}
        hits[arm] = hit
        k = sum(hit.values())
        S = sum(x['rank_of_true'] for x in per.values())
        res['arms'][arm] = {'hits': k, 'p_binomial_one_sided': binom_tail(len(items), k), 'rate_CP95': clopper_pearson(k, len(items)),
                            'rank_sum': S, 'p_rank_sum_one_sided': ranksum_p(S), 'mean_rank_of_true': round(S / len(items), 4),
                            '没有合格卷': sum(1 for x in per.values() if not x['有合格卷']), 'format_invalid': sum(1 for x in per.values() if x['有合格卷'] and not x['format_ok']),
                            'per_item': per}
        oh = {i: orig['arms'][arm]['per_item'][i]['hit'] for i in items}
        res['与原M4e逐题配对'][f'{arm}组：Fable对Opus'] = paired(hit, oh)
        res['与原M4e逐题配对'][f'{arm}组：Fable对Opus']['Opus认对题数'] = sum(oh.values())
    res['Fable组间配对'] = {'链组对平铺组': paired(hits['链'], hits['平']), '平铺组对第三版先天组': paired(hits['平'], hits['三']), '链组对第三版先天组': paired(hits['链'], hits['三'])}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({arm: {k: res['arms'][arm][k] for k in ('hits', 'p_binomial_one_sided', 'rate_CP95', 'mean_rank_of_true')} for arm in ARMS}
                     | {k: {kk: v[kk] for kk in ('只前一组', '只后一组', '配对差', '配对差95%区间（条件精确）')} for k, v in res['与原M4e逐题配对'].items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
