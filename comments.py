"""結果コメント生成ロジック。

「判定」ではなく「入力条件に基づく説明」を返す方針。
結果コメントは以下の3つの役割に分けて生成する。

- analysis（結果の分析）：入力条件・計算結果から見た現在の状態
- advice（一言アドバイス）：次にどこを調整すればよいかの短い助言
- lifestyle_memo（生活スタイルのメモ）：選んだ生活スタイルへの一般的な補足

移動手段（なし／バイクあり／車あり／車＋バイクあり）や医療保険の有無に
合わせて文言が自然に変わるようにし、入力内容と矛盾する一般論を避ける。
"""

# 医療保険なしの補足（結果の分析に含める）
NO_INSURANCE_COMMENT = (
    "医療保険なしの場合、月額生活費は抑えられますが、"
    "入院・手術・高額医療費への備えは別途必要です。"
)

# 生活スタイル別のメモ（モードに依らず常に表示）。
# 役割：一言アドバイス（次に見直す行動）とは分け、その生活スタイルで
# 見落としやすい点・注意点を補足する。生活スタイルの再説明は繰り返さない。
LIFESTYLE_MEMOS = {
    "ミニマム生活": (
        "長期滞在では、医療費、帰国費用、家電故障、為替変動などへの余力に"
        "注意が必要です。毎月の支出だけでなく、突発的な支出に備えられるかも"
        "確認してください。"
    ),
    "節約生活": (
        "切り詰めすぎると長続きしにくいため、外食・交際・趣味の余白を"
        "どこまで残すかを意識しておくと、無理なく続けやすくなります。"
    ),
    "標準生活": (
        "標準的な配分でも、医療費の備えや為替変動、予備費までは月々の生活費に"
        "含まれにくい点に注意してください。これらを別枠で確保できると、"
        "長期滞在の安定性が高まります。"
    ),
    "余裕生活": (
        "外食・交際・趣味・移動などは、一度上げた水準を下げにくく固定化しやすい"
        "点に注意してください。住まい・医療・移動手段のゆとりが過剰になっていないかも、"
        "ときどき見直すとよいでしょう。"
    ),
}


def lifestyle_memo(style: str) -> str:
    """選んだ生活スタイルに対する補足メモを返す。"""
    return LIFESTYLE_MEMOS.get(style, "")


# 生活から試算するモードの一言アドバイス（選んだ生活スタイルで実行可能な助言）。
# ミニマム生活では「一段控えめにする」助言を出さず、固定費の見直しに誘導する。
# ミニマム生活は医療保険の有無で文言を出し分けるため、_minimum_advice() で生成する。
STYLE_ADVICE = {
    "節約生活": (
        "月額生活費をさらに抑えたい場合は、ミニマム生活との違いを確認しつつ、"
        "家賃・管理費などの固定費もあわせて見直すとよいでしょう。"
    ),
    "標準生活": (
        "月額生活費を抑えたい場合は、節約生活にした場合の差額や、"
        "家賃・管理費などの固定費を確認するとよいでしょう。"
    ),
    "余裕生活": (
        "余裕生活は快適さを重視した前提です。月額生活費を抑えたい場合は、"
        "標準生活や節約生活と比較して、外食・交際・趣味・移動手段の差額を"
        "確認するとよいでしょう。"
    ),
}


def _minimum_advice(has_insurance: bool) -> str:
    """ミニマム生活の一言アドバイス。医療保険なしのときは「医療保険」を
    見直し候補に含めない（選択条件と矛盾させないため）。"""
    items = (
        "家賃・管理費、医療保険、光熱・通信費"
        if has_insurance
        else "家賃・管理費、光熱・通信費"
    )
    return (
        "ミニマム生活は、すでに日常生活費をかなり抑えた前提です。"
        f"さらに月額生活費を抑えたい場合は、{items}などの固定費を"
        "見直す必要があります。"
    )


def _fixed_items_phrase(vehicle_choice: str, has_insurance: bool) -> str:
    """固定的な支出の主な内訳を、入力内容に合わせた語句で返す。"""
    items = ["住まい"]
    if has_insurance:
        items.append("医療保険")
    if vehicle_choice == "車あり":
        items.append("車の維持費")
    elif vehicle_choice == "車＋バイクあり":
        items.append("車とバイクの維持費")
    elif vehicle_choice == "バイクあり":
        items.append("バイク維持費")
    return "・".join(items) + "などの固定的な支出"


def _adjustable_phrase(vehicle_choice: str, has_insurance: bool) -> str:
    """見直し候補になりやすい固定費の語句を、入力内容に合わせて返す。"""
    base = "家賃・医療保険" if has_insurance else "家賃"
    if vehicle_choice in ("車あり", "車＋バイクあり"):
        return base + "や車の維持費"
    return base


def analysis_lead(
    *,
    mode: str,
    vehicle_choice: str,
    has_insurance: bool,
    fixed_ratio: float | None,
    fulfillment_ratio: float | None,
) -> str:
    """結果の分析の先頭に置く、固定費と日常生活費の状況説明を返す。"""
    fixed_phrase = _fixed_items_phrase(vehicle_choice, has_insurance)

    if mode == "budget" and fulfillment_ratio is not None:
        if fulfillment_ratio < 0.75:
            return (
                f"月額予算に対して、{fixed_phrase}が大きく、"
                "外食・交際・趣味に回せる金額はかなり限られています。"
            )
        if fulfillment_ratio < 1.0:
            return (
                f"月額予算に対して、{fixed_phrase}を確保すると、"
                "外食・交際・趣味は少し抑える必要があります。"
            )
        return (
            f"月額予算に対して、{fixed_phrase}を確保したうえで、"
            "外食・交際・趣味にも回せています。"
        )

    if fixed_ratio is not None:
        if fixed_ratio >= 60:
            return (
                f"選んだ条件では、{fixed_phrase}が生活費全体の"
                f"{fixed_ratio:.0f}%を占め、比重は高めです。"
            )
        if fixed_ratio >= 40:
            return (
                f"選んだ条件では、{fixed_phrase}が生活費全体の"
                f"約{fixed_ratio:.0f}%を占めています。"
            )
        return (
            f"選んだ条件では、{fixed_phrase}は比較的抑えられており、"
            "調整の余地は外食・交際・趣味などの日常生活費側に残っています。"
        )

    return "入力した条件をもとに生活費を試算しています。"


def advice_comment(
    *,
    mode: str,
    vehicle_choice: str,
    has_insurance: bool,
    style: str,
    fixed_ratio: float | None,
    fulfillment_ratio: float | None,
    reserve_jpy: float | None = None,
    monthly_jpy: float | None = None,
) -> str:
    """次にどこを調整すればよいかの短い助言を返す。

    生活から試算するモードでは、選んだ生活スタイルで実行可能な助言を返す
    （例：ミニマム生活では「一段控えめにする」とは言わない）。予算から試算
    するモードでは、予算と必要生活費の関係に応じた助言を返す。
    """
    adjust = _adjustable_phrase(vehicle_choice, has_insurance)

    if mode == "budget" and fulfillment_ratio is not None:
        if fulfillment_ratio < 0.75:
            return (
                f"この条件では、{adjust}の条件を見直すか、"
                "月額予算を少し上げられるかを確認するとよいでしょう。"
            )
        if fulfillment_ratio < 1.0:
            return (
                f"あと少し余裕を持たせたい場合は、{adjust}の条件か"
                "月額予算を確認するとよいでしょう。"
            )
        # 必要生活費は確保できている。余り（予備費）の大きさで助言を分ける。
        if reserve_is_small(reserve_jpy, monthly_jpy):
            return (
                "予算と必要生活費がほぼ同じため、余りはわずかです。"
                "突発的な医療費や帰国費用、為替変動などへの予備費を"
                "別に確保できるか確認するとよいでしょう。"
            )
        return (
            "余った分は、予備費や帰国費用、為替変動への備えとして"
            "残しておくと安心です。"
        )

    # 生活から試算するモード：選んだ生活スタイルで実行可能な助言を返す。
    if style == "ミニマム生活":
        return _minimum_advice(has_insurance)
    return STYLE_ADVICE.get(style, STYLE_ADVICE["標準生活"])


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
MOBILITY_LOW_COMMENT_NO_VEHICLE = (
    "移動に使える金額が限られているため、Mobility が低めに出ています。"
    "外出頻度や交通費の前提を確認するとよいでしょう。"
)
MOBILITY_LOW_COMMENT_WITH_VEHICLE = (
    "移動に使える金額が限られているため、Mobility が低めに出ています。"
    "行動範囲を広げたい場合は、交通費や車・バイクの前提を確認してください。"
)
HEALTH_LOW_COMMENT_WITH_INSURANCE = (
    "医療保険や医療費、食費に関わる支出が十分ではない可能性があります。"
    "長期滞在では、医療費や健康維持の余力を別途確認する必要があります。"
)
HEALTH_LOW_COMMENT_NO_INSURANCE = (
    "健康面のスコアが低めです。医療費自己負担や、万一の医療費に備える余力を"
    "確認してください。"
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


def score_low_comments(
    scores: dict,
    *,
    vehicle_choice: str = "なし",
    has_insurance: bool = True,
) -> list[str]:
    """レーダーの五角形で「低め」に出ている領域の説明コメントを返す。

    選択条件と矛盾しないよう、Health は医療保険の有無、Mobility は車・バイクの
    有無に応じて文言を出し分ける（選んでいない費目の見直しはすすめない）。
    """
    out: list[str] = []
    low = 50.0

    if scores.get("Health", 100) < low:
        out.append(
            HEALTH_LOW_COMMENT_WITH_INSURANCE
            if has_insurance
            else HEALTH_LOW_COMMENT_NO_INSURANCE
        )
    if scores.get("Life Satisfaction", 100) < low:
        out.append(LIFE_SATISFACTION_LOW_COMMENT)
    if scores.get("Stability", 100) < low:
        out.append(STABILITY_LOW_COMMENT)
    if scores.get("Mobility", 100) < low:
        out.append(
            MOBILITY_LOW_COMMENT_WITH_VEHICLE
            if vehicle_choice != "なし"
            else MOBILITY_LOW_COMMENT_NO_VEHICLE
        )

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
) -> dict:
    """結果コメントを「結果の分析・一言アドバイス・生活スタイルのメモ」に分けて返す。"""
    analysis: list[str] = [
        analysis_lead(
            mode=mode,
            vehicle_choice=vehicle_choice,
            has_insurance=has_insurance,
            fixed_ratio=fixed_ratio,
            fulfillment_ratio=fulfillment_ratio,
        )
    ]

    low_comments = (
        score_low_comments(
            scores, vehicle_choice=vehicle_choice, has_insurance=has_insurance
        )
        if scores is not None
        else []
    )
    analysis.extend(low_comments)

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
            analysis.append(reserve_stab)

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
        analysis.append(BALANCED_COMMENT)

    if not has_insurance:
        analysis.append(NO_INSURANCE_COMMENT)

    advice = advice_comment(
        mode=mode,
        vehicle_choice=vehicle_choice,
        has_insurance=has_insurance,
        style=style,
        fixed_ratio=fixed_ratio,
        fulfillment_ratio=fulfillment_ratio,
        reserve_jpy=reserve_jpy,
        monthly_jpy=monthly_jpy,
    )

    return {
        "analysis": analysis,
        "advice": advice,
        "lifestyle_memo": lifestyle_memo(style),
    }
