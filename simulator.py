"""計算ロジック。

固定費・日常生活費の計算、予算配分、レーダーチャート用スコア算出を担当する。
Streamlit には依存しない純粋なロジックのみを置く。
"""

from __future__ import annotations

import data


# 固定・準固定費の費目（日本語ラベル）。表示順もこの順で扱う。
FIXED_LABELS = [
    "家賃・管理費",
    "光熱・通信費",
    "医療保険",
    "医療費自己負担",
    "ビザ・滞在関連費",
    "その他固定費",
    "車・バイク維持費",
]


def build_fixed_costs(
    age: int,
    rent: float,
    util: float,
    insurance_thb: float,
    visa: float,
    other: float,
    vehicle_thb: float,
) -> dict:
    """固定・準固定費の内訳（THB／月）を返す。

    医療費自己負担は年齢から自動設定する。
    """
    out_of_pocket = data.get_medical_out_of_pocket(age)
    return {
        "家賃・管理費": float(rent),
        "光熱・通信費": float(util),
        "医療保険": float(insurance_thb),
        "医療費自己負担": float(out_of_pocket),
        "ビザ・滞在関連費": float(visa),
        "その他固定費": float(other),
        "車・バイク維持費": float(vehicle_thb),
    }


def _fulfillment(realized: float, desired: float) -> float:
    """充足率（0.0〜1.0）。希望額が0なら満たされているとみなす。"""
    if desired <= 0:
        return 1.0
    return max(0.0, min(realized / desired, 1.0))


def compute_scores(
    desired: dict,
    realized: dict,
    *,
    insurance_thb: float,
    has_insurance: bool,
    out_of_pocket_thb: float,
    rent_thb: float,
    util_thb: float,
    daily_goods_realized: float,
    vehicle_thb: float,
    reserve_thb: float,
    fixed_funded_ratio: float,
    fixed_total_thb: float,
) -> dict:
    """レーダーチャート用の5指標スコア（0〜100）を返す。

    各費目の希望額に対する充足率を基本に算出する。
    """

    def f(key: str) -> float:
        return _fulfillment(realized.get(key, 0.0), desired.get(key, 0.0))

    # Life Satisfaction：外食・交際・趣味の充足率（加重平均）。
    # どれか1つが0でも、他が確保されていれば極端に低くなりすぎないようにする。
    w = data.LIFE_SATISFACTION_WEIGHTS
    life_satisfaction = (
        f("dining_out") * w["dining_out"]
        + f("social") * w["social"]
        + f("leisure") * w["leisure"]
    ) * 100

    # Health：食費・医療費自己負担・医療保険の充足度
    food_ratio = f("food")
    # 医療費自己負担は固定費として確保される前提なので、固定費の充足度を使う
    oop_ratio = fixed_funded_ratio if out_of_pocket_thb > 0 else 1.0
    insurance_ratio = 1.0 if has_insurance else 0.35
    health = (food_ratio + oop_ratio + insurance_ratio) / 3 * 100

    # Mobility：交通費・車バイク維持費の充足度
    transport_ratio = f("local_transport")
    # 車・バイクがあると行動範囲が広がる（最大1.0、無しでもベース0.55）
    if vehicle_thb >= 8000:
        vehicle_ratio = 1.0
    elif vehicle_thb > 0:
        vehicle_ratio = 0.8
    else:
        vehicle_ratio = 0.55
    mobility = (transport_ratio + vehicle_ratio) / 2 * 100

    # Living Environment：家賃管理費・光熱通信費・日用品の充足度
    daily_goods_ratio = _fulfillment(daily_goods_realized, desired.get("daily_goods", 0.0))
    # 家賃・光熱は固定費。固定費が確保できているかで評価
    rent_ratio = fixed_funded_ratio if rent_thb > 0 else 1.0
    util_ratio = fixed_funded_ratio if util_thb > 0 else 1.0
    living_env = (rent_ratio + util_ratio + daily_goods_ratio) / 3 * 100

    # Stability：固定費の確保・医療保険・予備費
    insurance_component = 1.0 if has_insurance else 0.3
    # 予備費：固定費の半月分あれば満点扱い
    if fixed_total_thb > 0:
        reserve_component = min(max(reserve_thb, 0.0) / (fixed_total_thb * 0.5), 1.0)
    else:
        reserve_component = min(max(reserve_thb, 0.0) / 5000.0, 1.0)
    stability = (
        fixed_funded_ratio * 0.5 + insurance_component * 0.25 + reserve_component * 0.25
    ) * 100

    return {
        "Life Satisfaction": round(life_satisfaction, 1),
        "Stability": round(stability, 1),
        "Health": round(health, 1),
        "Mobility": round(mobility, 1),
        "Living Environment": round(living_env, 1),
    }


def simulate_from_lifestyle(
    *,
    fixed_costs: dict,
    style: str,
    fx_rate: float,
    has_insurance: bool,
    insurance_thb: float,
    out_of_pocket_thb: float,
    vehicle_thb: float,
) -> dict:
    """生活から試算するモード。

    希望する生活スタイルを積み上げて月額生活費を算出する。
    """
    desired = dict(data.LIFESTYLE_PRESETS[style])
    daily_total = sum(desired.values())
    fixed_total = sum(fixed_costs.values())
    monthly_thb = fixed_total + daily_total
    monthly_jpy = monthly_thb * fx_rate
    annual_jpy = monthly_jpy * 12

    # 生活から試算では希望額は満たされている前提
    realized = dict(desired)

    scores = compute_scores(
        desired,
        realized,
        insurance_thb=insurance_thb,
        has_insurance=has_insurance,
        out_of_pocket_thb=out_of_pocket_thb,
        rent_thb=fixed_costs.get("家賃・管理費", 0.0),
        util_thb=fixed_costs.get("光熱・通信費", 0.0),
        daily_goods_realized=realized.get("daily_goods", 0.0),
        vehicle_thb=vehicle_thb,
        reserve_thb=0.0,
        fixed_funded_ratio=1.0,
        fixed_total_thb=fixed_total,
    )

    return {
        "fixed_costs": fixed_costs,
        "fixed_total_thb": fixed_total,
        "daily_costs": realized,
        "daily_total_thb": daily_total,
        "monthly_thb": monthly_thb,
        "monthly_jpy": monthly_jpy,
        "annual_jpy": annual_jpy,
        "scores": scores,
    }


def allocate_daily_costs(desired: dict, remaining_thb: float) -> dict:
    """日常生活費の配分を行う。

    生活の土台（基礎生活費）を優先して守りつつ、楽しみ・余白費は
    予算に応じて比例配分で圧縮する。特定費目だけが極端に0にならないようにする。

    - 残額が希望額以上：全費目を希望額どおり（余りは呼び出し側で予備費に）
    - 不足時：
        1. 基礎生活費の最低ライン（食費70%・日用品50%・交通費50%）を確保
        2. 最低ラインにも届かない場合は、基礎生活費内で比例配分
        3. 最低ライン確保後の残りは、基礎の上積み分と楽しみ・余白費に
           希望額に対する比例で配分
    """
    allocated = {k: 0.0 for k in desired}
    desired_total = sum(desired.values())

    if remaining_thb <= 0 or desired_total <= 0:
        if remaining_thb >= desired_total and desired_total > 0:
            return dict(desired)
        return allocated

    # 希望額をすべて賄える場合
    if remaining_thb >= desired_total:
        return dict(desired)

    basic = data.BASIC_CATEGORIES
    enjoy = data.ENJOYMENT_CATEGORIES

    # 基礎生活費の最低ライン
    basic_min = {k: desired.get(k, 0.0) * data.BASIC_MIN_RATIO.get(k, 0.0) for k in basic}
    basic_min_total = sum(basic_min.values())

    if remaining_thb <= basic_min_total:
        # 最低ラインにも届かない → 基礎生活費内で比例配分
        if basic_min_total > 0:
            for k in basic:
                allocated[k] = remaining_thb * (basic_min[k] / basic_min_total)
        return allocated

    # 最低ラインを確保
    for k in basic:
        allocated[k] = basic_min[k]
    leftover = remaining_thb - basic_min_total

    # 残りを「基礎の上積み（希望まで）」と「楽しみ・余白費（希望まで）」に比例配分
    wants = {}
    for k in basic:
        wants[k] = max(desired.get(k, 0.0) - basic_min[k], 0.0)
    for k in enjoy:
        wants[k] = desired.get(k, 0.0)
    wants_total = sum(wants.values())

    if wants_total <= 0:
        return allocated

    ratio = min(leftover / wants_total, 1.0)
    for k in basic:
        allocated[k] += wants[k] * ratio
    for k in enjoy:
        allocated[k] = wants[k] * ratio

    return allocated


def simulate_from_budget(
    *,
    fixed_costs: dict,
    style: str,
    fx_rate: float,
    budget_jpy: float,
    has_insurance: bool,
    insurance_thb: float,
    out_of_pocket_thb: float,
    vehicle_thb: float,
) -> dict:
    """予算から試算するモード。

    月額予算から固定・準固定費を先に差し引き、残りを日常生活費に配分する。
    予算を無理に使い切らず、余剰は予備費として残す。
    """
    desired = dict(data.LIFESTYLE_PRESETS[style])
    desired_total = sum(desired.values())
    fixed_total = sum(fixed_costs.values())

    budget_thb = budget_jpy / fx_rate
    required_thb = fixed_total + desired_total  # 希望どおりの生活に必要な額

    allocated = {k: 0.0 for k in desired}

    if budget_thb <= fixed_total:
        # 予算が固定費すら賄えない
        fixed_funded_ratio = (budget_thb / fixed_total) if fixed_total > 0 else 1.0
        reserve_thb = 0.0
        remaining_after_fixed = budget_thb - fixed_total  # 負の値
    else:
        fixed_funded_ratio = 1.0
        remaining = budget_thb - fixed_total
        # 生活の土台を優先しつつ、楽しみ・余白費は比例配分で圧縮する
        allocated = allocate_daily_costs(desired, remaining)
        reserve_thb = max(remaining - sum(allocated.values()), 0.0)
        remaining_after_fixed = remaining

    daily_funded = sum(allocated.values())
    fulfillment_ratio = (daily_funded / desired_total) if desired_total > 0 else 1.0

    # 希望額との差分（費目別）
    diff_by_category = {k: allocated[k] - desired[k] for k in desired}

    scores = compute_scores(
        desired,
        allocated,
        insurance_thb=insurance_thb,
        has_insurance=has_insurance,
        out_of_pocket_thb=out_of_pocket_thb,
        rent_thb=fixed_costs.get("家賃・管理費", 0.0),
        util_thb=fixed_costs.get("光熱・通信費", 0.0),
        daily_goods_realized=allocated.get("daily_goods", 0.0),
        vehicle_thb=vehicle_thb,
        reserve_thb=reserve_thb,
        fixed_funded_ratio=fixed_funded_ratio,
        fixed_total_thb=fixed_total,
    )

    return {
        "budget_jpy": budget_jpy,
        "budget_thb": budget_thb,
        "fixed_costs": fixed_costs,
        "fixed_total_thb": fixed_total,
        "desired": desired,
        "desired_total_thb": desired_total,
        "required_thb": required_thb,
        "required_jpy": required_thb * fx_rate,
        "allocated": allocated,
        "daily_funded_thb": daily_funded,
        "diff_by_category": diff_by_category,
        "fulfillment_ratio": fulfillment_ratio,
        "reserve_thb": max(reserve_thb, 0.0),
        "reserve_jpy": max(reserve_thb, 0.0) * fx_rate,
        "remaining_after_fixed_thb": remaining_after_fixed,
        "diff_vs_budget_jpy": budget_jpy - required_thb * fx_rate,
        "fixed_funded_ratio": fixed_funded_ratio,
        "scores": scores,
    }
