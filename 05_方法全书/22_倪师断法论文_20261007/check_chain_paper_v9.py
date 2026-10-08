"""论文第十四稿（推理链）核数与核引文 v9：v1—v8 原样保留。v9 由 v8 改来，只加不减：
- 补充材料手写段落的数字（supp_v14）：从结果文件、审计记录、请求文件、账本与程序源码算出应有的写法，逐条核对；纯定义单列；
- 补充材料未覆盖扫描（uncovered_supp）：去掉程序生成的四节后，凡含数字的一句没有被任何要核写法覆盖的，列出；
- 声明里的花费只算三项深化研究的七个批次（内审另记），免得内审批次混进研究花费。
以下为 v8 的说明。
论文第十四稿（推理链）核数与核引文 v8：v1—v7 原样保留。v8 由 v7 改来：
- 正文（--paper）与补充材料（--supp）合在一起核：第十三稿的数字多半搬进了补充材料，写法不变，v7 的要核写法照核；
  已从第十四稿删去或改写的写法，单列在「旧写法未见」，逐条说明去向（REMOVED），不算不合格；
- 附录 A 的样例表改在补充材料 S2 里找；图表编号分正文（图 1–9、表 1–6）与补充材料（S图 1–12、表 S1–S20）各核一遍；
- 另核第十四稿新写的数字（new_v14）：三项深化研究的结果（m4f_analysis_v1、trad_final_v1、m4e_fable_v1、describe_m4f_v1、qs_units_v1、
  api_runs/ledger.json）与正文改写处的旧数字；引文另核表6 的《全书》引文（句或整段的连续片段）；
- 最后扫一遍正文：凡数字所在的一句，没有被任何一条要核写法覆盖的，列出供人工核对（UNCOVERED）。
以下为 v7 的说明。
论文第十三稿（推理链）核数与核引文 v7：v1—v6 原样保留；v7 只按第五轮内审后的改写换掉 10 处要核的写法（事后补算的标注、选中异性一项改名、摘要删去补算的折扣数字、表4 召回率一行的性质）。
以下为 v6 的说明。
论文第十二稿（推理链）核数与核引文 v6：v1—v5 原样保留；v6 按第四轮内审后的改写更新要核的写法，另核 00j 的补充描述（supp_posthoc_v1.json）与附录 E 整张表；插图数字改读 figures_chain_v5。
以下为 v5 的说明。
论文第十一稿（推理链）核数与核引文 v5：只读，不改论文。v1—v4 原样保留；v5 在 v4 全部要核的写法之外，加核三项补充研究（7.7–7.9、摘要、表4、讨论、结论、附录 C、附录 D）的数字，
来源为 23_.../chain_results_v1/m4e_analysis_v1.json、types_final_v1.json、recall_v1.json、m4e_v1/describe_m4e_v1.json、各项存档的审计文件与 design_review_00h/意见.md；插图数字改读 figures_chain_v4。
以下为 v4 的说明。
论文第十稿（推理链）核数与核引文 v4：只读，不改论文。v1—v3 原样保留；v4 只按第三轮内审后的改动换掉几条要核的写法（事后 p 值改为括注、22 人原平均 u）。
以下为 v3 的说明。
论文第九稿（推理链）核数与核引文 v3：只读，不改论文。v1、v2 原样保留；v3 按第九稿的写法重列要核的数，另读 posthoc2_v1.json 与知识库计数。
以下为 v2 的说明。
论文第八稿（推理链）核数与核引文 v2：只读，不改论文。v1 原样保留；v2 按第八稿的写法重列要核的数，并多核几样：
一、引文：「……」（T编号）形式的原话，去掉空白后必须是该条讲稿原话的连续片段（中间有「……」的分段核）。
二、数字：从登记过的结果文件算出应有的写法，逐条核对正文里有这一写法。来源：checks/chain_paper_counts_v1.json、checks/chain_paper_extra_v1.json、
    23_.../chain_results_v1/posthoc_v1.json 与 reproduce_v1.json、reproduce_diag_v1.json、figures_chain_v2/图中数字_chain_v2.json。
三、附录 A：表里每一行的原话摘录与知识库里的那一步完全相同；样例一条不漏。
四、图表：图文件都存在；图号与表号都按出现的先后从 1 连续编号；正文提到的图号都有图。
写出 <out>（文件已存在就停）。用法：python3 check_chain_paper_v2.py --paper <论文.md> --out <新文件>"""
import argparse, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
W5 = os.path.dirname(HERE)
CH = os.path.join(W5, '23_倪师推理链_20261007')
CORPUS = os.path.join(W5, '20_全书倪师全面比对_20261005', 'packets_v1', 'Q01', 'ni_corpus.txt')
norm = lambda s: re.sub(r'\s+', '', s or '')


def pct(x, d=1):
    return f'{x * 100:.{d}f}%'


def jl(*p):
    return json.load(open(os.path.join(*p), encoding='utf-8'))


def extra_v6(md):
    import glob, math
    RS = os.path.join(CH, 'chain_results_v1')
    m = jl(RS, 'm4e_analysis_v1.json'); t = jl(RS, 'types_final_v1.json'); r = jl(RS, 'recall_v1.json'); sp_ = jl(RS, 'supp_posthoc_v1.json')
    desc = jl(CH, 'm4e_v1', 'describe_m4e_v1.json'); kb = jl(CH, 'chain_kb_v1.json')
    f2 = lambda v: f'{v:.2f}'.replace('-', '−')
    dec = lambda p: f'{p:.{-math.floor(math.log10(p)) + 1}f}'
    A = m['arms']; ch, fl, v3 = A['链'], A['平'], A['三']
    assert ch['p_binomial_one_sided'] < .001 and ch['p_rank_sum_one_sided'] < .001 and ch['passed_top1']
    P1, P2 = m['paired']['链组对平铺组'], m['paired']['平铺组对第三版先天组']
    assert P1['只前一组'] == P1['只后一组'] and P1['配对差'] == 0
    s22 = ch['subsets']['陪衬同性别22题']
    L = [x for it in desc['items'].values() for k, x in it['各份'].items() if k[0] == '链']
    tl = sum(x['有相同片段的陈述条数'] for x in L if x['owner_is_true']) / sum(1 for x in L if x['owner_is_true'])
    fl_ = sum(x['有相同片段的陈述条数'] for x in L if not x['owner_is_true']) / sum(1 for x in L if not x['owner_is_true'])
    rm = [x['第四版剔除步数'] for x in desc['items'].values()]
    nkb = sum(1 for x in kb['steps'] if x['可操作'] and x['适用'] == '先天')
    n = m['n_items']; ci = ch['rate_CP95']
    S4, S5, S6 = sp_['S4·陪衬不按性别的题'], sp_['S5·选中最长'], sp_['S6·当事人完全相同的题组']
    w = [
        ('M4e·链', f"28 题认对 {ch['hits']} 题（瞎猜期望 {n // 4} 题），单侧 p < 0.001，认对率 {ch['hits'] / n:.2f}（95% 区间 {ci[0]:.2f}–{ci[1]:.2f}）"),
        ('M4e·判据', '认本人检验事先定的判据（至少认对 12 题）达到' if ch['hits'] >= 12 else '（不合）'),
        ('M4e·名次', f"真论断平均排在第 {ch['mean_rank_of_true']:.2f} 位（瞎猜是 2.5 位），p < 0.001"),
        ('M4e·平铺', f"**平铺组**：同样认对 {fl['hits']} 题" if fl['hits'] == ch['hits'] else '（不合）'),
        ('M4e·三', f"**第三版先天组**：认对 {v3['hits']} 题"),
        ('M4e·配对1', f"链组与平铺组各有 {P1['只前一组']} 题只有一组认出，配对差为 0，95% 区间 {f2(P1['配对差95%区间（条件精确）'][0])} 至 {f2(P1['配对差95%区间（条件精确）'][1])}"),
        ('M4e·配对2', f"平铺组与第三版先天组是 {P2['只前一组']} 题对 {P2['只后一组']} 题，配对差 {f2(P2['配对差'])}，95% 区间 {f2(P2['配对差95%区间（条件精确）'][0])} 至 {f2(P2['配对差95%区间（条件精确）'][1])}"),
        ('M4e·22题', f"陪衬与本人同性别的 {s22['n_items']} 题里，链组仍认对 {s22['hits']} 题（p = {s22['p_binomial_one_sided']:.4f}）"),
        ('M4e·6题', f"另 {len(S4['题'])} 题本人的性别不能从画面确定（候选盘男女都有），论断只取各候选盘都推出的判断，陪衬也没有按性别挑。这 {len(S4['题'])} 题链组认对 {S4['链']} 题（事后补算）"),
        ('M4e·6题口径', '程序数出来的其实是「选中了性别已定的陪衬」，说明不了性别矛盾，不作依据'),
        ('M4e·最长', f"审者选中四份里最长一份的有 {S5['链']['选中最长一份的题数']} 题（瞎猜期望 7 题），其中 {S5['链']['其中恰是真论断']} 题恰是真论断（事后补算）；28 题里真论断本身最长的有 {S5['链']['真论断本身最长的题数']} 题"),
        ('M4e·片段', f"链组真论断 {tl:.2f} 条，陪衬 {fl_:.2f} 条"),
        ('M4e·年龄', f"链组 {ch['subsets']['不带年龄较多的一半']['hits']}/14 对 {ch['subsets']['不带年龄较少的一半']['hits']}/14"),
        ('M4e·题组', f"28 题里有 {sp_['S6·涉及题数']} 题分成 {len(S6)} 组"),
        ('M4e·剔除', f"每题引擎可用的 {nkb} 步里少了 {min(rm)} 至 {max(rm)} 步"),
        ('M4e·审者', f"每题每组一名，共 {3 * n} 名"),
        ('M4e·M4d', f"链组与 M4d 全文组都认出的 {m['与M4d逐题对照（只作描述）']['链组对M4dfull']['都认出']} 题，只 M4d 认出的 {m['与M4d逐题对照（只作描述）']['链组对M4dfull']['只后一组']} 题，只链组认出的 {m['与M4d逐题对照（只作描述）']['链组对M4dfull']['只前一组']} 题"),
        ('M4e·表4', f"| 认本人 | 补充研究（主检验未通过后设计，事先登记） | 四选一，推理链先天论断，28 题，p < 0.05 算通过 | 认对 {ch['hits']} 题（瞎猜 {n // 4} 题），p < 0.001，通过 |"),
        ('M4e·摘要', f"28 题认对 {ch['hits']} 题，认对率 {ch['hits'] / n:.2f}（95% 区间 {ci[0]:.2f}–{ci[1]:.2f}；瞎猜期望 {n // 4} 题，p < 0.001）"),
        ('M4e·摘要另两组', f"同一份论断平铺列出也认对 {fl['hits']} 题，第三版的先天论断认对 {v3['hits']} 题"),
        ('M4e·结论', f"28 题认对 {ch['hits']} 题，认对率 {ch['hits'] / n:.2f}（95% 区间 {ci[0]:.2f}–{ci[1]:.2f}；瞎猜期望 {n // 4} 题）"),
        ('M4e·8.2', f"审者从四份里认出本人 {ch['hits']}/{n}"),
        ('M4e·英文', f"in {ch['hits']} of {n} items (rate {ch['hits'] / n:.2f}, 95% CI {ci[0]:.2f}–{ci[1]:.2f}; chance {n // 4}; one-sided p < 0.001); the same readings listed flat also scored {fl['hits']} and the third-version natal readings {v3['hits']}"),
    ]
    # 附录 E 整张表
    row = lambda name, f: f"| {name} | " + ' | '.join(f(A[a]) for a in '链平三') + ' |'
    sub = lambda key: (lambda a: str(a['subsets'][key]['hits']))
    lt = {a: S5[a] for a in '链平三'}
    E_rows = [
        row('认对题数（28 题；瞎猜期望 7）', lambda a: str(a['hits'])),
        row('二项检验单侧 p', lambda a: dec(a['p_binomial_one_sided'])),
        row('认对率的 95% 区间', lambda a: f"{a['rate_CP95'][0]:.2f}–{a['rate_CP95'][1]:.2f}"),
        row('真论断名次之和（瞎猜期望 70）', lambda a: str(a['rank_sum'])),
        row('名次检验单侧 p', lambda a: dec(a['p_rank_sum_one_sided'])),
        row('真论断平均名次', lambda a: f"{a['mean_rank_of_true']:.2f}"),
        row('陪衬同性别的 22 题，认对', sub('陪衬同性别22题')),
        f"| 陪衬不限性别的 6 题，认对（事后补算） | {S4['链']} | {S4['平']} | {S4['三']} |",
        row('上述 6 题里选中性别已定的陪衬（原想看性别矛盾，本人性别不定，口径不成立）', lambda a: str(a['不同性别陪衬的题里选中异性论断的题数'])),
        row('剔除身份存疑的 24 题，认对', sub('剔除身份存疑')),
        row('只看第 0 档的 8 题，认对', sub('只看第0档')),
        row('剔除陈述含干支或生肖纪年的 24 题，认对', sub('剔除陈述含干支或生肖纪年')),
        row('不带年龄的陈述较多的 14 题，认对', sub('不带年龄较多的一半')),
        row('不带年龄的陈述较少的 14 题，认对', sub('不带年龄较少的一半')),
        '| 选中最长一份的题数（括号内为其中恰是真论断的，事后补算） | ' + ' | '.join(f"{lt[a]['选中最长一份的题数']}（{lt[a]['其中恰是真论断']}）" for a in '链平三') + ' |',
        '| 真论断本身最长的题数 | ' + ' | '.join(str(lt[a]['真论断本身最长的题数']) for a in '链平三') + ' |',
        row('所选字母 A／B／C／D（真论断为 ' + '／'.join(str(m['真论断字母分布'][x]) for x in 'ABCD') + '）', lambda a: '／'.join(str(a['所选字母分布'][x]) for x in 'ABCD')),
        row('四份论断两两 Jaccard 均值（认对的题／没认对的题）', lambda a: f"{a['认对与没认对的题四份论断平均Jaccard']['认对']:.3f}／{a['认对与没认对的题四份论断平均Jaccard']['没认对']:.3f}"),
    ]
    for full, lab in (('full', '与 M4d 全文组逐题：都认出／只本组／只 M4d／都没认出'), ('syn', '与 M4d 综合论断组逐题：同上')):
        cells = []
        for a, g in (('链', '链组'), ('平', '平组'), ('三', '三组')):
            v = m['与M4d逐题对照（只作描述）'][f'{g}对M4d{full}']
            cells.append(f"{v['都认出']}／{v['只前一组']}／{v['只后一组']}／{v['都没认出']}")
        E_rows.append(f'| {lab} | ' + ' | '.join(cells) + ' |')
    for k_, rw in enumerate(E_rows):
        w.append((f'附录E·{k_ + 1}', rw))
    mc = m['paired']
    w.append(('附录E·McNemar', f"链组对平铺组 {mc['链组对平铺组']['附表·精确McNemar双侧p']:.1f}，平铺组对第三版先天组 {mc['平铺组对第三版先天组']['附表·精确McNemar双侧p']:.2f}，链组对第三版先天组 {mc['链组对第三版先天组']['附表·精确McNemar双侧p']:.2f}"))
    w.append(('附录E·题组', '；'.join('、'.join(g) for g in S6)))
    # 推理类型
    D = t['类型分布·全部']; ag = t['一致程度·全部']['类型']; ag2 = t['一致程度·剔除试编与审稿样例']['类型']
    for ty in ['取象', '术数机理', '类属展开', '性情因果', '处境常理']:
        v = D[ty]; lo, hi = v['95%（按T成团重抽）']
        w.append((f'类型·表6·{ty}', f"| {v['条数']} | {v['条数'] / D['n'] * 100:.1f}% | {lo * 100:.1f}–{hi * 100:.1f}% |"))
    lo, hi = D['其他']['95%（按T成团重抽）']
    assert '其他' in t['解读规则']['特定一致率<0.5的类（只报区间）']
    w.append(('类型·表6·其他只报区间', f"| — | 其他 | 五问都答「否」 | — | — | {lo * 100:.1f}–{hi * 100:.1f}% |"))
    w.append(('类型·其他条数', f"最后归进这一类的 {D['其他']['条数']} 步都是两人有分歧、由裁定定下的" if t['混淆矩阵（行=甲，列=乙）']['其他']['其他'] == 0 else '（不合）'))
    sp = [v for k, v in t['每类特定一致率'].items() if k != '其他']
    pq = t['五问答是的比例']; fA, fB, fC = t['三个标记']['标A'], t['标B×知识库命例特指']['True'], t['三个标记']['标C']
    inf = [x for x in kb['steps'] if x['类型'] == '推理步']
    withx = sum(1 for x in inf if x['附加条件']); case = sum(1 for x in inf if x['命例特指'])
    g = lambda k, ty: t[k][ty]['条数'] / t[k]['n'] * 100
    pilot = jl(CH, 'types_v1', 'pilot_P1_result_v1.json')
    S1, S2, S3 = sp_['S1·标C按类型'], sp_['S2·标A×类型'], sp_['S3·标B与命例特指不一致']
    noX = S2['无附加条件']; nnoX = sum(noX.values())
    w += [
        ('类型·α', f"原始一致率 {ag['原始一致率']:.2f}，α = {ag['alpha']:.2f}（95% 区间 {ag['alpha_95%（按T成团重抽）'][0]:.2f}–{ag['alpha_95%（按T成团重抽）'][1]:.2f}）"),
        ('类型·α剔除', f"α 为 {ag2['alpha']:.2f}"),
        ('类型·特定', f"都在 {math.floor(min(sp) * 100) / 100:.2f} 以上"),
        ('类型·裁定', f"由裁定者定下的共 {t['裁定改动']['两人分歧被定']} 个问或标记"),
        ('类型·试编', f"类型的一致率就有 {pilot['类型原始一致率']:.2f}" if pilot['达到停止规则'] else '（不合）'),
        ('类型·先天', f"先天的 {t['类型分布·先天']['n']} 步：术数机理 {g('类型分布·先天', '术数机理'):.1f}%，类属展开 {g('类型分布·先天', '类属展开'):.1f}%"),
        ('类型·运限', f"运限的 {t['类型分布·运限']['n']} 步：术数机理 {g('类型分布·运限', '术数机理'):.1f}%"),
        ('类型·通则命例', f"通则的 {t['类型分布·通则']['n']} 步与命例特指的 {t['类型分布·命例特指']['n']} 步"),
        ('类型·取象对', f"取象 {g('类型分布·通则', '取象'):.1f}% 对 {g('类型分布·命例特指', '取象'):.1f}%"),
        ('类型·性情对', f"性情因果 {g('类型分布·通则', '性情因果'):.1f}% 对 {g('类型分布·命例特指', '性情因果'):.1f}%"),
        ('类型·处境对', f"处境常理 {g('类型分布·通则', '处境常理'):.1f}% 对 {g('类型分布·命例特指', '处境常理'):.1f}%"),
        ('类型·五问', '，'.join(f"问{i} {pq[f'问{i}'] * 100:.1f}%" for i in range(1, 6))),
        ('类型·标A', f"带附加条件的 {withx} 步里，{fA['主要靠附加条件']} 步主要靠附加条件推出，其中 {S2['主要靠附加条件']['术数机理']} 步归为术数机理"),
        ('类型·无附加', f"只看不带附加条件的 {nnoX} 步（事后补算），" + '，'.join(f"{ty} {noX.get(ty, 0) / nnoX * 100:.1f}%" for ty in ['类属展开', '术数机理', '处境常理', '性情因果', '取象'])),
        ('类型·标B', f"知识库标为命例特指的 {case} 步，归类者认为其中 {fB['仍成立']} 步离开那个人也说得通"),
        ('类型·标B不一', f"{S3['命例特指但原话不是在讲具体的人']} 步知识库标为命例特指，归类者却判原话不是在讲具体的人；{S3['通则但在讲具体的人']} 步知识库标为通则"),
        ('类型·标C', f"{fC['是']} 步（{fC['是'] / len(inf) * 100:.1f}%）"),
        ('类型·标C类属', f"这 {fC['是']} 步里 {S1['类属展开']} 步是类属展开"),
        ('类型·摘要', f"占 {round(D['术数机理']['条数'] / D['n'] * 100)}%，把一类人展开成成员与特征的占 {round(D['类属展开']['条数'] / D['n'] * 100)}%，原话明说借象说理的只占 {round(D['取象']['条数'] / D['n'] * 100)}%。两名归类者的一致程度 α = {ag['alpha']:.2f}"),
        ('类型·8.1', f"术数机理（{round(D['术数机理']['条数'] / D['n'] * 100)}%）与类属展开（{round(D['类属展开']['条数'] / D['n'] * 100)}%）"),
        ('类型·8.1折扣', f"术数机理 {D['术数机理']['条数']} 步里有 {S2['主要靠附加条件']['术数机理']} 步主要靠附加的盘面条件推出，这类步按说明是照附加条件那一环作答的，归进术数机理在相当程度上由归类规则决定；类属展开 {D['类属展开']['条数']} 步里有 {S1['类属展开']} 步，归类者认为前提和结论意思几乎相同，或原话其实没有说由前提推出"),
        ('类型·8.1无附加', f"只看不带附加条件的 {nnoX} 步，类属展开最多（{round(noX['类属展开'] / nnoX * 100)}%），其次是术数机理（{round(noX['术数机理'] / nnoX * 100)}%）与处境常理（{round(noX['处境常理'] / nnoX * 100)}%）"),
        ('类型·8.1运限', f"运限的推理步里术数机理占 {round(g('类型分布·运限', '术数机理'))}%，比先天的 {round(g('类型分布·先天', '术数机理'))}% 多"),
        ('类型·8.1命例', f"命例特指的 {case} 步，归类者认为其中 {fB['仍成立']} 步"),
        ('类型·8.3不一', f"{S3['命例特指但原话不是在讲具体的人']} 步命例特指的，归类者判原话不是在讲具体的人；{S3['通则但在讲具体的人']} 步通则的"),
        ('类型·T96依据', f"「{sp_['S9·T96-c2问4依据']['甲']}」（T96）" if sp_['S9·T96-c2问4依据']['甲'] == sp_['S9·T96-c2问4依据']['乙'] else '（不合）'),
    ]
    # 召回率
    R = r['召回率']; ri, rq, ri2, rq2 = R['推理步·明确漏'], R['定性步·明确漏'], R['推理步·明确漏加两可'], R['定性步·明确漏加两可']
    S = r['strata_sizes']; nh = r['计入的原话条数']; J = r['裁定档次分布（主张条数）']; Lc = r['链长·留出盘命宫最长链']; go = r['链长·漏步去向']; ad = r['链长·加进副本的步']
    cf, cc = r['Chapman·找漏者']['推理步'], r['Chapman·对照·原抽取甲乙']['推理步']
    S7, S8 = sp_['S7·两可的推理步主张按连接'], sp_['S8·明确漏的推理步去向']
    iv = lambda v: f"{v['95%区间（Gamma后验合成）'][0]:.2f}–{v['95%区间（Gamma后验合成）'][1]:.2f}"
    assert Lc['原知识库'] == Lc['加进漏步后'] and Lc['变长的盘数'] == 0 and r['链长·判定'].startswith('样本里确认的漏步不改变')
    w += [
        ('召回·分层', f"含推理步的 {S['S1']} 条（核查之后；定稿时为 291 条），只有起步的 {S['S2']} 条，一步都没有的 {S['S3']} 条"),
        ('召回·抽样', f"依次随机抽 {nh['S1']}、{nh['S2']}、{nh['S3']} 条，共 {sum(nh.values())} 条，分成 12 包"),
        ('召回·主张', f"共报 {sum(J.values())} 条主张，裁定为明确漏 {J['明确漏']} 条、两可 {J['两可']} 条、不合规矩 {J['不合规矩']} 条、已有 {J['已有']} 条"),
        ('召回·确认', f"明确漏掉的推理步 {sum(ri['各层确认漏步数'].values())} 条、起步 {sum(rq['各层确认漏步数'].values())} 条"),
        ('召回·推理步', f"推理步的召回率估计为 {ri['召回率']:.2f}（95% 区间 {iv(ri)}），至少 {ri['单侧95%下界']:.2f}"),
        ('召回·起步', f"起步的召回率为 {rq['召回率']:.2f}（{iv(rq)}）"),
        ('召回·两可', f"推理步召回率降到 {ri2['召回率']:.2f}（{iv(ri2)}），起步为 {rq2['召回率']:.2f}"),
        ('召回·两可连接', f"裁定为两可的推理步主张（合并两人之前）{sum(S7.values())} 条里，找漏者写的连接是「紧接承上」的 {S7['紧接承上']} 条，其余 {S7['其他连接']} 条有承接词"),
        ('召回·表4', f"| 召回率 | 补充研究（事先定解读线：单侧下界 ≥ 0.8） | 300 条原话分层抽样，两人找漏、一人裁定 | 只算明确漏：推理步 {ri['召回率']:.2f}（95% 区间 {iv(ri)}，至少 {ri['单侧95%下界']:.2f}），起步 {rq['召回率']:.2f}；算上两可：推理步 {ri2['召回率']:.2f} |"),
        ('召回·8.3', f"推理步召回率就在 {ri2['召回率']:.2f} 与 {ri['召回率']:.2f} 之间"),
        ('召回·摘要下界', f"只算明确漏掉的，推理步约九成抽到了（至少 {ri['单侧95%下界']:.2f}）"),
        ('召回·英文', f"(one-sided lower bound {ri['单侧95%下界']:.2f})"),
        ('召回·接进', f"{sum(go.values())} 条明确漏掉的步里，能照知识库的写法接进去的有 {go['加进副本']} 条，其中推理步只有 {ad['推理步']} 条、起步 {ad['定性步']} 条"),
        ('召回·推理步去向', f"{sum(S8.values())} 条明确漏掉的推理步里，有 {sum(S8.values()) - S8['加进副本']} 条没能接进去：{S8['不是先天']} 条不是先天，{S8['判断映射不到唯一结点']} 条的判断对不上唯一的结点"),
        ('召回·8.1两条', f"但其中推理步只有 {ad['推理步']} 条"),
        ('召回·链长', f"中位数 {Lc['加进漏步后']['中位数']:g} 步，4 步以上占 {Lc['加进漏步后']['4步以上比例'] * 100:.1f}%"),
        ('召回·Chapman', f"一人 {cf['n1']} 条、一人 {cf['n2']} 条，两人都找到 {cf['m']} 条），据此推算「两人都漏」的是 {cf['两人都漏的估计']:g} 条"),
        ('召回·对照', f"「两人都漏」的推理步也只有 {cc['两人都漏的估计']:.1f} 条"),
        ('召回·M', f"推到全部原话约 {round(ri['M估计'])} 条"),
        ('召回·敏感性', f"有 {r['敏感性·推理步漏步与核查不成立的步结论相同']} 条明确漏的推理步，与本条原话核查判不成立的步结论相同"),
    ]
    au = lambda *p: len(glob.glob(os.path.join(CH, *p, '*.audit.json')))
    cnt = [au('m4e_v1', f'judge_returns_{a_}') for a_ in '链平三'], au('types_v1', 'pilot_returns'), au('types_v1', 'formal_returns'), au('types_v1', 'adj_returns'), au('recall_v1', 'finder_returns'), au('recall_v1', 'adj_returns')
    tot = sum(cnt[0]) + sum(cnt[1:])
    w.append(('附录C·份数', f"审者 {sum(cnt[0])} 份、试编 {cnt[1]} 份、归类 {cnt[2]} 份（含一份不合格及其重跑）、归类裁定 {cnt[3]} 份、找漏 {cnt[4]} 份、找漏裁定 {cnt[5]} 份，共 {tot} 份"))
    rv = open(os.path.join(CH, 'design_review_00h', '意见.md'), encoding='utf-8').read()
    secs = [x for x in re.split(r'^### ', rv, flags=re.M)[1:] if re.match(r'(甲|乙|丙|共)-\d+', x)]
    head9 = len(re.findall(r'^[0-9]+[.]', rv.split('## 先列最要紧的几条')[1].split('---')[0], flags=re.M))
    w.append(('审稿意见条数', f"审稿意见共 {len(secs)} 条，其中 {sum(1 for x in secs if '必须改' in x)} 条全部或部分标为必须改，最要紧的 {head9} 条列在开头"))
    return w


REMOVED = {
    '摘要·规模': '第十四稿摘要改写，只留「1685 步、1028 个判断结点」（v14·摘要规模）',
    '摘要·胜过': '第十四稿摘要只报 p = 0.066（v14·摘要主检验）',
    'Q3过半': '第十三稿摘要的「过半」一句删去；正文 7.2 改写为「84 个连一步以它为结论的都没有」（v14·诊断）',
    '8.3不可操作': '第十四稿 8.4 改写（v14·局限两类步）',
    '非先天推理步': '第十四稿 8.4「只做先天」一句不再列条数',
    'M4e·表4': '检验总表改写为两行认本人（v14·表3认本人一、二）',
    'M4e·摘要': '第十四稿摘要改写（v14·摘要M4e）',
    'M4e·摘要另两组': '另两组的认对数只在补充材料 S7（v13 原文）与正文 7.3（v14·M4e三组）',
    'M4e·结论': '第十四稿结论改写，不再列 M4e 的区间',
    'M4e·英文': '英文摘要改写（v14·英文M4e）',
    '类型·摘要': '旧五类的结果移到补充材料 S9；摘要改报新框架（v14·摘要推理方式）',
    '类型·8.1': '第十三稿 8.1 的旧五类讨论删去，结果见补充材料 S9',
    '类型·8.1折扣': '同上',
    '类型·8.1无附加': '同上',
    '类型·8.1运限': '同上',
    '类型·8.3不一': '第十三稿 8.3 的这一条局限删去（标记出入见补充材料 S9）',
    '召回·表4': '检验总表改写（v14·表3召回）',
    '召回·8.3': '第十四稿 8.4 改写为「推理步召回率在 0.68 与 0.90 之间」（v14·局限召回）',
    '召回·英文': '英文摘要改写为「lower bound 0.83」（v14·英文召回）',
    '召回·8.1两条': '第十四稿 7.5 改写为「（推理步只有 2 条）」（v14·召回接回）',
}


def new_v14(main_md, supp_md):
    import statistics
    RS = os.path.join(CH, 'chain_results_v1')
    m = jl(RS, 'm4f_analysis_v1.json'); t = jl(RS, 'trad_final_v1.json'); fb = jl(RS, 'm4e_fable_v1.json'); e = jl(RS, 'm4e_analysis_v1.json')
    desc = jl(CH, 'm4f_v1', 'describe_m4f_v1.json'); key = jl(CH, 'm4f_v1', 'key_m4f_v1.json'); qu = jl(CH, 'trad_v1', 'qs_units_v1.json')['统计']
    led = jl(CH, 'api_runs', 'ledger.json')['runs']; rec = jl(RS, 'recall_v1.json')
    c = jl(HERE, 'checks', 'chain_paper_counts_v1.json'); B = c['知识库']; M = c['主检验']
    f2 = lambda v: f'{v:.2f}'
    pc = lambda v: f'{v * 100:.1f}%'
    P = lambda v: 'p < 0.001' if v < 0.001 else f'p = {v:.3f}'.rstrip('0') if False else ('p < 0.001' if v < 0.001 else f'p = {v:.3f}')
    G = m['组']; g, gs, gl = G['正'], G['换陈述'], G['换论断']
    A, Bc = m['对比']['对比甲：正题−换陈述']['按比例'], m['对比']['对比乙：正题−换论断']['按比例']
    D = t['分布']; Ag = t['一致程度·全部']
    qi, ri, wi = D['起步'], D['推理步'], D['全书']
    dq = lambda d, k: d['断事里各类'][k]
    cmp1, cmp2 = t['对照']['起步对全书'], t['对照']['起步对推理步']
    o2 = t['与旧框架（再编码稳定性，不作效度证据）']
    ct = o2['交叉表（行=旧，列=新）']
    rs = lambda k: sum(ct[k].values())
    sub = m['子集']
    D4 = desc['items'].values()
    added = [len(x['内容核对并入的T']) for x in D4 if x['内容核对并入的T']]
    cost = sum(led['api_runs/' + k]['花费美元'] for _, k, _ in STUDY_RUNS)
    from decimal import Decimal, ROUND_HALF_UP
    tri = lambda v: str((Decimal(str(v)) * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
    ciq = lambda v: f'{tri(v[0])}–{tri(v[1])}'
    def frac(d, k):
        # 比例用条数现算（避开结果文件四位小数的二次舍入）
        if k == '定名':
            return Decimal(d['问A·定名比例']['条数']) / Decimal(d['n'])
        if k == '象名':
            return Decimal(d['定名里象名比例']['条数']) / Decimal(d['定名里象名比例']['n'])
        if k == '明说':
            return Decimal(d['断事里问D明说道理']['是']) / Decimal(d['断事条数'])
        return Decimal(d['断事里各类'][k]['条数']) / Decimal(d['断事条数'])
    trc = lambda d, k: str((frac(d, k) * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
    w = [
        ('摘要规模', f"1685 步、1028 个判断结点，每一步附原话"),
        ('摘要主检验', f"24 人的结果是单侧 p = {M['主检验']['p_单侧']:.3f}"),
        ('摘要M4e', f"28 题认对 {e['arms']['链']['hits']} 题（瞎猜 7 题，p < 0.001）"),
        ('摘要M4f', f"审者挑中本人的比例为 {f2(g['认对率'])}（{g['选中焦点的卷数X']}/{g['有效卷数']}，95% 区间 {f2(g['认对率95%区间'][0])}–{f2(g['认对率95%区间'][1])}；瞎猜 0.25；p < 0.001）"),
        ('摘要换陈述', f"陈述换成别人的时候为 {f2(gs['认对率'])}（p = {gs['P(X≥实测)']:.2f}），两者之差 {f2(A['平均差'])}（95% 区间 {f2(A['平均差95%区间'][0])}–{f2(A['平均差95%区间'][1])}，p = {A['符号翻转单尾p(正>对照)']:.3f}）"),
        ('摘要换论断', f"差 {f2(Bc['平均差'])}（p = {Bc['符号翻转单尾p(正>对照)']:.3f}）"),
        ('摘要推理方式', f"725 条断语归类（一致程度 α 为 {Ag['起步']['类型']['alpha']:.2f}–{Ag['全书']['类型']['alpha']:.2f}）"),
        ('摘要象与道理', f"明说借象（{tri(dq(qi, '象')['比例'])}% 对 {tri(dq(wi, '象')['比例'])}%）与明说道理（{tri(qi['断事里问D明说道理']['比例'])}% 对 {tri(wi['断事里问D明说道理']['比例'])}%）"),
        ('摘要推理步', f"人情事理（{round(dq(ri, '情')['比例'] * 100)}%）与类别（{round(dq(ri, '义')['比例'] * 100)}%）"),
        ('摘要召回', f"推理步约九成抽到了（至少 {rec['召回率']['推理步·明确漏']['单侧95%下界']:.2f}）"),
        ('英文M4e', f"in {e['arms']['链']['hits']} of 28 items with real-person foils (p < 0.001) and in {g['选中焦点的卷数X']} of {g['有效卷数']} judgments ({f2(g['认对率'])}, 95% CI {f2(g['认对率95%区间'][0])}–{f2(g['认对率95%区间'][1])}; chance 0.25; p < 0.001)"),
        ('英文换陈述', f"the rate was {f2(gs['认对率'])} when the description belonged to someone else (difference {f2(A['平均差'])}, p = {A['符号翻转单尾p(正>对照)']:.3f})"),
        ('英文换论断', f"(difference {f2(Bc['平均差'])}, p = {Bc['符号翻转单尾p(正>对照)']:.3f})"),
        ('英文推理方式', f"725 judgments from the classical *Zi Wei Dou Shu Quanshu* with categories borrowed from the *Yi* commentaries (α {Ag['起步']['类型']['alpha']:.2f}–{Ag['全书']['类型']['alpha']:.2f})"),
        ('英文象与道理', f"give images ({tri(dq(qi, '象')['比例'])}% vs {tri(dq(wi, '象')['比例'])}%) and reasons ({tri(qi['断事里问D明说道理']['比例'])}% vs {tri(wi['断事里问D明说道理']['比例'])}%)"),
        ('英文推理步', f"human affairs ({round(dq(ri, '情')['比例'] * 100)}%) and categories ({round(dq(ri, '义')['比例'] * 100)}%)"),
        ('英文召回', f"(lower bound {rec['召回率']['推理步·明确漏']['单侧95%下界']:.2f})"),
        ('三·全书', '把古籍原文切成 3025 个单元，其中 2990 句属古籍原文层'),
        ('表3认本人一', f"| 认本人（第一次） | 补充研究 | 28 题认对 {e['arms']['链']['hits']} 题（瞎猜 7 题），p < 0.001；换审者模型重审 {fb['arms']['链']['hits']}/28 |"),
        ('表3认本人二', f"| 认本人（第二次） | 补充研究 | 正题 {g['选中焦点的卷数X']}/{g['有效卷数']}（{f2(g['认对率'])}；瞎猜 0.25），p < 0.001；比陈述换成别人时高 {f2(A['平均差'])}，p = {A['符号翻转单尾p(正>对照)']:.3f} |"),
        ('表3推理方式', f"| 推理方式 | 补充研究 | 起步 {qi['n']}、推理步 {ri['n']}、《全书》断语 {wi['n']} 条；类型 α {Ag['起步']['类型']['alpha']:.2f}–{Ag['全书']['类型']['alpha']:.2f} |"),
        ('表3召回', f"| 召回率 | 补充研究 | 只算明确漏：推理步 {rec['召回率']['推理步·明确漏']['召回率']:.2f}（95% 区间 {rec['召回率']['推理步·明确漏']['95%区间（Gamma后验合成）'][0]:.2f}–{rec['召回率']['推理步·明确漏']['95%区间（Gamma后验合成）'][1]:.2f}，至少 {rec['召回率']['推理步·明确漏']['单侧95%下界']:.2f}） |"),
        ('M4e三组', f"推理链写法的论断 28 题认对 {e['arms']['链']['hits']} 题（瞎猜期望 7 题）"),
        ('M4e平铺', f"同一份推理结果平铺列出，也认对 {e['arms']['平']['hits']} 题"),
        ('M4e三版', f"前作第三版的先天论断认对 {e['arms']['三']['hits']} 题"),
        ('M4e重审', f"链组 {fb['arms']['链']['hits']}/28，平铺组 {fb['arms']['平']['hits']}/28，第三版先天组 {fb['arms']['三']['hits']}/28"),
        ('M4e重审差', f"三组的差在 {min(fb['与原M4e逐题配对'][k]['配对差'] for k in fb['与原M4e逐题配对']):.2f} 至 {max(fb['与原M4e逐题配对'][k]['配对差'] for k in fb['与原M4e逐题配对']):.2f} 之间".replace('-', '−')),
        ('M4f陈述', f"不足 6 条的 3 题用全部，共 {sum(x['陈述条数'] for x in D4)} 条"),
        ('M4f补剔', f"{len(added)} 题各补剔了 {min(added)}–{max(added)} 条"),
        ('M4f审者', f"每题每组 {key['judges_per_arm']} 名，共 {len(key['packets'])} 名"),
        ('M4f正题', f"84 卷里 {g['选中焦点的卷数X']} 卷选中本人论断（{f2(g['认对率'])}，95% 区间 {f2(g['认对率95%区间'][0])}–{f2(g['认对率95%区间'][1])}；瞎猜 0.25），单侧 p < 0.001"),
        ('M4f多数票', f"28 题认对 {g['多数票认对题数']} 题"),
        ('M4f换陈述', f"{gs['选中焦点的卷数X']}/84（{f2(gs['认对率'])}，区间 {f2(gs['认对率95%区间'][0])}–{f2(gs['认对率95%区间'][1])}），高于瞎猜但不显著（单侧 p = {gs['P(X≥实测)']:.2f}）"),
        ('M4f换论断', f"{gl['选中焦点的卷数X']}/84（{f2(gl['认对率'])}，区间 {f2(gl['认对率95%区间'][0])}–{f2(gl['认对率95%区间'][1])}），单侧 p = {gl['P(X≥实测)']:.3f}"),
        ('M4f对比甲', f"平均差 {f2(A['平均差'])}（区间 {f2(A['平均差95%区间'][0])}–{f2(A['平均差95%区间'][1])}），p = {A['符号翻转单尾p(正>对照)']:.3f}"),
        ('M4f对比乙', f"平均差 {f2(Bc['平均差'])}（区间 −{abs(Bc['平均差95%区间'][0]):.2f} 至 {f2(Bc['平均差95%区间'][1])}），p = {Bc['符号翻转单尾p(正>对照)']:.3f}"),
        ('M4f无效', f"{len(key['packets'])} 卷没有一份无效" if not m['无效卷'] else '（不合）'),
        ('M4f解读乙', f"没有达到显著（p = {Bc['符号翻转单尾p(正>对照)']:.3f}）"),
        ('M4f解读论断组', f"换论断组接近显著（p = {gl['P(X≥实测)']:.3f}）"),
        ('M4f子集K', f"陈述满 6 条（三组都满足的 {sub['陈述满K条']['对比甲（三组都满足的题）']['题数']} 题）：p = {sub['陈述满K条']['对比甲（三组都满足的题）']['符号翻转单尾p(正>对照)']:.3f}"),
        ('M4f子集存疑', f"去掉涉及身份存疑者（{sub['去掉涉及身份存疑者']['对比甲（三组都满足的题）']['题数']} 题）：p = {sub['去掉涉及身份存疑者']['对比甲（三组都满足的题）']['符号翻转单尾p(正>对照)']:.2f}"),
        ('M4f子集主检验', '主检验在六种事先定的子集里都显著' if all(sub[k]['正']['P(X≥实测)'] < .05 for k in sub) and len(sub) == 6 else '（不合）'),
        ('M4f两次', f"第一次 {e['arms']['链']['hits']}/28；第二次正题 {f2(g['认对率'])}"),
        ('推理方式对象', f"倪海厦全部 1685 步（起步 {qi['n']}、推理步 {ri['n']}）"),
        ('切分', f"切法相同的 {qu['相同']} 句照用，不同的 {qu['裁定']} 句由第三人定稿，共切出 {qu['断语']} 条断语；另有 {qu['无断语句']} 句没有断语"),
        ('类型α', f"起步 {Ag['起步']['类型']['alpha']:.2f}，推理步 {Ag['推理步']['类型']['alpha']:.2f}，《全书》{Ag['全书']['类型']['alpha']:.2f}"),
        ('问Aα', f"「定名还是断事」的 α 在 {min(Ag[g_]['问A']['alpha'] for g_ in ('起步', '推理步', '全书')):.2f} 至 {max(Ag[g_]['问A']['alpha'] for g_ in ('起步', '推理步', '全书')):.2f} 之间"),
        ('其余α', f"五种依据与「明说道理」的 α 在 {min(Ag[g_][k]['alpha'] for g_ in ('起步', '推理步', '全书') for k in ('C1', 'C2', 'C3', 'C4', 'C5', '问D')):.2f} 至 {max(Ag[g_][k]['alpha'] for g_ in ('起步', '推理步', '全书') for k in ('C1', 'C2', 'C3', 'C4', 'C5', '问D')):.2f} 之间"),
        ('特定一致率', '每类的特定一致率都不低于 0.50' if min(v for g_ in ('起步', '推理步', '全书') for v in Ag[g_]['类型']['每类特定一致率'].values() if v is not None) >= .5 else '（不合）'),
        ('表5条数', f"| 条数 | {qi['n']} | {ri['n']} | {wi['n']} |"),
        ('表5定名', f"| 定名 | {trc(qi, '定名')}%（{ciq(qi['问A·定名比例']['95%'])}） | {trc(ri, '定名')}%（{ciq(ri['问A·定名比例']['95%'])}） | {trc(wi, '定名')}%（{ciq(wi['问A·定名比例']['95%'])}） |"),
        ('表5象名', f"| 定名里的象名 | {trc(qi, '象名')}%（{ciq(qi['定名里象名比例']['95%'])}） | {ri['定名里象名比例']['条数']}/{ri['定名里象名比例']['n']} | {trc(wi, '象名')}%（{ciq(wi['定名里象名比例']['95%'])}） |"),
    ]
    for k, lab in (('位', '位'), ('直断', '直断'), ('象', '象'), ('时', '时'), ('义', '义'), ('情', '情')):
        w.append((f'表5{k}', f"| 断事里：{lab} | " + ' | '.join(f"{trc(d, k)}%（{ciq(dq(d, k)['95%'])}）" for d in (qi, ri, wi)) + ' |'))
    w.append(('表5明说', '| 断事里：明说道理 | ' + ' | '.join(f"{trc(d, '明说')}%（{ciq(d['断事里问D明说道理']['95%'])}）".replace('（0.0–', '（0–') for d in (qi, ri, wi)) + ' |'))
    w += [
        ('对照象', f"{tri(dq(qi, '象')['比例'])}% 对 {tri(dq(wi, '象')['比例'])}%，差 {tri(cmp1['断事里象比例']['差'])} 个百分点（区间 {ciq(cmp1['断事里象比例']['差的95%'])}）"),
        ('对照道理', f"{tri(qi['断事里问D明说道理']['比例'])}% 对 {tri(wi['断事里问D明说道理']['比例'])}%，差 {tri(cmp1['断事里问D比例']['差'])} 个百分点（区间 {ciq(cmp1['断事里问D比例']['差的95%'])}）"),
        ('对照其余含0', '两组之差的 95% 区间都包含 0' if all(cmp1[k]['差的95%'][0] < 0 < cmp1[k]['差的95%'][1] for k in ('定名比例', '断事里位比例', '断事里时比例', '断事里义比例', '断事里情比例', '断事里直断比例')) else '（不合）'),
        ('推理步情义', f"情占 {trc(ri, '情')}%，义占 {trc(ri, '义')}%，直断只有 {trc(ri, '直断')}%"),
        ('推理步位', f"位降到 {tri(dq(ri, '位')['比例'])}%，比起步低 {tri(cmp2['断事里位比例']['差'])} 个百分点（区间 {ciq(cmp2['断事里位比例']['差的95%'])}）"),
        ('推理步道理', f"明说道理 {tri(ri['断事里问D明说道理']['比例'])}%，比起步高 {tri(-cmp2['断事里问D比例']['差'])} 个百分点（区间 {tri(-cmp2['断事里问D比例']['差的95%'][1])}–{tri(-cmp2['断事里问D比例']['差的95%'][0])}）"),
        ('运限起步', f"时占 {tri(D['起步·运限']['断事里各类']['时']['比例'])}%，直断只有 {tri(D['起步·运限']['断事里各类']['直断']['比例'])}%；先天的起步直断占 {tri(D['起步·先天']['断事里各类']['直断']['比例'])}%"),
        ('以此类推', f"各只有 {len(t['以此类推类说法']['起步'])}、{len(t['以此类推类说法']['推理步'])}、{len(t['以此类推类说法']['全书'])} 条"),
        ('新旧一致', f"新旧一致率 {o2['按对应的一致率']:.2f}"), ('相容率', f"相容率 {o2['相容率']:.2f}"),
        ('旧取象', f"旧「取象」{rs('取象')} 步，{ct['取象'].get('象', 0)} 步新归象"),
        ('旧类属', f"旧「类属展开」{rs('类属展开')} 步，{ct['类属展开'].get('义', 0)} 步新归义"),
        ('旧性情处境', f"旧「性情因果」{rs('性情因果')} 步里 {ct['性情因果'].get('情', 0)} 步、「处境常理」{rs('处境常理')} 步里 {ct['处境常理'].get('情', 0)} 步"),
        ('旧术数', f"旧「术数机理」{rs('术数机理')} 步最分散：位 {ct['术数机理'].get('位', 0)}、情 {ct['术数机理'].get('情', 0)}、象 {ct['术数机理'].get('象', 0)}、时 {ct['术数机理'].get('时', 0)}、义 {ct['术数机理'].get('义', 0)}"),
        ('讨论象', f"明说借象的占一成多，《全书》不到 2%；进一步讲出为什么的，他占 {tri(qi['断事里问D明说道理']['比例'])}%，《全书》只有 {tri(wi['断事里问D明说道理']['比例'])}%" if .1 < dq(qi, '象')['比例'] < .2 and dq(wi, '象')['比例'] < .02 else '（不合）'),
        ('讨论推理步', '近四成凭人情事理' if .35 < dq(ri, '情')['比例'] < .4 and .2 < dq(ri, '义')['比例'] < .3 else '（不合）'),
        ('讨论换论断', f"换论断组 p = {gl['P(X≥实测)']:.3f}"),
        ('讨论重审', f"三组认对 {min(fb['arms'][k]['hits'] for k in fb['arms'])} 至 {max(fb['arms'][k]['hits'] for k in fb['arms'])} 题"),
        ('局限召回', f"推理步召回率在 {rec['召回率']['推理步·明确漏加两可']['召回率']:.2f} 与 {rec['召回率']['推理步·明确漏']['召回率']:.2f} 之间"),
        ('局限两类步', f"条件是「其他」（原话没说出盘面）的 {B['不可操作']} 步，以及先天可操作里条件含「格」的 28 步"),
        ('召回接回', '（推理步只有 2 条）'),
        ('结论M4f', f"挑中本人的比例为 {f2(g['认对率'])}（瞎猜 0.25）"),
        ('声明花费', f"花费约 {round(cost)} 美元"),
    ]
    return w


def quotes_v14(text):
    """表6 的《全书》引文：去掉省略号分段后，每段都要是所引那句或整段的连续片段。"""
    Q = {u['编号']: u for u in jl(CH, 'trad_v1', 'qs_units_v1.json')['条目']}
    allq = ''.join(u['所在整段'] for u in Q.values())
    out = []
    sec = text.split('**表6　')[1].split('\n\n')[1] if '**表6　' in text else ''
    for row in sec.split('\n'):
        if not row.startswith('|') or row.startswith('|---') or row.startswith('| 类目'):
            continue
        cell = row.strip('|').split('|')[3]
        for q in re.findall(r'「([^「」]+)」', cell):
            parts = [p_ for p_ in q.split('……') if p_]
            out.append({'T': '全书', '引文': q, 'ok': all(p_ in allq for p_ in parts)})
    return out


def uncovered(main_md, phrases):
    """正文里含数字的句子：先把全文里已核过的写法换掉（长的先换，跨句的也算），再去掉 T 编号、年份、图表与节号、
    检验代号（M4e、M4f）、盘号 r30、视频号、SHA-256 与语料提交号；若仍有数字，就列出。"""
    body = main_md.split('## 参考文献')[0]
    body = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', body)
    for ph in sorted(set(phrases), key=len, reverse=True):
        body = body.replace(ph, '〔核〕')
    out = []
    for sent in re.split(r'(?<=[。；！？])|\n', body):
        s_ = sent.strip()
        if not s_ or not re.search(r'\d', s_):
            continue
        rest = s_
        rest = re.sub(r'「[^「」]*」（T\d+[^）]*）', ' ', rest)
        rest = re.sub(r'T\d+(-c\d+)?', ' ', rest)
        rest = re.sub(r'(图|表|S图|表S|S)\s?\d+', ' ', rest)
        rest = re.sub(r'M4[a-z]?|r30|BV1KJsLekEfA|SHA-256|c900061', ' ', rest)
        rest = re.sub(r'(?<![\d.])[1-9]\.\d(?![\d%])', ' ', rest)
        rest = re.sub(r'(19|20)\d\d', ' ', rest)
        rest = re.sub(r'^\s*\d+\.\s', ' ', rest)
        nums = re.findall(r'\d+(?:\.\d+)?%?', rest)
        nums = [n_ for n_ in nums if not ((len(n_.rstrip('%')) >= 3 or '.' in n_ or n_.endswith('%')) and any(n_ in ph for ph in phrases))]
        if nums:
            out.append({'句': s_[:160], '未覆盖的数': nums})
    return out


def new_v14b(main_md):
    """第十四稿正文里其余数字的出处（v8 末轮补）。设计常数也从程序源码或设定文件里读，不手填。"""
    import glob
    from collections import Counter
    E21 = os.path.join(W5, '21_倪师断法引擎_20261005'); C20 = os.path.join(W5, '20_全书倪师全面比对_20261005')
    RS = os.path.join(CH, 'chain_results_v1')
    c = jl(HERE, 'checks', 'chain_paper_counts_v1.json')
    Ex, J, K, N, B, V, TR, M, S, X = (c[k] for k in ('抽取', '裁定', '核查', '归一', '知识库', '覆盖', '可追溯', '主检验', '讲述时段', '示例盘r30'))
    post, post2, diag = jl(RS, 'posthoc_v1.json'), jl(RS, 'posthoc2_v1.json'), jl(RS, 'reproduce_diag_v1.json')
    rec, fb = jl(RS, 'recall_v1.json'), jl(RS, 'm4e_fable_v1.json')
    key, k4 = jl(CH, 'm4f_v1', 'key_m4f_v1.json'), jl(E21, 'm4_v1', 'key_v1.json')
    pilot, tu = jl(CH, 'trad_v1', 'pilot_result_P1.json'), jl(CH, 'trad_v1', 'trad_units_v1.json')
    fig = jl(HERE, 'figures_chain_v5', '图中数字_chain_v5.json')
    rules = jl(E21, 'kb_final_v1', 'kb_merged_v2.json')['rules']
    m_ = jl(C20, 'merged_v1', 'merged_v1.json')
    cat = Counter(r['category'] + ('·' + r['relation'] if r['relation'] else '') for r in m_['ni_rows'])
    corpus_lines = [ln for ln in open(CORPUS, encoding='utf-8') if ln.strip()]
    corpus = {ln.split('｜')[0]: ln.rstrip('\n').split('｜', 4)[4] for ln in corpus_lines}
    nb = len(glob.glob(os.path.join(CH, 'chain_packets_v2', 'K*'))); npl = len(glob.glob(os.path.join(CH, 'pilot_packets_v1', 'K*')))
    eng = open(os.path.join(CH, 'ni_chain_engine_v1.py'), encoding='utf-8').read()
    repsrc = open(os.path.join(CH, 'chain_reproduce_v1.py'), encoding='utf-8').read()
    tbsrc = open(os.path.join(CH, 'trad_build_v1.py'), encoding='utf-8').read()
    rounds = int(re.search(r'^MAX_ROUNDS = (\d+)', eng, flags=re.M).group(1))
    P1, P3, P7, P8 = (post[k] for k in ('P1a·只用通则步的覆盖', 'P3·同性别对照', 'P7·分布', 'P8·连线方向'))
    P1b, P2 = post['P1b·只用通则步的主检验（事后）'], post['P2·候选盘']
    Q1, Q3, Q4, Q6 = (post2[k] for k in ('Q1·判断集的步在本人盘上（拆开）', 'Q3·推不出的结点在整个知识库里（按人累计）', 'Q4·推得出的判断本人盘推出多少', 'Q6·不加前后2分钟'))
    d1 = diag['D1可达性']
    n = V['盘数']; dist = {int(k): v for k, v in fig['图12']['最长链分布'].items()}
    main6 = P8['往后推'] + P8['同层'] + P8['往回推']
    sens = [P1b['平均u'], P2['每张候选各算再平均的平均u'], P3['平均u'], Q6['平均u']]
    ns = [v['n_statements'] for v in k4['items'].values()]
    pair = fb['与原M4e逐题配对']
    R = rec['召回率']; rq, rr2 = R['定性步·明确漏'], R['推理步·明确漏加两可']
    S_ = rec['计入的原话条数']
    n_qs = len(tu['qs_sentences'])
    bad = '（不合）'
    w = [
        ('前作规则', f"整理成 {len(rules)} 条「如果……就……」的规则"),
        ('语料条数', f"按整理主题归在紫微斗数各类之下的有 {len(corpus_lines)} 条，去掉讲易经、医理的 {cat['不属于紫微']} 条与讲排盘的 {cat['排盘方法']} 条，余下 {Ex['条目']} 条是本文用的全部原话，前作已分成 {nb} 批"
         if len(corpus_lines) - cat['不属于紫微'] - cat['排盘方法'] == Ex['条目'] == sum(rec['strata_sizes'].values()) else bad),
        ('命主', f"纳入检验的命主 {S['M4人数']} 人"),
        ('时段', '前后各加 2 分钟' if '时段已含前后各 2 分钟' in repsrc else bad),
        ('留出盘', f"{M['holdout_charts']} 张留出随机盘（男命 {P3['留出盘性别']['男']} 张、女命 {P3['留出盘性别']['女']} 张）" if P3['留出盘性别']['男'] + P3['留出盘性别']['女'] == M['holdout_charts'] == n else bad),
        ('全书抽句', f"本文从中随机抽 {n_qs} 句" if n_qs == tu_n_check(tbsrc) else bad),
        ('全书原文', f"从《全书》2990 句古籍原文里随机抽的 {n_qs} 句" if 'assert len(classical) == 2990' in tbsrc and 'assert len(frozen) == 3025' in tbsrc else bad),
        ('局限全书', f"《全书》只抽 {n_qs} 句"),
        ('批次', f"{nb} 批原话，每批由抽取者甲、乙各自独立抽取"),
        ('试抽', f"正式抽取之前先拿 {npl} 批试抽，改定说明后 {nb} 批全部重抽"),
        ('判断名', f"{N['判断名']} 个判断名由两名归类者各自归并"),
        ('自推', f"核查成立的 {K['成立合计']} 步换成结点后，有 {B['排除']['归一后同义自推']} 步变成自己推自己"),
        ('命例特指', f"{B['收下的步']} 步里命例特指的 {B['命例特指·全部']} 步"),
        ('命例特指引擎', f"引擎可用的 {B['引擎可用']} 步里有 {B['命例特指·引擎可用']} 步"),
        ('局限命例', f"引擎可用的步里有 {B['命例特指·引擎可用']} 步是讲具体命主时说的"),
        ('方向', f"主链六层之内的 {main6} 条里，往后推的 {P8['往后推']} 条，同层的 {P8['同层']} 条，往回推的 {P8['往回推']} 条"),
        ('深度起步', '起步的条件成立就得出判断（深度 1）' if '定性步得出的深度为 1' in eng else bad),
        ('深度推理步', '（深度 = 1 + 前提里最大的深度）' if '推理步得出的深度为 1 ＋ 前提里最深的那个' in eng else bad),
        ('轮数', f"最多 {rounds} 轮"),
        ('r30结点', f"命宫推出 {X['覆盖口径']['命宫结点']} 个判断，其中 {X['覆盖口径']['最短推法也要经过推理步的结点']} 个至少经过一步推理步"),
        ('r30最长', f"最长的一条有 {X['覆盖口径']['最长链步数']} 步"),
        ('表3抽取', f"独立核查判成立 {K['成立合计']} / {J['定稿步']} 步（{pct(K['成立合计'] / J['定稿步'])}）"),
        ('表3覆盖', f"{n} 张留出随机盘，{pct(V['走到行为路线成败'] / n)} 的盘命宫推到行为、路线或成败"),
        ('表3链长', f"最长链中位数 {V['最长链步数']['中位数']:g} 步"),
        ('表3可追溯', f"{TR['counts']['推法']} 条推导路径、{TR['counts']['结点']} 个判断，全部合格" if TR['all_ok'] else bad),
        ('表3主检验', f"{M['人数']['计入']} 人平均 u = {M['主检验']['平均u']:.3f}，p = {M['主检验']['p_单侧']:.3f}，**未通过**"),
        ('覆盖盘数', f"在 {n} 张留出随机盘上各推一次"),
        ('链长2与4', f"2 步的盘占 {pct(dist[2] / n)}，4 步以上的约三分之一" if .3 < sum(v for k, v in dist.items() if k >= 4) / n < .37 else bad),
        ('命例步长链', '4 步以上的长链，链上都至少用到一条命例步' if P1['最长链']['最大'] == 3 else bad),
        ('只用通则', f"只用通则步时，最长链最多 {P1['最长链']['最大']} 步"),
        ('8.1长链', '4 步以上的长链都用到了命例步' if P1['最长链']['最大'] == 3 else bad),
        ('可追溯盘数', f"{TR['charts']} 张盘上 {TR['counts']['结点']} 个判断、{TR['counts']['推法']} 条推导路径"),
        ('排位', f"在 {M['holdout_charts']} 张留出随机盘上各算一个得分"),
        ('重复', f"重复 {M['n_mc']} 次求单侧 p"),
        ('人数', f"{M['人数']['M4命例']} 人里 {M['人数']['不计入（倪师判断集为空）']} 人判断集为空，计入 {M['人数']['计入']} 人，判断集按人累计 {S['计入者判断集结点数']['合计']} 个结点"),
        ('得分0', f"{P7['本人盘得分为0的人数']} 人的本人盘一个判断也没推出"),
        ('可达', f"{d1['倪师判断集结点合计']} 个判断里，剔除之后引擎可用的步里还能推出的只有 {d1['结构上可达的结点']} 个（{pct(d1['结构上可达的结点'] / d1['倪师判断集结点合计'])}）"),
        ('Q3', f"本人时段以外有 {Q3['整个知识库在本人时段外都没有以它为结论的步']} 个连一步以它为结论的都没有"),
        ('Q4', f"{Q4['剔除后仍有步可推的结点·按人累计']} 个推得出的判断，本人盘只推出 {Q4['本人盘推出的']} 个"),
        ('Q4人', f"{Q4['其中本人盘一个也没推出的人数']} 人一个也没推出"),
        ('Q1', f"判断集里条件写得出的起步 {Q1['起步·各候选都成立'] + Q1['起步·条件都不成立'] + Q1.get('起步·部分候选成立', 0)} 步，在重建的本人命盘上成立的 {Q1['起步·各候选都成立']} 步，不成立的 {Q1['起步·条件都不成立']} 步"),
        ('敏感', f"去掉前后 2 分钟，平均 u 在 {min(sens):.2f} 至 {max(sens):.2f} 之间"),
        ('功效', f"只有 {M['人数']['计入']} 人，各人也不完全独立"),
        ('M4e题数', f"沿用前作的 {len(k4['items'])} 题"),
        ('M4e陈述', f"每题陈述 {min(ns)} 到 {max(ns)} 条不等"),
        ('重审题包', f"把这 {fb['n_items'] * len(fb['arms'])} 份题包原样重审"),
        ('重审含0', '区间都包含 0' if all(v['配对差95%区间（条件精确）'][0] < 0 < v['配对差95%区间（条件精确）'][1] for v in pair.values()) else bad),
        ('摘要K', f"每题统一 {key['K']} 条陈述"), ('M4fK', f"每题统一取 {key['K']} 条"), ('局限K', f"在陈述满 {key['K']} 条"),
        ('NGRAM', f"有 {key['NGRAM']} 字以上相同片段"),
        ('试编', f"{pilot['n']} 条达到事先定的停止规则"),
        ('T75', '女命太阳陷 → 34 岁后看不到太阳' if '34岁以后' in corpus['T75'] else bad),
        ('T75b', '事发在 33 岁前' if '33岁之前' in corpus['T75'] else bad),
        ('召回抽样', f"{sum(rec['strata_sizes'].values())} 条原话按知识库分三层（含推理步的、只有起步的、一步都没有的），依次随机抽 {S_['S1']}、{S_['S2']}、{S_['S3']} 条，共 {sum(S_.values())} 条"),
        ('召回起步', f"起步 {rq['召回率']:.2f}（{rq['95%区间（Gamma后验合成）'][0]:.2f}–{rq['95%区间（Gamma后验合成）'][1]:.2f}）"),
        ('召回两可', f"推理步降到 {rr2['召回率']:.2f}（{rr2['95%区间（Gamma后验合成）'][0]:.2f}–{rr2['95%区间（Gamma后验合成）'][1]:.2f}）"),
        ('漏步', f"漏步有 {rec['链长·漏步去向']['加进副本']} 条（推理步只有 {rec['链长·加进副本的步']['推理步']} 条），补回去以后，{rec['链长·留出盘命宫最长链']['盘数']} 张盘的最长链分布与原来完全相同"
         if rec['链长·留出盘命宫最长链']['变长的盘数'] == 0 and rec['链长·留出盘命宫最长链']['原知识库'] == rec['链长·留出盘命宫最长链']['加进漏步后'] else bad),
        ('两人都漏', '「两人都漏」的是 0 条' if all(v['两人都漏的估计'] == 0 for v in rec['Chapman·找漏者'].values()) else bad),
        ('个性行为', f"个性 → 行为推导却只有 {c['层间连线']['个性→行为']} 条连线"),
        ('结论忠实', f"独立核查判为忠实的 {K['成立合计']} 步收进知识库"),
        ('英文规模', f"{B['收下的步']:,} steps ({B['结点']:,} judgment nodes"),
        ('英文主检验', f"({M['人数']['计入']} persons, one-sided p = {M['主检验']['p_单侧']:.3f})"),
        ('英文K', 'six statements each' if key['K'] == 6 else bad),
    ]
    return w


def tu_n_check(tbsrc):
    m = re.search(r'^N_QS = (\d+)', tbsrc, flags=re.M)
    return int(m.group(1)) if m else -1


STUDY_RUNS = (('《全书》切分', 'seg_r1', 'trad_v1/seg_returns'), ('切分裁定', 'segadj_r1', 'trad_v1/seg_adj_returns'), ('归类试编', 'pilot_r1', 'trad_v1/pilot_returns'),
              ('正式归类', 'coder_r1', 'trad_v1/formal_returns'), ('归类裁定', 'adj_r1', 'trad_v1/adj_returns'), ('第二次认本人', 'm4f_r1', 'm4f_v1/returns'),
              ('第一次认本人用 Fable 重审', 'm4e_fable_r1', 'm4e_v1/fable_returns'))
GEN_SECS = ('## S8　', '## S10　', '## S12　', '## S13　')


def supp_v14(supp_md):
    """补充材料里手写段落的数字。程序生成的 S8、S10、S12、S13 与 S4.2 花费表另由生成脚本逐字复现核对（generated_ok）；
    这里也照样从账本与请求文件重算花费表。设计常数从程序源码或设定文件里读；纯定义（α 的取值含义、1/4、1 − u、编号）单列为「定义」。"""
    import glob, sys
    E21 = os.path.join(W5, '21_倪师断法引擎_20261005')
    RS = os.path.join(CH, 'chain_results_v1')
    c = jl(HERE, 'checks', 'chain_paper_counts_v1.json')
    B, M, S = c['知识库'], c['主检验'], c['讲述时段']
    post, post2, diag, rep = (jl(RS, f) for f in ('posthoc_v1.json', 'posthoc2_v1.json', 'reproduce_diag_v1.json', 'reproduce_v1.json'))
    rec, fb, e = jl(RS, 'recall_v1.json'), jl(RS, 'm4e_fable_v1.json'), jl(RS, 'm4e_analysis_v1.json')
    key, k4 = jl(CH, 'm4f_v1', 'key_m4f_v1.json'), jl(E21, 'm4_v1', 'key_v1.json')
    ex = jl(RS, 'example_r30_v1.json')['第四版·命宫结点']; exn = {v['名']: v for v in ex.values()}
    clo = jl(RS, 'cand_closure_check_v1.json')
    tpil = jl(CH, 'types_v1', 'pilot_P1_result_v1.json')
    led = jl(CH, 'api_runs', 'ledger.json')['runs']
    rules = jl(E21, 'kb_final_v1', 'kb_merged_v2.json')['rules']
    cr = {}
    for ln in open(CORPUS, encoding='utf-8'):
        if ln.strip():
            t = ln.rstrip('\n').split('｜', 4); cr[t[0]] = t
    src = lambda f: open(os.path.join(CH, f), encoding='utf-8').read()
    eng, m4src, rv, m4b, anz = src('ni_chain_engine_v1.py'), src('m4e_sources_v1.py'), src('chain_reproduce_v1.py'), src('m4e_build_v1.py'), src('m4f_analyze_v1.py')
    sys.path.insert(0, CH)
    from types_build_v1 import REVIEW25
    opin = src(os.path.join('design_review_00l', '意见.md'))
    must = sorted({int(x) for x in re.findall(r'必\s?(\d+)', opin)}); sugg = sorted({int(x) for x in re.findall(r'建\s?(\d+)', opin)})
    nb = len(glob.glob(os.path.join(CH, 'chain_packets_v2', 'K*'))); npl = len(glob.glob(os.path.join(CH, 'pilot_packets_v1', 'K*')))
    AUD = {'抽取': 'chain_returns_v2', '裁定': 'chain_adj_returns_v1', '核查': 'chain_check_returns_v1', '归一': 'chain_norm_returns_v1', '归一裁定': 'chain_norm_adj_returns_v1'}
    na = {k: len(glob.glob(os.path.join(CH, d, '*.audit.json'))) for k, d in AUD.items()}
    nviol = sum(bool(json.load(open(f, encoding='utf-8')).get('violations')) for d in AUD.values() for f in glob.glob(os.path.join(CH, d, '*.audit.json')))
    nreq = {k: sum(1 for ln in open(os.path.join(CH, 'api_runs', k, 'requests.jsonl'), encoding='utf-8') if ln.strip()) for _, k, _ in STUDY_RUNS}
    run_ok = True
    for _, k, d in STUDY_RUNS:
        au = [json.load(open(f, encoding='utf-8')) for f in glob.glob(os.path.join(CH, d, '*.audit.json'))]
        run_ok &= len(au) == nreq[k] and all(a['ok'] and not a.get('rerun') for a in au)
    P1, P4, P5, P7 = (post[k] for k in ('P1a·只用通则步的覆盖', 'P4·讲述时段重叠', 'P5·推不出的结点', 'P7·分布'))
    Q1, Q2, Q7 = post2['Q1·判断集的步在本人盘上（拆开）'], post2['Q2·去重'], post2['Q7·候选盘性别不一']
    d1 = diag['D1可达性']
    h20 = next(p for p in rep['各人'] if p['person_id'] == 'H20'); h16 = next(p for p in rep['各人'] if p['person_id'] == 'H16')
    g20 = next(p for p in diag['各人'] if p['person_id'] == 'H20'); g16 = next(p for p in diag['各人'] if p['person_id'] == 'H16')
    none_reach = [p['person_id'] for p in diag['各人'] if p['结构上可达'] == 0]
    u_none = [next(r['u'] for r in rep['各人'] if r['person_id'] == q) for q in none_reach]
    fig = jl(HERE, 'figures_chain_v5', '图中数字_chain_v5.json'); dist = {int(k): v for k, v in fig['图12']['最长链分布'].items()}
    share4 = sum(v for k, v in dist.items() if k >= 4) / c['覆盖']['盘数']
    same_sex = len(e['subset_defs']['陪衬同性别']); n_mixed = e['n_items'] - same_sex
    pad = '时段已含前后各 2 分钟' in rv
    ngram = int(re.search(r'^NGRAM = (\d+)', m4src, flags=re.M).group(1))
    zero_noexcl = sum(1 for r in diag['各人'] if r['不剔除·本人盘得分'] == 0)
    p2c = [r['person_id'] for r in post['各人'] if abs(r['u'] - r['P2·每张候选各算u平均']) > 1e-4]
    w103 = {d['T']: d['depth'] for d in exn['武官星']['推法']}
    bad = '（不合）'
    w = [
        ('定义·深度', '起步得出的判断，深度是 1' if '定性步得出的深度为 1' in eng else bad),
        ('定义·α', '1 是完全一致，0 相当于随手乱归'),
        ('定义·四分之一', '假定焦点是四份里任一份的机会各 1/4' if "OWN = ('焦点', '陪衬1', '陪衬2', '陪衬3')" in anz else bad),
        ('试抽', f"先拿 {npl} 批试抽"), ('重抽', f"{nb} 批全部重抽"),
        ('表S1条数', f"按 T 编号顺序的前 {len(c['核查不成立例'])} 条"),
        ('T86', '| T86 | 宜嫁大 7 岁以上 |' if '7岁' in cr['T86'][4] else bad),
        ('样例', f"推理步共 {c['附录·推理步样例·候选数']} 条，按 T 编号顺序取前 {len(c['附录·推理步样例'])} 条"),
        ('定义·一致率示例', '合并一致率是 1/3'),
        ('表S3条数', f"成员最多的 {len(c['归一样例'])} 个结点"),
    ]
    w += [(f"表S3·{g['名']}", f"| {g['层']} | {g['名']} | {'、'.join(g['成员'])} |") for g in c['归一样例']]
    w += [
        ('存档', f"抽取 {na['抽取']} 份、裁定 {na['裁定']} 份、核查 {na['核查']} 份（有一批没有可核的步）、归一 {na['归一']} 份、归一裁定 {na['归一裁定']} 份，共 {sum(na.values())} 份"),
        ('存档合格', f"{sum(na.values())} 份全部合格" if nviol == 0 else bad),
        ('认领更正', '把第 10 批两份抽取' if 'K10' in src('00d_收取认领目录更正_v1.md') else bad),
        ('12实14', f"「本人盘得分为 0 的有 12 人」实为 {P7['本人盘得分为0的人数']} 人" if '12 人' in src('00f_内审后更正与事后补充分析_v1.md') else bad),
        ('性别不定', f"在本人性别不定的 {n_mixed} 题里"), ('陪衬不按性别', f"陪衬不按性别的 {n_mixed} 题"), ('性别不定2', f"但这 {n_mixed} 题本人的性别本来就定不下"),
        ('前作规则', f"前作的规则数（{len(rules)} 条）取自前作登记过的知识库文件"),
        ('意见', f"意见 {len(must) + len(sugg)} 条（必须改 {len(must)} 条、建议改 {len(sugg)} 条）" if must == list(range(1, len(must) + 1)) and sugg == list(range(1, len(sugg) + 1)) else bad),
        ('审者', f"每组每题 {key['judges_per_arm']} 名审者"),
        ('531', f"全部 {sum(nreq.values())} 份一次合格，没有重跑" if run_ok else bad),
    ]
    w += [(f'花费表·{nm}', f"| {nm} | {nreq[k]} | {led['api_runs/' + k]['花费美元']:.2f} |") for nm, k, _ in STUDY_RUNS]
    w += [
        ('花费表·合计', f"| 合计 | {sum(nreq.values())} | {sum(led['api_runs/' + k]['花费美元'] for _, k, _ in STUDY_RUNS):.2f} |"),
        ('深度1', '深度 = 1。' if '定性步得出的深度为 1' in eng else bad),
        ('深度推理步', '深度 = 1 + 前提里最大的深度。' if '推理步得出的深度为 1 ＋ 前提里最深的那个' in eng else bad),
        ('T419', f"T419 在视频分集 {int(re.match(r'P(\d+)', cr['T419'][1]).group(1))} 的 {cr['T419'][2]}，T1458 在同一集的 {cr['T1458'][2]}" if re.match(r'P(\d+)', cr['T419'][1]).group(1) == re.match(r'P(\d+)', cr['T1458'][1]).group(1) else bad),
        ('生杀', f"「有生杀之权」属{exn['有生杀之权']['层']}层，却在第 {min(d['depth'] for d in exn['有生杀之权']['推法'])} 步就由盘面得出"),
        ('暗权', f"「暗权」属{exn['暗权']['层']}层，在第 {min(d['depth'] for d in exn['暗权']['推法'])} 步才得出"),
        ('武官星', f"「武官星」有 {len(exn['武官星']['推法'])} 条推导路径"),
        ('T103', '深度都是 1，按步的编号的字面先后，T103 排在 T97 前面' if w103.get('T103') == w103.get('T97') == 1 and 'T103' < 'T97' and exn['武官星']['推法'][0]['T'] == 'T103' else bad),
        ('长链', '全部步时最长链 4 步以上的盘（约三分之一），最长链上都至少用到了一条命例步' if P1['最长链']['最大'] == 3 and .3 < share4 < .37 else bad),
        ('闭合', f"对第一次认本人的 {clo['M4e论断份数']} 份论断（{clo['多候选的份数']} 份多候选）复核，新旧两种做法结果完全相同" if clo['结果不同或有悬空前提的份数'] == 0 else bad),
        ('命主', f"纳入检验的命主有 {S['M4人数']} 人（前作第三节）"), ('命主同', f"命主就是前作的 {len(k4['items'])} 人，用同一批候选盘"),
        ('定义·u', '1 − u 就是本人盘胜过的随机盘比例'),
        ('p算法', f"从 {M['holdout_charts']} 张留出盘里随机抽一张当作「本人盘」算平均 u，重复 {M['n_mc']} 次（种子 {M['seed']}）"),
        ('结果人数', f"{M['人数']['M4命例']} 人里，{M['人数']['不计入（倪师判断集为空）']} 人的判断集是空的，不计入；计入 {M['人数']['计入']} 人，每人的判断集有 {S['计入者判断集结点数']['最少']} 至 {S['计入者判断集结点数']['最多']} 个结点，按人累计 {S['计入者判断集结点数']['合计']} 个"),
        ('功效', f"{M['人数']['计入']} 人的检验功效有限"),
        ('H38H39', 'H38、H39 都是候选盘一男一女的人' if {'H38', 'H39'} <= {p['person_id'] for p in Q7['各人']} else bad),
        ('156', f"{M['人数']['计入']} 人的 {S['计入者判断集结点数']['合计']} 个判断里，剔除各人时段内的步之后"),
        ('全推不出', f"判断集全都推不出的 {len(none_reach)} 人除外" if len(none_reach) == d1['计入人数'] - d1['至少一个结点结构上可达的人数'] else bad),
        ('全推不出u', f"判断集全都推不出的 {len(none_reach)} 人 u 恰为 0.5" if all(abs(u - .5) < 1e-9 for u in u_none) else bad),
        ('不剔除零', f"{M['人数']['计入']} 人里有 {zero_noexcl} 人一个也推不回"),
        ('H20', f"H20 的 {h20['倪师判断集结点数']} 个判断里，有 {g20['结构上可达']} 个在剔除之后还有别的步能推出，本人盘推出了其中 {round(h20['本人盘得分'] * h20['倪师判断集结点数'])} 个"),
        ('H16', 'H16 的两个判断，剔除之后引擎能用的步都推不出，本人盘和随机盘都是 0，u 正好是 0.5'
         if h16['倪师判断集结点数'] == 2 and g16['结构上可达'] == 0 and h16['本人盘得分'] == 0 and h16['留出盘平均得分'] == 0 and h16['u'] == .5 else bad),
        ('98', f"条件写得出的 {Q1['起步·各候选都成立'] + Q1['起步·条件都不成立'] + Q1['推理步·各候选都成立'] + Q1['推理步·附加条件不成立'] + Q1['推理步·附加条件成立但前提没推出']} 步里"),
        ('部分0', '统计程序里这一类的计数为 0' if not any('部分' in k for k in Q1) else bad),
        ('93', f"那 {P5['合计']} 个推不出的判断"),
        ('93b', f"另外，{P5['合计']} 个里只有 {P5['时段内有通则步以它为结论']} 个在本人时段内另有通则步以它为结论，其中引擎能用的只有 {P5['时段内有引擎可用的通则步以它为结论']} 个，也就是说，因通则被一起剔掉而推不出的，最多只有 {P5['时段内有引擎可用的通则步以它为结论']} 个"),
        ('去重', f"{M['人数']['计入']} 人的 {S['计入者判断集结点数']['合计']} 个判断，"),
        ('时段重叠', f"{M['人数']['M4命例']} 人里有 {P4['有重叠的两人对']} 对两人的时段互相重叠，多数是前后各加 2 分钟造成的" if pad else bad),
        ('候选盘', f"每张候选盘各算一个 u 再取平均，{M['人数']['计入']} 人里只有 {p2c[0]} 一人的 u 变了" if len(p2c) == 1 else bad),
        ('5人', f"这 {Q7['人数']} 人里有 {sum(1 for m in Q7['各人'] if m['u'] > .6)} 人的 u 在 0.6 以上"),
        ('5人b', f"在这 {Q7['人数']} 人身上都推不出来"),
        ('2分钟a', '把各人时段的前后 2 分钟都去掉再算一次' if pad else bad), ('2分钟b', '不加前后 2 分钟）' if pad else bad), ('2分钟c', '去掉前后 2 分钟再算' if pad else bad),
        ('功效区间', f"只有 {M['人数']['计入']} 人，平均 u 的区间从 {P7['平均u的自助法95%区间'][0]:.2f} 到 {P7['平均u的自助法95%区间'][1]:.2f}"),
        ('1至17', f"每人 {S['计入者判断集结点数']['最少']} 至 {S['计入者判断集结点数']['最多']} 个"),
        ('600陈述', f"{len(k4['items'])} 题共 {sum(v['n_statements'] for v in k4['items'].values())} 条陈述"),
        ('8字', f"按时间重叠或 {ngram} 字以上的相同片段找出"),
        ('三组', f"论断分三组，每组 {e['n_items']} 题" if len(e['arms']) == 3 else bad),
        ('4字', '与陈述有 4 字以上相同片段的陈述平均只有一条多' if 'def grams4' in m4b else bad),
        ('链平', f"链组与平铺组都认对 {e['arms']['链']['hits']} 题，配对差为 0" if e['arms']['链']['hits'] == e['arms']['平']['hits'] else bad),
        ('84题包', f"{fb['n_items'] * len(fb['arms'])} 份题包逐字节原样"),
        ('旧试编', f"试编 {tpil['n']} 步时"), ('审稿25', f"审稿时看过的 {len(REVIEW25)} 步"),
        ('T75c2', '看不到太阳 → 事发在33岁前' if '33岁之前' in cr['T75'][4] else bad),
        ('漏步10', f"把这 {rec['链长·漏步去向']['加进副本']} 条加进知识库的副本"),
        ('找回12', f"找回了 {sum(rec['召回率']['推理步·明确漏']['各层确认漏步数'].values())} 条明确漏的推理步"),
    ]
    o = e
    for arm, nm in (('链', '链组'), ('平', '平铺组'), ('三', '第三版先天组')):
        a_ = fb['arms'][arm]; pr = fb['与原M4e逐题配对'][f'{arm}组：Fable对Opus']
        sg = lambda v: f'{v:+.2f}'.replace('-', '−')
        pv = 'p < 0.001' if a_['p_binomial_one_sided'] < .001 else f"{a_['p_binomial_one_sided']:.3f}"
        w.append((f'表S9·{nm}', f"| {nm} | {o['arms'][arm]['hits']}/28 | {a_['hits']}/28 | {'< 0.001' if a_['p_binomial_one_sided'] < .001 else pv} | {a_['rate_CP95'][0]:.2f}–{a_['rate_CP95'][1]:.2f} | {pr['只前一组']}／{pr['只后一组']} | {sg(pr['配对差'])}（{sg(pr['配对差95%区间（条件精确）'][0])} 至 {sg(pr['配对差95%区间（条件精确）'][1])}） |"))
    return w


def uncovered_supp(supp_md, phrases):
    """补充材料的手写段落：去掉程序生成的四节（S8、S10、S12、S13），再去掉节号与 S 编号、反引号里的文件名、时间码、编码表的行号与「问N」，其余同 uncovered。"""
    secs = re.split(r'(?m)^(?=## S\d+　)', supp_md)
    txt = '\n'.join(s for s in secs if not s.startswith(GEN_SECS))
    for ph in sorted(set(phrases), key=len, reverse=True):   # 先换已核写法（含时间码的写法也能认），再去编号
        txt = txt.replace(ph, '〔核〕')
    txt = re.sub(r'`[^`]*`', ' ', txt)
    txt = re.sub(r'\bv\d+\b', ' ', txt)
    txt = re.sub(r'S\d+(\.\d+)*', ' ', txt)
    txt = re.sub(r'\d\d:\d\d:\d\d', ' ', txt)
    txt = re.sub(r'(?m)^\| [1-5] \|', '| ', txt)
    txt = re.sub(r'问\d', ' ', txt)
    return uncovered(txt + '\n## 参考文献\n', phrases)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--paper', required=True); ap.add_argument('--supp', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    main_md = open(a.paper, encoding='utf-8').read()
    supp_md = open(a.supp, encoding='utf-8').read()
    md = main_md + '\n' + supp_md
    c = jl(HERE, 'checks', 'chain_paper_counts_v1.json')
    x = jl(HERE, 'checks', 'chain_paper_extra_v1.json')
    fig = jl(HERE, 'figures_chain_v5', '图中数字_chain_v5.json')
    RS = os.path.join(CH, 'chain_results_v1')
    post, rep, diag, post2 = jl(RS, 'posthoc_v1.json'), jl(RS, 'reproduce_v1.json'), jl(RS, 'reproduce_diag_v1.json'), jl(RS, 'posthoc2_v1.json')
    kbc = jl(CH, 'chain_kb_v1.json')['counts']['按类型适用可操作']
    corpus = {}
    for ln in open(CORPUS, encoding='utf-8'):
        t = ln.rstrip('\n').split('｜')
        corpus[t[0]] = norm(t[4])
    res = {'引文': [], '数字': [], '附录A': [], '图表': []}
    for m in re.finditer(r'「([^「」]{4,})」[）\)]?\s*（(T\d+)[，、；）]', md):
        q, T = m.group(1), m.group(2)
        parts = [p for p in re.split(r'……', q) if p.strip()]
        res['引文'].append({'T': T, '引文': q[:40], 'ok': T in corpus and all(norm(p) in corpus[T] for p in parts)})
    E, J, K, N, B, V, TR, M, D, S, X = (c[k] for k in ('抽取', '裁定', '核查', '归一', '知识库', '覆盖', '可追溯', '主检验', '事后诊断', '讲述时段', '示例盘r30'))
    n = V['盘数']; lay = V['各层盘数']; ba = B['按类型适用']
    src = post['P10·抽取一致']['定稿来源按类型']
    q_both = src['定性步·甲乙'] / sum(v for k, v in src.items() if k.startswith('定性步'))
    r_both = src['推理步·甲乙'] / sum(v for k, v in src.items() if k.startswith('推理步'))
    dist = {int(k): v for k, v in fig['图12']['最长链分布'].items()}
    P1, P2, P3, P4, P5, P6, P7, P8, P9 = (post[k] for k in ('P1a·只用通则步的覆盖', 'P2·候选盘', 'P3·同性别对照', 'P4·讲述时段重叠', 'P5·推不出的结点',
                                                       'P6·判断集的步在本人盘上', 'P7·分布', 'P8·连线方向', 'P9·命宫两说按层的盘数'))
    P1b = post['P1b·只用通则步的主检验（事后）']
    q_ok = B['引擎可用的定性步']; r_ok = B['引擎可用的推理步']
    q_no = ba['定性步·先天'] - q_ok; r_no = ba['推理步·先天'] - r_ok
    q_nx = ba['定性步·大限'] + ba['定性步·流年'] + ba['定性步·小限']; r_nx = ba['推理步·大限'] + ba['推理步·流年'] + ba['推理步·小限']
    main6 = P8['往后推'] + P8['同层'] + P8['往回推']
    xb = x['b·格与可操作']
    d1 = D['D1可达性']; d3 = D['D3不剔除']; d4 = D['D4构成']['步']
    ev = d4['定性步·可操作·无格无其他'] + d4['推理步·可操作·无格无其他']
    h20 = next(p for p in rep['各人'] if p['person_id'] == 'H20')
    Q1, Q2, Q3, Q4, Q5, Q6, Q7 = (post2[k] for k in ('Q1·判断集的步在本人盘上（拆开）', 'Q2·去重', 'Q3·推不出的结点在整个知识库里（按人累计）', 'Q4·推得出的判断本人盘推出多少',
                                                  'Q5·按时段重叠量混入', 'Q6·不加前后2分钟', 'Q7·候选盘性别不一'))
    def kc(t, sc, op):
        return sum(v for k, v in kbc.items() if k.startswith(t + '·') and (k.split('·')[1] == '先天') == (sc == '先天') and k.endswith('·' + op))
    tq = [kc('定性步', '先天', '可操作'), kc('定性步', '先天', '不可操作'), kc('定性步', '非', '可操作'), kc('定性步', '非', '不可操作')]
    tr = [kc('推理步', '先天', '可操作'), kc('推理步', '先天', '不可操作'), kc('推理步', '非', '可操作'), kc('推理步', '非', '不可操作')]
    assert sum(tq) == B['定性步'] and sum(tr) == B['推理步']
    lt4 = (dist[1] + dist[2] + dist[3]) / n
    assert .62 < lt4 < .70 and abs(dist[5] / n - .2) < .02   # 「约三分之二」「两成」
    mixed = Q7['各人']; m6 = sum(1 for m in mixed if m['u'] > .6)
    p2c = [r for r in post['各人'] if abs(r['u'] - r['P2·每张候选各算u平均']) > 1e-4]
    assert len(p2c) == 1
    top3 = [v for _, v in x['c·最长链5步的盘']['最常见的链前3']]
    want = [
        ('摘要·规模', f"定稿 {J['定稿步']} 步，独立核查判为忠实的 {K['成立合计']} 步（{pct(K['成立合计'] / J['定稿步'])}）收进知识库，归一后为 {B['收下的步']} 步、{B['结点']} 个判断结点"),
        ('摘要·胜过', f"约 {round((1 - M['主检验']['平均u']) * 100)}%"), ('结论·规模', f"归一后为 {B['收下的步']} 步、{B['结点']} 个判断，每一步都对得回原话"),
        ('甲乙抽出', f"甲抽出 {E['甲抽出']} 步，乙抽出 {E['乙抽出']} 步"),
        ('定稿', f"定稿 {J['定稿步']} 步：起步 {J['定性步']} 步，推理步 {J['推理步']} 步"), ('有步条目', f"{J['有步的条目']} 条原话"),
        ('有推理步条目', f"含推理步的原话有 {J['有推理步的条目']} 条"),
        ('按条一致', f"{E['推理步有无一致']} 条（{pct(E['推理步有无一致'] / E['条目'])}）"), ('都说没有', f"{E['推理步有无一致'] - E['两人都有推理步']} 条"),
        ('至少一个说有', f"{post['P10·抽取一致']['至少一人说有推理步的条目']} 条里，甲乙都说有的是 {E['两人都有推理步']} 条（{pct(E['两人都有推理步'] / post['P10·抽取一致']['至少一人说有推理步的条目'])}）"),
        ('按步一致', f"{E['定稿来源']['甲乙']} 步（{pct(E['定稿来源']['甲乙'] / J['定稿步'])}）"), ('按类型', f"起步 {pct(q_both)}，推理步 {pct(r_both)}"),
        ('只甲只乙', f"只甲抽到的 {E['定稿来源']['只甲']} 步、只乙抽到的 {E['定稿来源']['只乙']} 步"), ('补入', f"补入的 {E['定稿来源']['补入']} 步"),
        ('没收', f"没收的有 {E['甲抽出'] - E['甲被收']} 步，乙有 {E['乙抽出'] - E['乙被收']} 步"), ('方法', f"{J['方法']} 条原话"), ('警告', f"另有 {J['warnings']} 步"),
        ('起步成立', f"判成立 {K['定性步成立']} 步（{pct(K['定性步成立'] / J['定性步'])}）"), ('推理步成立', f"判成立 {K['推理步成立']} 步（{pct(K['推理步成立'] / J['推理步'])}）"),
        ('合计成立', f"合计成立 {K['成立合计']} 步（{pct(K['成立合计'] / J['定稿步'])}）"), ('不成立', f"{K['不成立合计']} 步不进知识库"),
        ('判断名', f"共 {N['判断名']} 个"), ('归一结点', f"归成 {N['结点']} 个结点"), ('拆分', f"{N['拆成多个结点的判断名']} 个判断名"), ('改层', f"改层 {N['裁定改层']} 处"),
        ('合计一致率', pct(N['全组合并一致率'])), ('G3', pct(N['合并一致率']['G3'])), ('G2', pct(N['合并一致率']['G2'])), ('G3伙伴', pct(N['同结点伙伴完全相同比例']['G3'])),
        ('自推', f"有 {B['排除']['归一后同义自推']} 步变成"), ('知识库', f"知识库定为 {B['收下的步']} 步、{B['结点']} 个结点"),
        ('没进库结点', f"{x['a·没进知识库的结点']['差']} 个结点只出现在核查不成立的步里"),
        ('表3起步', '| 起步 | ' + ' | '.join(map(str, tq)) + f" | {B['定性步']} |"), ('表3推理步', '| 推理步 | ' + ' | '.join(map(str, tr)) + f" | {B['推理步']} |"),
        ('表3合计', '| 合计 | ' + ' | '.join(str(a_ + b_) for a_, b_ in zip(tq, tr)) + f" | {B['收下的步']} |"),
        ('不可操作', f"不可操作的步共 {B['不可操作']} 步（先天 {tq[1] + tr[1]} 步，大限流年小限 {tq[3] + tr[3]} 步）"),
        ('含格可操作', f"有 {x['b·格与可操作']['先天·可操作·含格']} 步的条件含「格」"),
        ('命例特指', f"命例特指的有 {B['命例特指·全部']} 步"), ('命例特指引擎', f"有 {B['命例特指·引擎可用']} 步，其中推理步 {B['命例特指·引擎可用的推理步']} 步"),
        ('连线', f"{B['推理步连线']} 条连线"), ('方向', f"{main6} 条连线里，往后推的 {P8['往后推']} 条，同层的 {P8['同层']} 条，往回推的 {P8['往回推']} 条；其余 {P8['涉及其余领域']} 条"),
        ('定性→路线', f"定性 → 路线（{c['层间连线']['定性→路线']} 条）"), ('路线→成败', f"路线 → 成败（{c['层间连线']['路线→成败']} 条）"),
        ('定性→成败', f"定性 → 成败（{c['层间连线']['定性→成败']} 条）"), ('个性→行为', f"个性 → 行为只有 {c['层间连线']['个性→行为']} 条"),
        ('长相', f"长相往后推的只有 {c['层间连线']['长相→成败']} 条"), ('武官星', f"推出 {len(fig['图7']['武官星'])} 个后续判断"),
        ('r30', f"命宫一共推出 {X['覆盖口径']['命宫结点']} 个判断，其中 {X['覆盖口径']['最短推法也要经过推理步的结点']} 个"),
        ('r30推理步', f"推理步有 {X['覆盖口径']['用上的推理步条数']} 条"), ('上四分位', f"不超过 {V['用上的推理步条数']['上四分位']:g} 条"),
        ('r30最长', f"最长链 {X['覆盖口径']['最长链步数']} 步，约三分之二的盘不到 4 步，另有两成的盘达到 5 步"), ('r30两说', f"命宫有 {X['覆盖口径']['两说处数']} 处两说"),
        ('覆盖任一', f"{V['走到行为路线成败']} 张（{pct(V['走到行为路线成败'] / n)}）"), ('覆盖成败', f"{V['走到成败']} 张（{pct(V['走到成败'] / n)}）"),
        ('路线层', f"路线的 {pct(lay['路线'] / n)}"), ('行为层', f"行为 {pct(lay['行为'] / n)}"), ('个性层', f"个性 {pct(lay['个性'] / n)}"), ('长相层', f"长相 {pct(lay['长相'] / n)}"),
        ('定性层', f"{pct(lay['定性'] / n)} 的盘经推理步推到了定性层"),
        ('推理步条数', f"中位数 {V['用上的推理步条数']['中位数']:g} 条，中间一半的盘在 {V['用上的推理步条数']['下四分位']:g} 至 {V['用上的推理步条数']['上四分位']:g} 条之间，最多 {V['用上的推理步条数']['最大']} 条"),
        ('最长链', f"中位数 {V['最长链步数']['中位数']:g} 步，最多 {V['最长链步数']['最大']} 步"),
        ('链长分布', f"2 步的盘占 {pct(dist[2] / n)}，3 步 {pct(dist[3] / n)}，4 步 {pct(dist[4] / n)}，5 步 {pct(dist[5] / n)}，只有 1 步（没用上推理步）的 {pct(dist[1] / n)}"),
        ('经推理步', pct(V['经推理步的结点']['合计'] / V['经推理步的结点']['结点合计']) + ' 至少要经过一步推理步'),
        ('两说盘', f"{V['有两说的盘']} 张（{pct(V['有两说的盘'] / n)}）"), ('两说中位', f"每张盘中位数 {V['两说处数']['中位数']:g} 处"),
        ('5步盘', f"5 步的那 {dist[5]} 张盘"), ('前三条', f"最常见的三条（{top3[0]}、{top3[1]}、{top3[2]} 张）"),
        ('不计入', f"{M['人数']['不计入（倪师判断集为空）']} 人的判断集是空的"), ('计入', f"计入 {M['人数']['计入']} 人"),
        ('判断集', f"{S['计入者判断集结点数']['最少']} 至 {S['计入者判断集结点数']['最多']} 个结点，按人累计 {S['计入者判断集结点数']['合计']} 个，不重复的 {Q2['判断集结点·不重复']} 个"),
        ('剔除', f"在 {S['计入者剔除的引擎步']['最少']} 至 {S['计入者剔除的引擎步']['最多']} 步之间，中位数 {S['计入者剔除的引擎步']['中位数']:g} 步"),
        ('剔除占比', f"约占 {B['引擎可用']} 步的 {round(S['计入者剔除的引擎步']['中位数'] / B['引擎可用'] * 100)}%"),
        ('平均u', f"平均 u = {M['主检验']['平均u']:.3f}"), ('胜过', f"胜过 {pct(1 - M['主检验']['平均u'])} 的随机盘"), ('中位u', f"中位数 {M['主检验']['u中位数']:g}"),
        ('p', f"p = {M['主检验']['p_单侧']:.3f}"), ('p白话', f"约为 {pct(M['主检验']['p_单侧'])}"),
        ('区间', f"{P7['平均u的自助法95%区间'][0]:.2f} 至 {P7['平均u的自助法95%区间'][1]:.2f}"),
        ('得分0', f"{P7['本人盘得分为0的人数']} 人的本人盘一个判断也没推出来"), ('u<0.5', f"u 小于 0.5 的 {M['主检验']['u小于0.5的人数']} 人"),
        ('u<=0.05', f"只有 {M['主检验']['u不大于0.05的人数']} 人的 u 不大于 0.05"), ('u>0.8', '、'.join(P7['u大于0.8的人']) + ' 三人的 u 在 0.8 以上'),
        ('只用起步', f"平均 u = {M['另报·只用定性步']['平均u']:.3f}，p = {M['另报·只用定性步']['p_单侧']:.3f}"),
        ('连线复现', f"共 {M['另报·推理步连线']['连线合计']} 条"), ('连线1', f"只复现了 {M['另报·推理步连线']['本人盘复现']} 条（{pct(M['另报·推理步连线']['比例'])}）"),
        ('连线随机', f"平均复现 {pct(M['另报·推理步连线']['留出盘复现比例的平均（各人平均再平均）'])}"),
        ('可追溯', f"{TR['counts']['结点']} 个判断、{TR['counts']['推法']} 条推导路径"),
        ('D1结构', f"只有 {d1['结构上可达的结点']} 个（{pct(d1['结构上可达的结点'] / d1['倪师判断集结点合计'])}）"),
        ('D1实际', f"{d1['实际可达的结点']} 个（{pct(d1['实际可达的结点'] / d1['倪师判断集结点合计'])}）"),
        ('D1其余', f"其余 {d1['倪师判断集结点合计'] - d1['结构上可达的结点']} 个"), ('D2', f"另外 {D['D2分组描述']['人数']} 人，平均 u 为 {D['D2分组描述']['平均u']:.3f}"),
        ('D2余', f"{D['D2分组描述']['其余人数']} 个人的判断一个也推不出"),
        ('D4', f"来自 {sum(d4.values())} 步：{ev} 步"), ('D4格', f"{d4['定性步·可操作·含格']} 步靠「格」"),
        ('D4其他', f"{d4['定性步·不可操作·含其他'] + d4['推理步·不可操作·含其他']} 步原话没说出盘面"),
        ('D3', f"本人盘平均推出判断集的 {pct(d3['本人盘得分平均'])}，随机盘平均 {pct(d3['留出盘得分平均'])}，平均 u 为 {d3['平均u']:.3f}"),
        ('D3零', f"有 {sum(1 for r in diag['各人'] if r['不剔除·本人盘得分'] == 0)} 人一个也推不回"),
        ('H20', f"H20（u = {h20['u']:.3f}，两张候选盘一男一女，剔除 {h20['剔除的步']} 步）"), ('H20随机', f"平均只推出 {pct(h20['留出盘平均得分'])}"),
        ('H16', f"H16（u = 0.5，一张候选盘，剔除 {next(p for p in rep['各人'] if p['person_id'] == 'H16')['剔除的步']} 步）"),
        ('Q4', f"至少还有一个判断推得出的有 {Q4['至少一个结点剔除后仍有步可推的人数']} 人；这 {Q4['至少一个结点剔除后仍有步可推的人数']} 人里，{Q4['其中本人盘一个也没推出的人数']} 人的本人盘一个也没推出"),
        ('Q4数', f"共 {Q4['剔除后仍有步可推的结点·按人累计']} 个，本人盘只推出 {Q4['本人盘推出的']} 个"),
        ('Q1起步', f"起步 {Q1['起步·各候选都成立'] + Q1['起步·条件都不成立'] + Q1.get('起步·部分候选成立', 0)} 步：条件在本人盘对应的宫里成立的 {Q1['起步·各候选都成立']} 步，不成立的 {Q1['起步·条件都不成立']} 步"),
        ('Q1推理步', f"推理步 {Q1['推理步·各候选都成立'] + Q1['推理步·附加条件成立但前提没推出'] + Q1['推理步·附加条件不成立']} 步：都成立的 {Q1['推理步·各候选都成立']} 步，附加条件成立但前提没推出来的 {Q1['推理步·附加条件成立但前提没推出']} 步，附加条件不成立的 {Q1['推理步·附加条件不成立']} 步"),
        ('Q3', f"有 {Q3['整个知识库在本人时段外都没有以它为结论的步']} 个连一步以它为结论的都没有；{Q3['本人时段外有先天但不可操作的步']} 个只有先天但不可操作的步，{Q3['本人时段外只有大限流年小限的步']} 个只有大限流年小限的步"),
        ('P5', f"只有 {P5['时段内有通则步以它为结论']} 个在本人时段内另有通则步以它为结论，其中引擎能用的只有 {P5['时段内有引擎可用的通则步以它为结论']} 个"),
        ('Q2', f"不重复的是 {Q2['判断集结点·不重复']} 个，其中 {Q2['出现在两人以上判断集里的结点']} 个出现在两人以上的判断集里；{Q2['判断集的步·按人累计']} 步不重复的是 {Q2['判断集的步·不重复']} 步；{Q2['剔除后推不出·按人累计']} 个推不出的判断，不重复的是 {Q2['剔除后推不出·不重复']} 个"),
        ('P4对', f"{P4['有重叠的两人对']} 对两人的时段互相重叠"), ('P4最多', f"最多的一对重叠 {max(p['重叠秒数'] for p in P4['明细'])} 秒"),
        ('P4步', f"有 {P4['落在两人以上时段内的知识库步']} 步同时落在两人以上的时段内"),
        ('Q5', f"有 {Q5['其中同时落在别人时段内的']} 步同时落在别人的时段内，涉及 {Q5['涉及人数']} 人；计入的人里有 {Q5['计入者之间时段重叠的两人对']} 对时段重叠，其中 {Q5['其中共有判断集结点的对数']} 对的判断集有共同的判断，合计 {Q5['共有结点合计']} 个"),
        ('Q6', f"计入 {Q6['计入人数']} 人，平均 u 为 {Q6['平均u']:.3f}"),
        ('P2变', f"只有 {p2c[0]['person_id']} 一人的 u 变了（{p2c[0]['u']:.3f} → {p2c[0]['P2·每张候选各算u平均']:.3f}）"),
        ('P2', f"平均 u 为 {P2['每张候选各算再平均的平均u']:.3f}"), ('P2单', f"{P2['单候选人数']} 人平均 u 为 {P2['单候选平均u']:.3f}"),
        ('P2多', f"{P2['多候选人数']} 人为 {P2['多候选原平均u']:.3f}"), ('P2多各算', f"也只到 {P2['多候选每张各算平均u']:.3f}"),
        ('Q7', f"候选盘一男一女的 {Q7['人数']} 人，平均 u 为 {Q7['平均u']:.3f}"), ('Q7六', f"有 {m6} 人的 u 在 0.6 以上"),
        ('三·五人', f"其中计入主检验的有 {Q7['人数']} 人"),
        ('P3', f"{P3['人数']} 人，只和同性别的随机盘比，平均 u 为 {P3['平均u']:.3f}；这 {P3['人数']} 人原为 {P3['这些人的原平均u']:.3f}"),
        ('P1步', f"只用 {P1['通则步']} 步通则步（其中推理步 {P1['其中推理步']} 步）"),
        ('P1覆盖', f"{pct(P1['推到行为路线成败任一层'] / P1['盘数'])} 的盘命宫仍能推到行为、路线或成败，{pct(P1['推到成败'] / P1['盘数'])} 推到成败"),
        ('P1链', f"最长链最多 {P1['最长链']['最大']} 步，2 步的占 {pct(P1['最长链分布']['2'] / P1['盘数'])}"),
        ('P1b', f"照主检验的办法再算一次，平均 u = {P1b['平均u']:.3f}"), ('P1b·p括注', f"另算过一个事后 p 值（{P1b['p_单侧_事后']:.3f}）"),
        ('Q6原', f"这 {Q6['计入人数']} 人原来的平均 u 为 {sum(next(p for p in rep['各人'] if p['person_id'] == q)['u'] for q, _, _ in Q6['各人']) / Q6['计入人数']:.3f}"),
        ('Q6原8.2', f"这 {Q6['计入人数']} 人的平均 u 从 {sum(next(p for p in rep['各人'] if p['person_id'] == q)['u'] for q, _, _ in Q6['各人']) / Q6['计入人数']:.3f} 变为 {Q6['平均u']:.3f}"),
        ('Q3过半', '过半' if .5 < Q3['整个知识库在本人时段外都没有以它为结论的步'] / d1['倪师判断集结点合计'] < .6 else '（不合）'),
        ('8.2数', f"仍推得出的 {Q4['剔除后仍有步可推的结点·按人累计']} 个判断，本人盘只推出 {Q4['本人盘推出的']} 个；{Q4['至少一个结点剔除后仍有步可推的人数']} 人里有 {Q4['其中本人盘一个也没推出的人数']} 人一个也没推出"),
        ('8.2男女', f"他们的平均 u 是 {Q7['平均u']:.3f}"), ('8.2四成', '有四成同时落在别人的时段内' if .38 < Q5['其中同时落在别人时段内的'] / Q5['判断集的步·按人累计'] < .45 else '（不合）'),
        ('推理步占比', f"推理步只有 {B['推理步']} 步（{round(B['推理步'] / B['收下的步'] * 100)}%）"),
        ('P9', f"成败层（600 张盘里有 {P9['成败']} 张）和定性层（{P9['定性']} 张）"),
        ('8.3不可操作', f"不可操作的 {B['不可操作']} 步（先天 {tq[1] + tr[1]} 步，大限流年小限 {tq[3] + tr[3]} 步）"),
        ('非先天推理步', f"{r_nx} 条推理步只存档"), ('留出性别', f"男命 {P3['留出盘性别']['男']} 张、女命 {P3['留出盘性别']['女']} 张"),
    ]
    want += extra_v6(md)
    old_missing = []
    for name, w in want:
        if w in md:
            res['数字'].append({'项': name, '应写': w, 'ok': True})
        elif name in REMOVED:
            old_missing.append({'项': name, '应写': w, '去向': REMOVED[name]})
        else:
            res['数字'].append({'项': name, '应写': w, 'ok': False})
    for name, w in new_v14(main_md, supp_md):
        res['数字'].append({'项': 'v14·' + name, '应写': w, 'ok': w in md})
    for name, w in new_v14b(main_md):
        res['数字'].append({'项': 'v14b·' + name, '应写': w, 'ok': w in main_md})
    res['旧写法未见'] = old_missing
    kb = jl(CH, 'chain_kb_v1.json')
    by_T = {}
    for s in kb['steps']:
        by_T.setdefault(s['T'], []).append(s['原话摘录'])
    sec = supp_md.split('## S2　')[1].split('## S3　')[0]
    for row in re.findall(r'^\| (T\d+) \|.*\| 「(.+)」 \|$', sec, flags=re.M):
        res['附录A'].append({'T': row[0], 'ok': row[1] in by_T.get(row[0], [])})
    for s_ in c['附录·推理步样例']:
        flag = f"{'是' if s_['命例特指'] else '否'}／{'是' if s_['可操作'] else '否'}"
        res['附录A'].append({'T': s_['T'], '项': '样例在表里且标注对', 'ok': f"| {flag} | 「{s_['原话摘录']}」 |" in sec})
    md = main_md
    figs = re.findall(r'^!\[图(\d+)　[^\]]*\]\(([^)]+)\)', md, flags=re.M)
    res['图表'].append({'项': '图号按出现先后连续', 'ok': [int(f[0]) for f in figs] == list(range(1, len(figs) + 1))})
    for k, f in figs:
        res['图表'].append({'项': f'图{k}文件', 'ok': os.path.exists(os.path.join(HERE, f))})
    tabs = [int(t) for t in re.findall(r'^\*\*表(\d+)　', md, flags=re.M)]
    res['图表'].append({'项': '表号按出现先后连续', 'ok': tabs == list(range(1, len(tabs) + 1)), '次序': tabs})
    body = re.sub(r'!\[.*?\]\(.*?\)', '', md)
    refs = set(int(t) for t in re.findall(r'图(\d+)', body))
    res['图表'].append({'项': '正文提到的图都存在', 'ok': refs <= set(range(1, len(figs) + 1)), '提到': sorted(refs)})
    trefs = set(int(t) for t in re.findall(r'表(\d+)', body))
    res['图表'].append({'项': '正文提到的表都存在', 'ok': trefs <= set(tabs), '提到': sorted(trefs)})
    sf = re.findall(r'^!\[S图(\d+)　[^\]]*\]\(([^)]+)\)', supp_md, flags=re.M)
    res['图表'].append({'项': 'S图号按出现先后连续', 'ok': [int(f[0]) for f in sf] == list(range(1, len(sf) + 1))})
    for k, f in sf:
        res['图表'].append({'项': f'S图{k}文件', 'ok': os.path.exists(os.path.join(HERE, f))})
    st = [int(t) for t in re.findall(r'^\*\*表S(\d+)　', supp_md, flags=re.M)]
    res['图表'].append({'项': '表S号按出现先后连续', 'ok': st == list(range(1, len(st) + 1)), '次序': st})
    res['引文'] += quotes_v14(main_md + '\n' + supp_md)
    for name, w in supp_v14(supp_md):
        res['数字'].append({'项': 'S·' + name, '应写': w, 'ok': w in supp_md})
    allph = [x['应写'] for x in res['数字'] if x['ok']]
    res['补充材料未覆盖'] = uncovered_supp(supp_md, allph)
    res['未覆盖'] = uncovered(main_md, [w for _, w in want if w in main_md] + [w for _, w in new_v14(main_md, supp_md) + new_v14b(main_md) if w in main_md])
    bad = {k: [y for y in v if not y.get('ok', True)] for k, v in res.items() if k not in ('旧写法未见', '未覆盖', '补充材料未覆盖')}
    out = {'paper': os.path.basename(a.paper), '各项数目': {k: len(v) for k, v in res.items()}, '不合格': bad, '明细': res}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'各项数目': out['各项数目'], '不合格': bad, '旧写法未见条数': len(res['旧写法未见']), '未覆盖句数': len(res['未覆盖']), '补充材料未覆盖句数': len(res['补充材料未覆盖'])}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
