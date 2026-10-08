"""论文第七稿（推理链）正文要用的全部数字与表格内容（只读登记过的结果文件，不新做统计）；正文里的数字都从这里抄，核数脚本也以它为准。
另取三份按事先写定的规则挑出的样例（不挑好看的）：
- 附录推理步样例：知识库里连接词含「所以」、前提与结论都在主链六层的推理步，按 T 编号（数字）顺序取前 10 条；
- 核查不成立的例子：判「不成立」的推理步，按 T 编号顺序取前 5 条；
- 归一样例：成员最多的 6 个结点。
写出 <out>；文件已存在就停。用法：python3 chain_paper_counts_v1.py --out <新文件>"""
import argparse, collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W5 = os.path.dirname(HERE)
CH = os.path.join(W5, '23_倪师推理链_20261007')
MAIN6 = ['定性', '长相', '个性', '行为', '路线', '成败']


def jl(*p):
    return json.load(open(os.path.join(*p), encoding='utf-8'))


def tnum(t):
    return int(re.sub(r'\D', '', t) or 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    M, RS = os.path.join(CH, 'chain_merged_v1'), os.path.join(CH, 'chain_results_v1')
    adj, chk, norm = jl(M, 'adjudicated_v1.json'), jl(M, 'check_v1.json'), jl(M, 'normalized_v1.json')
    kb = jl(CH, 'chain_kb_v1.json')
    labels = {l['编号']: l for l in jl(CH, 'chain_norm_packets_v1', 'labels_all.json')['labels']}
    cov, rep, diag, tr, ex = (jl(RS, f) for f in ('coverage_v1.json', 'reproduce_v1.json', 'reproduce_diag_v1.json', 'trace_check_v1.json', 'example_r30_v1.json'))
    nd = kb['nodes']
    g = adj['一致程度']
    c = chk['counts']
    R = [s for s in kb['steps'] if s['类型'] == '推理步']
    eng = [s for s in kb['steps'] if s['可操作'] and s['适用'] == '先天']
    out = {}
    out['抽取'] = {'条目': g['按条']['条目'], '推理步有无一致': g['按条']['推理步有无一致'], '一致比例': round(g['按条']['推理步有无一致'] / g['按条']['条目'], 4),
                 '两人都有推理步': g['按条']['两人都有推理步'], '只一人有推理步': g['按条']['只一人有推理步'],
                 '甲抽出': g['按步·甲乙各自']['甲·收'] + g['按步·甲乙各自']['甲·不收'], '甲被收': g['按步·甲乙各自']['甲·收'],
                 '乙抽出': g['按步·甲乙各自']['乙·收'] + g['按步·甲乙各自']['乙·不收'], '乙被收': g['按步·甲乙各自']['乙·收'],
                 '定稿来源': g['按步·定稿来源'], '甲乙都抽到比例': round(g['按步·定稿来源']['甲乙'] / adj['counts']['定稿步'], 4)}
    out['裁定'] = {k: adj['counts'][k] for k in ('定稿步', '合格', '定性步', '推理步', '有步的条目', '有推理步的条目', '方法', 'problems', 'warnings')}
    ok = c['定性步成立'] + c['推理步成立']
    out['核查'] = {**{k: c[k] for k in ('定性步成立', '定性步不成立', '推理步成立', '推理步不成立', '定性步成立比例', '推理步成立比例')},
                 '成立合计': ok, '不成立合计': c['定性步不成立'] + c['推理步不成立'], '成立比例': round(ok / c['待核'], 4)}
    ag = norm['agreement']
    out['归一'] = {**norm['counts'], '合并一致率': {k: v['合并一致率'] for k, v in ag.items()},
                 '全部配对判断相同比例最低': min(v['全部配对判断相同比例'] for v in ag.values()),
                 '同结点伙伴完全相同比例': {k: v['同结点伙伴完全相同的判断名比例'] for k, v in ag.items()},
                 '裁定改层': sum(v['裁定改层'] for v in ag.values()),
                 '全组合并一致率': round(sum(v['两人都合的对数'] for v in ag.values()) / sum(v['任一人合的对数'] for v in ag.values()), 4)}
    kc = kb['counts']
    by_app = collections.Counter((s['类型'], s['适用']) for s in kb['steps'])
    out['知识库'] = {'收下的步': kc['收下的步'], '定性步': kc['定性步'], '推理步': kc['推理步'], '结点': kc['结点'], '排除': kb['excluded'],
                  '引擎可用': kc['引擎可用（可操作且先天）'], '引擎可用的推理步': kc['引擎可用的推理步'], '引擎可用的定性步': kc['引擎可用（可操作且先天）'] - kc['引擎可用的推理步'],
                  '按类型适用': {f'{k[0]}·{k[1]}': n for k, n in sorted(by_app.items())},
                  '不可操作': sum(1 for s in kb['steps'] if not s['可操作']),
                  '命例特指·全部': sum(1 for s in kb['steps'] if s['命例特指']),
                  '命例特指·引擎可用': sum(1 for s in eng if s['命例特指']), '命例特指·引擎可用的推理步': sum(1 for s in eng if s['命例特指'] and s['类型'] == '推理步'),
                  '推理步连线': sum(len(s['premises']) * len(s['conclusions']) for s in R),
                  '多前提的推理步': sum(1 for s in R if len(s['premises']) > 1), '带附加条件的推理步': sum(1 for s in R if s.get('附加条件'))}
    lay = collections.Counter((nd[p]['层'] if nd[p]['层'] in MAIN6 else '其余', nd[cn]['层'] if nd[cn]['层'] in MAIN6 else '其余') for s in R for p in s['premises'] for cn in s['conclusions'])
    out['层间连线'] = {f'{k[0]}→{k[1]}': v for k, v in lay.most_common()}
    m = cov['命宫']
    out['覆盖'] = {'盘数': cov['charts'], '走到行为路线成败': m['推理步走到行为路线成败任一层的盘'], '比例': m['比例'], '走到成败': m['推理步走到成败层的盘'], '比例·成败': m['比例·成败'],
                 '各层盘数': m['推理步走到各层的盘数'], '用上的推理步条数': m['用上的推理步条数'], '最长链步数': m['最长链步数'],
                 '经推理步的结点': m['最短推法也要经过推理步的结点'], '两说处数': m['两说处数'], '有两说的盘': m['有两说的盘'], '十二宫': cov['十二宫合计']}
    out['可追溯'] = {k: tr[k] for k in ('charts', 'counts', '推法合格比例', '成稿带出处比例', 'all_ok', 'n_problems')}
    out['主检验'] = {k: rep[k] for k in ('人数', '主检验', '另报·只用定性步', '另报·推理步连线', 'seed', 'n_mc', 'holdout_charts')}
    out['事后诊断'] = {k: diag[k] for k in ('D1可达性', 'D2分组描述', 'D3不剔除', 'D4构成')}
    out['示例盘r30'] = {'覆盖口径': ex['第四版·命宫覆盖口径'], '主线': ex['第四版·命宫主线'], '身宫': ex['shen']}
    # 样例（规则见文件头）
    so = [s for s in R if '所以' in (s.get('连接') or '') and all(nd[n]['层'] in MAIN6 for n in s['premises'] + s['conclusions'])]
    so.sort(key=lambda s: (tnum(s['T']), s['step_id']))
    out['附录·推理步样例'] = [{'step_id': s['step_id'], 'T': s['T'], '前提': '＋'.join(f"{nd[p]['层']}「{nd[p]['名']}」" for p in s['premises']),
                          '结论': '、'.join(f"{nd[n]['层']}「{nd[n]['名']}」" for n in s['conclusions']), '附加条件': s.get('附加条件') or [],
                          '原话摘录': s['原话摘录'], '命例特指': s['命例特指'], '可操作': s['可操作'], '适用': s['适用']} for s in so[:10]]
    out['附录·推理步样例·候选数'] = len(so)
    bad = [x for x in chk['不成立'] if x['类型'] == '推理步']
    bad.sort(key=lambda x: (tnum(x['T']), x['step_id']))
    out['核查不成立例'] = bad[:5]
    big = sorted(norm['nodes'].items(), key=lambda kv: (-len(kv[1]['成员']), kv[0]))[:6]
    out['归一样例'] = [{'结点': k, '层': v['层'], '名': v['名'], '成员': [f"{labels[x]['判断']}（{labels[x]['次数']}）" for x in v['成员']]} for k, v in big]
    # 讲述时段：28 人的时段覆盖 1374 条里多少条、知识库里多少步；计入的人各剔除多少步、判断集多大
    sys.path.insert(0, CH); sys.path.insert(0, os.path.join(W5, '21_倪师断法引擎_20261005'))
    import chain_reproduce_v1 as RP
    persons = [p for p in jl(W5, '21_倪师断法引擎_20261005', 'm3_merged_v1', 'm3_statements_merged_v1.json')['persons'] if p.get('eligible')]
    segs = [g for p in persons for g in p['segments']]
    items = [it for f in sorted(os.listdir(os.path.join(W5, '21_倪师断法引擎_20261005', 'kb_packets_v2'))) if f.startswith('K')
             for it in jl(W5, '21_倪师断法引擎_20261005', 'kb_packets_v2', f, 'batch.json')['倪师条目']]
    inc = [p for p in rep['各人'] if p['计入']]
    rm = sorted(p['剔除的步'] for p in inc)
    gs = sorted(p['倪师判断集结点数'] for p in inc)
    out['讲述时段'] = {'M4人数': len(persons), '条目': len(items), '落在任一人时段内的条目': sum(1 for it in items if RP.in_segs(it, segs)),
                   '知识库步': len(kb['steps']), '落在任一人时段内的步': sum(1 for s in kb['steps'] if RP.in_segs(s, segs)),
                   '计入者剔除的引擎步': {'最少': rm[0], '最多': rm[-1], '中位数': (rm[len(rm) // 2 - 1] + rm[len(rm) // 2]) / 2 if len(rm) % 2 == 0 else rm[len(rm) // 2]},
                   '计入者判断集结点数': {'最少': gs[0], '最多': gs[-1], '合计': sum(gs)},
                   '计入者候选盘数': dict(collections.Counter(p['候选盘数'] for p in inc))}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in out.items() if not k.startswith('附录') and k not in ('核查不成立例', '归一样例', '示例盘r30')}, ensure_ascii=False)[:6000])


if __name__ == '__main__':
    main()
