import streamlit as st
import pandas as pd
import os
from datetime import datetime

def show_input_form(DATA_DIR):
    st.header("⚾ 投球データ入力フォーム")


    PASSWORD = "Kazukiapp0514"
    password = st.text_input("データ入力用パスワード", type="password")

    if password != PASSWORD:
        st.info("分析だけ見る場合は上のボタンを押してください")
        return  # パスワードが違う場合は入力フォームを表示しない


    # 選択肢定義（ここを先に書く）
    pitch_types = ["ストレート", "スライダー", "カーブ", "フォーク", "チェンジアップ", "ツーシーム", "カットボール", "シュート", "その他"]
    locations = ["内角高め", "内角真ん中", "内角低め", "外角高め", "外角真ん中", "外角低め", "真ん中高め", "真ん中低め", "真ん中"]
    pitch_counts = ["0", "1S ", "2S ", "1B ", "2B ", "3B ", "1B1S", "1B2S ","2B1S ","3B1S ", "2B2S ", "3B2S "]
    batting_sides = ["右", "左"]
    results = ["ストライク", "ボール", "ファール", "スイング", "見三振", "空三振", "四球", "死球",
               "1ゴロ", "2ゴロ", "3ゴロ", "4ゴロ", "5ゴロ", "6ゴロ",
               "1フライ", "2フライ", "3フライ", "4フライ", "5フライ", "6フライ", "7フライ", "8フライ", "9フライ",
               "1ライナー", "2ライナー", "3ライナー", "4ライナー", "5ライナー", "6ライナー", "7ライナー", "8ライナー", "9ライナー",
               "1ヒット", "2ヒット", "3ヒット", "4ヒット", "5ヒット", "6ヒット", "7ヒット", "8ヒット", "9ヒット",
               "72B ", "82B ", "92B ", "73B ", "83B ", "93B ", "7HR ", "8HR ", "9HR ",
               "1バント", "2バント", "3バント", "4バント", "5バント",
               "1E ", "2E ", "3E ", "4E ", "5E ", "6E ", "7E ", "8E ", "9E "]
    motions = [" ", "クイック"]
    pickoff = [" ", "牽制"]
    field_zones = ["なし", "レフト", "左中間", "センター", "右中間", "ライト", "サード","ショート", "セカンド", "ファースト"]

    # 🔁 初期化処理
    if st.session_state.get("form_submitted", False):
        for pt in pitch_types:
            st.session_state[f"pt_{pt}"] = False
        for loc in locations:
            st.session_state[f"loc_{loc}"] = False
        for pc in pitch_counts:
            st.session_state[f"pc_{pc}"] = False
        for bs in batting_sides:
            st.session_state[f"bs_{bs}"] = False
        st.session_state["speed_input"] = ""
        st.session_state["result_select"] = results[0]
        st.session_state["motion_select"] = motions[0]
        st.session_state["pickoff_select"] = pickoff[0]
        st.session_state["zone_select"] = field_zones[0]
        st.session_state["form_submitted"] = False

    # ----------------------------
    # 入力フォーム
    # ----------------------------
    with st.form("input_form"):
        pitcher_name = st.text_input("投手名（新規でもOK）", key="pitcher_name")
        speed_input = st.text_input("球速 (km/h) ※任意", key="speed_input")

        st.subheader("✔️ 球種")
        col1, col2, col3 = st.columns(3)
        selected_pitch_types = []
        for i, pt in enumerate(pitch_types):
         with [col1, col2, col3][i % 3]:
            if st.checkbox(pt, key=f"pt_{pt}", value=st.session_state.get(f"pt_{pt}", False)):
                selected_pitch_types.append(pt)

        st.subheader("✔️ コース")
        col1, col2, col3 = st.columns(3)
        selected_locations = []
        for i, loc in enumerate(locations):
         with [col1, col2, col3][i % 3]:
            if st.checkbox(loc, key=f"loc_{loc}", value=st.session_state.get(f"loc_{loc}", False)):
                selected_locations.append(loc)

        st.subheader("✔️ カウント")
        col1, col2, col3 = st.columns(3)
        selected_pitch_counts = []
        for i, pc in enumerate(pitch_counts):
         with [col1, col2, col3][i % 3]:
            if st.checkbox(pc, key=f"pc_{pc}", value=st.session_state.get(f"pc_{pc}", False)):
                selected_pitch_counts.append(pc)

        st.subheader("✔️ 打者の左右")
        col1, col2 = st.columns(2)
        selected_batting_sides = []
        for i, bs in enumerate(batting_sides):
         with [col1, col2][i % 2]:
            if st.checkbox(bs, key=f"bs_{bs}", value=st.session_state.get(f"bs_{bs}", False)):
                selected_batting_sides.append(bs)
       

        selected_result = st.selectbox("🎯 結果（1つ選択）", results, key="result_select")
        selected_motion = st.selectbox("モーション", motions, key="motion_select")
        selected_pickoff = st.selectbox("牽制", pickoff, key="pickoff_select")
        selected_zone = st.selectbox("打球方向", field_zones, key="zone_select")

        submitted = st.form_submit_button("✅ データ送信")

    # ----------------------------
    # データ保存処理（フォーム外）
    # ----------------------------
    if submitted:
        try:
            speed = int(speed_input) if speed_input else None
        except ValueError:
            st.error("球速は数値で入力してください")
            st.stop()

        if not pitcher_name.strip():
            st.error("投手名を入力してください")
            st.stop()

        data = {
            "日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "投手名": pitcher_name,
            "球速": speed,
            "球種": ",".join(selected_pitch_types),
            "コース": ",".join(selected_locations),
            "カウント": ",".join(selected_pitch_counts),
            "打者左右": ",".join(selected_batting_sides),
            "結果": selected_result,
            "モーション": selected_motion,
            "牽制": selected_pickoff,
            "打球方向": selected_zone
        }

        filepath = os.path.join(DATA_DIR, f"{pitcher_name}.csv")
        df_new = pd.DataFrame([data])
        if os.path.exists(filepath):
            df_existing = pd.read_csv(filepath)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_csv(filepath, index=False, encoding="utf-8-sig")

        st.success(f"{pitcher_name} のデータを保存しました ✅")

        # 🔁 初期化のためフラグ立てて rerun
        st.session_state["form_submitted"] = True
        st.rerun()





