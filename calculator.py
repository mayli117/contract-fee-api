# calculator.py

from datetime import date, timedelta

import math

CYCLE_RULES = {

    1: (1, None),   # 1日 ~ 當月最後日 (None 表示月底)

    2: (6, 5),

    3: (11, 10),

    4: (16, 15),

    5: (21, 20),

    6: (26, 25),

}

def month_end_day(y, m):

    # return last day of month

    if m == 12:

        nxt = date(y+1, 1, 1)

    else:

        nxt = date(y, m+1, 1)

    return (nxt - timedelta(days=1)).day

def generate_periods(start_dt: date, end_dt: date, cycle: int):

    if cycle not in CYCLE_RULES:

        raise ValueError("cycle must be 1..6")

    day_start, day_end = CYCLE_RULES[cycle]

    periods = []

    # cycle 1 special: per-month 1..lastday

    if cycle == 1:

        cur = date(start_dt.year, start_dt.month, 1)

        while cur <= end_dt:

            last = month_end_day(cur.year, cur.month)

            ps = date(cur.year, cur.month, 1)

            pe = date(cur.year, cur.month, last)

            if pe >= start_dt and ps <= end_dt:

                periods.append((ps, pe))

            # advance to next month

            if cur.month == 12:

                cur = date(cur.year+1, 1, 1)

            else:

                cur = date(cur.year, cur.month+1, 1)

        return periods

    # cycle 2~6

    # helper: find period start for a given day

    def seg_of(d):

        if d.day >= day_start:

            ps = date(d.year, d.month, day_start)

            # pe is next month day_end

            if d.month == 12:

                pe = date(d.year+1, 1, day_end)

            else:

                pe = date(d.year, d.month+1, day_end)

        else:

            # period started previous month

            prev_month = d.month - 1 or 12

            prev_year = d.year if d.month != 1 else d.year-1

            ps = date(prev_year, prev_month, day_start)

            if prev_month == 12:

                pe = date(prev_year+1, 1, day_end)

            else:

                pe = date(prev_year, prev_month+1, day_end)

        return ps, pe

    ps, pe = seg_of(start_dt)

    while ps <= end_dt:

        if pe >= start_dt and ps <= end_dt:

            periods.append((ps, pe))

        # advance by one month

        nxt_month = ps.month + 1

        nxt_year = ps.year

        if nxt_month > 12:

            nxt_month = 1

            nxt_year += 1

        ps = date(nxt_year, nxt_month, day_start)

        # pe is next month day_end

        nxt_month2 = ps.month + 1

        nxt_year2 = ps.year

        if nxt_month2 > 12:

            nxt_month2 = 1

            nxt_year2 += 1

        pe = date(nxt_year2, nxt_month2, day_end)

    # filter

    return [(a,b) for a,b in periods if not (b < start_dt or a > end_dt)]

def overlap_days(a_start, a_end, b_start, b_end):

    s = max(a_start, b_start)

    e = min(a_end, b_end)

    if e < s:

        return 0

    return (e - s).days + 1

def round_money(x):

    return int(math.floor(x + 0.5))

def calc_monthly_diff(start_dt, end_dt, cycle, new_rent, old_rent):

    periods = generate_periods(start_dt, end_dt, cycle)

    per_month = []

    total_days = 0

    total_amount = 0

    diff = new_rent - old_rent

    for ps, pe in periods:

        days = overlap_days(ps, pe, start_dt, end_dt)

        if days <= 0:

            continue

        amount_raw = diff * days / 30.0

        amount = round_money(amount_raw)

        per_month.append({

            "label": f"{ps.isoformat()}~{pe.isoformat()}",

            "period_start": ps.isoformat(),

            "period_end": pe.isoformat(),

            "days": days,

            "monthly_diff": diff,

            "amount_raw": round(amount_raw, 4),

            "amount": amount

        })

        total_days += days

        total_amount += amount

    return {"per_month": per_month, "total_days": total_days, "total_amount": total_amount}

# penalty calculators (use parsed contract from parser.py)

def calc_mod_penalty(parsed: dict, usage_days: int):

    mod = parsed.get('mod_specific', {})

    if not mod:

        return 0

    if usage_days < 365 and mod.get('under_12_months'):

        return mod['under_12_months']

    if usage_days < 730 and mod.get('under_24_months'):

        return mod['under_24_months']

    return 0

def calc_channel_penalty(parsed: dict, package_name: str, usage_days: int):

    pkgs = parsed.get('package_amounts', {})

    if not pkgs:

        return 0

    # match package (exact or fuzzy)

    if package_name in pkgs:

        amt = pkgs[package_name]

    else:

        found = None

        for k in pkgs:

            if package_name in k or k in package_name:

                found = k

                break

        if found:

            amt = pkgs[found]

        else:

            # fallback: choose first

            amt = next(iter(pkgs.values()))

    total_days = parsed.get('contract_days', 730)

    used = usage_days

    penalty_raw = amt / total_days * used * (total_days - used) / total_days

    return round_money(penalty_raw)

def calc_subsidy_penalty(parsed: dict, usage_days: int, rate_key=None):

    daily_map = parsed.get('daily_amounts', {})

    if not daily_map:

        return 0

    total_days = parsed.get('contract_days', 730)

    remaining = max(total_days - usage_days, 0)

    if rate_key and rate_key in daily_map:

        daily = daily_map[rate_key]

    else:

        daily = daily_map.get('100M/40M') or list(daily_map.values())[0]

    return round_money(daily * remaining)
 