"""乙 推理类型：统计 v1（依据《00h_三项补充研究方案_v2.md》三、4 与 6）。只读存档与知识库，只输出统计量。
定类：五问里第一个答「是」的（问1 取象、问2 术数机理、问3 类属展开、问4 性情因果、问5 处境常理）；五问都不是「是」的为「其他」。
子命令：
  pilot --returns <试编存档目录> --round N：两名试编者（P{N}_甲、P{N}_乙）类型与五问各自的原始一致率，并按停止规则判定
        （类型的原始一致率 ≥ 0.70，且五问各自的原始一致率都 ≥ 0.70，就不再改说明）。写出 <out>。
  final --formal <正式材料目录> --returns <正式存档目录> --adj-returns <裁定存档目录> --pilot-samples <试编抽样文件…>：
        一致程度（类型、五问、三个标记各自的原始一致率与 Krippendorff α，95% 区间按 T 成团重抽 2000 次，
        种子「METIS-V4-推理类型区间-20261007」；类型另报各批 Cohen κ、两人混淆矩阵、每类特定一致率 2a/(2a+b+c)），
        全部 371 步与「剔除试编步与 25 条审稿样例」两个版本；裁定改动条数；
        最终类型（两人一致的照用，不同的按裁定）的分布与按 T 成团重抽的 95% 区间；五问各自答「是」的比例；
        按适用（先天／运限）、按命例特指分开；三个标记的分布；标B 与知识库命例特指的交叉表；按连接词分开（前 10 个）；
        每类按 T 编号次序的前两例（只给编号）；解读规则的判定（类型 α < 0.4；各类特定一致率 < 0.5）。写出 <out>。
存档用 save_returns_v4.py 的审计：每份按「原卷、重跑1、重跑2」取第一份合格的；三份都不合格的批按缺失照报。
用法：python3 types_analyze_v1.py pilot --returns types_v1/pilot_returns --round 1 --out <新文件>
      python3 types_analyze_v1.py final --kb chain_kb_v1.json --formal types_v1/formal --returns types_v1/formal_returns --adj-returns types_v1/adj_returns
             --pilot-samples types_v1/pilot/sample_P1.json [...] --out <新文件>"""
import argparse, collections, hashlib, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from types_build_v1 import QS, FLAGS, REVIEW25, norm_q

TYPES = ['取象', '术数机理', '类属展开', '性情因果', '处境常理', '其他']
N_BOOT = 2000
SEED = 'METIS-V4-推理类型区间-20261007'


def rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16], 16))


def type_of(ans):
    for q, t in zip(QS, TYPES):
        if norm_q(ans.get(q)) == '是':
            return t
    return '其他'


def accepted(rdir, name):
    for nm in (name, f'{name}_重跑1', f'{name}_重跑2'):
        f = os.path.join(rdir, nm + '.audit.json')
        if os.path.exists(f) and json.load(open(f, encoding='utf-8'))['ok']:
            return json.load(open(os.path.join(rdir, nm + '.json'), encoding='utf-8')), nm
    return None, None


def alpha_nominal(pairs):
    """两名评者、无缺失的名义尺度 Krippendorff α。pairs：[(a, b)]。"""
    o = collections.Counter()
    for a, b in pairs:
        o[(a, b)] += 1
        o[(b, a)] += 1
    nc = collections.Counter()
    for (c, k), v in o.items():
        nc[c] += v
    n = sum(nc.values())
    dis_o = sum(v for (c, k), v in o.items() if c != k)
    dis_e = sum(nc[c] * nc[k] for c in nc for k in nc if c != k)
    if dis_e == 0:
        return 1.0 if dis_o == 0 else 0.0
    return 1 - (n - 1) * dis_o / dis_e


def cohen_kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / n / n
    return None if pe == 1 else (po - pe) / (1 - pe)


def boot(units, stat, clusters, seed=SEED, n=N_BOOT):
    """units：{编号: 值}；clusters：{T: [编号]}；按 T 成团重抽，返回 2.5、97.5 百分位。"""
    r = rng(seed)
    keys = sorted(clusters, key=lambda t: int(t[1:]))
    vals = []
    for _ in range(n):
        pick = [i for _ in keys for i in clusters[keys[r.randrange(len(keys))]]]
        v = stat([units[i] for i in pick])
        if v is not None:
            vals.append(v)
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 4), round(vals[min(len(vals) - 1, int(0.975 * len(vals)))], 4)] if vals else None


def cmd_pilot(a):
    assert not os.path.exists(a.out)
    name = f'P{a.round}'
    A, _ = accepted(a.returns, f'{name}_甲')
    B, _ = accepted(a.returns, f'{name}_乙')
    assert A and B, '试编交卷不全或不合格'
    ia, ib = {x['编号']: x for x in A['归类']}, {x['编号']: x for x in B['归类']}
    assert set(ia) == set(ib)
    ids = sorted(ia)
    per_q = {q: sum(norm_q(ia[i].get(q)) == norm_q(ib[i].get(q)) for i in ids) / len(ids) for q in QS}
    ta, tb = {i: type_of(ia[i]) for i in ids}, {i: type_of(ib[i]) for i in ids}
    t_agree = sum(ta[i] == tb[i] for i in ids) / len(ids)
    stop = t_agree >= 0.70 and all(v >= 0.70 for v in per_q.values())
    res = {'round': a.round, 'n': len(ids), '类型原始一致率': round(t_agree, 4), '五问原始一致率': {q: round(v, 4) for q, v in per_q.items()},
           '标记原始一致率': {f: round(sum(str(ia[i].get(f, '')).strip() == str(ib[i].get(f, '')).strip() for i in ids) / len(ids), 4) for f in FLAGS},
           '甲类型分布': dict(collections.Counter(ta.values())), '乙类型分布': dict(collections.Counter(tb.values())),
           '分歧': [{'编号': i, '甲': ta[i], '乙': tb[i]} for i in ids if ta[i] != tb[i]],
           '停止规则': '类型原始一致率 ≥ 0.70 且五问各自 ≥ 0.70', '达到停止规则': stop}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != '分歧'}, ensure_ascii=False))


def cmd_final(a):
    assert not os.path.exists(a.out)
    kb = json.load(open(a.kb, encoding='utf-8'))
    steps = {s['step_id']: s for s in kb['steps'] if s['类型'] == '推理步'}
    man = json.load(open(os.path.join(a.formal, 'batches.json'), encoding='utf-8'))
    pilot_ids = set()
    for f in a.pilot_samples or []:
        pilot_ids |= set(json.load(open(f, encoding='utf-8'))['steps'])
    excl = pilot_ids | set(REVIEW25)
    ans_a, ans_b, batch_of, missing, adj = {}, {}, {}, [], {}
    reruns = {}
    for b in man['batches']:
        A, na = accepted(a.returns, f"{b['batch']}_甲")
        B, nb = accepted(a.returns, f"{b['batch']}_乙")
        reruns[b['batch']] = [na, nb]
        if not (A and B):
            missing.append(b['batch']); continue
        for x in A['归类']:
            ans_a[x['编号']] = x
        for x in B['归类']:
            ans_b[x['编号']] = x
        for i in b['steps']:
            batch_of[i] = b['batch']
        J, nj = accepted(a.adj_returns, b['batch'])
        reruns[b['batch']].append(nj)
        for x in (J or {}).get('裁定', []):
            adj[(x['编号'], x['项'])] = x.get('裁定', '')
    ids = sorted(batch_of, key=lambda i: (int(steps[i]['T'][1:]), i))
    clusters = collections.defaultdict(list)
    for i in ids:
        clusters[steps[i]['T']].append(i)
    out = {'schema': 'types-final-v1', 'n_steps': len(ids), '缺失的批': missing, '采用的交卷': reruns}

    def agreement(sel, label):
        sel = [i for i in ids if sel(i)]
        cl = collections.defaultdict(list)
        for i in sel:
            cl[steps[i]['T']].append(i)
        res = {'n': len(sel)}
        items = [('类型', lambda x: type_of(x))] + [(q, lambda x, q=q: norm_q(x.get(q)) or '空') for q in QS] + \
                [(f, lambda x, f=f: str(x.get(f, '')).strip() or '空') for f in FLAGS]
        for nm, fn in items:
            pairs = {i: (fn(ans_a[i]), fn(ans_b[i])) for i in sel}
            raw = sum(p[0] == p[1] for p in pairs.values()) / len(sel) if sel else None
            res[nm] = {'原始一致率': round(raw, 4) if raw is not None else None, 'alpha': round(alpha_nominal(list(pairs.values())), 4) if sel else None,
                       'alpha_95%（按T成团重抽）': boot(pairs, alpha_nominal, cl, seed=SEED + label + nm)}
        return res
    out['一致程度·全部'] = agreement(lambda i: True, '全部')
    out['一致程度·剔除试编与审稿样例'] = agreement(lambda i: i not in excl, '剔除')
    ta, tb = {i: type_of(ans_a[i]) for i in ids}, {i: type_of(ans_b[i]) for i in ids}
    out['各批Cohen_kappa（类型）'] = {b['batch']: (round(cohen_kappa([(ta[i], tb[i]) for i in b['steps'] if i in ta]), 4)
                                         if all(i in ta for i in b['steps']) else None) for b in man['batches']}
    out['混淆矩阵（行=甲，列=乙）'] = {t: {u: sum(1 for i in ids if ta[i] == t and tb[i] == u) for u in TYPES} for t in TYPES}
    spec = {}
    for t in TYPES:
        both = sum(1 for i in ids if ta[i] == t and tb[i] == t)
        one = sum(1 for i in ids if (ta[i] == t) != (tb[i] == t))
        spec[t] = round(2 * both / (2 * both + one), 4) if both + one else None
    out['每类特定一致率'] = spec
    # 最终答案
    final, changed = {}, collections.Counter()
    for i in ids:
        row = {}
        for k in QS + list(FLAGS):
            va = norm_q(ans_a[i].get(k)) if k in QS else str(ans_a[i].get(k, '')).strip()
            vb = norm_q(ans_b[i].get(k)) if k in QS else str(ans_b[i].get(k, '')).strip()
            if va == vb:
                row[k] = va
            else:
                v = adj.get((i, k))
                row[k] = (norm_q(v) if k in QS else str(v or '').strip()) or None
                changed['两人分歧被定' if row[k] is not None else '分歧未裁定（缺失）'] += 1
        final[i] = row
    out['裁定改动'] = dict(changed, 两人一致被改=0)
    ftype = {i: type_of(final[i]) for i in ids}
    out['最终类型'] = {i: ftype[i] for i in ids}

    def dist(sel, label):
        sel = [i for i in ids if sel(i)]
        cl = collections.defaultdict(list)
        for i in sel:
            cl[steps[i]['T']].append(i)
        res = {'n': len(sel)}
        for t in TYPES:
            u = {i: ftype[i] == t for i in sel}
            res[t] = {'条数': sum(u.values()), '比例': round(sum(u.values()) / len(sel), 4) if sel else None,
                      '95%（按T成团重抽）': boot(u, lambda v: sum(v) / len(v) if v else None, cl, seed=SEED + label + t)}
        return res
    out['类型分布·全部'] = dist(lambda i: True, '分布全部')
    out['类型分布·先天'] = dist(lambda i: steps[i]['适用'] == '先天', '分布先天')
    out['类型分布·运限'] = dist(lambda i: steps[i]['适用'] != '先天', '分布运限')
    out['类型分布·命例特指'] = dist(lambda i: steps[i]['命例特指'], '分布命例')
    out['类型分布·通则'] = dist(lambda i: not steps[i]['命例特指'], '分布通则')
    out['五问答是的比例'] = {q: round(sum(1 for i in ids if final[i][q] == '是') / len(ids), 4) for q in QS}
    out['三个标记'] = {f: dict(collections.Counter(final[i][f] for i in ids)) for f in FLAGS}
    out['标B×知识库命例特指'] = {str(c): dict(collections.Counter(final[i]['标B'] for i in ids if steps[i]['命例特指'] == c)) for c in (True, False)}
    conn = collections.Counter(steps[i].get('连接', '') for i in ids)
    out['按连接词（前10个）'] = {c: dict(collections.Counter(ftype[i] for i in ids if steps[i].get('连接', '') == c)) for c, _ in conn.most_common(10)}
    out['各类前两例（编号）'] = {t: [i for i in ids if ftype[i] == t][:2] for t in TYPES}
    out['标C为是的编号'] = [i for i in ids if final[i]['标C'] == '是']
    al = out['一致程度·全部']['类型']['alpha']
    out['解读规则'] = {'类型alpha<0.4（只写无法可靠区分）': al is not None and al < 0.4,
                   '特定一致率<0.5的类（只报区间）': [t for t, v in spec.items() if v is not None and v < 0.5]}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    show = {k: out[k] for k in ('n_steps', '缺失的批', '裁定改动', '每类特定一致率', '五问答是的比例', '解读规则')}
    show['类型alpha'] = out['一致程度·全部']['类型']
    show['类型分布'] = {t: (v['条数'], v['比例'], v['95%（按T成团重抽）']) for t, v in out['类型分布·全部'].items() if t != 'n'}
    print(json.dumps(show, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('pilot', 'final'))
    ap.add_argument('--round', type=int)
    ap.add_argument('--pilot-samples', nargs='*')
    for k in ('kb', 'formal', 'returns', 'adj-returns', 'out'):
        ap.add_argument('--' + k)
    a = ap.parse_args()
    {'pilot': cmd_pilot, 'final': cmd_final}[a.cmd](a)


if __name__ == '__main__':
    main()
