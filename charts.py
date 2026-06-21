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

# 「生活バランス」見出し直下に置く説明文
RADAR_BALANCE_DESCRIPTION = (
    "入力した生活費の配分から、暮らしやすさやWell-Beingにつながる要素の"
    "バランスを見える化しています。"
)

# レーダーチャートの見方（思想）の説明文
RADAR_BALANCE_NOTE = (
    "このレーダーチャートは、選択した生活スタイルに対する充足度を示しています。"
    "予算が不足する場合、住居・医療・食費など生活の土台を優先し、そのうえで"
    "外食・交際・趣味などの余白をどこまで残せるかを確認します。"
    "五角形がいびつな場合は、特定の領域に負担が偏っている可能性があります。"
)

# レーダーチャート全体の説明文（指標の出典に関する注記）
RADAR_NOTE = (
    "このレーダーチャートは、WHOQOL や OECD Better Life Index など、"
    "生活の質を複数の領域で捉える考え方を参考に、生活費の配分から"
    "暮らしのバランスを可視化したものです。"
)

# 指標の日本語説明
RADAR_DESCRIPTIONS = {
    "Life Satisfaction": "外食・交際・趣味など、生活の楽しみ",
    "Stability": "固定費・医療保険・予備費など、生活の安定性",
    "Health": "食費・医療費・医療保険など、健康維持",
    "Mobility": "交通費・車・バイクなど、行動範囲",
    "Living Environment": "住居・光熱通信・日用品など、生活環境",
}


# レーダーチャートはテーマに追随させず、独立した固定の見た目にする。
# ライト／ダークのどちらかで文字が沈む問題を避けるため、文字色・グリッド色・
# 背景色を固定する（ダーク系背景＋明るい固定文字色）。app.py 側で
# var(--text-color) による文字色上書き CSS を当てないこと。
RADAR_TEXT_COLOR = "#E5E7EB"
RADAR_GRID_COLOR = "rgba(156, 163, 175, 0.45)"
RADAR_BG_COLOR = "rgba(17, 24, 39, 0.85)"


def make_radar_chart(scores: dict, theme: str | None = None) -> go.Figure:
    """5指標スコア（0〜100）からレーダーチャートを作成する。

    Streamlit のテーマには追随させず、ダーク系の固定背景＋明るい固定文字色で
    描画する。ライト／ダークのどちらでも、項目名・目盛りが必ず読める。
    theme 引数は後方互換のため残しているが、配色には使用しない。
    """
    values = [float(scores.get(axis, 0)) for axis in RADAR_AXES]
    r = values + [values[0]]
    theta = RADAR_AXES + [RADAR_AXES[0]]

    # 線・塗りは固定のダーク背景上で映えるブルー
    line_color = "#60A5FA"
    fill_color = "rgba(96, 165, 250, 0.30)"

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
        paper_bgcolor=RADAR_BG_COLOR,
        plot_bgcolor=RADAR_BG_COLOR,
        font=dict(color=RADAR_TEXT_COLOR, size=13),
        polar=dict(
            # 外周ラベル用の余白を確保しつつ、チャート本体は大きめに表示
            domain=dict(x=[0.14, 0.86], y=[0.14, 0.86]),
            bgcolor=RADAR_BG_COLOR,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                tickfont=dict(color=RADAR_TEXT_COLOR, size=11),
                gridcolor=RADAR_GRID_COLOR,
                linecolor=RADAR_GRID_COLOR,
            ),
            angularaxis=dict(
                tickfont=dict(color=RADAR_TEXT_COLOR, size=12),
                gridcolor=RADAR_GRID_COLOR,
                linecolor=RADAR_GRID_COLOR,
            ),
        ),
        showlegend=False,
        margin=dict(l=90, r=90, t=80, b=70),
        height=500,
        autosize=True,
        # タップ／ドラッグでチャートが動いたように見えないよう操作を固定
        dragmode=False,
    )
    return fig
