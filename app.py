"""タイ移住 月額生活費シミュレーター

Streamlit 画面本体。共通条件をメイン画面上部（STEP 1）で入力し、
STEP 2 で試算方法を選び、STEP 3 で選んだ方法の結果のみを表示する
1ページ内ステップ式の動線。
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import charts
import comments
import data
import simulator


# 参考画像（部屋タイプ）の格納先
ROOM_SAMPLES_DIR = Path(__file__).parent / "assets" / "room_samples"

# 部屋タイプと家賃の目安（住まい固定費の参考情報。計算には使わない）
ROOM_TYPES = [
    {
        "image": "studio.jpg",
        "name": "スタジオ",
        "size": "約25〜35㎡",
        "pattaya": "12,000〜20,000THB/月",
        "bangkok": "12,000〜25,000THB/月",
        "desc": (
            "ベッド・ソファ・簡易キッチンが一体になったコンパクトな部屋。"
            "単身で費用を抑えたい人向け。"
        ),
    },
    {
        "image": "one_bedroom.jpg",
        "name": "1ベッドルーム",
        "size": "約35〜55㎡",
        "pattaya": "20,000〜30,000THB/月",
        "bangkok": "25,000〜45,000THB/月",
        "desc": (
            "リビングと寝室が分かれた標準的な部屋。"
            "単身で長期滞在する人に使いやすい選択肢。"
        ),
    },
    {
        "image": "two_bedroom.jpg",
        "name": "2ベッドルーム",
        "size": "約60〜85㎡",
        "pattaya": "35,000〜55,000THB/月",
        "bangkok": "50,000〜90,000THB/月",
        "desc": (
            "寝室が2つあり、リビングにも余裕のある部屋。"
            "夫婦、来客がある人、荷物が多い人向け。"
        ),
    },
]


st.set_page_config(page_title=data.APP_TITLE, layout="wide")


def jpy(value: float) -> str:
    return f"{round(value):,} 円"


def thb(value: float) -> str:
    return f"{round(value):,} THB"


def fmt_amount(value: float) -> str:
    """表の金額列用（3桁区切り）。"""
    return f"{round(value):,}"


def _step_session_value(key: str, delta: float, lo: float, hi: float, decimals: int):
    """−／＋ボタン用コールバック。step単位で増減し min/max でクランプする。"""
    new_value = st.session_state[key] + delta
    new_value = max(lo, min(hi, new_value))
    st.session_state[key] = round(new_value, decimals) if decimals else int(round(new_value))


def slider_with_steppers(
    label: str,
    *,
    min_value,
    max_value,
    default,
    step,
    key: str,
    decimals: int = 0,
):
    """スライダー＋直下の−／＋ボタン。スマホでも微調整しやすくする。

    値は st.session_state[key] で一元管理し、スライダーとボタンが同期する。
    計算ロジックには影響せず、返り値は従来のスライダーと同じ現在値。
    """
    if key not in st.session_state:
        st.session_state[key] = default

    st.slider(label, min_value=min_value, max_value=max_value, step=step, key=key)

    # −／＋ は横並び1行（左に−、右に＋）。
    # st.columns はスマホ幅で縦積みになるため、横方向コンテナ＋専用CSSで
    # 横並びを固定する。CSSは下記の st-key-stepper_ クラスにのみ効く（他UIに影響しない）。
    with st.container(key=f"stepper_{key}", horizontal=True):
        st.button(
            "−",
            key=f"{key}__minus",
            width="stretch",
            on_click=_step_session_value,
            args=(key, -step, min_value, max_value, decimals),
            help=f"{step} 下げる",
        )
        st.button(
            "＋",
            key=f"{key}__plus",
            width="stretch",
            on_click=_step_session_value,
            args=(key, step, min_value, max_value, decimals),
            help=f"{step} 上げる",
        )
    return st.session_state[key]


# ---------------------------------------------------------------------------
# ヘッダー（装飾アイコンは使わない）
# ---------------------------------------------------------------------------
st.title(data.APP_TITLE)
st.write(
    "月いくらで、どんなタイ生活になるのか。"
    "車や医療保険を入れると何が変わるのか。"
    "生活費の中身とバランスを見える化する生活設計ツールです。"
)
st.markdown(
    f"[{data.ASSET_SIM_NAME}]({data.ASSET_SIM_URL})で必要になる、"
    "海外生活中の月額生活費の目安づくりにも使えます。"
)

# −／＋ステッパー専用CSS。st-key-stepper_ で始まるコンテナ内だけに適用し、
# スマホ幅でも横並び1行を維持する（他のボタン・レイアウトには影響しない）。
st.markdown(
    """
    <style>
    [class*="st-key-stepper_"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0.5rem !important;
    }
    [class*="st-key-stepper_"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    /* ステッパーボタンだけ高さを約20〜25%コンパクトに（横幅・等幅は維持） */
    [class*="st-key-stepper_"] button {
        min-height: 0 !important;
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
        line-height: 1.2 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
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
    age = slider_with_steppers(
        "移住開始時の年齢",
        min_value=data.AGE_MIN,
        max_value=data.AGE_MAX,
        default=data.AGE_DEFAULT,
        step=data.AGE_STEP,
        key="age",
    )
    # 補足文はスライダー＋−／＋ボタン全体にかかる説明なのでボタンの下に置く
    st.markdown(
        "<div style='font-size:0.85rem; color:#888; "
        "margin-top:0.2rem; margin-bottom:1.4rem;'>"
        "※ この年齢をもとに、医療保険費の目安を調整します。"
        "</div>",
        unsafe_allow_html=True,
    )
with b2:
    fx_rate = slider_with_steppers(
        "為替レート（1THBあたり円）",
        min_value=data.FX_MIN,
        max_value=data.FX_MAX,
        default=data.FX_DEFAULT,
        step=data.FX_STEP,
        key="fx_rate",
        decimals=1,
    )

spacer()

# --- 住まい・固定費：金額スライダーは横幅いっぱい（1列）で操作しやすく ---
st.subheader("住まい・固定費")
rent = slider_with_steppers(
    "家賃・管理費（THB）",
    min_value=data.RENT_MIN,
    max_value=data.RENT_MAX,
    default=data.RENT_DEFAULT,
    step=data.RENT_STEP,
    key="rent",
)
st.caption("賃貸は家賃、購入済みコンドミニアムは管理費を入力してください。")


def render_room_card(room: dict):
    """部屋タイプカード（画像＋目安）を描画する。画像が無くても落ちない。"""
    image_path = ROOM_SAMPLES_DIR / room["image"]
    if image_path.exists():
        try:
            st.image(str(image_path), width="stretch")
        except Exception:
            st.caption("（画像を表示できませんでした）")
    else:
        st.caption("（画像が見つかりませんでした）")
    st.markdown(f"**{room['name']}**")
    st.markdown(
        f"{room['size']}  \n"
        f"パタヤ：{room['pattaya']}  \n"
        f"バンコク：{room['bangkok']}"
    )
    st.caption(room["desc"])


with st.expander("部屋タイプと家賃の目安を見る"):
    st.write("タイの家具付きコンドを想定した、住まい固定費の参考です。")

    cols = st.columns(3)
    for col, room in zip(cols, ROOM_TYPES):
        with col:
            render_room_card(room)

    st.write("")
    rent_guide_df = pd.DataFrame(
        [
            {
                "部屋タイプ": r["name"],
                "広さの目安": r["size"],
                "パタヤ家賃目安": r["pattaya"],
                "バンコク家賃目安": r["bangkok"],
            }
            for r in ROOM_TYPES
        ]
    )
    st.dataframe(rent_guide_df, hide_index=True, width="stretch")

    st.caption(
        "家賃目安は、2026年6月時点で確認したHipflat、PropertyScoutなどの"
        "不動産ポータル掲載情報を参考にしています。\n\n"
        "掲載平均では、PattayaはStudio約461USD、1BR約702USD、2BR約1,374USD、"
        "BangkokはStudio約489USD、1BR約771USD、2BR約1,605USDです。"
    )

util = slider_with_steppers(
    "光熱・通信費（THB）",
    min_value=data.UTIL_MIN,
    max_value=data.UTIL_MAX,
    default=data.UTIL_DEFAULT,
    step=data.UTIL_STEP,
    key="util",
)
st.caption("電気代・水道代・Wi-Fi・携帯通信費をまとめた概算です。")
st.caption(data.UTIL_NOTE)

visa = slider_with_steppers(
    "ビザ・滞在関連費（THB）",
    min_value=data.VISA_MIN,
    max_value=data.VISA_MAX,
    default=data.VISA_DEFAULT,
    step=data.VISA_STEP,
    key="visa",
)
st.caption("滞在延長、リエントリーパーミット、書類取得などを月割りした概算です。")

other = slider_with_steppers(
    "その他固定費（THB）",
    min_value=data.OTHER_MIN,
    max_value=data.OTHER_MAX,
    default=data.OTHER_DEFAULT,
    step=data.OTHER_STEP,
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
        slider_with_steppers(
            "医療保険料（THB）",
            min_value=data.CUSTOM_INS_MIN,
            max_value=data.CUSTOM_INS_MAX,
            default=int(default_insurance),
            step=data.CUSTOM_INS_STEP,
            key="custom_insurance",
        )
    )
    has_insurance = insurance_thb > 0
st.caption(data.INSURANCE_NOTE)

with st.expander("医療保険料の参考テーブルを見る"):
    insurance_reference_intro = getattr(
        data,
        "INSURANCE_REFERENCE_INTRO",
        [
            "医療保険料は、Pacific Crossの保険料表を参考にした概算です。",
            "このアプリでは、Premier Plusを基準に医療保険料の目安を反映しています。",
            "参考として、Premier / Premier Plus / Maxima の年齢別年間保険料を表示しています。",
        ],
    )
    insurance_reference_table = getattr(
        data,
        "INSURANCE_REFERENCE_TABLE",
        [
            {"年齢": "51〜55歳", "Premier": 44115, "Premier Plus": 63975, "Maxima": 74289},
            {"年齢": "56〜60歳", "Premier": 50651, "Premier Plus": 73452, "Maxima": 85249},
            {"年齢": "61〜65歳", "Premier": 60455, "Premier Plus": 87669, "Maxima": 101801},
            {"年齢": "66〜70歳", "Premier": 83328, "Premier Plus": 120843, "Maxima": 140322},
            {"年齢": "71〜75歳", "Premier": 124173, "Premier Plus": 180075, "Maxima": 209103},
            {"年齢": "76〜80歳", "Premier": 166654, "Premier Plus": 241683, "Maxima": 280636},
            {"年齢": "81〜85歳", "Premier": 207500, "Premier Plus": 300917, "Maxima": 349420},
            {"年齢": "86〜90歳", "Premier": 264477, "Premier Plus": 379106, "Maxima": 440216},
            {"年齢": "91〜95歳", "Premier": 333199, "Premier Plus": 483205, "Maxima": 561093},
            {"年齢": "96〜99歳", "Premier": 419779, "Premier Plus": 608764, "Maxima": 706889},
        ],
    )
    for line in insurance_reference_intro:
        st.write(line)
    st.caption("単位：THB/年")
    insurance_ref_df = pd.DataFrame(insurance_reference_table)
    for col in ("Premier", "Premier Plus", "Maxima"):
        insurance_ref_df[col] = insurance_ref_df[col].map("{:,}".format)
    st.dataframe(insurance_ref_df, hide_index=True)

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
    motorbike_cost = slider_with_steppers(
        "バイク維持費（THB）",
        min_value=0,
        max_value=10000,
        default=data.VEHICLE_DEFAULT_MOTORBIKE,
        step=500,
        key="motorbike_cost",
    )
    car_cost = slider_with_steppers(
        "車維持費（THB）",
        min_value=0,
        max_value=30000,
        default=data.VEHICLE_DEFAULT_CAR,
        step=500,
        key="car_cost",
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


# 固定・準固定費を構築（両方の試算で共通利用）
# 医療費自己負担は build_fixed_costs が年齢から内部算出するため、
# その結果を再利用して二重 lookup を避ける。
fixed_costs = simulator.build_fixed_costs(
    age=age,
    rent=rent,
    util=util,
    insurance_thb=insurance_thb,
    visa=visa,
    other=other,
    vehicle_thb=vehicle_thb,
)
out_of_pocket = fixed_costs["医療費自己負担"]


# ---------------------------------------------------------------------------
# 表示用ヘルパー
# ---------------------------------------------------------------------------
def render_fixed_table(fixed: dict) -> pd.DataFrame:
    rows = [{"費目": k, "月額(THB)": fmt_amount(v)} for k, v in fixed.items()]
    rows.append({"費目": "固定費 合計", "月額(THB)": fmt_amount(sum(fixed.values()))})
    return pd.DataFrame(rows)


def current_theme_type() -> str:
    """現在のテーマ種別（"light"/"dark"）を返す。取得できなければ "light"。"""
    try:
        theme_type = st.context.theme.type
    except Exception:
        theme_type = None
    return theme_type if theme_type in ("light", "dark") else "light"


# レーダーチャートは「見るだけ」の表示。モバイルで触っても動かないよう操作を抑制する。
RADAR_CHART_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
    "staticPlot": True,
}


def render_balance_section(scores: dict):
    """生活バランス：説明文＋横幅いっぱいの大きめレーダーチャート。"""
    st.markdown("#### 生活バランス")
    st.write(charts.RADAR_BALANCE_DESCRIPTION)
    fig = charts.make_radar_chart(scores, theme=current_theme_type())
    st.plotly_chart(fig, width="stretch", config=RADAR_CHART_CONFIG)
    st.caption(charts.RADAR_NOTE)


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


def render_comments(comment_result: dict):
    analysis = comment_result.get("analysis", [])
    advice = comment_result.get("advice")
    memo = comment_result.get("lifestyle_memo")

    if analysis:
        st.subheader("結果の分析")
        st.info("\n\n".join(analysis))
    if advice:
        st.subheader("一言アドバイス")
        st.info(advice)
    if memo:
        st.subheader("生活スタイルのメモ")
        st.info(memo)


# ===========================================================================
# STEP 2：試算方法を選ぶ
# ===========================================================================
st.write("")
st.divider()
st.header("STEP 2　試算方法を選ぶ")
st.write("どちらの試算方法でも、基本条件・住まい固定費・医療保険料は反映されます。")
st.write("")

if "method" not in st.session_state:
    st.session_state["method"] = "生活から試算する"

st.markdown(
    """
    <style>
    [class*="st-key-mode_tile_"] button {
        height: auto;
        min-height: 3.2rem;
        padding: 0.85rem 1rem;
        white-space: normal;
        line-height: 1.4;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

MODE_TILES = [
    (
        "生活から試算する",
        "これまでに選んだ条件を積み上げて、月々いくら必要かを見ます。",
    ),
    (
        "予算から試算する",
        "月額予算を自分で決めて、入力済みの固定費を反映しながら生活バランスを見ます。",
    ),
]

mode_cols = st.columns(2)
for mode_col, (tile_title, tile_desc) in zip(mode_cols, MODE_TILES):
    with mode_col:
        is_selected = st.session_state["method"] == tile_title
        if st.button(
            tile_title,
            key=f"mode_tile_{tile_title}",
            width="stretch",
            type="primary" if is_selected else "secondary",
        ):
            st.session_state["method"] = tile_title
            st.rerun()
        st.caption(tile_desc)

method = st.session_state["method"]


# ===========================================================================
# STEP 3：結果を見る
# ===========================================================================
st.write("")
st.divider()
st.header("STEP 3　結果を見る")
st.write("")


def show_lifestyle_result():
    st.subheader("生活から試算する")
    st.write("これまでに選んだ条件を積み上げて、必要な月額生活費と生活バランスを見ます。")

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

    st.caption(
        f"この月額生活費は、「[{data.ASSET_SIM_NAME}]({data.ASSET_SIM_URL})」で"
        "資産寿命を試算するときの入力目安として使えます。"
    )

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
        "想定する月額予算を入力してください。  \n"
        "住まい・医療保険料などを差し引いたうえで、残りを日常生活費に配分し、"
        "余りは予備費として残します。"
    )

    budget_jpy = slider_with_steppers(
        "月額予算（円）",
        min_value=data.BUDGET_MIN,
        max_value=data.BUDGET_MAX,
        default=data.BUDGET_DEFAULT,
        step=data.BUDGET_STEP,
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

    fixed_shortfall = bresult["remaining_after_fixed_thb"] < 0
    if fixed_shortfall:
        st.warning(
            "この予算では、固定費の希望額を全額確保できません。"
            "月額予算が固定・準固定費の合計を下回っているため、"
            "日常生活費にまわせるお金がありません。家賃や車などの見直しが必要です。\n\n"
            "下の固定・準固定費の表は「希望ベースの固定費」であり、"
            "実際にこの予算で支払える額ではない点にご注意ください。"
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
        if fixed_shortfall:
            st.caption(
                "この表は希望額ベースの固定費です。現在の予算では全額を確保できません。"
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
