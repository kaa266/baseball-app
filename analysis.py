import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib.font_manager as fm
import matplotlib.image as mpimg

DATA_DIR = "data"

def set_japanese_font():
    """Windows / macOS / Linux 向けの日本語フォント設定"""
    if os.name == 'nt':  # Windows
        font_path = "C:/Windows/Fonts/meiryo.ttc"  # Windows 標準の Meiryo
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
        else:
            plt.rcParams['font.family'] = "MS Gothic"
    else:  # macOS / Linux
        plt.rcParams['font.family'] = "Hiragino Maru Gothic Pro"  # macOS
        # Linuxの場合は Noto Sans CJK JP などに変更可能

def show_analysis(DATA_DIR):
    # データファイル一覧
    pitcher_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not pitcher_files:
        st.warning("データがありません。先に投球データを入力してください。")
        return

    # Windows用フォント設定
    if os.name == 'nt':
        font_path = "C:/Windows/Fonts/meiryo.ttc"
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
        else:
            font_name = "MS Gothic"
            font_prop = fm.FontProperties(fname=None)
    else:
        font_name = "Hiragino Maru Gothic Pro"
        font_prop = fm.FontProperties(fname=None)

    plt.rcParams['font.family'] = font_name
    plt.rcParams['axes.unicode_minus'] = False  # マイナス記号対応

    # ===== 投手選択・円グラフ =====
    selected_file = st.selectbox("投手を選択（円グラフ）", pitcher_files, key="select_file_pie")
    df = pd.read_csv(os.path.join(DATA_DIR, selected_file))
    if df.empty:
        st.info("この投手のデータがまだありません。")
        return

    st.write("### 球種の割合")
    pitch_counts = df["球種"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(pitch_counts, labels=pitch_counts.index, autopct="%1.1f%%", startangle=70,
           textprops={'fontproperties': font_prop})
    ax.axis("equal")
    st.pyplot(fig)

    # ===== カウント別 球種割合 =====
    st.title("🎯 カウント別 球種割合")
    if "カウント" not in df.columns or "球種" not in df.columns:
        st.warning("このデータには 'カウント' または '球種' の列がありません。")
        return

    # カウント列を統一
    df["カウント"] = df["カウント"].astype(str).str.strip() \
        .str.replace("０","0").str.replace("１","1") \
        .str.replace("２","2").str.replace("３","3")

    count_pitch = df.groupby(["カウント","球種"]).size().unstack(fill_value=0)
    count_pitch_percent = (count_pitch.T / count_pitch.sum(axis=1)).T * 100
    count_pitch_percent = count_pitch_percent.round(1)

    st.subheader("📋 表：カウント別 球種割合（%）")
    st.dataframe(count_pitch_percent.style.format("{:.1f}%"))

    st.subheader("📊 グラフ：カウント別 球種割合（棒グラフ）")
    df_bar = count_pitch_percent.reset_index().melt(id_vars="カウント", var_name="球種", value_name="割合")
    fig_bar, ax_bar = plt.subplots(figsize=(12,6))
    sns.barplot(data=df_bar, x="カウント", y="割合", hue="球種", ax=ax_bar)
    ax_bar.set_xlabel("カウント", fontproperties=font_prop)
    ax_bar.set_ylabel("割合", fontproperties=font_prop)
    ax_bar.set_xticklabels(ax_bar.get_xticklabels(), fontproperties=font_prop)
    ax_bar.set_yticklabels(ax_bar.get_yticklabels(), fontproperties=font_prop)
    ax_bar.legend(title="球種", prop=font_prop, bbox_to_anchor=(1.05,1), loc='upper left')
    plt.title("カウント別 球種割合", fontproperties=font_prop)
    plt.tight_layout()
    st.pyplot(fig_bar)

    # ===== ヒートマップ =====
    st.title("📊 ヒートマップ分析（投手目線）")
    selected_file = st.selectbox("投手を選択（ヒートマップ）", pitcher_files, key="select_file_heatmap")
    df = pd.read_csv(os.path.join(DATA_DIR, selected_file))
    if "打者左右" not in df.columns or "コース" not in df.columns:
        st.warning("必要な列（打者左右、コース）がありません。")
        return

    zones = ["内角高め","真ん中高め","外角高め",
             "内角真ん中","真ん中","外角真ん中",
             "内角低め","真ん中低め","外角低め"]
    zone_map = {
        "内角高め": (2,2), "真ん中高め": (2,1), "外角高め": (2,0),
        "内角真ん中": (1,2), "真ん中": (1,1), "外角真ん中": (1,0),
        "内角低め": (0,2), "真ん中低め": (0,1), "外角低め": (0,0),
    }

    def create_zone_matrix(zone_series, batter_side="右"):
        mat = np.zeros((3,3))
        for zone, count in zone_series.items():
            if zone in zone_map:
                i,j = zone_map[zone]
                if batter_side=="左":
                    j=2-j
                mat[i,j]=count
        return mat

    col1,col2 = st.columns(2)
    with col1:
        st.subheader("右打者")
        df_r = df[df["打者左右"]=="右"]
        counts_r = df_r["コース"].value_counts().reindex(zones,fill_value=0)
        mat_r = create_zone_matrix(counts_r,"右")
        fig_r, ax_r = plt.subplots()
        sns.heatmap(mat_r, annot=True, fmt=".0f", cmap="Reds", ax=ax_r,
                    annot_kws={"fontproperties":font_prop})
        ax_r.set_title("右打者", fontproperties=font_prop)
        ax_r.invert_yaxis()
        st.pyplot(fig_r)

    with col2:
        st.subheader("左打者")
        df_l = df[df["打者左右"]=="左"]
        counts_l = df_l["コース"].value_counts().reindex(zones,fill_value=0)
        mat_l = create_zone_matrix(counts_l,"左")
        fig_l, ax_l = plt.subplots()
        sns.heatmap(mat_l, annot=True, fmt=".0f", cmap="Blues", ax=ax_l,
                    annot_kws={"fontproperties":font_prop})
        ax_l.set_title("左打者", fontproperties=font_prop)
        ax_l.invert_yaxis()
        st.pyplot(fig_l)

    # ===== 打球方向 =====
    st.title("🏟️ 打球方向分析")
    selected_file = st.selectbox("投手を選択（打球方向）", pitcher_files, key="select_file_direction")
    df = pd.read_csv(os.path.join(DATA_DIR, selected_file))
    if "打球方向" not in df.columns or "打者左右" not in df.columns:
        st.warning("必要な列（打球方向、打者左右）がありません。")
        return

    df["打球方向"] = df["打球方向"].replace({
        "三塁":"サード","遊撃":"ショート","二塁":"セカンド","一塁":"ファースト",
        "3B":"サード","SS":"ショート","2B":"セカンド","1B":"ファースト"
    })

    positions = {
        "レフト":(0.2,0.75),"左中間":(0.35,0.85),"センター":(0.5,0.9),
        "右中間":(0.65,0.85),"ライト":(0.8,0.75),
        "サード":(0.28,0.48),"ショート":(0.42,0.54),"セカンド":(0.58,0.54),"ファースト":(0.72,0.48)
    }

    img_path = os.path.join("images","istockphoto-165551036-612x612 (1).jpg")
    if not os.path.exists(img_path):
        st.error(f"画像が見つかりません: {img_path}")
        return

    img = mpimg.imread(img_path)

    def plot_direction(ax, df_side, title):
        total = len(df_side)
        counts = df_side["打球方向"].value_counts().reindex(positions.keys(),fill_value=0)
        percents = (counts/total*100).round(1) if total>0 else counts
        ax.imshow(img, extent=[0,1,0,1])
        for dir, (x,y) in positions.items():
            ax.text(x,y,f"{dir}\n{percents[dir]}%", ha="center", va="center", color="black",
                    fontproperties=font_prop, weight="bold")
        ax.set_title(title, fontproperties=font_prop)
        ax.axis("off")

    col1,col2 = st.columns(2)
    with col1:
        st.subheader("右打者")
        df_r = df[df["打者左右"]=="右"]
        fig_r, ax_r = plt.subplots(figsize=(6,6))
        plot_direction(ax_r, df_r, "右打者")
        st.pyplot(fig_r)
    with col2:
        st.subheader("左打者")
        df_l = df[df["打者左右"]=="左"]
        fig_l, ax_l = plt.subplots(figsize=(6,6))
        plot_direction(ax_l, df_l, "左打者")
        st.pyplot(fig_l)
