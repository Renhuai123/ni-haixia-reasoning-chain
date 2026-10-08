"""倪师推理链：第四版在 600 张新留出盘上的覆盖（依据《00_推理链方案_v1.md》七、2；只作描述，不设门槛；运行前登记）。
每张盘用 ni_chain_engine_v1.infer 推一次（全部可用的步），统计命宫：
- 「推理步走到」某层：该层有结点，且这个结点至少有一种推法是推理步（前提非空）；
  报：推理步走到「行为、路线、成败」任一层的盘占多少；走到「成败」层的占多少；
- 命宫里实际用上的推理步条数（同一条推理步在命宫推出几个结点只算一条）：中位数、四分位、最大；
- 最长一条链的步数：命宫各结点最短推法深度的最大值（定性步得出的深度为 1）；中位数、四分位、最大；
- 命宫结点里，最短推法也要经过推理步（不能由定性步直接得出）的比例：全部盘合计，以及逐盘比例的平均；
- 「两说」处数（命宫；以及十二宫合计）：分布。
另报全部十二宫合计的结点数与经推理步得出的结点数，作参照。
写出 <out>；文件已存在就停。用法：python3 chain_coverage_v1.py --kb <chain_kb> --charts <v4 留出盘> --out <新文件>"""
import argparse, collections, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E


def q(xs):
    xs = sorted(xs)
    if not xs:
        return None
    qs = statistics.quantiles(xs, n=4, method='inclusive') if len(xs) > 1 else [xs[0]] * 3
    return {'中位数': statistics.median(xs), '下四分位': qs[0], '上四分位': qs[2], '最大': xs[-1], '平均': round(sum(xs) / len(xs), 3)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('kb', 'charts', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    nodes, steps = C.load_kb(a.kb)
    by = {s['step_id']: s for s in steps}
    rows = [r for r in json.load(open(a.charts, encoding='utf-8'))['rows'] if 'error' not in r]
    reach_any = reach_win = 0
    n_r_steps, max_depth, two_m, two_all, frac = [], [], [], [], []
    tot_nodes = tot_via_r = 0
    all_nodes = all_via_r = 0
    layer_reach = collections.Counter()
    for row in rows:
        ch = E.Chart(row)
        der = C.infer(ch, nodes, steps)
        dp = der['命宫']
        r_layers = {nodes[n]['层'] for n, xs in dp.items() if any(x['premises'] for x in xs)}
        for lay in r_layers:
            layer_reach[lay] += 1
        reach_any += bool(r_layers & {'行为', '路线', '成败'})
        reach_win += '成败' in r_layers
        n_r_steps.append(len({x['step'] for xs in dp.values() for x in xs if x['premises']}))
        max_depth.append(max((xs[0]['depth'] for xs in dp.values()), default=0))
        via = sum(1 for xs in dp.values() if xs[0]['premises'])
        tot_nodes += len(dp); tot_via_r += via
        if dp:
            frac.append(via / len(dp))
        two_m.append(len(C.two_sayings(dp, nodes)))
        two_all.append(sum(len(C.two_sayings(der[p], nodes)) for p in C.PALACES))
        all_nodes += sum(len(der[p]) for p in C.PALACES)
        all_via_r += sum(1 for p in C.PALACES for xs in der[p].values() if xs[0]['premises'])
    n = len(rows)
    res = {'schema': 'chain-coverage-v1', 'charts': n, 'kb_steps_used': len(steps), 'kb_inference_steps_used': sum(s['类型'] == '推理步' for s in steps),
           '命宫': {'推理步走到行为路线成败任一层的盘': reach_any, '比例': round(reach_any / n, 4),
                   '推理步走到成败层的盘': reach_win, '比例·成败': round(reach_win / n, 4),
                   '推理步走到各层的盘数': {k: layer_reach[k] for k in C.LAYER_ORDER if layer_reach[k]},
                   '用上的推理步条数': q(n_r_steps), '最长链步数': q(max_depth),
                   '最短推法也要经过推理步的结点': {'合计': tot_via_r, '结点合计': tot_nodes, '比例': round(tot_via_r / tot_nodes, 4) if tot_nodes else None,
                                          '逐盘比例的平均': round(sum(frac) / len(frac), 4) if frac else None},
                   '两说处数': q(two_m), '有两说的盘': sum(1 for x in two_m if x)},
           '十二宫合计': {'结点': all_nodes, '最短推法也要经过推理步的结点': all_via_r, '两说处数': q(two_all)}}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
