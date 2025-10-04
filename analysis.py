import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib.image as mpimg
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from io import BytesIO

plt.rcParams['font.family'] = 'DejaVu Sans'  # Matplotlib 標準英語フォント


DATA_DIR = "data"

# PDF作成関数
def create_pdf(figures, title="投手分析レポート"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # タイトル
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, title)
    c.setFont("Helvetica", 10)

    y = height - 100
    for fig in figures:
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
        img_buffer.seek(0)
        # PDFに画像を貼る（BytesIO -> ImageReader を使う）
        image = ImageReader(img_buffer)
        c.drawImage(image, 50, y - 250, width=500, height=300)
        y -= 300
        if y < 100:
            c.showPage()
            y = height - 100
    c.save()
    buffer.seek(0)
    return buffer

    

def show_analysis(DATA_DIR):

    pitcher_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not pitcher_files:
        st.warning("No data found. Please input pitcher data first.")
        return
    
     # --- PDF用にグラフを集めるリスト ---
    figures = []

    
    # 1回だけ投手選択
    selected_file = st.selectbox("Select Pitcher", pitcher_files)
    df = pd.read_csv(os.path.join(DATA_DIR, selected_file))
    if df.empty:
        st.info("No data available for this pitcher yet.")
        return

   # --- Pitch type distribution ---
    st.write("### Pitch Type Distribution")

# データの値（カタカナ）を英語に変換
    df["pitch_type"] = df["球種"].replace({
    "直球": "Fastball",
    "スライダー": "Slider",
    "チェンジアップ": "Changeup",
    "カーブ": "Curveball",
    "ツーシーム": "Two-Seam",
    "シンカー": "Sinker",
    "ストレート": "Fastball",
    "シュート": "Two-Seam",
    "カットボール": "cut ball",
})

# 変換後の 'pitch_type' 列のデータを使ってカウント
    pitch_counts = df["pitch_type"].value_counts()

    fig, ax = plt.subplots()
    ax.pie(pitch_counts, labels=pitch_counts.index, autopct="%1.1f%%", startangle=70)
    ax.axis("equal")
    st.pyplot(fig)

    # --- Count-based pitch percentage ---
    st.title("🎯 Count-based Pitch Percentage")
    if "カウント" not in df.columns or "球種" not in df.columns:
        st.warning("CSV must contain 'カウント' and '球種' columns.")
        return

    df["カウント"] = df["カウント"].astype(str).str.strip().str.replace("０","0").str.replace("１","1")\
                    .str.replace("２","2").str.replace("３","3")
    
    pitch_type_map = {
        "ストレート": "Fastball",
        "フォーシーム": "Fastball",
        "ツーシーム": "Two-Seam",
        "シンカー": "Sinker",
        "カットボール": "cut Ball",
        "スライダー": "Slider",
        "カーブ": "Curveball",
        "フォーク": "Off-speed Pitch",
        "チェンジアップ": "Changeup ",
        "スプリット": "Off-speed Pitch",
    }
    df['球種'] = df['球種'].apply(lambda x: pitch_type_map.get(x, x))
    count_pitch = df.groupby(["カウント", "球種"]).size().unstack(fill_value=0)
    count_pitch_percent = (count_pitch.T / count_pitch.sum(axis=1)).T * 100
    count_pitch_percent = count_pitch_percent.round(1)

    st.subheader("📋 Table: Count-based Pitch %")
    st.dataframe(count_pitch_percent.style.format("{:.1f}%"))

    st.subheader("📊 Bar Chart: Count-based Pitch %")
    df_bar = count_pitch_percent.reset_index().melt(id_vars="カウント", var_name="Pitch Type", value_name="Percentage")
    plt.figure(figsize=(12,6))
    ax = sns.barplot(data=df_bar, x="カウント", y="Percentage", hue="Pitch Type")
    ax.set_title("Count-based Pitch Percentage")
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
    figures.append(plt.gcf())   # PDFに入れる
    # --- Heatmap ---
    st.title("📊 Heatmap (Pitcher Perspective)")
    if "打者左右" not in df.columns or "コース" not in df.columns:
        st.error("CSV must contain '打者左右' and 'コース' columns.")
        return

    zones = ["内角高め","真ん中高め","外角高め",
             "内角真ん中","真ん中","外角真ん中",
             "内角低め","真ん中低め","外角低め"]
    zone_map = {
        "内角高め": (2,2), "真ん中高め": (2,1), "外角高め":(2,0),
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
        st.subheader("Right-handed Batters")
        df_right = df[df["打者左右"]=="右"]
        counts_right = df_right["コース"].value_counts().reindex(zones, fill_value=0)
        mat_right = create_zone_matrix(counts_right, batter_side="右")
        fig_r, ax_r = plt.subplots()
        sns.heatmap(mat_right, annot=True, fmt=".0f", cmap="Reds", ax=ax_r)
        ax_r.set_title("Right-handed Batters")
        ax_r.invert_yaxis()
        st.pyplot(fig_r)
        figures.append(fig_r)   # PDFに入れる

    with col2:
        st.subheader("Left-handed Batters")
        df_left = df[df["打者左右"]=="左"]
        counts_left = df_left["コース"].value_counts().reindex(zones, fill_value=0)
        mat_left = create_zone_matrix(counts_left, batter_side="左")
        fig_l, ax_l = plt.subplots()
        sns.heatmap(mat_left, annot=True, fmt=".0f", cmap="Blues", ax=ax_l)
        ax_l.set_title("Left-handed Batters")
        ax_l.invert_yaxis()
        st.pyplot(fig_l)
        figures.append(fig_l)   # PDFに入れる
    # --- Batted Ball Direction Analysis ---
    st.title("🏟️ Batted Ball Direction Analysis")

    if "打球方向" not in df.columns or "打者左右" not in df.columns:
     st.error("This CSV does not contain '打球方向' or '打者左右' columns.")
     return

# 打球方向を分割して展開
    df_exploded = df.assign(打球方向=df["打球方向"].str.split(",")).explode("打球方向")

# 打球方向の値を変換
    df_exploded["打球方向"] = df_exploded["打球方向"].replace({
    "三塁":"Third Base","遊撃":"Shortstop","二塁":"Second Base","一塁":"First Base",
    "3B":"Third Base","SS":"Shortstop","2B":"Second Base","1B":"First Base",
    "サード":"Third Base", "ショート":"Shortstop", "セカンド":"Second Base", "ファースト":"First Base",
    "レフト":"Left","左中間":"Left Center","センター":"Center","右中間":"Right Center","ライト":"Right"
})

# 方向リスト
    outfield = ["Left","Left Center","Center","Right Center","Right"]
    infield = ["Third Base","Shortstop","Second Base","First Base"]
    all_directions = outfield + infield

# 打球位置
    positions = {
    "Left":(0.2,0.75),"Left Center":(0.35,0.85),"Center":(0.5,0.9),
    "Right Center":(0.65,0.85),"Right":(0.8,0.75),
    "Third Base":(0.28,0.48),"Shortstop":(0.42,0.54),"Second Base":(0.58,0.54),"First Base":(0.72,0.48)
}

     # 内野の表示名変換用辞書
    infield_display_names = {
        "Third Base": "3B",
        "Shortstop": "SS",
        "Second Base": "2B",
        "First Base": "1B"
        }

    def plot_direction(ax, df_side, title):
        total = len(df_side)
        if total == 0:
           direction_percents = pd.Series(0, index=all_directions)
        else:
           direction_counts = df_side["打球方向"].value_counts().reindex(all_directions, fill_value=0)
           direction_percents = (direction_counts / total * 100).round(1)

        img_path = os.path.join("images","istockphoto-165551036-612x612 (1).jpg")
        if not os.path.exists(img_path):
           st.error(f"Image not found: {img_path}")
           return
        img = mpimg.imread(img_path)
        ax.imshow(img, extent=[0,1,0,1])

        for direction, (x,y) in positions.items():
            percent = direction_percents.get(direction,0)
            ax.text(x, y, f"{direction}\n{percent:.1f}%", ha="center", va="center", color="black", weight="bold")

        ax.set_title(title)
        ax.axis("off")

# プロット
    col1, col2 = st.columns(2)

    with col1:
         st.subheader("Right-handed Batter")
         df_r = df_exploded[df_exploded["打者左右"]=="右"]
         fig_r, ax_r = plt.subplots(figsize=(6,6))
         plot_direction(ax_r, df_r, "Right-handed")
         st.pyplot(fig_r)
         figures.append(fig_r)   # PDFに入れる
    with col2:
         st.subheader("Left-handed Batter")
         df_l = df_exploded[df_exploded["打者左右"]=="左"]
         fig_l, ax_l = plt.subplots(figsize=(6,6))
         plot_direction(ax_l, df_l, "Left-handed")
         st.pyplot(fig_l)
         figures.append(fig_l)   # PDFに入れる


    if st.button("📄 PDFを作成する"):
        pdf_buffer = create_pdf(figures, title=f"{selected_file.replace('.csv','')} 投手分析レポート")
        st.download_button(
            label="📥 PDFをダウンロード",
            data=pdf_buffer,
            file_name=f"{selected_file.replace('.csv','')}_analysis.pdf",
            mime="application/pdf"
        )     