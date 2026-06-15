"""タイ移住生活費シミュレーター by Life Spending Designer

Streamlit 画面本体。共通条件をメイン画面上部（STEP 1）で入力し、
STEP 2 で試算方法を選び、STEP 3 で選んだ方法の結果のみを表示する
1ページ内ステップ式の動線。
"""

import pandas as pd
import streamlit as st

import charts
import comments
import data
import simulator


st.set_page_config(page_title=data.APP_TITLE, layout="wide")


def jpy(value: float) -> str:
    return f"{round(value):,} 円"


def thb(value: float) -> str:
    return f"{round(value):,} THB"


def fmt_amount(value: float) -> str:
    """表の金額列用（3桁区切り）。"""
    return f"{round(value):,}"


# ---------------------------------------------------------------------------
# ヘッダー（装飾アイコンは使わない）
# ---------------------------------------------------------------------------
st.title(data.APP_TITLE)
st.caption(data.APP_SUBTITLE)
st.write(
    "月いくらで、どんなタイ生活になるのか。"
    "車や医療保険を入れると何が変わるのか。"
    "生活費の中身とバランスを見える化する、移住後の生活設計ツールです。"
)


# ===========================================================================
# STEP 1：共通条件を入力する
# ===========================================================================
st.write("")
st.divider()
st.header("STEP 1　共通条件を入力する")
st.write("ここで入力した条件は、どちらの試算方法でも共通して使われます。")
st.write("")


def spacer():
    """セクション間の控えめな余白。"""
    st.write("")


# --- 生活スタイル（アプリ全体の前提になる重要な選択肢なので最初に置く）---
st.subheader("生活スタイル")
st.write(
    "まず、想定する暮らし方を選んでください。"
    "この選択により、日常生活費の前提と、レーダーチャートの評価基準が変わります。"
)
style = st.radio(
    "生活スタイル",
    list(data.LIFESTYLE_PRESETS.keys()),
    index=2,
    key="style",
)
st.caption(f"{style}：{data.LIFESTYLE_DESCRIPTIONS[style]}")
st.caption(data.LIFESTYLE_NOTE)

with st.expander("4つの生活スタイルの違いを見る"):
    for name, desc in data.LIFESTYLE_DESCRIPTIONS.items():
        st.markdown(f"- **{name}**：{desc}")

spacer()

# --- 基本条件（年齢・為替）：操作レンジが小さいので2列でも余裕がある ---
st.subheader("基本条件")
b1, b2 = st.columns(2)
with b1:
    age = st.slider(
        "年齢", data.AGE_MIN, data.AGE_MAX, data.AGE_DEFAULT, data.AGE_STEP, key="age"
    )
with b2:
    fx_rate = st.slider(
        "為替レート（1THBあたり円）",
        data.FX_MIN,
        data.FX_MAX,
        data.FX_DEFAULT,
        data.FX_STEP,
        key="fx_rate",
    )

spacer()

# --- 住まい・固定費：金額スライダーは横幅いっぱい（1列）で操作しやすく ---
st.subheader("住まい・固定費")
rent = st.slider(
    "家賃・管理費（THB）",
    data.RENT_MIN,
    data.RENT_MAX,
    data.RENT_DEFAULT,
    data.RENT_STEP,
    key="rent",
)
st.caption("賃貸は家賃、購入済みコンドミニアムは管理費を入力してください。")

util = st.slider(
    "光熱・通信費（THB）",
    data.UTIL_MIN,
    data.UTIL_MAX,
    data.UTIL_DEFAULT,
    data.UTIL_STEP,
    key="util",
)
st.caption("電気代・水道代・Wi-Fi・携帯通信費をまとめた概算です。")
st.caption(data.UTIL_NOTE)

visa = st.slider(
    "ビザ・滞在関連費（THB）",
    data.VISA_MIN,
    data.VISA_MAX,
    data.VISA_DEFAULT,
    data.VISA_STEP,
    key="visa",
)
st.caption("滞在延長、リエントリーパーミット、書類取得などを月割りした概算です。")

other = st.slider(
    "その他固定費（THB）",
    data.OTHER_MIN,
    data.OTHER_MAX,
    data.OTHER_DEFAULT,
    data.OTHER_STEP,
    key="other",
)
st.caption("住居保険、サブスク、日本側で残る固定費など、毎月ほぼ決まって出る費用です。")

spacer()

# --- 医療 ---
st.subheader("医療")
insurance_choice = st.radio(
    "医療保険", data.INSURANCE_CHOICES, key="insurance_choice"
)
default_insurance = data.get_medical_insurance(age)

if insurance_choice == "医療保険に入る":
    insurance_thb = float(default_insurance)
    has_insurance = True
    st.info(f"年齢帯の概算保険料：{thb(insurance_thb)} / 月")
elif insurance_choice == "入らない":
    insurance_thb = 0.0
    has_insurance = False
    st.caption("医療保険料は0THBとして計算します。")
else:  # 自分で入力する
    insurance_thb = float(
        st.slider(
            "医療保険料（THB）",
            data.CUSTOM_INS_MIN,
            data.CUSTOM_INS_MAX,
            int(default_insurance),
            data.CUSTOM_INS_STEP,
            key="custom_insurance",
        )
    )
    has_insurance = insurance_thb > 0
st.caption(data.INSURANCE_NOTE)

spacer()

# --- 移動手段 ---
st.subheader("移動手段")
vehicle_choice = st.radio(
    "車・バイク",
    list(data.VEHICLE_COSTS.keys()),
    key="vehicle_choice",
)
st.caption("車・バイク維持費は、生活スタイルとは別に加算します。")

with st.expander("車・バイクの詳細設定"):
    motorbike_cost = st.slider(
        "バイク維持費（THB）", 0, 10000, data.VEHICLE_DEFAULT_MOTORBIKE, 500, key="motorbike_cost"
    )
    car_cost = st.slider(
        "車維持費（THB）", 0, 30000, data.VEHICLE_DEFAULT_CAR, 500, key="car_cost"
    )

if vehicle_choice == "なし":
    vehicle_thb = 0.0
elif vehicle_choice == "バイクあり":
    vehicle_thb = float(motorbike_cost)
elif vehicle_choice == "車あり":
    vehicle_thb = float(car_cost)
else:  # 車＋バイクあり
    vehicle_thb = float(car_cost + motorbike_cost)

st.caption(data.VEHICLE_NOTE)


# 年齢別の医療費自己負担
out_of_pocket = data.get_medical_out_of_pocket(age)

# 固定・準固定費を構築（両方の試算で共通利用）
fixed_costs = simulator.build_fixed_costs(
    age=age,
    rent=rent,
    util=util,
    insurance_thb=insurance_thb,
    visa=visa,
    other=other,
    vehicle_thb=vehicle_thb,
)


# ---------------------------------------------------------------------------
# 表示用ヘルパー
# ---------------------------------------------------------------------------
def render_fixed_table(fixed: dict) -> pd.DataFrame:
    rows = [{"費目": k, "月額(THB)": fmt_amount(v)} for k, v in fixed.items()]
    rows.append({"費目": "固定費 合計", "月額(THB)": fmt_amount(sum(fixed.values()))})
    return pd.DataFrame(rows)


def render_balance_section(scores: dict):
    """生活バランス：横幅いっぱいの大きめレーダーチャート。"""
    st.markdown("#### 生活バランス")
    st.plotly_chart(charts.make_radar_chart(scores), width="stretch")


def render_radar_guide_section():
    """レーダーチャートの各指標説明と注記。"""
    st.markdown("#### レーダーチャートの見方")

    desc_left, desc_right = st.columns(2)
    mid = (len(charts.RADAR_AXES) + 1) // 2
    with desc_left:
        for axis in charts.RADAR_AXES[:mid]:
            st.markdown(f"- **{axis}**：{charts.RADAR_DESCRIPTIONS[axis]}")
    with desc_right:
        for axis in charts.RADAR_AXES[mid:]:
            st.markdown(f"- **{axis}**：{charts.RADAR_DESCRIPTIONS[axis]}")

    st.write("")
    st.caption(charts.RADAR_BALANCE_NOTE)
    st.caption(charts.RADAR_NOTE)


def render_comments(comment_list: list[str]):
    if not comment_list:
        return
    st.subheader("結果の分析")
    for c in comment_list:
        st.info(c)


# ===========================================================================
# STEP 2：試算方法を選ぶ
# ===========================================================================
st.write("")
st.divider()
st.header("STEP 2　試算方法を選ぶ")
st.write("")
method = st.radio(
    "試算方法",
    ["生活から試算する", "予算から試算する"],
    label_visibility="collapsed",
    horizontal=True,
    key="method",
)


# ===========================================================================
# STEP 3：結果を見る
# ===========================================================================
st.write("")
st.divider()
st.header("STEP 3　結果を見る")
st.write("")


def show_lifestyle_result():
    st.subheader("生活から試算する")
    st.write("希望する生活スタイルを積み上げると、月いくら必要かを試算します。")

    result = simulator.simulate_from_lifestyle(
        fixed_costs=fixed_costs,
        style=style,
        fx_rate=fx_rate,
        has_insurance=has_insurance,
        insurance_thb=insurance_thb,
        out_of_pocket_thb=out_of_pocket,
        vehicle_thb=vehicle_thb,
    )

    c1, c2 = st.columns(2)
    c1.metric("月額生活費（円）", jpy(result["monthly_jpy"]))
    c2.metric("月額生活費（THB）", thb(result["monthly_thb"]))

    st.write("")

    render_balance_section(result["scores"])

    fixed_ratio = (
        result["fixed_total_thb"] / result["monthly_thb"] * 100
        if result["monthly_thb"]
        else 0
    )

    life_comments = comments.build_comments(
        mode="lifestyle",
        has_insurance=has_insurance,
        vehicle_choice=vehicle_choice,
        style=style,
        fixed_ratio=fixed_ratio,
        scores=result["scores"],
    )
    render_comments(life_comments)

    st.write("")
    render_radar_guide_section()

    st.write("")

    # 費目別内訳：左に固定・準固定費、右に日常生活費
    st.markdown("#### 費目別内訳")
    fixed_col, daily_col = st.columns(2)
    with fixed_col:
        st.markdown("**固定・準固定費**")
        st.dataframe(
            render_fixed_table(result["fixed_costs"]), hide_index=True, width="stretch"
        )
    with daily_col:
        st.markdown("**日常生活費**")
        daily_rows = [
            {"費目": data.CATEGORY_LABELS[k], "月額(THB)": fmt_amount(v)}
            for k, v in result["daily_costs"].items()
        ]
        daily_rows.append(
            {"費目": "日常生活費 合計", "月額(THB)": fmt_amount(result["daily_total_thb"])}
        )
        st.dataframe(pd.DataFrame(daily_rows), hide_index=True, width="stretch")


def show_budget_result():
    st.subheader("予算から試算する")
    st.write(
        "月額予算から固定・準固定費を先に差し引き、残りを日常生活費に配分します。"
        "予算を無理に使い切らず、余りは予備費として残します。"
    )

    budget_jpy = st.slider(
        "月額予算（円）",
        data.BUDGET_MIN,
        data.BUDGET_MAX,
        data.BUDGET_DEFAULT,
        data.BUDGET_STEP,
        key="budget_jpy",
    )

    bresult = simulator.simulate_from_budget(
        fixed_costs=fixed_costs,
        style=style,
        fx_rate=fx_rate,
        budget_jpy=budget_jpy,
        has_insurance=has_insurance,
        insurance_thb=insurance_thb,
        out_of_pocket_thb=out_of_pocket,
        vehicle_thb=vehicle_thb,
    )

    row1_left, row1_right = st.columns(2)
    row1_left.metric("月額予算（円）", jpy(bresult["budget_jpy"]))
    row1_right.metric("必要生活費（円）", jpy(bresult["required_jpy"]))

    row2_left, row2_right = st.columns(2)
    diff = bresult["diff_vs_budget_jpy"]
    row2_left.metric("予算との差額（円）", jpy(diff))
    row2_right.metric(
        "日常生活費充足率", f"{bresult['fulfillment_ratio'] * 100:.0f}%"
    )

    if bresult["remaining_after_fixed_thb"] < 0:
        st.warning(
            "月額予算が固定・準固定費を下回っています。"
            "日常生活費にまわせるお金がありません。家賃や車などの見直しが必要です。"
        )

    st.metric("予備費として残るお金（円）", jpy(bresult["reserve_jpy"]))
    st.caption(f"（{thb(bresult['reserve_thb'])}）")

    st.write("")

    render_balance_section(bresult["scores"])

    budget_monthly_jpy = (
        bresult["fixed_total_thb"] + bresult["daily_funded_thb"]
    ) * fx_rate
    budget_comments = comments.build_comments(
        mode="budget",
        has_insurance=has_insurance,
        vehicle_choice=vehicle_choice,
        style=style,
        fulfillment_ratio=bresult["fulfillment_ratio"],
        scores=bresult["scores"],
        reserve_jpy=bresult["reserve_jpy"],
        monthly_jpy=budget_monthly_jpy,
    )
    render_comments(budget_comments)

    st.write("")
    render_radar_guide_section()

    st.write("")

    # 費目別内訳：左に固定・準固定費、右に日常生活費の配分
    st.markdown("#### 費目別内訳")
    fixed_col, daily_col = st.columns(2)
    with fixed_col:
        st.markdown("**固定・準固定費**")
        st.dataframe(
            render_fixed_table(bresult["fixed_costs"]), hide_index=True, width="stretch"
        )
    with daily_col:
        st.markdown("**日常生活費の配分**")
        alloc_rows = []
        for k in data.LIFESTYLE_PRIORITY:
            alloc_rows.append(
                {
                    "費目": data.CATEGORY_LABELS[k],
                    "配分額(THB)": fmt_amount(bresult["allocated"][k]),
                    "希望額(THB)": fmt_amount(bresult["desired"][k]),
                    "希望との差分(THB)": fmt_amount(bresult["diff_by_category"][k]),
                }
            )
        st.dataframe(pd.DataFrame(alloc_rows), hide_index=True, width="stretch")


# STEP 2 で選ばれた方法の結果だけを表示する
if method == "生活から試算する":
    show_lifestyle_result()
else:
    show_budget_result()


# ---------------------------------------------------------------------------
# 注意書き
# ---------------------------------------------------------------------------
st.divider()
st.caption(data.DISCLAIMER)
