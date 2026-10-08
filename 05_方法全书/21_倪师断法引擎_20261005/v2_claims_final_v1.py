"""引擎第二版：规则 → 属性取值的最终归类（依据《15a》《15b》）。取舍原则整理包和第二版引擎都只从这里取归类，不另写一套。
- 路线、成就两个领域的规则：用双人归类加裁定的冻结表 v2_route_labels_v1/route_labels_final.json（《15b》）；
- 其余领域：用关键词表第二版 v2_claims_v2.py（《15a》）。
用法：from v2_claims_final_v1 import rule_claims；rule_claims(规则) → [(属性, 取值), ...]"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v2_claims_v2 import claims, ATTRS_FOR_DOMAIN, TABLE

ROUTE_FILE = os.path.join(HERE, 'v2_route_labels_v1', 'route_labels_final.json')
ROUTE_DOMAINS = ('路线', '成就')
# 双人归类方案里的取值（见 v2_route_labels_v1.py 的说明）：路线五种，每种都可有否定写法；成就只有高、低
ROUTE_VALUES = {'路线': ['当官', '武职', '经商', '受雇', '专业'], '成就': ['高', '低']}
_route = None


def route_labels():
    global _route
    if _route is None:
        _route = {rid: [tuple(x) for x in v] for rid, v in json.load(open(ROUTE_FILE, encoding='utf-8'))['labels'].items()}
        bad = [(rid, x) for rid, v in _route.items() for x in v
               if x[0] not in ROUTE_VALUES or x[1].removeprefix('非') not in ROUTE_VALUES[x[0]] or (x[0] == '成就' and x[1].startswith('非'))]
        assert not bad, ('归类表里有方案外的取值', bad[:5])
    return _route


def rule_claims(r):
    d = r['结论']['领域']
    if d in ROUTE_DOMAINS:
        return list(route_labels()[r['rule_id']])
    if d not in ATTRS_FOR_DOMAIN:
        return []
    return claims(d, r['结论']['内容'])


def attr_values(attr):
    """attrs.txt 用：属性的取值说明"""
    if attr in ROUTE_VALUES:
        return '、'.join(ROUTE_VALUES[attr]) + ('（每种都另有否定写法 非X，如 非当官）' if attr == '路线' else '')
    return '、'.join(x['v'] + ('（另有 非' + x['v'] + '）' if x['neg'] else '') for x in TABLE[attr])
