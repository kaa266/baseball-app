import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib.image as mpimg

# Standard font for Streamlit Cloud
plt.rcParams['font.family'] = "DejaVu Sans"

DATA_DIR = "data"
IMG_DIR = "images"

def show_analysis(DATA_DIR):
    # --- Select pitcher ---
    pitcher_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not pitcher_files:
        st.warning("No data available. Please input pitcher data first.")
        return

    selected_file = st.selectbox("Select Pitcher", pitcher_files)
    df = pd.read_csv(os.path.join(DATA_DIR, selected_file))
    if df.empty:
        st.info("No data available for this pitcher yet.")
        return

    # --- Pitch type pie chart ---
    st.write("### Pitch Type Distribution")
    pitch_counts = df["球種"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(pitch_counts, labels=pitch_counts.index, autopct="%1.1f%%", startangle=70)
    ax.axis("equal")
    st.pyplot(fig)

    # --- Pitch type by count ---
    st.title("🎯 Pitch Type by Count")
    if "カウント" not in df.columns or "球種" not in df.columns:
        st.warning("This data does not contain 'カウント' or '球種' columns.")
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
    plt.xticks(rotation=45)
    plt.legend(title="Pitch Type", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(plt.gcf())

    # --- Heatmap analysis ---
    st.title("📊 Heatmap Analysis (Pitcher view)")
    if "打者左右" not in df.columns or "コース" not in df.columns:
        st.warning("Data does not contain '打者左右' or 'コース' columns.")
    else:
        zones = ["High Inside","High Center","High Outside",
                 "Middle Inside","Middle Center","Middle Outside",
                 "Low Inside","Low Center","Low Outside"]
        zone_map = {
            "High Inside":(2,2),"High Center":(2,1),"High Outside":(2,0),
            "Middle Inside":(1,2),"Middle Center":(1,1),"Middle Outside":(1,0),
            "Low Inside":(0,2),"Low Center":(0,1),"Low Outside":(0,0)
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
            st.subheader("Right-handed batters")
            df_right = df[df["打者左右"]=="右"]
            counts_right = df_right["コース"].value_counts().reindex(zones, fill_value=0)
            mat_right = create_zone_matrix(counts_right, "Right")
            fig_r, ax_r = plt.subplots()
            sns.heatmap(mat_right, annot=True, fmt=".0f", cmap="Reds", ax=ax_r)
            ax_r.set_title("Right-handed")
            ax_r.invert_yaxis()
            st.pyplot(fig_r)

        with col2:
            st.subheader("Left-handed batters")
            df_left = df[df["打者左右"]=="左"]
            counts_left = df_left["コース"].value_counts().reindex(zones, fill_value=0)
            mat_left = create_zone_matrix(counts_left, "Left")
            fig_l, ax_l = plt.subplots()
            sns.heatmap(mat_left, annot=True, fmt=".0f", cmap="Blues", ax=ax_l)
            ax_l.set_title("Left-handed")
            ax_l.invert_yaxis()
            st.pyplot(fig_l)

    # --- Hit direction analysis ---
    st.title("🏟️ Hit Direction Analysis (Field view)")
    if "打球方向" not in df.columns or "打者左右" not in df.columns:
        st.warning("Data does not contain '打球方向' or '打者左右' columns.")
        return

    df["打球方向"] = df["打球方向"].replace({
        "三塁":"Third","遊撃":"Short","二塁":"Second","一塁":"First",
        "3B":"Third","SS":"Short","2B":"Second","1B":"First"
    })

    outfield = ["Left","Left Center","Center","Right Center","Right"]
    infield = ["Third","Short","Second","First"]
    all_directions = outfield + infield

    positions = {
        "Left":(0.2,0.75),"Left Center":(0.35,0.85),"Center":(0.5,0.9),
        "Right Center":(0.65,0.85),"Right":(0.8,0.75),
        "Third":(0.28,0.48),"Short":(0.42,0.54),"Second":(0.58,0.54),"First":(0.72,0.48)
    }

    def plot_direction(ax, df_side, title):
        total = len(df_side)
        direction_counts = df_side["打球方向"].value_counts().reindex(all_directions, fill_value=0)
        direction_percents = (direction_counts / total * 100).round(1) if total>0 else direction_counts

        img_path = os.path.join(IMG_DIR,"field.jpg")
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
        st.subheader("Right-handed batters")
        df_r = df[df["打者左右"]=="右"]
        fig_r, ax_r = plt.subplots(figsize=(6,6))
        plot_direction(ax_r, df_r, "Right-handed")
        st.pyplot(fig_r)

    with col2:
        st.subheader("Left-handed batters")
        df_l = df[df["打者左右"]=="左"]
        fig_l, ax_l = plt.subplots(figsize=(6,6))
        plot_direction(ax_l, df_l, "Left-handed")
        st.pyplot(fig_l)

