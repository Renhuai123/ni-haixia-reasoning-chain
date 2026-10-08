"""第十七稿正文（定稿）：在第十六稿（论文正文_v16.md）上按内审第三轮意见逐处替换（意见与处理见 review_v16/意见处理_v1.md），
并在声明里补上第二、三轮内审。每一处替换的原句必须在第十六稿里恰好出现一次（否则停）；新写的数字由 check_chain_paper_v12.py 逐项核。
插图路径改指 figures_chain_v9（只有图04 改了纵向排法）。写出 论文正文_v17.md（已存在就停）。用法：python3 make_v17.py"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.join(os.path.dirname(HERE), '23_倪师推理链_20261007')
s = open(os.path.join(HERE, '论文正文_v16.md'), encoding='utf-8').read()
led = json.load(open(os.path.join(CH, 'api_runs', 'ledger.json'), encoding='utf-8'))['runs']
rev = sum(led[f'api_runs/{k}']['花费美元'] for k in ('paper_review_v14_r1', 'paper_review_v15_r2', 'paper_review_v16_r3'))


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:80])
    s = s.replace(a, b)


# W2-1：1685 步里多数是起步，摘要、英文摘要、结论写清楚
rep('本文把他《天纪》讲稿里「后一个判断由前一个判断推出」的推导逐条抽出来，做成推理链知识库（1685 步、1028 个判断结点，每一步附原话）和第四版引擎。',
    '本文把他《天纪》讲稿里由盘面直接下判断的「起步」，以及「后一个判断由前一个判断推出」的推理步逐条抽出来，做成推理链知识库（1685 步，其中起步 1314、推理步 371；1028 个判断结点，每一步附原话）和第四版引擎。')
rep("we extracted the stated steps deriving one judgment about a person from another, building a knowledge base of 1,685 steps (1,028 judgment nodes, each tied to Ni's words)",
    "we extracted the stated steps by which Ni reaches a judgment about a person, either directly from the chart or from another judgment, building a knowledge base of 1,685 steps (1,314 start steps and 371 inference steps; 1,028 judgment nodes, each tied to Ni's words)")
rep('只用倪海厦《天纪》讲稿，可以把他明说出来的「后一个判断由前一个判断推出」的推导逐步抽出来：独立核查判为忠实的 1687 步收进知识库，',
    '只用倪海厦《天纪》讲稿，可以把他明说出来的起步与「后一个判断由前一个判断推出」的推理步逐步抽出来：独立核查判为忠实的 1687 步（起步 1314、推理步 373）收进知识库，')

# W2-2：1084 与 1028 之差
rep('知识库定为 1685 步、1028 个结点（表2）。', '知识库定为 1685 步、1028 个结点（表2；归一表里另有 56 个结点只出现在核查不成立的步里，不进知识库）。')

# W2-7
rep('- 第二种定类次序（象、义、位、时、情）、按适用分开与按结论层交叉的全表，见补充材料 S10。',
    '- 第二种定类次序（象、义、位、时、情）、按适用分开的全表，以及起步的定名、断事与结论层的交叉计数，见补充材料 S10。')

# W1-3：义理一派里的儒理、史事两路
rep('取象、取义、爻位三分里无对应；近于义理一派以人事说《易》（本文的类比） |', '取象、取义、爻位三分里无对应；近于义理一派里儒理、史事两路以人事说《易》（本文的类比） |')
rep('推理步以人情事理说理，近于义理一派以人事说《易》的路子。', '推理步以人情事理说理，近于义理一派里儒理、史事两路以人事说《易》的路子。')

# W1-2、W1-4：关联性思维一段写明分母，「凭」改「明说的依据／理由」
rep('按本文的编码，倪海厦由盘面起步，四成多凭位置、一成凭象，近于关联式，另有三成多直断，无从归类；一推到人，推理步近四成凭性情与处境的因果，近于因果式，但两成多凭类属归入，仍属关联式。',
    '按本文的编码，倪海厦由盘面起步下的断事里，明说的依据四成多是位置、一成是象，近于关联式，另有三成多直断，无从归类（给星定名的两成不在此列）；一推到人，推理步明说的理由近四成是性情与处境的因果，近于因果式，但两成多是类属归入，仍属关联式。')

# W2-5：刘玉平期号
rep('「取象、取义、爻位」的概括据二手研究（刘玉平，2002）；', '「取象、取义、爻位」的概括据二手研究（刘玉平，2002；引文据转载本核对，原刊页码未核）；')
rep('刘玉平. 孔颖达的易学诠释学[J]. 周易研究, 2002（期号未核实，据爱思想网转载）.', '刘玉平. 孔颖达的易学诠释学[J]. 周易研究, 2002(3)（期号据作者在山东大学历史学院的成果列表；页码未核，引文据爱思想网转载本核对）.')

# 声明：三轮内审
rep('- 第十四稿写成后，经同一接口请 6 名 Claude Fable 5.1 审稿人从不同角度各读一遍正文与补充材料的 PDF，另花费约 7 美元；意见与处理逐条记录，随数据公开。',
    f'- 论文另经三轮内审，都经同一接口调用 Claude Fable 5.1，每名审稿人读正文与补充材料的 PDF：第十四稿 6 名（各从一个角度），第十五稿 3 名，第十六稿 2 名，共花费约 {round(rev)} 美元；意见与处理逐条记录，随数据公开。')

# 插图路径
n_fig = s.count('figures_chain_v8/')
assert n_fig == 9, n_fig
s = s.replace('figures_chain_v8/', 'figures_chain_v9/')

open(os.path.join(HERE, '论文正文_v17.md'), 'x', encoding='utf-8').write(s)
print('已写出 论文正文_v17.md，字数', len(s), '；三轮内审花费', round(rev, 2))
