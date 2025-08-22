import streamlit as st
from input_form import show_input_form
from analysis import show_analysis
import os

st.set_page_config(page_title="野球分析アプリ", layout="wide")

st.markdown("# ⚾ 野球分析アプリ")

# 環境変数からパスワードを取得
PASSWORD = os.environ.get("BASEBALL_APP_PASSWORD", "default_password")

# 認証
st.session_state.setdefault("authenticated", False)

if not st.session_state.authenticated:
    input_pw = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if input_pw == PASSWORD:
            st.session_state.authenticated = True
            st.success("ログイン成功！")
        else:
            st.error("パスワードが違います")


# 保存先ディレクトリ
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# タブUIでページ切り替え
tab1, tab2 = st.tabs(["📄 データ入力", "📊 分析"])



with tab1:
     st.subheader("投球データ入力フォーム")
     st.write(DATA_DIR)
     st.caption(DATA_DIR)  # ← フォルダパスをちいさく表示（美しく）
     show_input_form(DATA_DIR)  # ← ここが重要！

with tab2:
    show_analysis(DATA_DIR)    # ← analysis側も引数取るならここも必要





