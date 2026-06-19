"""レーダーチャート生成（Plotly）。"""

import plotly.graph_objects as go

# レーダーチャートの指標（表示順）
RADAR_AXES = [
    "Life Satisfaction",
    "Stability",
    "Health",
    "Mobility",
    "Living Environment",
]

# レーダーチャートの見方（思想）の説明文
RADAR_BALANCE_NOTE = (
    "このレーダーチャートは、選択した生活スタイルに対する充足度を示しています。"
    "予算が不足する場合、住居・医療・食費など生活の土台を優先し、そのうえで"
    "外食・交際・趣味などの余白をどこまで残せるかを確認します。"
    "五角形がいびつな場合は、特定の領域に負担が偏っている可能性があります。"
)

# レーダーチャート全体の説明文（指標の出典に関する注記）
RADAR_NOTE = (
    "この指標は、WHOQOL や OECD Better Life Index など、生活の質を"
    "複数領域で捉える考え方を参考にした概算です。実際の幸福度、健康状態、"
    "生活満足度を判定・保証するものではありません。"
)

# 指標の日本語説明
RADAR_DESCRIPTIONS = {
    "Life Satisfaction": "外食・交際・趣味など、生活の楽しみ",
    "Stability": "固定費・医療保険・予備費など、生活の安定性",
    "Health": "食費・医療費・医療保険など、健康維持",
    "Mobility": "交通費・車・バイクなど、行動範囲",
    "Living Environment": "住居・光熱通信・日用品など、生活環境",
}


def make_radar_chart(scores: dict, theme: str | None = None) -> go.Figure:
    """5指標スコア（0〜100）からレーダーチャートを作成する。

    theme: "dark" でダークテーマ向けの白系、それ以外（"light"/None）は
        ライトテーマ向けの濃いグレー系の配色を使う。線・塗りは両テーマで
        視認できるブルーで共通。
    """
    values = [float(scores.get(axis, 0)) for axis in RADAR_AXES]
    r = values + [values[0]]
    theta = RADAR_AXES + [RADAR_AXES[0]]

    # 線・塗りは両テーマ共通（暗背景・明背景どちらでも視認できるブルー）
    line_color = "#3B82F6"
    fill_color = "rgba(59, 130, 246, 0.25)"

    if theme == "dark":
        # ダークテーマ：白系でラベル・目盛り・グリッドを浮かせる
        grid_color = "rgba(255, 255, 255, 0.25)"
        angular_grid_color = "rgba(255, 255, 255, 0.22)"
        axis_line_color = "rgba(255, 255, 255, 0.35)"
        tick_font_color = "rgba(255, 255, 255, 0.75)"
        label_font_color = "rgba(255, 255, 255, 0.85)"
    else:
        # ライトテーマ：濃いグレー系（白背景で読める）
        grid_color = "rgba(0, 0, 0, 0.18)"
        angular_grid_color = "rgba(0, 0, 0, 0.15)"
        axis_line_color = "rgba(0, 0, 0, 0.28)"
        tick_font_color = "rgba(0, 0, 0, 0.65)"
        label_font_color = "rgba(0, 0, 0, 0.80)"

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=r,
            theta=theta,
            fill="toself",
            line=dict(color=line_color, width=3),
            fillcolor=fill_color,
            name="スコア",
            hovertemplate="%{theta}: %{r:.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        font=dict(color=label_font_color),
        polar=dict(
            # 外周ラベル用の余白を確保しつつ、チャート本体は大きめに表示
            domain=dict(x=[0.14, 0.86], y=[0.14, 0.86]),
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                gridcolor=grid_color,
                linecolor=axis_line_color,
                tickfont=dict(size=12, color=tick_font_color),
            ),
            angularaxis=dict(
                gridcolor=angular_grid_color,
                linecolor=axis_line_color,
                tickfont=dict(size=13, color=label_font_color),
            ),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=90, r=90, t=80, b=70),
        height=500,
        autosize=True,
        # タップ／ドラッグでチャートが動いたように見えないよう操作を固定
        dragmode=False,
    )
    return fig
