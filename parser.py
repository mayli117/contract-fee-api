# parser.py

import re

import dateparser

from collections import defaultdict

from typing import Dict, Any

from .utils import clean_text, clause_split, find_money, find_percentage, parse_roc_date_if_any

def parse_contract_text(raw_text: str) -> Dict[str, Any]:

    text = clean_text(raw_text)

    sentences = clause_split(text)

    out = defaultdict(list)

    # keyword groups

    groups = {

        'package': ['自選餐','家庭特選餐','家庭豪華餐','影劇館','自選20','全選'],

        'mod': ['MOD','影劇館','未租滿','退訂','解約金'],

        'subsidy': ['補貼款','每日優惠金額','日優惠','補貼'],

        'circuit': ['電路費','光世代','100M','300M','500M','1G','2G'],

        'internet': ['上網費','HiNet','上網費用'],

        'penalty': ['違約金','違約費','提前解約','未滿約']

    }

    # 1) dates

    dates = set()

    # find explicit patterns (民國 or 西元)

    for m in re.findall(r'\d{2,4}[./-]\d{1,2}[./-]\d{1,2}', text):

        p = dateparser.parse(m, languages=['zh'])

        if p:

            dates.add(p.date().isoformat())

    # also attempt to find chinese "YYYY年MM月DD日" etc.

    for m in re.findall(r'\d{2,4}年\d{1,2}月\d{1,2}日', text):

        p = dateparser.parse(m, languages=['zh'])

        if p:

            dates.add(p.date().isoformat())

    # try ROC format like 114/04/11

    roc_dates = parse_roc_date_if_any(text)

    for d in roc_dates:

        dates.add(d.isoformat())

    if dates:

        out['dates'] = sorted(list(dates))

    # 2) per-sentence keyword match + money/pct extraction

    for s in sentences:

        for gname, keys in groups.items():

            for k in keys:

                if k in s:

                    out[gname].append({

                        'text': s,

                        'amount': find_money(s),

                        'pct': find_percentage(s)

                    })

                    break

    # 3) package amounts: e.g. 自選餐(全選)(2,520元)、家庭特選餐(3,792元)

    pkg_matches = re.findall(r'([^，,()（）\n]+?餐)[\s\(\（]*[^\d]*(\d{1,3}(?:[,\d{3}]+)?)\s*元', text)

    packages = {}

    for name, val in pkg_matches:

        packages[name.strip()] = int(val.replace(',', ''))

    if packages:

        out['package_amounts'] = packages

    # 4) daily amounts mapping: try specific phrases

    daily_map = {}

    for m in re.findall(r'(100M/40M|300M/300M|500M/500M|1G/1G|2G/1G|2G/2G)[\s,，:：]*([0-9.]+)\s*元', text):

        daily_map[m[0]] = float(m[1])

    wifi_m = re.search(r'Wi[- ]?Fi.*?：?\s*([0-9.]+)\s*元', text)

    if wifi_m:

        daily_map['WiFi'] = float(wifi_m.group(1))

    if daily_map:

        out['daily_amounts'] = daily_map

    # 5) contract days (prefer explicit 730 or "2年/24個月")

    if '730' in text:

        out['contract_days'] = 730

    elif re.search(r'2年|24個月', text):

        out['contract_days'] = 730

    # 6) MOD specific rules (e.g. 未租滿12個月解約金398元)

    mod12 = re.search(r'未租滿\s*12\s*個?月.*?解約金\s*[:：]?\s*([0-9,]+)\s*元', text)

    mod24 = re.search(r'未租滿\s*24\s*個?月.*?解約金\s*[:：]?\s*([0-9,]+)\s*元', text)

    if mod12:

        out['mod_specific'] = out.get('mod_specific', {})

        out['mod_specific']['under_12_months'] = int(mod12.group(1).replace(',', ''))

    if mod24:

        out['mod_specific'] = out.get('mod_specific', {})

        out['mod_specific']['under_24_months'] = int(mod24.group(1).replace(',', ''))

    return dict(out)
 