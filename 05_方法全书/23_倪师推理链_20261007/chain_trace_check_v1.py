"""倪师推理链：可追溯核对（依据《00_推理链方案_v1.md》七、4；要求 100%；运行前登记）。
在 600 张第四版留出盘上逐张推理，核对：
1. 每个推出的结点的每一种推法，所用的步都有 T 编号，T 编号在倪师讲稿语料里，步的原话摘录逐字出自该条讲稿（去掉空白后比较）；
2. 推理步的每个前提结点，在同一宫里确实已经推出（推导链不断）；
3. 「推理链」一节的成稿里，每个推出的结点都出现一次，且带着它最短推法那一步的 T 编号。
任何一项不合格都逐条列出。写出 <out>；文件已存在就停。
用法：python3 chain_trace_check_v1.py --kb <chain_kb> --charts <v4 留出盘> --corpus <ni_corpus.txt> --out <新文件>"""
import argparse, collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E

norm = lambda s: re.sub(r'\s+', '', s or '')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('kb', 'charts', 'corpus', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    nodes, steps = C.load_kb(a.kb)
    by = {s['step_id']: s for s in steps}
    corpus = {}
    for ln in open(a.corpus, encoding='utf-8'):
        t = ln.rstrip('\n').split('｜')
        corpus[t[0]] = norm(t[4])
    rows = [r for r in json.load(open(a.charts, encoding='utf-8'))['rows'] if 'error' not in r]
    c = collections.Counter(); bad = []
    for row in rows:
        ch = E.Chart(row)
        der = C.infer(ch, nodes, steps)
        text = C.render_chain(der, nodes, by, ch)
        lines = text.split('\n')
        for pal in C.PALACES:
            for n, xs in der[pal].items():
                c['结点'] += 1
                for x in xs:
                    c['推法'] += 1
                    st = by[x['step']]
                    if st['T'] not in corpus or norm(st['原话摘录']) not in corpus[st['T']]:
                        bad.append({'chart': row['id'], '宫': pal, '结点': n, 'step': x['step'], 'problem': '原话摘录不在该条讲稿里'}); continue
                    if any(p not in der[pal] for p in x['premises']):
                        bad.append({'chart': row['id'], '宫': pal, '结点': n, 'step': x['step'], 'problem': '前提结点没有推出'}); continue
                    c['推法合格'] += 1
                shown = [l for l in lines if l.startswith(f"  {nodes[n]['层']}：{nodes[n]['名']} ← ") and f"〔{by[xs[0]['step']]['T']}「" in l]
                if not shown:
                    bad.append({'chart': row['id'], '宫': pal, '结点': n, 'problem': '成稿里找不到这个结点（或没带 T 编号）'})
                else:
                    c['成稿里带出处的结点'] += 1
    res = {'schema': 'chain-trace-check-v1', 'charts': len(rows), 'counts': dict(c),
           '推法合格比例': round(c['推法合格'] / c['推法'], 6) if c['推法'] else None,
           '成稿带出处比例': round(c['成稿里带出处的结点'] / c['结点'], 6) if c['结点'] else None,
           'all_ok': not bad, 'problems': bad[:200], 'n_problems': len(bad)}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'problems'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
