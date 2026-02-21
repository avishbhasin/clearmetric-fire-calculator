"""
Stress test for FIRE Calculator — tests all calculation paths with edge cases.
Extracts the calculation engine from app.py and hammers it with boundary conditions.
"""

import numpy as np
import sys

EQUITY_RETURN = 0.10
EQUITY_STD = 0.16
BOND_RETURN = 0.05
BOND_STD = 0.04

def fire_calculations(
    current_age=30, target_retire_age=45, life_expectancy=90,
    annual_income=100_000, tax_rate=25, monthly_expenses=4_000,
    current_savings=150_000, monthly_investment=2_500,
    equity_pct=70, inflation=3.0, income_growth=3,
    swr=4.0, ss_monthly=0, ss_start_age=67,
):
    """Mirrors the calculation engine from app.py exactly."""
    years_to_fire = max(target_retire_age - current_age, 1)
    years_in_retirement = max(life_expectancy - target_retire_age, 1)
    inflation_rate = inflation / 100
    swr_rate = swr / 100
    equity_frac = equity_pct / 100
    bond_frac = 1 - equity_frac
    income_growth_rate = income_growth / 100

    nominal_return = equity_frac * EQUITY_RETURN + bond_frac * BOND_RETURN
    real_return = nominal_return - inflation_rate
    monthly_real = (1 + real_return) ** (1/12) - 1

    annual_expenses = monthly_expenses * 12
    expenses_at_retirement = annual_expenses * (1 + inflation_rate) ** years_to_fire
    fire_number = expenses_at_retirement / swr_rate if swr_rate > 0 else float('inf')

    fv_current = current_savings * (1 + real_return) ** years_to_fire
    fv_investments = 0
    monthly_inv = monthly_investment
    for year in range(years_to_fire):
        for month in range(12):
            months_left = (years_to_fire - year) * 12 - month
            fv_investments += monthly_inv * (1 + monthly_real) ** months_left
        monthly_inv *= (1 + income_growth_rate)

    projected_corpus = fv_current + fv_investments
    gap = fire_number - projected_corpus
    on_track = projected_corpus >= fire_number

    # Years to FIRE
    def calc_years_to_fire():
        corpus = current_savings
        mi = monthly_investment
        for yr in range(100):
            for _ in range(12):
                corpus = corpus * (1 + monthly_real) + mi
            if corpus >= fire_number:
                return yr + 1
            mi *= (1 + income_growth_rate)
        return None

    actual_fire_years = calc_years_to_fire()
    actual_fire_age = current_age + actual_fire_years if actual_fire_years else None

    # Extra monthly needed
    def calc_additional_monthly():
        if on_track:
            return 0
        months = years_to_fire * 12
        if monthly_real == 0:
            return gap / months
        return gap * monthly_real / ((1 + monthly_real) ** months - 1)

    extra_monthly = calc_additional_monthly()

    net_annual_income = annual_income * (1 - tax_rate / 100)
    savings_rate = (monthly_investment * 12) / net_annual_income * 100 if net_annual_income > 0 else 0

    return {
        "fire_number": fire_number,
        "projected_corpus": projected_corpus,
        "gap": gap,
        "on_track": on_track,
        "actual_fire_years": actual_fire_years,
        "actual_fire_age": actual_fire_age,
        "extra_monthly": extra_monthly,
        "savings_rate": savings_rate,
        "real_return": real_return,
        "monthly_real": monthly_real,
        "expenses_at_retirement": expenses_at_retirement,
        "years_to_fire": years_to_fire,
    }


def run_monte_carlo_test(
    n_sims=100, yrs=15, current=150_000, monthly=2_500,
    inc_growth=0.03, eq_frac=0.70, bnd_frac=0.30, infl=0.03,
    swr_r=0.04, expense_retire=72_000, ss_monthly_val=0,
    ss_age=67, retire_age=45, life_exp=90,
):
    """Mirrors Monte Carlo from app.py."""
    rng = np.random.default_rng(42)
    blended_mean = eq_frac * EQUITY_RETURN + bnd_frac * BOND_RETURN - infl
    blended_std = np.sqrt((eq_frac * EQUITY_STD) ** 2 + (bnd_frac * BOND_STD) ** 2)

    final_corpus = np.zeros(n_sims)
    all_paths = np.zeros((n_sims, yrs + 1))

    for sim in range(n_sims):
        corpus = current
        mi = monthly
        all_paths[sim, 0] = corpus

        for yr in range(yrs):
            annual_r = rng.normal(blended_mean, blended_std)
            corpus += mi * 12
            corpus *= (1 + annual_r)
            mi *= (1 + inc_growth)
            all_paths[sim, yr + 1] = corpus

        final_corpus[sim] = corpus

    target = expense_retire / swr_r if swr_r > 0 else float('inf')
    success_rate = np.mean(final_corpus >= target) * 100

    retire_years = life_exp - retire_age
    survived = np.zeros(n_sims, dtype=bool)
    for sim in range(n_sims):
        c = final_corpus[sim]
        annual_withdraw = expense_retire
        for yr in range(max(retire_years, 0)):
            annual_r = rng.normal(blended_mean * 0.8, blended_std)
            age_now = retire_age + yr
            ss_income = ss_monthly_val * 12 if age_now >= ss_age else 0
            c = c * (1 + annual_r) - annual_withdraw + ss_income
            annual_withdraw *= (1 + infl)
            if c <= 0:
                break
        survived[sim] = c > 0

    survival_rate = np.mean(survived) * 100

    return {
        "success_rate": success_rate,
        "survival_rate": survival_rate,
        "median": float(np.median(final_corpus)),
        "p10": float(np.percentile(final_corpus, 10)),
        "p90": float(np.percentile(final_corpus, 90)),
        "all_paths_shape": all_paths.shape,
    }


# ================================================================
# TEST CASES
# ================================================================
passed = 0
failed = 0
errors = []

def test(name, fn):
    global passed, failed, errors
    try:
        result = fn()
        if result is True or result is None:
            passed += 1
            print(f"  ✅ {name}")
        else:
            failed += 1
            errors.append(f"{name}: returned {result}")
            print(f"  ❌ {name}: {result}")
    except Exception as e:
        failed += 1
        errors.append(f"{name}: EXCEPTION {e}")
        print(f"  💥 {name}: {type(e).__name__}: {e}")


print("=" * 60)
print("FIRE CALCULATOR — STRESS TEST SUITE")
print("=" * 60)

# --- Default values (sanity check) ---
print("\n1. DEFAULT VALUES")
def test_defaults():
    r = fire_calculations()
    assert r["fire_number"] > 0, f"FIRE number should be positive, got {r['fire_number']}"
    assert r["projected_corpus"] > 0, f"Projected corpus should be positive"
    assert r["savings_rate"] > 0, f"Savings rate should be positive"
    assert r["actual_fire_years"] is not None, f"Should be able to calculate FIRE years"
    assert r["actual_fire_age"] > 30, f"FIRE age should be > current age"
    assert not np.isnan(r["fire_number"]), "FIRE number should not be NaN"
    assert not np.isinf(r["fire_number"]), "FIRE number should not be infinite"
    return True
test("Default inputs produce valid results", test_defaults)

# --- Zero expenses ---
print("\n2. ZERO EXPENSES")
def test_zero_expenses():
    r = fire_calculations(monthly_expenses=0)
    assert r["fire_number"] == 0, f"FIRE number should be 0 with 0 expenses, got {r['fire_number']}"
    assert r["on_track"] == True, "Should be on track with 0 expenses"
    return True
test("Zero expenses → FIRE number is 0, on track", test_zero_expenses)

# --- Zero savings, zero investment ---
print("\n3. ZERO EVERYTHING")
def test_zero_savings_zero_invest():
    r = fire_calculations(current_savings=0, monthly_investment=0)
    assert r["projected_corpus"] == 0, f"Projected corpus should be 0, got {r['projected_corpus']}"
    assert r["on_track"] == False, "Should NOT be on track with no savings/investment"
    assert r["actual_fire_years"] is None, "Should not be able to reach FIRE"
    return True
test("Zero savings + zero investment → not reachable", test_zero_savings_zero_invest)

# --- Zero income ---
print("\n4. ZERO INCOME")
def test_zero_income():
    r = fire_calculations(annual_income=0)
    assert r["savings_rate"] == 0, f"Savings rate should be 0 with no income, got {r['savings_rate']}"
    return True
test("Zero income → savings rate is 0 (no division by zero)", test_zero_income)

# --- Age edge cases ---
print("\n5. AGE EDGE CASES")
def test_age_equals_target():
    r = fire_calculations(current_age=45, target_retire_age=45)
    assert r["years_to_fire"] == 1, "years_to_fire clamped to 1"
    assert not np.isnan(r["fire_number"]), "No NaN"
    assert not np.isinf(r["projected_corpus"]), "No infinity"
    return True
test("current_age == target_retire_age → clamped to 1 year", test_age_equals_target)

def test_age_past_target():
    r = fire_calculations(current_age=50, target_retire_age=45)
    assert r["years_to_fire"] == 1, "years_to_fire clamped to 1"
    return True
test("current_age > target_retire_age → clamped to 1 year", test_age_past_target)

def test_young_aggressive():
    r = fire_calculations(current_age=18, target_retire_age=25)
    assert r["years_to_fire"] == 7
    assert r["actual_fire_years"] is not None
    return True
test("Age 18 targeting 25 → valid 7-year horizon", test_young_aggressive)

def test_late_retirement():
    r = fire_calculations(current_age=60, target_retire_age=80, life_expectancy=95)
    assert r["years_to_fire"] == 20
    return True
test("Age 60 targeting 80 → 20-year horizon", test_late_retirement)

# --- Life expectancy edge cases ---
print("\n6. LIFE EXPECTANCY EDGE CASES")
def test_life_eq_retire():
    r = fire_calculations(target_retire_age=45, life_expectancy=45)
    assert not np.isnan(r["fire_number"]), "No NaN"
    return True
test("life_expectancy == retire_age → no crash", test_life_eq_retire)

def test_life_below_retire():
    r = fire_calculations(target_retire_age=80, life_expectancy=60)
    assert not np.isnan(r["fire_number"]), "No NaN"
    return True
test("life_expectancy < retire_age → no crash", test_life_below_retire)

# --- Investment allocation extremes ---
print("\n7. ALLOCATION EXTREMES")
def test_all_stocks():
    r = fire_calculations(equity_pct=100)
    expected_return = 1.0 * EQUITY_RETURN + 0.0 * BOND_RETURN
    assert abs(r["real_return"] - (expected_return - 0.03)) < 0.001
    return True
test("100% stocks → correct return calculation", test_all_stocks)

def test_all_bonds():
    r = fire_calculations(equity_pct=0)
    expected_return = 0.0 * EQUITY_RETURN + 1.0 * BOND_RETURN
    assert abs(r["real_return"] - (expected_return - 0.03)) < 0.001
    return True
test("0% stocks (all bonds) → correct return calculation", test_all_bonds)

# --- Inflation edge cases ---
print("\n8. INFLATION EDGE CASES")
def test_high_inflation():
    r = fire_calculations(inflation=6.0)
    assert r["real_return"] < r["real_return"].__class__(0.05), "Real return should be low with 6% inflation"
    assert r["fire_number"] > 0, "FIRE number still positive"
    return True
test("6% inflation → lower real return, still works", test_high_inflation)

def test_inflation_exceeds_returns():
    r = fire_calculations(inflation=6.0, equity_pct=0)  # bonds return 5%, inflation 6%
    assert r["real_return"] < 0, f"Real return should be negative: {r['real_return']}"
    assert r["fire_number"] > 0, "FIRE number still positive"
    return True
test("Inflation > returns → negative real return, no crash", test_inflation_exceeds_returns)

# --- Very large values ---
print("\n9. LARGE VALUES")
def test_millionaire():
    r = fire_calculations(current_savings=5_000_000, monthly_investment=20_000, annual_income=500_000)
    assert r["on_track"] == True, "Millionaire should be on track"
    assert r["fire_number"] > 0
    assert not np.isinf(r["projected_corpus"])
    return True
test("$5M savings, $20K/mo investment → on track, no overflow", test_millionaire)

def test_very_high_expenses():
    r = fire_calculations(monthly_expenses=50_000)
    assert r["fire_number"] > 10_000_000, "FIRE number should be huge"
    assert r["on_track"] == False, "Should not be on track with $50K/mo expenses"
    return True
test("$50K/mo expenses → huge FIRE number, not on track", test_very_high_expenses)

# --- Very small values ---
print("\n10. SMALL VALUES")
def test_tiny_expenses():
    r = fire_calculations(monthly_expenses=100)
    assert r["fire_number"] < 100_000, "FIRE number should be small"
    assert r["on_track"] == True, "Should be on track with $100/mo expenses"
    return True
test("$100/mo expenses → small FIRE number, on track", test_tiny_expenses)

def test_one_dollar_investment():
    r = fire_calculations(monthly_investment=1, current_savings=0)
    assert r["projected_corpus"] > 0, "Even $1/mo grows"
    assert not np.isnan(r["projected_corpus"])
    return True
test("$1/mo investment → small but valid corpus", test_one_dollar_investment)

# --- Tax rate extremes ---
print("\n11. TAX RATE EXTREMES")
def test_zero_tax():
    r = fire_calculations(tax_rate=0)
    expected_sr = (2500 * 12) / 100_000 * 100
    assert abs(r["savings_rate"] - expected_sr) < 0.1
    return True
test("0% tax → full income for savings rate calc", test_zero_tax)

def test_max_tax():
    r = fire_calculations(tax_rate=50)
    expected_sr = (2500 * 12) / (100_000 * 0.5) * 100
    assert abs(r["savings_rate"] - expected_sr) < 0.1
    return True
test("50% tax → halved income for savings rate calc", test_max_tax)

# --- Social Security ---
print("\n12. SOCIAL SECURITY")
def test_social_security():
    r_no_ss = fire_calculations(ss_monthly=0)
    r_ss = fire_calculations(ss_monthly=2000)
    # Core calculations don't change with SS (it only affects MC survival)
    assert r_no_ss["fire_number"] == r_ss["fire_number"], "SS doesn't affect FIRE number"
    return True
test("Social Security doesn't affect FIRE number", test_social_security)

# --- Monte Carlo stress tests ---
print("\n13. MONTE CARLO STRESS TESTS")
def test_mc_default():
    r = run_monte_carlo_test()
    assert 0 <= r["success_rate"] <= 100
    assert 0 <= r["survival_rate"] <= 100
    assert r["median"] > 0
    assert r["p10"] <= r["median"] <= r["p90"]
    assert r["all_paths_shape"] == (100, 16)
    return True
test("MC default → valid percentiles, rates in [0,100]", test_mc_default)

def test_mc_zero_savings():
    r = run_monte_carlo_test(current=0, monthly=0)
    assert r["median"] == 0 or r["median"] < 1, "No growth from nothing"
    return True
test("MC zero savings/investment → near-zero corpus", test_mc_zero_savings)

def test_mc_one_year():
    r = run_monte_carlo_test(yrs=1)
    assert r["all_paths_shape"] == (100, 2)
    assert 0 <= r["success_rate"] <= 100
    return True
test("MC 1-year horizon → valid shape and rates", test_mc_one_year)

def test_mc_high_ss():
    r_no_ss = run_monte_carlo_test(ss_monthly_val=0, ss_age=67, retire_age=45,
                                    current=500_000, monthly=5_000)
    r_ss = run_monte_carlo_test(ss_monthly_val=5000, ss_age=45, retire_age=45,
                                 current=500_000, monthly=5_000)
    assert r_ss["survival_rate"] >= r_no_ss["survival_rate"], \
        f"SS should help: {r_ss['survival_rate']}% vs {r_no_ss['survival_rate']}% without"
    assert not np.isnan(r_ss["survival_rate"])
    return True
test("MC high Social Security → survival >= no-SS scenario", test_mc_high_ss)

def test_mc_all_stocks():
    r = run_monte_carlo_test(eq_frac=1.0, bnd_frac=0.0)
    assert r["median"] > 0
    assert not np.isnan(r["success_rate"])
    return True
test("MC 100% stocks → no NaN", test_mc_all_stocks)

def test_mc_all_bonds():
    r = run_monte_carlo_test(eq_frac=0.0, bnd_frac=1.0)
    assert r["median"] > 0
    assert not np.isnan(r["success_rate"])
    return True
test("MC 100% bonds → no NaN", test_mc_all_bonds)

def test_mc_negative_real_return():
    r = run_monte_carlo_test(eq_frac=0.0, bnd_frac=1.0, infl=0.06)
    assert not np.isnan(r["success_rate"])
    assert not np.isnan(r["survival_rate"])
    return True
test("MC negative real return → no NaN", test_mc_negative_real_return)

def test_mc_retire_at_life_expectancy():
    r = run_monte_carlo_test(retire_age=90, life_exp=90)
    assert r["survival_rate"] == 100, "0 retirement years → everyone survives"
    return True
test("MC retire_age == life_expectancy → 100% survival", test_mc_retire_at_life_expectancy)

# --- Mathematical consistency ---
print("\n14. MATHEMATICAL CONSISTENCY")
def test_fire_number_formula():
    r = fire_calculations(monthly_expenses=4000, inflation=3.0, swr=4.0,
                          current_age=30, target_retire_age=45)
    annual = 4000 * 12
    inflated = annual * (1.03 ** 15)
    expected_fire = inflated / 0.04
    assert abs(r["fire_number"] - expected_fire) < 1, f"FIRE number mismatch: {r['fire_number']} vs {expected_fire}"
    return True
test("FIRE number = inflated_expenses / SWR", test_fire_number_formula)

def test_on_track_consistency():
    r = fire_calculations()
    if r["on_track"]:
        assert r["gap"] <= 0, f"On track but gap is positive: {r['gap']}"
        assert r["extra_monthly"] == 0, f"On track but extra needed: {r['extra_monthly']}"
    else:
        assert r["gap"] > 0, f"Not on track but gap is negative: {r['gap']}"
        assert r["extra_monthly"] > 0, f"Not on track but no extra needed"
    return True
test("on_track consistency with gap and extra_monthly", test_on_track_consistency)

def test_savings_rate_formula():
    r = fire_calculations(annual_income=100_000, tax_rate=25, monthly_investment=2_500)
    net = 100_000 * 0.75
    expected_sr = (2500 * 12) / net * 100
    assert abs(r["savings_rate"] - expected_sr) < 0.01, f"Savings rate: {r['savings_rate']} vs {expected_sr}"
    return True
test("Savings rate = (investment × 12) / net_income × 100", test_savings_rate_formula)

# ================================================================
# SUMMARY
# ================================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
print("=" * 60)

if errors:
    print("\nFAILURES:")
    for e in errors:
        print(f"  ❌ {e}")
    sys.exit(1)
else:
    print("\n✅ ALL TESTS PASSED — Calculation engine is solid.")
    sys.exit(0)
