import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib.font_manager as fm
import matplotlib.image as mpimg

# ---------- ローカル環境用フォント（日本語対応） ----------
font_path = "C:/Windows/Fonts/meiryo.ttc"
if os.path.exists(font_path):
    jp_font = fm.FontProperties(fname=font_path)
else:
    jp_font = fm.FontProperties(family="MS Gothic")  # 保険

plt.rcParams['font.family'] = jp_font.get_name()

DATA_DIR = "data"

def show_analysis(DATA_DIR):
    # 投手選択（1回だけ）
    pitcher_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not pitcher_files:
        st.warning("No data available. Please input pitcher data first.")
        return

    selected_file = st.selectbox("Select Pitcher", pitcher_files)
    df = pd.read_csv(os.path.join(DATA_DIR, selected_file))
    if df.empty:
        st.info("No data available for this pitcher yet.")
        return

    # ---------- Pitch Type Pie Chart ----------
    st.write("### Pitch Type Distribution")
    pitch_counts = df["球種"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(pitch_counts, labels=pitch_counts.index, autopct="%1.1f%%", startangle=70)
    ax.axis("equal")
    st.pyplot(fig)

    # ---------- Pitch Type by Count ----------
    st.title("🎯 Pitch Type by Count")
    if "カウント" not in df.columns or "球種" not in df.columns:
        st.warning("CSV does not have 'カウント' or '球種' columns.")
        return

    df["カウント"] = df["カウント"].astype(str).str.strip().str.replace("０","0").str.replace("１","1")\
                    .str.replace("２","2").str.replace("３","3")
    count_pitch = df.groupby(["カウント", "球種"]).size().unstack(fill_value=0)
    count_pitch_percent = (count_pitch.T / count_pitch.sum(axis=1)).T * 100
    count_pitch_percent = count_pitch_percent.round(1)

    st.subheader("📋 Table: Pitch Type by Count (%)")
    st.dataframe(count_pitch_percent.style.format("{:.1f}%"))

    st.subheader("📊 Chart: Pitch Type by Count")
    df_bar = count_pitch_percent.reset_index().melt(id_vars="カウント", var_name="Pitch Type", value_name="Percentage")
    plt.figure(figsize=(12,6))
    ax = sns.barplot(data=df_bar, x="カウント", y="Percentage", hue="Pitch Type")
    ax.set_title("Pitch Type by Count")
    ax.set_xlabel("Count")
    ax.set_ylabel("Percentage (%)")
    for container in ax.containers:
        for bar in container:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{height:.1f}%', ha='center')
    plt.xticks(rotation=45)
    plt.legend(title="Pitch Type", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(plt.gcf())

    # ---------- Heatmap Analysis ----------
    st.title("📊 Heatmap Analysis (Pitcher's View)")
    if "打者左右" not in df.columns or "コース" not in df.columns:
        st.error("CSV must have '打者左右' and 'コース' columns.")
        return

    zones = ["内角高め","真ん中高め","外角高め",
             "内角真ん中","真ん中","外角真ん中",
             "内角低め","真ん中低め","外角低め"]
    zone_map = {
        "内角高め": (2,2), "真ん中高め": (2,1), "外角高め":(2,0),
        "内角真ん中":(1,2), "真ん中":(1,1), "外角真ん中":(1,0),
        "内角低め":(0,2), "真ん中低め":(0,1), "外角低め":(0,0)
    }

    def create_zone_matrix(zone_series, batter_side="Right"):
        mat = np.zeros((3,3))
        for zone, count in zone_series.items():
            if zone in zone_map:
                i,j = zone_map[zone]
                if batter_side=="Left":
                    j = 2-j
                mat[i,j] = count
        return mat

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Right-handed Batters")
        df_right = df[df["打者左右"]=="右"]
        counts_right = df_right["コース"].value_counts().reindex(zones, fill_value=0)
        mat_right = create_zone_matrix(counts_right, batter_side="Right")
        fig_r, ax_r = plt.subplots()
        sns.heatmap(mat_right, annot=True, fmt=".0f", cmap="Reds", ax=ax_r)
        ax_r.set_title("Right-handed Batters")
        ax_r.invert_yaxis()
        st.pyplot(fig_r)

    with col2:
        st.subheader("Left-handed Batters")
        df_left = df[df["打者左右"]=="左"]
        counts_left = df_left["コース"].value_counts().reindex(zones, fill_value=0)
        mat_left = create_zone_matrix(counts_left, batter_side="Left")
        fig_l, ax_l = plt.subplots()
        sns.heatmap(mat_left, annot=True, fmt=".0f", cmap="Blues", ax=ax_l)
        ax_l.set_title("Left-handed Batters")
        ax_l.invert_yaxis()
        st.pyplot(fig_l)

    # ---------- Hit Direction Analysis ----------
    st.title("🏟️ Hit Direction Analysis (Stadium Background)")
    if "打球方向" not in df.columns or "打者左右" not in df.columns:
        st.error("CSV must have '打球方向' and '打者左右' columns.")
        return

    df["打球方向"] = df["打球方向"].replace({
        "三塁":"Third","遊撃":"Short","二塁":"Second","一塁":"First",
        "3B":"Third","SS":"Short","2B":"Second","1B":"First"
    })

    outfield = ["Left","Left-Center","Center","Right-Center","Right"]
    infield = ["Third","Short","Second","First"]
    all_directions = outfield + infield

    positions = {
        "Left":(0.2,0.75),"Left-Center":(0.35,0.85),"Center":(0.5,0.9),
        "Right-Center":(0.65,0.85),"Right":(0.8,0.75),
        "Third":(0.28,0.48),"Short":(0.42,0.54),"Second":(0.58,0.54),"First":(0.72,0.48)
    }

    def plot_direction(ax, df_side, title):
        total = len(df_side)
        direction_counts = df_side["打球方向"].value_counts().reindex(all_directions, fill_value=0)
        direction_percents = (direction_counts / total * 100).round(1) if total>0 else direction_counts

        img_path = os.path.join("images","istockphoto-165551036-612x612 (1).jpg")
        if not os.path.exists(img_path):
            st.error(f"Image not found: {img_path}")
            return
        img = mpimg.imread(img_path)
        ax.imshow(img, extent=[0,1,0,1])

        for direction,(x,y) in positions.items():
            percent = direction_percents.get(direction,0)
            ax.text(x,y,f"{direction}\n{percent}%",ha="center",va="center",color="black",weight="bold")
        ax.set_title(title)
        ax.axis("off")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Right-handed Batters")
        df_r = df[df["打者左右"]=="右"]
        fig_r, ax_r = plt.subplots(figsize=(6,6))
        plot_direction(ax_r, df_r, "Right-handed Batters")
        st.pyplot(fig_r)

    with col2:
        st.subheader("Left-handed Batters")
        df_l = df[df["打者左右"]=="左"]
        fig_l, ax_l = plt.subplots(figsize=(6,6))
        plot_direction(ax_l, df_l, "Left-handed Batters")
        st.pyplot(fig_l)
