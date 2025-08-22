import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm 
import matplotlib.image as mpimg

DATA_DIR = "data"

def show_analysis():
    pitcher_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    if os.name == 'nt':  # Windows
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        if 'Yu Gothic' in available_fonts:
            font_name = 'Yu Gothic'
        elif 'Meiryo UI' in available_fonts:
            font_name = 'Meiryo UI'
        elif 'Meiryo' in available_fonts:
            font_name = 'Meiryo'
        else:
            font_name = 'MS Gothic'
    else:  # macOSやLinux
        font_name = 'Hiragino Maru Gothic Pro'  # macOS
        # font_name = 'Noto Sans CJK JP'  # Linuxの場合はこちらに切り替え

    # フォントをmatplotlibに適用
    plt.rcParams['font.family'] = font_name
    
    if not pitcher_files:
        st.warning("データがありません。先に投球データを入力してください。")
        return

    # 最初の選択ボックス（円グラフ用）
    selected_file = st.selectbox("投手を選択（円グラフ）", pitcher_files, key="select_file_pie")

    df = pd.read_csv(os.path.join(DATA_DIR, selected_file))

    if df.empty:
        st.info("この投手のデータがまだありません。")
        return

    # 球種割合の円グラフ
    st.write("### 球種の割合")
    pitch_counts = df["球種"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(pitch_counts, labels=pitch_counts.index, autopct="%1.1f%%", startangle=70)
    ax.axis("equal")
    st.pyplot(fig)



    st.title("🎯 カウント別 球種割合")

    

    if "カウント" not in df.columns or "球種" not in df.columns:
        st.warning("このデータには 'カウント' または '球種' の列がありません。")
        return

# ✅ カウント列の前後スペースや全角数字を統一
    df["カウント"] = df["カウント"].astype(str).str.strip() \
    .str.replace("０", "0").str.replace("１", "1") \
    .str.replace("２", "2").str.replace("３", "3")

    # カウント × 球種 の頻度表
    count_pitch = df.groupby(["カウント", "球種"]).size().unstack(fill_value=0)

    # 各カウント内での球種の割合を計算（行方向に正規化）
    count_pitch_percent = (count_pitch.T / count_pitch.sum(axis=1)).T * 100
    count_pitch_percent = count_pitch_percent.round(1)

    # 表で表示（DataFrame）
    st.subheader("📋 表：カウント別 球種割合（%）")
    st.dataframe(count_pitch_percent.style.format("{:.1f}%"))

    # 棒グラフで表示（棒グラフは球種ごとに色分け）
    st.subheader("📊 グラフ：カウント別 球種割合（棒グラフ）")
    df_bar = count_pitch_percent.reset_index().melt(id_vars="カウント", var_name="球種", value_name="割合")

    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_bar, x="カウント", y="割合", hue="球種")
    plt.xticks(rotation=45)
    plt.title("カウント別 球種割合")
    plt.legend(title="球種", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(plt.gcf())
    


    
    st.title("📊 ヒートマップ分析(投手目線)")

# データフォルダを確認
    data_dir = "data"
    files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]

    if not files:
     st.warning("データが存在しません。まずはデータを入力してください。")
     st.stop()

# 投手名を選択
     selected_file = st.selectbox("投手を選択（ヒートマップ）", files, key="select_file_heatmap")
     df = pd.read_csv(os.path.join(data_dir, selected_file))

    if "打者左右" not in df.columns or "コース" not in df.columns:
     st.error("必要なデータ（打者左右, コース）がありません。")
     st.stop()

# ゾーンの並び順（9分割）
    zones = [
    "内角高め", "真ん中高め", "外角高め",
    "内角真ん中", "真ん中",     "外角真ん中",
    "内角低め", "真ん中低め", "外角低め"
]

# ゾーン名 → ヒートマップ上の位置
    zone_map = {
    "内角高め": (2, 2), "真ん中高め": (2, 1), "外角高め": (2, 0),
    "内角真ん中": (1, 2), "真ん中": (1, 1), "外角真ん中": (1, 0),
    "内角低め": (0, 2), "真ん中低め": (0, 1), "外角低め": (0, 0),
}

# マトリックス作成関数
    def create_zone_matrix(zone_series, batter_side="右"):
     mat = np.zeros((3, 3))
     for zone, count in zone_series.items():
        if zone in zone_map:
            i, j = zone_map[zone]
            if batter_side == "左":
                j = 2 - j  # 左右反転
            mat[i, j] = count
     return mat

# ヒートマップ描画
    col1, col2 = st.columns(2)

    with   col1:
     st.subheader("右打者へのヒートマップ")
     df_right = df[df["打者左右"] == "右"]
     counts_right = df_right["コース"].value_counts().reindex(zones, fill_value=0)
     mat_right = create_zone_matrix(counts_right, batter_side="右")
     fig_r, ax_r = plt.subplots()
     sns.heatmap(mat_right, annot=True, fmt=".0f", cmap="Reds", ax=ax_r)
     ax_r.set_title("右打者")
     ax_r.invert_yaxis()
     st.pyplot(fig_r)

    with col2:
     st.subheader("左打者へのヒートマップ")
     df_left = df[df["打者左右"] == "左"]
     counts_left = df_left["コース"].value_counts().reindex(zones, fill_value=0)
     mat_left = create_zone_matrix(counts_left, batter_side="左")
     fig_l, ax_l = plt.subplots()
     sns.heatmap(mat_left, annot=True, fmt=".0f", cmap="Blues", ax=ax_l)
     ax_l.set_title("左打者")
     ax_l.invert_yaxis()
     st.pyplot(fig_l)


    st.title("🏟️ 打球方向分析（野球場背景付き）")

    pitcher_files = [f for f in os.listdir("data") if f.endswith(".csv")]

    if not pitcher_files:
        st.warning("データがありません。先にデータを入力してください。")
        return

    selected_file = st.selectbox("投手を選択", pitcher_files)
    df = pd.read_csv(os.path.join("data", selected_file))

    if "打球方向" not in df.columns or "打者左右" not in df.columns:
        st.error("このCSVに '打球方向' または '打者左右' 列がありません。")
        return

    # 表記統一
    df["打球方向"] = df["打球方向"].replace({
        "三塁": "サード", "遊撃": "ショート", "二塁": "セカンド", "一塁": "ファースト",
        "3B": "サード", "SS": "ショート", "2B": "セカンド", "1B": "ファースト"
    })

    # 打球方向カテゴリ
    outfield = ["レフト", "左中間", "センター", "右中間", "ライト"]
    infield = ["サード", "ショート", "セカンド", "ファースト"]
    all_directions = outfield + infield

    # 位置マップ
    positions = {
        "レフト":     (0.20, 0.75),
        "左中間":     (0.35, 0.85),
        "センター":   (0.50, 0.90),
        "右中間":     (0.65, 0.85),
        "ライト":     (0.80, 0.75),
        "サード":     (0.28, 0.48),
        "ショート":   (0.42, 0.54),
        "セカンド":   (0.58, 0.54),
        "ファースト": (0.72, 0.48)
    }

    def plot_direction(ax, df_side, title):
        total = len(df_side)
        direction_counts = df_side["打球方向"].value_counts().reindex(all_directions, fill_value=0)
        direction_percents = (direction_counts / total * 100).round(1) if total > 0 else direction_counts

        img_path = os.path.join("images", "istockphoto-165551036-612x612(1).jpg")
        st.write("画像パス:", img_path)
        st.write("絶対パス:", os.path.abspath(img_path))
        st.write("画像存在チェック:", os.path.exists(img_path))

        if not os.path.exists(img_path):
         st.error(f"画像が見つかりません: {img_path}")
         return

        img = mpimg.imread(img_path)
        ax.imshow(img, extent=[0, 1, 0, 1])

        for direction, (x, y) in positions.items():
            percent = direction_percents.get(direction, 0)
            ax.text(x, y, f"{direction}\n{percent}%", fontsize=12, ha="center", va="center", color="black", weight="bold")

        ax.set_title(title)
        ax.axis("off")

    # 右打者・左打者で分割表示
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("右打者")
        df_r = df[df["打者左右"] == "右"]
        fig_r, ax_r = plt.subplots(figsize=(6, 6))
        plot_direction(ax_r, df_r, "右打者")
        st.pyplot(fig_r)

    with col2:
        st.subheader("左打者")
        df_l = df[df["打者左右"] == "左"]
        fig_l, ax_l = plt.subplots(figsize=(6, 6))
        plot_direction(ax_l, df_l, "左打者")
        st.pyplot(fig_l)