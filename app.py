import streamlit as st
from input_form import show_input_form
from analysis import show_analysis
import os

# 認証情報の読み込み（必ず最初に配置）
try:
    users = st.secrets["auth"]["users"].split(',')
    password = st.secrets["auth"]["password"]
except KeyError:
    st.error("secrets.toml に認証情報がありません。アプリを停止します。")
    st.stop() # 認証情報がない場合はここでアプリを停止

# セッションステートでログイン状態を管理
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- ログインフォーム ---
if not st.session_state['logged_in']:
    st.set_page_config(page_title="野球分析アプリ - ログイン", layout="centered") # ログインページは中央寄せにすることも可能
    st.markdown("# ⚾ 野球分析アプリ - ログイン")
    with st.form("login_form"):
        st.markdown("### ログインが必要です")
        username_input = st.text_input("ユーザー名")
        password_input = st.text_input("パスワード", type="password")
        submit_button = st.form_submit_button("ログイン")

    if submit_button:
        if username_input in users and password_input == password:
            st.session_state['logged_in'] = True
            st.success(f"{username_input}さん、ようこそ！")
            st.experimental_rerun() # ログイン成功後、アプリを再実行してコンテンツを表示
        else:
            st.error("ユーザー名またはパスワードが間違っています。")
else:
    # --- ログイン成功後のアプリのメインコンテンツ ---
    st.set_page_config(page_title="野球分析アプリ", layout="wide") # アプリ本体はwideレイアウト

    st.markdown("# ⚾ 野球分析アプリ")

    # 保存先ディレクトリ
    DATA_DIR = "data"
    os.makedirs(DATA_DIR, exist_ok=True)

    # タブUIでページ切り替え
    tab1, tab2 = st.tabs(["📄 データ入力", "📊 分析"])

    with tab1:
        st.subheader("投球データ入力フォーム")
        st.write(DATA_DIR)
        st.caption(DATA_DIR)
        show_input_form(DATA_DIR)

    with tab2:
        show_analysis(DATA_DIR)

    # ログアウトボタン（ログイン成功後に表示）
    st.sidebar.button("ログアウト", on_click=lambda: st.session_state.update(logged_in=False, username=None))



