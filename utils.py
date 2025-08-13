# utils.py

import re

import datetime

import dateparser

def clean_text(s):

    s = s.replace('\r', '\n')

    s = re.sub(r'\u200b','', s)

    s = re.sub(r'\t+', ' ', s)

    s = re.sub(r' +', ' ', s)

    return s.strip()

def clause_split(text):

    parts = re.split(r'[。；;。\n]', text)

    return [p.strip() for p in parts if p.strip()]

def find_money(s):

    s2 = s.replace(',', '').replace('，','')

    m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(元|NT|新台幣)?', s2)

    if m:

        try:

            return float(m.group(1))

        except:

            return None

    return None

def find_percentage(s):

    m = re.search(r'(\d{1,3}(?:\.\d+)?)\s*%', ''.join(s.split()))

    if m:

        return float(m.group(1))

    return None

def parse_roc_date_if_any(text):

    """

    Parse ROC style dates like 114/04/11 -> return list of date objects

    """

    res = []

    for m in re.findall(r'(\d{3,4})[./-](\d{1,2})[./-](\d{1,2})', text):

        y = int(m[0])

        mth = int(m[1])

        d = int(m[2])

        if y < 1900:

            y = y + 1911

        try:

            res.append(datetime.date(y, mth, d))

        except:

            continue

    return res
 