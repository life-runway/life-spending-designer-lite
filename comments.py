"""結果コメント生成ロジック。

「判定」ではなく「入力条件に基づく説明」を返す方針。
生活スタイル、固定費比率、予算充足状況、医療保険・車・最小生活などの
注意点に応じて、表示するコメント文字列のリストを組み立てる。
"""

# 医療保険なしコメント
NO_INSURANCE_COMMENT = (
    "医療保険なしの場合、月額生活費は抑えられますが、"
    "入院・手術・高額医療費への備えは別途必要です。"
)

# 車ありコメント（予算充足・予備費の状況で出し分ける）
CAR_COMMENT_SHORTAGE = (
    "車を持つことで生活圏は広がりますが、車・バイク維持費は毎月の固定的な"
    "支出になります。同じ予算内では、外食・交際・趣味・レジャーに回せる余力が"
    "小さくなります。"
)
CAR_COMMENT_LOW_RESERVE = (
    "車を持つことで生活圏は広がりますが、車・バイク維持費は毎月の固定的な"
    "支出になります。生活費は確保できていますが、予備費や為替変動への余力も"
    "あわせて確認しておくと安心です。"
)
CAR_COMMENT_COMFORTABLE = (
    "車を持つことで生活圏は広がり、移動の自由度は高くなります。"
    "生活費と予備費の両方を確保できており、車のある生活も比較的無理なく"
    "想定できます。"
)
CAR_COMMENT_LIFESTYLE = (
    "車を持つことで生活圏は広がり、移動の自由度は高くなります。車・バイク維持費は"
    "毎月の固定的な支出になるため、固定費の重さもあわせて確認してください。"
)

MINIMAL_COMMENT = (
    "最小生活は、かなり支出を抑えた条件です。長期滞在では医療費、"
    "帰国費用、家電故障、為替変動などへの余力に注意が必要です。"
)

# 生活スタイル別の説明コメント
LIFESTYLE_STYLE_COMMENTS = {
    "最小生活": (
        "かなり支出を抑えた生活設計です。外食・交際・趣味に回せる金額は限られるため、"
        "長期滞在では医療費、帰国費用、家電故障、為替変動などへの余力に"
        "注意が必要です。"
    ),
    "控えめ生活": (
        "基礎的な生活費を抑えながら、外食・交際・趣味を少し残す生活設計です。"
        "大きな余裕はありませんが、車や医療保険の有無、家賃水準によって"
        "現実性が変わります。"
    ),
    "標準生活": (
        "食費・外食・交際・趣味をある程度残した、無理の少ない生活設計です。"
    ),
    "余裕生活": (
        "外食・交際・趣味・レジャーにも余白を持たせた生活設計です。"
        "生活の楽しみは残しやすい一方、家賃・医療保険・車などの固定費が"
        "大きい場合は、総額が高くなります。"
    ),
}


def lifestyle_style_comment(style: str) -> str:
    """選んだ生活スタイルに対する説明コメントを返す。"""
    return LIFESTYLE_STYLE_COMMENTS.get(
        style, "入力条件に基づいて生活費を試算しています。"
    )


def fixed_ratio_comment(fixed_ratio: float) -> str:
    """固定・準固定費の比重についての説明コメントを返す。"""
    if fixed_ratio < 40:
        return (
            "家賃・医療保険・車などの固定的な支出は比較的抑えられています。"
            "生活費を調整する余地は、外食・交際・趣味などの日常生活費側に"
            "残っています。"
        )
    if fixed_ratio < 60:
        return (
            f"固定的な支出は生活費全体の{fixed_ratio:.0f}%です。"
            "生活費を下げたい場合は、外食・交際・趣味だけでなく、"
            "家賃や移動手段の前提も確認すると効果が見えやすくなります。"
        )
    return (
        f"家賃・医療保険・車などの固定的な支出が生活費全体の{fixed_ratio:.0f}%を"
        "占め、比重は高めです。毎月の総額を下げたい場合、外食や趣味を削るだけでは"
        "限界があり、住居費や車の有無を見直す方が効果が大きくなります。"
    )


def budget_fit_comment(fulfillment_ratio: float) -> str:
    """予算に対する充足状況の説明コメントを返す。"""
    if fulfillment_ratio >= 1.0:
        return (
            "選択した生活スタイルに必要な支出をおおむね確保できています。"
            "余った金額は、突発費や帰国費用、為替変動への備えとして残せます。"
        )
    if fulfillment_ratio >= 0.75:
        return (
            "選択した生活スタイルにかなり近い内容まで確保できますが、"
            "一部の外食・交際・趣味は少し抑える必要があります。"
        )
    return (
        "固定費と基礎生活費を優先すると、外食・交際・趣味に回せる金額は"
        "かなり限られます。家賃、医療保険、車の有無を見直すと、"
        "生活費全体への影響が大きくなります。"
    )


# 五角形（レーダー）の結果と連動したコメント
LIFE_SATISFACTION_LOW_COMMENT = (
    "住居・医療・食費など生活の土台は比較的確保されています。"
    "一方で、外食・交際・趣味に回せる金額が限られているため、"
    "Life Satisfaction が低めに出ています。長期滞在では、"
    "楽しみの余白をどこまで残すか確認するとよいでしょう。"
)
STABILITY_LOW_COMMENT = (
    "毎月の生活費に対する余力が小さく、Stability が低めに出ています。"
    "突発費、帰国費用、為替変動への備えを別枠で持てるか確認すると、"
    "より安心感のある生活設計になります。"
)
MOBILITY_LOW_COMMENT = (
    "移動に使える金額が限られているため、Mobility が低めに出ています。"
    "行動範囲を広げたい場合は、交通費や車・バイクの前提を確認してください。"
)
HEALTH_LOW_COMMENT = (
    "医療保険や医療費、食費に関わる支出が十分ではない可能性があります。"
    "長期滞在では、医療費や健康維持の余力を別途確認する必要があります。"
)
BALANCED_COMMENT = (
    "生活の土台を確保しながら、外食・交際・趣味にも一定の余力を残せています。"
    "大きな偏りは少なく、選択した生活スタイルに近い配分です。"
)

RESERVE_SMALL_COMMENT = (
    "必要生活費は確保できていますが、予備費はまだ小さめです。突発的な医療費、"
    "家電故障、帰国費用、為替変動などへの備えを増やすと、生活の安定性は"
    "高まりやすくなります。"
)

STABILITY_NOT_FULL_COMMENT = (
    "必要生活費は確保できていますが、予備費や固定費の重さも安定性に影響します。"
)


def score_low_comments(scores: dict) -> list[str]:
    """レーダーの五角形で「低め」に出ている領域の説明コメントを返す。"""
    out: list[str] = []
    low = 50.0

    if scores.get("Health", 100) < low:
        out.append(HEALTH_LOW_COMMENT)
    if scores.get("Life Satisfaction", 100) < low:
        out.append(LIFE_SATISFACTION_LOW_COMMENT)
    if scores.get("Stability", 100) < low:
        out.append(STABILITY_LOW_COMMENT)
    if scores.get("Mobility", 100) < low:
        out.append(MOBILITY_LOW_COMMENT)

    return out


def is_balanced(scores: dict) -> bool:
    """大きな偏りがなく、全体的に確保できているか。"""
    return all(
        scores.get(axis, 0) >= 60.0
        for axis in (
            "Life Satisfaction",
            "Stability",
            "Health",
            "Mobility",
            "Living Environment",
        )
    )


def reserve_is_small(reserve_jpy: float | None, monthly_jpy: float | None) -> bool:
    """予備費が小さいか。月額生活費の5%未満、または2万円未満を目安とする。"""
    if reserve_jpy is None:
        return False
    threshold = 20000.0
    if monthly_jpy:
        threshold = max(threshold, monthly_jpy * 0.05)
    return reserve_jpy < threshold


def reserve_stability_comment(
    stability: float,
    reserve_jpy: float | None,
    monthly_jpy: float | None,
) -> str | None:
    """必要生活費を満たした状態での、予備費・Stability に関する補足コメント。"""
    if stability >= 100:
        return None

    if reserve_is_small(reserve_jpy, monthly_jpy):
        return RESERVE_SMALL_COMMENT
    return STABILITY_NOT_FULL_COMMENT


def car_comment(
    *,
    mode: str,
    fulfillment_ratio: float | None,
    reserve_jpy: float | None,
    monthly_jpy: float | None,
) -> str:
    """車あり時のコメントを、予算充足状況・予備費に応じて出し分ける。"""
    if mode == "budget" and fulfillment_ratio is not None:
        if fulfillment_ratio < 1.0:
            return CAR_COMMENT_SHORTAGE
        if reserve_is_small(reserve_jpy, monthly_jpy):
            return CAR_COMMENT_LOW_RESERVE
        return CAR_COMMENT_COMFORTABLE
    return CAR_COMMENT_LIFESTYLE


def build_comments(
    *,
    mode: str,
    has_insurance: bool,
    vehicle_choice: str,
    style: str,
    fixed_ratio: float | None = None,
    fulfillment_ratio: float | None = None,
    scores: dict | None = None,
    reserve_jpy: float | None = None,
    monthly_jpy: float | None = None,
) -> list[str]:
    """表示するコメントのリストを返す。"""
    comments: list[str] = []

    if mode == "lifestyle":
        comments.append(lifestyle_style_comment(style))
        if fixed_ratio is not None:
            comments.append(fixed_ratio_comment(fixed_ratio))
    else:
        if fulfillment_ratio is not None:
            comments.append(budget_fit_comment(fulfillment_ratio))

    low_comments: list[str] = []
    if scores is not None:
        low_comments = score_low_comments(scores)
        comments.extend(low_comments)

    reserve_stab = None
    if (
        mode == "budget"
        and scores is not None
        and fulfillment_ratio is not None
        and fulfillment_ratio >= 1.0
    ):
        reserve_stab = reserve_stability_comment(
            scores.get("Stability", 100.0), reserve_jpy, monthly_jpy
        )
        if reserve_stab is not None:
            comments.append(reserve_stab)

    budget_enough = mode != "budget" or (
        fulfillment_ratio is not None and fulfillment_ratio >= 1.0
    )
    if (
        scores is not None
        and not low_comments
        and reserve_stab is None
        and budget_enough
        and is_balanced(scores)
    ):
        comments.append(BALANCED_COMMENT)

    if not has_insurance:
        comments.append(NO_INSURANCE_COMMENT)

    if vehicle_choice in ("車あり", "車＋バイクあり"):
        comments.append(
            car_comment(
                mode=mode,
                fulfillment_ratio=fulfillment_ratio,
                reserve_jpy=reserve_jpy,
                monthly_jpy=monthly_jpy,
            )
        )

    if style == "最小生活" and mode == "budget":
        comments.append(MINIMAL_COMMENT)

    return comments
