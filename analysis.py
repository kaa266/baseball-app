# analysis.py 完全版（クラウド対応）
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use("Agg")  # Streamlit Cloud対応
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.image as mpimg
import os
import platform

# -------------------------
# 日本語フォント設定
# -------------------------
if platform.system() == "Windows":
    font_path = "C:/Windows/Fonts/meiryo.ttc"
else:
    font_path = os.path.join("font","ipaexg.ttf")  # プロジェクト内フォルダから読む

if os.path.exists(font_path):
    jp_font = fm.FontProperties(fname=font_path)
else:
    jp_font = fm.FontProperties(family="DejaVu Sans")

# -------------------------
# データディレクトリ
# -------------------------
DATA_DIR = "data"

# -------------------------
# 投球分析関数
# -------------------------
def show_analysis(DATA_DIR=DATA_DIR):
    if not os.path.exists(DATA_DIR):
        st.error(f"データフォルダが存在しません: {DATA_DIR}")
        return

    pitcher_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not pitcher_files:
        st.warning("データがありません。先に投球データを入力してください。")
        return

    # -------------------------
    # 球種割合（円グラフ）
    # -------------------------
    selected_file = st.selectbox("投手を選択（円グラフ）", pitcher_files, key="select_file_pie")
    df = pd.read_csv(os.path.join(DATA_DIR, selected_file))
    if df.empty:
        st.info("この投手のデータがまだありません。")
        return

    st.write("### 球種の割合")
    pitch_counts = df["球種"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(pitch_counts, labels=pitch_counts.index, autopct="%1.1f%%",
           startangle=70, textprops={'fontproperties': jp_font})
    ax.axis("equal")
    st.pyplot(fig)
    plt.close(fig)

    # -------------------------
    # カウント別球種割合（棒グラフ）
    # -------------------------
    st.title("🎯 カウント別 球種割合")
    if "カウント" not in df.columns or "球種" not in df.columns:
        st.warning("このデータには 'カウント' または '球種' の列がありません。")
        return

    df["カウント"] = df["カウント"].astype(str).str.strip() \
        .str.replace("０","0").str.replace("１","1") \
        .str.replace("２","2").str.replace("３","3")

    count_pitch = df.groupby(["カウント","球種"]).size().unstack(fill_value=0)
    count_pitch_percent = (count_pitch.T / count_pitch.sum(axis=1)).T * 100
    count_pitch_percent = count_pitch_percent.round(1)

    st.subheader("📋 表：カウント別 球種割合（%）")
    st.dataframe(count_pitch_percent.style.format("{:.1f}%"))

    st.subheader("📊 グラフ：カウント別 球種割合（棒グラフ）")
    df_bar = count_pitch_percent.reset_index().melt(id_vars="カウント",
                                                   var_name="球種",
                                                   value_name="割合")
    fig, ax = plt.subplots(figsize=(12,6))
    sns.barplot(data=df_bar, x="カウント", y="割合", hue="球種", ax=ax)
    ax.set_title("カウント別 球種割合", fontproperties=jp_font)
    ax.set_xlabel("カウント", fontproperties=jp_font)
    ax.set_ylabel("割合（%）", fontproperties=jp_font)
    for container in ax.containers:
        for bar in container:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{height:.1f}%',
                    ha='center', fontproperties=jp_font)
    plt.xticks(rotation=45)
    plt.legend(title="球種", prop=jp_font, bbox_to_anchor=(1.05,1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # -------------------------
    # ヒートマップ（投球コース）
    # -------------------------
    if "打者左右" not in df.columns or "コース" not in df.columns:
        st.warning("このデータには '打者左右' または 'コース' の列がありません。")
        return

    zones = ["内角高め","真ん中高め","外角高め",
             "内角真ん中","真ん中","外角真ん中",
             "内角低め","真ん中低め","外角低め"]
    zone_map = {
        "内角高め": (2,2), "真ん中高め":(2,1), "外角高め":(2,0),
        "内角真ん中":(1,2), "真ん中":(1,1), "外角真ん中":(1,0),
        "内角低め":(0,2), "真ん中低め":(0,1), "外角低め":(0,0)
    }

    def create_zone_matrix(zone_series, batter_side="右"):
        mat = np.zeros((3,3))
        for zone, count in zone_series.items():
            if zone in zone_map:
                i,j = zone_map[zone]
                if batter_side=="左":
                    j = 2-j
                mat[i,j] = count
        return mat

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("右打者へのヒートマップ")
        df_right = df[df["打者左右"]=="右"]
        counts_right = df_right["コース"].value_counts().reindex(zones, fill_value=0)
        mat_right = create_zone_matrix(counts_right, "右")
        fig, ax = plt.subplots()
        sns.heatmap(mat_right, annot=True, fmt=".0f", cmap="Reds", ax=ax,
                    annot_kws={"fontproperties":jp_font})
        ax.set_title("右打者", fontproperties=jp_font)
        ax.invert_yaxis()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        st.subheader("左打者へのヒートマップ")
        df_left = df[df["打者左右"]=="左"]
        counts_left = df_left["コース"].value_counts().reindex(zones, fill_value=0)
        mat_left = create_zone_matrix(counts_left, "左")
        fig, ax = plt.subplots()
        sns.heatmap(mat_left, annot=True, fmt=".0f", cmap="Blues", ax=ax,
                    annot_kws={"fontproperties":jp_font})
        ax.set_title("左打者", fontproperties=jp_font)
        ax.invert_yaxis()
        st.pyplot(fig)
        plt.close(fig)

    # -------------------------
    # 打球方向（野球場背景付き）
    # -------------------------
    st.title("🏟️ 打球方向分析（野球場背景付き）")
    if "打球方向" not in df.columns or "打者左右" not in df.columns:
        st.warning("このCSVに '打球方向' または '打者左右' 列がありません。")
        return

    df["打球方向"] = df["打球方向"].replace({
        "三塁":"サード","遊撃":"ショート","二塁":"セカンド","一塁":"ファースト",
        "3B":"サード","SS":"ショート","2B":"セカンド","1B":"ファースト"
    })

    outfield = ["レフト","左中間","センター","右中間","ライト"]
    infield = ["サード","ショート","セカンド","ファースト"]
    all_directions = outfield + infield

    positions = {
        "レフト":(0.2,0.75),"左中間":(0.35,0.85),"センター":(0.5,0.9),
        "右中間":(0.65,0.85),"ライト":(0.8,0.75),
        "サード":(0.28,0.48),"ショート":(0.42,0.54),
        "セカンド":(0.58,0.54),"ファースト":(0.72,0.48)
    }

    def plot_direction(ax, df_side, title):
        total = len(df_side)
        direction_counts = df_side["打球方向"].value_counts().reindex(all_directions, fill_value=0)
        direction_percents = (direction_counts / total * 100).round(1) if total>0 else direction_counts

        img_path = os.path.join("images","istockphoto-165551036-612x612 (1).jpg")
        if not os.path.exists(img_path):
            st.warning(f"背景画像が見つかりません: {img_path}")
            return
        img = mpimg.imread(img_path)
        ax.imshow(img, extent=[0,1,0,1])

        for direction,(x,y) in positions.items():
            percent = direction_percents.get(direction,0)
            ax.text(x,y,f"{direction}\n{percent}%",ha="center",va="center",
                    color="black",weight="bold", fontproperties=jp_font)
        ax.set_title(title, fontproperties=jp_font)
        ax.axis("off")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("右打者")
        df_r = df[df["打者左右"]=="右"]
        fig, ax = plt.subplots(figsize=(6,6))
        plot_direction(ax, df_r, "右打者")
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        st.subheader("左打者")
        df_l = df[df["打者左右"]=="左"]
        fig, ax = plt.subplots(figsize=(6,6))
        plot_direction(ax, df_l, "左打者")
        st.pyplot(fig)
        plt.close(fig)
