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

# 生活スタイル別のメモ（モードに依らず常に表示）
LIFESTYLE_MEMOS = {
    "ミニマム生活": (
        "ミニマム生活は、かなり支出を抑えた条件です。長期滞在では医療費、"
        "帰国費用、家電故障、為替変動などへの余力に注意が必要です。"
    ),
    "節約生活": (
        "節約生活は、基礎生活を保ちながら支出を抑える条件です。"
        "無理なく続けるには、外食・交際・趣味の余白をどこまで残すか"
        "確認するとよいでしょう。"
    ),
    "標準生活": (
        "標準生活は、食費・外食・交際・趣味をある程度残す条件です。"
        "長期滞在では、生活の楽しみと固定費のバランスを確認するとよいでしょう。"
    ),
    "余裕生活": (
        "余裕生活は、外食・交際・趣味・レジャーにも余白を持たせる条件です。"
        "支出が大きくなりやすいため、住まい・移動手段・医療保険との"
        "バランスを確認するとよいでしょう。"
    ),
}


def lifestyle_memo(style: str) -> str:
    """選んだ生活スタイルに対する補足メモを返す。"""
    return LIFESTYLE_MEMOS.get(style, "")


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
    fixed_ratio: float | None,
    fulfillment_ratio: float | None,
) -> str:
    """次にどこを調整すればよいかの短い助言を返す。"""
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
        return (
            "余った分は、予備費や帰国費用、為替変動への備えとして"
            "残しておくと安心です。"
        )

    if fixed_ratio is not None:
        if fixed_ratio >= 60:
            return (
                f"毎月の総額を下げたい場合は、{adjust}の前提を見直すと"
                "効果が見えやすくなります。"
            )
        if fixed_ratio >= 40:
            if vehicle_choice in ("車あり", "車＋バイクあり"):
                return (
                    "月額生活費を抑えたい場合は、生活スタイルを一段控えめにするか、"
                    "家賃や車の前提を見直すとよいでしょう。"
                )
            return (
                "月額生活費を抑えたい場合は、生活スタイルを一段控えめにするか、"
                "家賃の前提を見直すとよいでしょう。"
            )
        return (
            "余白を増やしたい場合は、外食・交際・趣味の予算を"
            "少しずつ調整するとよいでしょう。"
        )

    return "気になる費目から、入力条件を少しずつ調整してみてください。"


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

    low_comments = score_low_comments(scores) if scores is not None else []
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
        fixed_ratio=fixed_ratio,
        fulfillment_ratio=fulfillment_ratio,
    )

    return {
        "analysis": analysis,
        "advice": advice,
        "lifestyle_memo": lifestyle_memo(style),
    }
