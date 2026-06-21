"""プリセット、初期値、保険料テーブルなどの定義。

このモジュールは計算に使う固定データのみを持ち、
Streamlit や計算ロジックには依存しません。
"""

APP_TITLE = "タイ移住 月額生活費シミュレーター"

# 連携先アプリ（資産寿命の試算ツール）
ASSET_SIM_NAME = "海外移住 資産寿命シミュレーター（簡易版）"
ASSET_SIM_URL = "https://life-runway-lite-liferunway.streamlit.app/"

# ---------------------------------------------------------------------------
# 年齢別の医療保険料（月額・THB）
# Pacific Cross Premier Plus（割引なし）を参考にした概算。
# 50〜55歳は本来の表に無いため暫定的に6,000THB。
# ---------------------------------------------------------------------------
MEDICAL_INSURANCE_MONTHLY_THB = {
    (50, 55): 6000,  # 暫定値。元の料率表に無いため公開Lite版では保守的に6,000THBで丸める
    (56, 60): 6000,  # 暫定値。50代後半も同じく6,000THBで保守的に扱う（意図的な丸め）
    (61, 65): 7000,
    (66, 70): 10000,
    (71, 75): 15000,
    (76, 80): 20000,
    (81, 85): 25000,
}

# 生活スタイル別の医療保険デフォルトプラン。
# 最小・控えめは Premier、標準は基準の Premier Plus、余裕は Maxima。
STYLE_INSURANCE_PLAN = {
    "最小生活": "Premier",
    "控えめ生活": "Premier",
    "標準生活": "Premier Plus",
    "余裕生活": "Maxima",
}

# 上の MEDICAL_INSURANCE_MONTHLY_THB は Premier Plus を基準にした月額概算。
# 他プランは年間料率表の比率がほぼ一定（Premier≈0.69、Maxima≈1.16）なので、
# Premier Plus 基準額に係数を掛けて概算する（標準=Premier Plus は係数1.0で不変）。
INSURANCE_PLAN_FACTOR = {
    "Premier": 0.69,
    "Premier Plus": 1.0,
    "Maxima": 1.16,
}

# ---------------------------------------------------------------------------
# 生活スタイル別の医療費自己負担（月額・THB）。
# 保険対象外の通院・薬代・簡単な検査・歯科眼科の自己負担・予防医療などを
# 月割りした概算。病気リスクの違いではなく、医療費への予備費をどこまで
# 厚く見るかの違いとして、生活スタイルに応じた初期値を設定する。
# ---------------------------------------------------------------------------
MEDICAL_OUT_OF_POCKET_BY_STYLE = {
    "最小生活": 1500,
    "控えめ生活": 2000,
    "標準生活": 2000,
    "余裕生活": 3000,
}

# ---------------------------------------------------------------------------
# 車・バイク維持費（月額・THB）
# ---------------------------------------------------------------------------
VEHICLE_COSTS = {
    "なし": 0,
    "バイクあり": 2500,
    "車あり": 8500,
    "車＋バイクあり": 11000,
}

# 詳細設定スライダーの初期値（THB／月）。フォールバック用の単一値。
VEHICLE_DEFAULT_MOTORBIKE = 2500
VEHICLE_DEFAULT_CAR = 8500

# 生活スタイル別のユーザー入力項目の初期値・推奨値（THB／月）。
# これらは強制固定ではなく、生活スタイル選択時の初期値として使う。
# ユーザーが手入力で変えた値は、生活スタイル変更時も保持する（app.py 側で制御）。
#
# バイクは所有・走行距離・新車/中古などで決まり、生活スタイル差は小さめ。
MOTORBIKE_BY_STYLE = {
    "最小生活": 1500,
    "控えめ生活": 2000,
    "標準生活": 2500,
    "余裕生活": 3000,
}
# 車はバイクより生活スタイル差が出やすい（車格・任意保険・整備・遠出など）。
CAR_BY_STYLE = {
    "最小生活": 6000,
    "控えめ生活": 7000,
    "標準生活": 8500,
    "余裕生活": 11000,
}
# その他固定費（日本側サブスク・保険・年会費など）。ゼロ固定にはしない。
OTHER_BY_STYLE = {
    "最小生活": 1000,
    "控えめ生活": 2000,
    "標準生活": 4000,
    "余裕生活": 5000,
}

# 日常生活費「交通費」を移動手段に応じて減額する係数。
# 車・バイク維持費は固定・準固定費側に別途計上されるため、日常側の交通費は
# 車・バイクを持つほど下げる。ただしソンテウ・配車・臨時移動などは残るため
# ゼロにはせず、車・バイクありの場合は最低 TRANSPORT_MIN_WITH_VEHICLE_THB を残す。
VEHICLE_TRANSPORT_FACTOR = {
    "なし": 1.0,
    "バイクあり": 0.7,
    "車あり": 0.6,
    "車＋バイクあり": 0.5,
}
TRANSPORT_MIN_WITH_VEHICLE_THB = 1000

# ---------------------------------------------------------------------------
# 生活スタイル別プリセット（日常生活費・THB／月）
# 家賃・医療保険・医療費・光熱通信・ビザ・車バイクを除いた日常生活費。
# ---------------------------------------------------------------------------
LIFESTYLE_PRESETS = {
    # 最小生活：自炊中心・バイク移動・外食/交際/趣味/物品購入をかなり抑える、
    # 実際に支出を抑えて暮らすタイ長期滞在者の支出感覚に寄せた下限モデル。
    "最小生活": {
        "food": 6000,
        "daily_goods": 2000,
        "local_transport": 1500,
        "dining_out": 2500,
        "social": 1500,
        "leisure": 2000,
    },
    "控えめ生活": {
        "food": 7500,
        "daily_goods": 3000,
        "local_transport": 1800,
        "dining_out": 3500,
        "social": 3000,
        "leisure": 4500,
    },
    "標準生活": {
        "food": 9000,
        "daily_goods": 4000,
        "local_transport": 2100,
        "dining_out": 5000,
        "social": 6000,
        "leisure": 9000,
    },
    "余裕生活": {
        "food": 12000,
        "daily_goods": 5000,
        "local_transport": 4000,
        "dining_out": 8000,
        "social": 10000,
        "leisure": 11000,
    },
}

# 日常生活費の費目ラベル（日本語表示名）
CATEGORY_LABELS = {
    "food": "食費",
    "daily_goods": "日用品",
    "local_transport": "交通費",
    "dining_out": "外食費",
    "social": "交際費",
    "leisure": "趣味・レジャー",
}

# 不足時の配分優先順位（表示順などで使用）
LIFESTYLE_PRIORITY = [
    "food",
    "daily_goods",
    "local_transport",
    "dining_out",
    "social",
    "leisure",
]

# 日常生活費の2層分け
#  A. 基礎生活費：生活の土台。優先して確保する
#  B. 楽しみ・余白費：予算に応じて比例配分で圧縮する
BASIC_CATEGORIES = ["food", "daily_goods", "local_transport"]
ENJOYMENT_CATEGORIES = ["dining_out", "social", "leisure"]

# 基礎生活費の最低ライン（希望額に対する比率）。
# 予算が極端に足りない場合でも、この水準を目安に土台を守る。
BASIC_MIN_RATIO = {
    "food": 0.70,
    "daily_goods": 0.50,
    "local_transport": 0.50,
}

# Life Satisfaction のスコア加重（楽しみ・余白費の充足率の重み付け）
LIFE_SATISFACTION_WEIGHTS = {
    "dining_out": 0.30,
    "social": 0.30,
    "leisure": 0.40,
}

# 生活スタイルの説明文
LIFESTYLE_DESCRIPTIONS = {
    "最小生活": "自炊中心、バイク移動、外食・交際・趣味・物品購入をかなり抑える生活。住まいを安くできるほど、総額も下がります。",
    "控えめ生活": "基礎生活を保ちつつ、外食・交際・趣味は少なめに抑える生活",
    "標準生活": "食費・外食・交際・趣味をある程度残す、無理の少ない生活",
    "余裕生活": "外食・交際・趣味・レジャーにも余白を持たせる生活",
}

# ---------------------------------------------------------------------------
# 入力初期値・レンジ
# ---------------------------------------------------------------------------
AGE_MIN, AGE_MAX, AGE_DEFAULT, AGE_STEP = 50, 85, 60, 1
FX_MIN, FX_MAX, FX_DEFAULT, FX_STEP = 4.0, 6.0, 5.0, 0.1
RENT_MIN, RENT_MAX, RENT_DEFAULT, RENT_STEP = 0, 80000, 15000, 1000
UTIL_MIN, UTIL_MAX, UTIL_DEFAULT, UTIL_STEP = 1500, 12000, 4500, 100

# 光熱・通信費の生活スタイル別初期値（THB／月）。
# 通信費は生活スタイルで極端に変わらないため、差はつけすぎない。
UTIL_BY_STYLE = {
    "最小生活": 2800,
    "控えめ生活": 3500,
    "標準生活": 4500,
    "余裕生活": 5500,
}
VISA_MIN, VISA_MAX, VISA_DEFAULT, VISA_STEP = 0, 3000, 500, 100
OTHER_MIN, OTHER_MAX, OTHER_DEFAULT, OTHER_STEP = 0, 50000, 0, 1000
CUSTOM_INS_MIN, CUSTOM_INS_MAX, CUSTOM_INS_STEP = 0, 60000, 1000
BUDGET_MIN, BUDGET_MAX, BUDGET_DEFAULT, BUDGET_STEP = 100000, 500000, 200000, 10000

# 医療保険の選択肢
INSURANCE_CHOICES = ["医療保険に入る", "入らない", "自分で入力する"]

# ---------------------------------------------------------------------------
# 注意書き・補足テキスト
# ---------------------------------------------------------------------------
INSURANCE_NOTE = (
    "医療保険料は、生活スタイルに応じた初期プランをもとにした概算です。"
    "実際の保険料は、年齢、健康状態、補償内容、免責、通院特約、"
    "割引条件などにより変わります。"
)

# 参考テーブル（表示専用・計算には使わない）。単位は THB/年。
INSURANCE_REFERENCE_INTRO = [
    "医療保険料は、Pacific Crossの保険料表を参考にした概算です。",
    "このアプリでは、生活スタイルに応じて Premier / Premier Plus / Maxima の"
    "初期プランを切り替え、医療保険料の目安を反映しています。",
    "参考として、Premier / Premier Plus / Maxima の年齢別年間保険料を表示しています。",
]

INSURANCE_REFERENCE_TABLE = [
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
]

UTIL_NOTE = (
    "タイでは水道代は小さい一方、エアコン利用で電気代が大きく変わります。"
    "Wi-FiとSIMは安ければ500〜1,000THB程度ですが、"
    "全体では3,500〜5,500THBあたりを標準帯と考えています。"
)

VEHICLE_NOTE = (
    "車・バイク維持費は、燃料代、保険、税金、整備費などを含めた月額概算です。"
    "車両購入費、ローン、減価償却、大きな修理費は含んでいません。"
)

LIFESTYLE_NOTE = (
    "生活スタイルは、家賃・管理費、医療保険、医療費自己負担、光熱・通信費、"
    "ビザ費用、車・バイク維持費を除いた日常生活費です。"
)


def _lookup_range_table(table: dict, age: int) -> int:
    """(下限, 上限) をキーに持つテーブルから age に該当する値を返す。

    範囲外の場合は、最も近い端の値を返す（落ちないようにする）。
    """
    for (low, high), value in table.items():
        if low <= age <= high:
            return value
    # 範囲外フォールバック
    keys = sorted(table.keys())
    if age < keys[0][0]:
        return table[keys[0]]
    return table[keys[-1]]


def get_medical_insurance(age: int) -> int:
    """年齢別の医療保険料（月額THB）を返す（Premier Plus 基準）。"""
    return _lookup_range_table(MEDICAL_INSURANCE_MONTHLY_THB, age)


def get_insurance_plan_for_style(style: str) -> str:
    """生活スタイル別の医療保険デフォルトプラン名を返す。"""
    return STYLE_INSURANCE_PLAN.get(style, "Premier Plus")


def get_medical_insurance_by_style(age: int, style: str) -> int:
    """年齢＋生活スタイル別プランの医療保険料（月額THB）の初期値を返す。

    Premier Plus 基準の月額にプラン係数を掛け、100THB単位に丸める。
    標準生活（Premier Plus）は係数1.0なので従来値と一致する。
    """
    base = _lookup_range_table(MEDICAL_INSURANCE_MONTHLY_THB, age)
    plan = get_insurance_plan_for_style(style)
    factor = INSURANCE_PLAN_FACTOR.get(plan, 1.0)
    return int(round(base * factor / 100.0) * 100)


def get_medical_out_of_pocket(style: str) -> int:
    """生活スタイル別の医療費自己負担（月額THB）の初期値を返す。"""
    return MEDICAL_OUT_OF_POCKET_BY_STYLE.get(style, 2000)
