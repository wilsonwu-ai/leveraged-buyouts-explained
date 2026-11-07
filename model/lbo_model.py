#!/usr/bin/env python3
"""Illustrative leveraged buyout behind the page "Leveraged buyouts, explained".

An illustrative company, not a real deal. It uses the same inputs as the worked example in
"Buying a business, explained" (wilsonwu-ai.github.io/buying-a-business-explained) so the two pages agree.

Run: python3 -I model/lbo_model.py   -> writes model/lbo_model.json (merged into model/site_data.json by build_data.py)

Formulas (all shown on the page or in the repo):
- Cash flow available for debt service (CFADS) = EBITDA x (1 - cash tax share) - capex share x revenue
- Project cost = price + closing costs and cash reserve
- Buyer cash = 5% of project; seller note on full standby = 5% of project; SBA loan = the rest (minus any investors)
- Yearly SBA payment = 12 x monthly annuity payment at the loan rate over 10 years
- DSCR = CFADS / yearly SBA payment (lenders in the example want at least 1.25x)
- Sale price = exit multiple x exit-year EBITDA; owner's proceeds = sale price - SBA balance - seller note with interest

Simplifications (stated on the page): SBA rules follow one SBA loan broker's reading of SOP 50 10 8.1; ignores the SBA
guaranty fee, lender fees, working-capital swings, taxes on the sale and deal costs at exit. Cash taxes are a flat 10% of
EBITDA; capex is 2% of revenue. The standby note accrues 6% a year and is repaid from the sale. Not investment, legal or
tax advice.
"""
import json
import math
from pathlib import Path

# ---------- inputs (same as the first explainer) ----------
EBITDA = 1_000_000
REVENUE = 5_000_000
TAX = 0.10
CAPEX = 0.02
CLOSING = 250_000              # closing costs plus a cash cushion, same total as the first explainer
CLOSING_FEES = 150_000         # illustrative split: quality of earnings, lawyers, lender and other fees
RESERVE = CLOSING - CLOSING_FEES   # cash cushion left in the bank account on Day 1
DSO_DAYS = 45                  # illustrative: customers pay about 45 days after the work
SBA_RATE, SBA_YEARS = 0.0975, 10
STANDBY_RATE = 0.06
INJECTION = 0.10
OWN_CASH = 0.05
DSCR_FLOOR = 1.25
SBA_CAP = 5_000_000
PREF, STEP_UP = 0.10, 2.0
ENTRY_MULTIPLE = 4.0
HOLD = 6                      # the page talks about selling in 5 to 7 years; the example uses 6

SCENARIOS = {
    # name: (yearly EBITDA growth, exit multiple, one-time EBITDA change in year 1)
    "base": (0.07, 4.5, 0.0),      # the plan: growth from sales, pricing and AI-run operations, a modest size premium
    "flat": (0.00, 4.0, 0.0),      # nothing improves: value comes only from paying down the loan
    "downside": (0.00, 3.5, -0.20),  # earnings fall 20% in year 1 and stay there; buyers pay less
    "break": (0.00, 3.5, -0.35),     # earnings fall 35%: the company can no longer cover the loan payment
}
LABELS = {"base": "If the plan works", "flat": "Nothing improves", "downside": "Earnings fall 20%",
          "break": "Earnings fall 35%"}
STACK_LABELS = {"a": "Pay 4.0x", "b": "Pay 5.0x", "c": "Pay 5.0x, investors fill the gap",
                "d": "Highest price the bank test allows"}
# Illustrative quality of earnings: what the seller's numbers show versus what holds up.
QOE_STEPS = [("Repairs called one-time that happen every year", -80_000),
             ("Relatives on payroll who do real work", -70_000),
             ("Year-end jobs counted before they were finished", -100_000)]
# Every spare dollar after the loan payment is assumed to go back into the business (hiring, systems, working capital),
# so the owner's return below counts sale proceeds only. cash_after_debt is kept for reference.


def cfads(ebitda=EBITDA, revenue=REVENUE):
    return ebitda * (1 - TAX) - CAPEX * revenue


def annual_payment(loan, rate=SBA_RATE, years=SBA_YEARS):
    r, n = rate / 12, years * 12
    return 12 * loan * r / (1 - (1 + r) ** -n)


def balance(loan, years_paid, rate=SBA_RATE, years=SBA_YEARS):
    r, n = rate / 12, years * 12
    m = loan * r / (1 - (1 + r) ** -n)
    left = n - 12 * years_paid
    return 0.0 if left <= 0 else m * (1 - (1 + r) ** -left) / r


def loan_for_payment(payment, rate=SBA_RATE, years=SBA_YEARS):
    r, n = rate / 12, years * 12
    return (payment / 12) * (1 - (1 + r) ** -n) / r


def irr(cfs):
    lo, hi = -0.99, 10.0
    npv = lambda x: sum(cf / (1 + x) ** i for i, cf in enumerate(cfs))
    for _ in range(400):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def stack(price, investors=0.0):
    project = price + CLOSING
    own = OWN_CASH * project
    standby = (INJECTION - OWN_CASH) * project
    sba = project - own - standby - investors
    pay = annual_payment(sba)
    return {"price": price, "multiple": price / EBITDA, "project_cost": project, "closing_and_reserve": CLOSING,
            "buyer_cash": own, "standby_seller_note": standby, "investor_equity": investors, "sba_loan": sba,
            "seller_cash_at_close": price - standby,
            "sba_share_of_project_pct": 100 * sba / project, "annual_sba_payment": pay, "cfads": cfads(),
            "dscr": cfads() / pay, "cash_left_after_payment": cfads() - pay, "passes": cfads() / pay >= DSCR_FLOOR,
            "sba_cap_ok": sba <= SBA_CAP}


def scenario(name, price=ENTRY_MULTIPLE * EBITDA, years=HOLD):
    g, exit_m, shock = SCENARIOS[name]
    s = stack(price)
    rows, flows = [], [-s["buyer_cash"]]
    for t in range(0, years + 1):
        e = EBITDA * (1 + shock if t >= 1 else 1) * (1 + g) ** t
        rev = REVENUE * (1 + shock if t >= 1 else 1) * (1 + g) ** t
        debt = balance(s["sba_loan"], t)
        note = s["standby_seller_note"] * (1 + STANDBY_RATE) ** t
        cash_after_debt = 0.0 if t == 0 else max(0.0, cfads(e, rev) - s["annual_sba_payment"])
        dscr = None if t == 0 else cfads(e, rev) / s["annual_sba_payment"]
        rows.append({"year": t, "ebitda": e, "revenue": rev, "sba_balance": debt, "note_balance": note,
                     "cash_after_debt": cash_after_debt, "dscr": dscr})
        if t >= 1:
            flows.append(cash_after_debt)
    e_exit = rows[-1]["ebitda"]
    sale = exit_m * e_exit
    proceeds = max(0.0, sale - rows[-1]["sba_balance"] - rows[-1]["note_balance"])
    flows[-1] += proceeds
    along_the_way = sum(r["cash_after_debt"] for r in rows[1:])
    growth_part = (e_exit - EBITDA) * ENTRY_MULTIPLE
    multiple_part = (exit_m - ENTRY_MULTIPLE) * e_exit
    return {"name": name, "growth_pct": 100 * g, "exit_multiple": exit_m, "year1_shock_pct": 100 * shock,
            "hold_years": years, "entry_price": price, "exit_ebitda": e_exit,
            "bridge": {"price_paid": price, "earnings_growth": growth_part, "multiple_change": multiple_part,
                       "sale_price": sale, "sba_still_owed": rows[-1]["sba_balance"],
                       "seller_note_with_interest": rows[-1]["note_balance"], "owner_proceeds": proceeds},
            "sba_paid_down": s["sba_loan"] - rows[-1]["sba_balance"],
            "cash_along_the_way": along_the_way, "buyer_cash_in": s["buyer_cash"],
            "buyer_cash_back": along_the_way + proceeds,
            "moic_with_payouts": (along_the_way + proceeds) / s["buyer_cash"], "irr_with_payouts_pct": 100 * irr(flows),
            "moic_proceeds_only": proceeds / s["buyer_cash"],
            "irr_proceeds_only_pct": 100 * irr([-s["buyer_cash"]] + [0.0] * (years - 1) + [proceeds]) if proceeds > 0 else -100.0,
            "yearly_shortfall": max(0.0, s["annual_sba_payment"] - cfads(rows[-1]["ebitda"], rows[-1]["revenue"])),
            "min_dscr": min(r["dscr"] for r in rows[1:]), "rows": rows}


def qoe():
    claimed = EBITDA - sum(a for _, a in QOE_STEPS)
    items = [{"label": "EBITDA in the seller's numbers, with add-backs", "amount": claimed, "kind": "total"}]
    items += [{"label": l, "amount": a, "kind": "step"} for l, a in QOE_STEPS]
    items.append({"label": "EBITDA that holds up after quality of earnings", "amount": EBITDA, "kind": "total"})
    return {"items": items, "claimed_ebitda": claimed, "verified_ebitda": EBITDA, "gap": claimed - EBITDA,
            "multiple": ENTRY_MULTIPLE, "price_on_claimed": ENTRY_MULTIPLE * claimed,
            "price_on_verified": ENTRY_MULTIPLE * EBITDA, "overpay": ENTRY_MULTIPLE * (claimed - EBITDA)}


def day1(weeks=13):
    """13 weeks after closing. Weekly sales and cash costs are flat. 'peg': the receivables come with the business, so
    customer payments keep arriving from week 1. 'no_ar': the seller keeps the receivables, so nothing arrives until
    customers pay for the new owner's first work, about DSO_DAYS later. Loan payments in weeks 5, 9 and 13."""
    s = stack(ENTRY_MULTIPLE * EBITDA)
    sales_w, costs_w = REVENUE / 52, (REVENUE - EBITDA) / 52
    pay_m, pay_weeks = s["annual_sba_payment"] / 12, {5, 9, 13}
    first_in = math.ceil(DSO_DAYS / 7) + 1
    cash_peg = cash_no = RESERVE
    rows = [{"week": 0, "cash_peg": cash_peg, "cash_no_ar": cash_no}]
    for w in range(1, weeks + 1):
        out = costs_w + (pay_m if w in pay_weeks else 0.0)
        cash_peg += sales_w - out
        cash_no += (sales_w if w >= first_in else 0.0) - out
        rows.append({"week": w, "cash_peg": cash_peg, "cash_no_ar": cash_no})
    low_no = min(r["cash_no_ar"] for r in rows)
    return {"weeks": rows, "reserve": RESERVE, "closing_fees": CLOSING_FEES, "weekly_sales": sales_w,
            "weekly_costs": costs_w, "monthly_loan_payment": pay_m, "dso_days": DSO_DAYS, "first_payment_week": first_in,
            "low_point_no_ar": low_no, "shortfall_no_ar": max(0.0, -low_no), "cash_needed_no_ar": RESERVE - low_no,
            "low_point_peg": min(r["cash_peg"] for r in rows),
            "case_labels": {"peg": "Receivables come with the business", "no_ar": "Seller keeps the receivables"}}


def main():
    a = stack(4_000_000)
    b = stack(5_000_000)
    need = (b["project_cost"] * (1 - INJECTION)) - loan_for_payment(cfads() / DSCR_FLOOR)
    c = stack(5_000_000, need)
    price_ok = loan_for_payment(cfads() / DSCR_FLOOR) / (1 - INJECTION) - CLOSING
    d = stack(price_ok)
    sens = []
    m = 3.5
    while m <= 5.5001:
        s = stack(m * EBITDA)
        sens.append({"multiple": round(m, 2), "price": s["price"], "sba_loan": s["sba_loan"],
                     "annual_sba_payment": s["annual_sba_payment"], "dscr": s["dscr"], "passes": s["passes"]})
        m += 0.25
    out = {
        "inputs": {"ebitda": EBITDA, "revenue": REVENUE, "tax_share_pct": 100 * TAX, "capex_share_pct": 100 * CAPEX,
                   "closing_and_reserve": CLOSING, "sba_rate_pct": 100 * SBA_RATE, "sba_years": SBA_YEARS,
                   "standby_rate_pct": 100 * STANDBY_RATE, "injection_pct": 100 * INJECTION,
                   "own_cash_pct": 100 * OWN_CASH, "dscr_floor": DSCR_FLOOR, "sba_cap": SBA_CAP,
                   "pref_pct": 100 * PREF, "step_up": STEP_UP, "entry_multiple": ENTRY_MULTIPLE, "hold_years": HOLD,
                   "closing_fees": CLOSING_FEES, "reserve": RESERVE, "dso_days": DSO_DAYS},
        "cfads": cfads(),
        "stack": {"a": a, "b": b, "c": {**c, "investor_equity_needed": need,
                                        "investor_common_pct": 100 * STEP_UP * need / 5_000_000,
                                        "buyer_common_pct": 100 - 100 * STEP_UP * need / 5_000_000},
                  "d": d},
        "sens": sens,
        "scenarios": {k: {**scenario(k), "label": LABELS[k]} for k in SCENARIOS},
        "stack_labels": STACK_LABELS,
        "qoe": qoe(),
        "day1": day1(),
    }
    Path(__file__).with_name("lbo_model.json").write_text(json.dumps(out, indent=1))
    base, flat, down, brk = (out["scenarios"][k] for k in ("base", "flat", "downside", "break"))
    print(f"A 4.0x: project {a['project_cost']:,.0f} SBA {a['sba_loan']:,.0f} pay {a['annual_sba_payment']:,.0f} "
          f"DSCR {a['dscr']:.2f}")
    print(f"B 5.0x: DSCR {b['dscr']:.2f}; C investors {need:,.0f} buyer owns {out['stack']['c']['buyer_common_pct']:.1f}%; "
          f"D price {price_ok:,.0f} ({price_ok / EBITDA:.2f}x)")
    q, d1 = out["qoe"], out["day1"]
    print(f"QoE claimed {q['claimed_ebitda']:,.0f} verified {q['verified_ebitda']:,.0f} overpay at {q['multiple']}x {q['overpay']:,.0f}")
    print(f"Day1 reserve {d1['reserve']:,.0f}; seller keeps AR: low {d1['low_point_no_ar']:,.0f}, cash needed {d1['cash_needed_no_ar']:,.0f}; "
          f"peg low {d1['low_point_peg']:,.0f}; first customer cash week {d1['first_payment_week']}")
    for s in (base, flat, down, brk):
        br = s["bridge"]
        print(f"{s['name']:8s} exit EBITDA {s['exit_ebitda']:,.0f} sale {br['sale_price']:,.0f} owed "
              f"{br['sba_still_owed'] + br['seller_note_with_interest']:,.0f} proceeds {br['owner_proceeds']:,.0f} "
              f"x{s['moic_proceeds_only']:.1f} IRR {s['irr_proceeds_only_pct']:.1f}% minDSCR {s['min_dscr']:.2f} short {s['yearly_shortfall']:,.0f}")


if __name__ == "__main__":
    main()
