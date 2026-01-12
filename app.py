import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import os
import urllib.request
from datetime import datetime
import pandas as pd
import numpy as np
import io
import base64

# --- Google Sheets連携用 ---
from google.oauth2.service_account import Credentials
import gspread

# --- フォント設定 (安定版) ---
def configure_font():
    font_filename = 'NotoSansJP-Regular.ttf'
    font_url = 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP-Regular.ttf'
    if not os.path.exists(font_filename):
        try:
            urllib.request.urlretrieve(font_url, font_filename)
        except Exception:
            pass
    if os.path.exists(font_filename):
        fm.fontManager.addfont(font_filename)
        plt.rcParams['font.family'] = 'Noto Sans JP'
    else:
        plt.rcParams['font.family'] = 'sans-serif'

configure_font()

# --- ページ設定 ---
st.set_page_config(page_title="時間感覚テスト", layout="centered")

# --- URLパラメータから結果を復元 ---
query_params = st.query_params
restored_from_url = False
restored_scores = {}

if all(k in query_params for k in ['ei', 'eq', 'ra', 'rp']):
    try:
        restored_scores = {
            's_exp_int': int(query_params['ei']),
            's_exp_qty': int(query_params['eq']),
            's_rec_acc': int(query_params['ra']),
            's_rec_pos': int(query_params['rp'])
        }
        restored_from_url = True
    except (ValueError, TypeError):
        pass

# --- スタイル調整 (CSS) ---
st.markdown("""
<style>
    body { font-family: 'Helvetica Neue', Arial, sans-serif; }
    .disclaimer-box {
        background-color: #262730; color: #FAFAFA; padding: 15px;
        border-left: 5px solid #FF4B4B; border-radius: 4px; margin-bottom: 25px;
        font-size: 0.85rem; line-height: 1.5;
    }
    .disclaimer-title { font-weight: bold; color: #FF4B4B; display: block; margin-bottom: 5px; }
    .summary-box {
        background-color: rgba(255, 75, 75, 0.1); padding: 20px;
        border-radius: 10px; margin-bottom: 20px;
        border: 1px solid rgba(255, 75, 75, 0.2);
    }
    .summary-title { font-size: 1.2rem; font-weight: bold; color: inherit; margin-bottom: 10px; opacity: 0.9; }
    .summary-text { color: inherit; opacity: 0.8; }
    .positive-box {
        background-color: rgba(0, 200, 83, 0.1); padding: 20px;
        border-radius: 10px; margin-bottom: 20px;
        border: 1px solid rgba(0, 200, 83, 0.3);
    }
    .percentile-box {
        background-color: rgba(100, 100, 255, 0.1); padding: 20px;
        border-radius: 10px; margin-bottom: 20px;
        border: 1px solid rgba(100, 100, 255, 0.3);
    }
    .percentile-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 10px; }
    .restored-notice {
        background-color: rgba(255, 193, 7, 0.2); padding: 15px;
        border-radius: 10px; margin-bottom: 20px;
        border: 1px solid rgba(255, 193, 7, 0.5);
    }
    .save-section {
        background-color: rgba(100, 100, 100, 0.1); padding: 15px;
        border-radius: 10px; margin: 20px 0;
        border: 1px solid rgba(100, 100, 100, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- Google Sheets接続関数 ---
@st.cache_resource
def get_gspread_client():
    """Google Sheets接続を取得"""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.warning(f"Google Sheets接続エラー: {e}")
        return None

def load_all_responses():
    """全回答データを読み込み"""
    try:
        gc = get_gspread_client()
        if gc is None:
            return pd.DataFrame()
        
        sheet_url = st.secrets["app"]["spreadsheet_url"]
        worksheet_name = st.secrets["app"]["worksheet_name"]
        
        sh = gc.open_by_url(sheet_url)
        ws = sh.worksheet(worksheet_name)
        
        data = ws.get_all_records()
        if data:
            return pd.DataFrame(data)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def save_response(user_data: dict):
    """回答データを保存"""
    try:
        gc = get_gspread_client()
        if gc is None:
            return False
        
        sheet_url = st.secrets["app"]["spreadsheet_url"]
        worksheet_name = st.secrets["app"]["worksheet_name"]
        
        sh = gc.open_by_url(sheet_url)
        ws = sh.worksheet(worksheet_name)
        
        existing_data = ws.get_all_values()
        if not existing_data:
            headers = ["timestamp", "nickname", "grade", "s_exp_int", "s_exp_qty", "s_rec_acc", "s_rec_pos"]
            ws.append_row(headers)
        
        row = [
            user_data.get("timestamp", ""),
            user_data.get("nickname", ""),
            user_data.get("grade", ""),
            user_data.get("s_exp_int", 0),
            user_data.get("s_exp_qty", 0),
            user_data.get("s_rec_acc", 0),
            user_data.get("s_rec_pos", 0),
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"データ保存エラー: {e}")
        return False

def calculate_percentile(value, all_values):
    """パーセンタイルを計算"""
    if len(all_values) == 0:
        return None
    return (np.sum(all_values < value) / len(all_values)) * 100

def generate_result_url(s_exp_int, s_exp_qty, s_rec_acc, s_rec_pos):
    """結果再表示用のURLを生成"""
    try:
        base_url = st.secrets["app"]["app_url"]
    except (KeyError, TypeError):
        base_url = ""
    
    if not base_url:
        return f"?ei={s_exp_int}&eq={s_exp_qty}&ra={s_rec_acc}&rp={s_rec_pos}"
    
    base_url = base_url.rstrip('/')
    return f"{base_url}?ei={s_exp_int}&eq={s_exp_qty}&ra={s_rec_acc}&rp={s_rec_pos}"

def generate_summary_text(s_exp_int, s_exp_qty, s_rec_acc, s_rec_pos, summary_future, summary_past):
    """結果サマリのテキストを生成"""
    text = f"""[時間感覚テスト 診断結果]
----------------------------------------
■ 診断サマリ
  Future（未来）: {', '.join(summary_future)}
  Past（過去）: {', '.join(summary_past)}

■ スコア詳細
  予期の濃さ (Intensity): {s_exp_int}/25
  予期の量 (Quantity): {s_exp_qty}/25
  想起の正確性 (Accuracy): {s_rec_acc}/25
  想起の肯定度 (Positivity): {s_rec_pos}/25
----------------------------------------"""
    return text

# --- グラフ画像ダウンロード（サマリ付き版・英語）---
def generate_result_image_with_summary(s_exp_int, s_exp_qty, s_rec_acc, s_rec_pos, summary_future_en, summary_past_en):
    """サマリ付きの結果画像を生成（英語版・文字化け防止）"""
    
    fig = plt.figure(figsize=(10, 14))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 2, 2], hspace=0.3, wspace=0.3)
    
    # --- サマリセクション（上段全体） ---
    ax_summary = fig.add_subplot(gs[0, :])
    ax_summary.axis('off')
    
    summary_title = "Time Perception Test Result"
    summary_content = f"""
Future Perspective: {', '.join(summary_future_en)}
Past Perspective: {', '.join(summary_past_en)}

Score Details:
  Expectation Intensity: {s_exp_int}/25    Expectation Quantity: {s_exp_qty}/25
  Recall Accuracy: {s_rec_acc}/25    Recall Positivity: {s_rec_pos}/25
"""
    
    ax_summary.text(0.5, 0.85, summary_title, transform=ax_summary.transAxes,
                   fontsize=16, fontweight='bold', ha='center', va='top',
                   color='#2C3E50')
    
    bbox_props = dict(boxstyle="round,pad=0.5", facecolor='#F8F9FA', edgecolor='#E74C3C', linewidth=2)
    ax_summary.text(0.5, 0.45, summary_content, transform=ax_summary.transAxes,
                   fontsize=10, ha='center', va='center',
                   color='#34495E', bbox=bbox_props,
                   family='monospace', linespacing=1.5)
    
    # --- Future Matrix（中段左） ---
    ax_future = fig.add_subplot(gs[1, 0])
    plot_matrix_on_ax(ax_future, s_exp_qty, s_exp_int, 
                     "Quantity", "Intensity",
                     "Future Matrix", "Low", "High", "Weak", "Strong")
    
    # --- Past Matrix（中段右） ---
    ax_past = fig.add_subplot(gs[1, 1])
    plot_matrix_on_ax(ax_past, s_rec_pos, s_rec_acc,
                     "Positivity", "Accuracy",
                     "Past Matrix", "Negative", "Positive", "Low", "High")
    
    # --- 推奨戦略のサマリ（下段全体） ---
    ax_strategy = fig.add_subplot(gs[2, :])
    ax_strategy.axis('off')
    
    strategies = []
    if s_exp_int <= 12:
        strategies.append("- Future Connection")
    if s_exp_int >= 13:
        strategies.append("- Pressure Release")
    if s_exp_qty >= 13:
        strategies.append("- Mental Declutter")
    if s_exp_qty <= 12:
        strategies.append("- Deep Focus")
    if s_rec_acc <= 12:
        strategies.append("- Estimation Calibration")
    if s_rec_pos >= 13 and s_rec_acc <= 12:
        strategies.append("- Optimism Calibration")
    if s_rec_pos <= 12:
        strategies.append("- Confidence Building")
    
    positives = []
    if s_rec_acc >= 13:
        positives.append("+ Recall Accuracy: Good")
    if s_rec_pos >= 13 and s_rec_acc >= 13:
        positives.append("+ Recall Balance: Ideal")
    
    strategy_title = "Recommended Strategies"
    strategy_text = "\n".join(strategies) if strategies else "Excellent Balance - No specific intervention needed."
    
    if positives:
        strategy_text += "\n\n" + "\n".join(positives)
    
    ax_strategy.text(0.5, 0.9, strategy_title, transform=ax_strategy.transAxes,
                    fontsize=14, fontweight='bold', ha='center', va='top',
                    color='#2C3E50')
    
    bbox_props_strategy = dict(boxstyle="round,pad=0.5", facecolor='#E8F6E8', edgecolor='#27AE60', linewidth=2)
    ax_strategy.text(0.5, 0.5, strategy_text, transform=ax_strategy.transAxes,
                    fontsize=11, ha='center', va='center',
                    color='#2C3E50', bbox=bbox_props_strategy,
                    linespacing=1.8)
    
    ax_strategy.text(0.5, 0.05, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Dirbato Co., Ltd.",
                    transform=ax_strategy.transAxes, fontsize=8, ha='center', va='bottom',
                    color='#95A5A6')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    
    return buf

def plot_matrix_on_ax(ax, x_score, y_score, x_label, y_label, title, x_min, x_max, y_min, y_max):
    """既存のAxesにマトリクスを描画（英語版・文字化け防止）"""
    ax.set_xlim(0, 25)
    ax.set_ylim(0, 25)
    ax.axvline(x=12.5, color='#BDC3C7', linestyle='--', alpha=0.7)
    ax.axhline(y=12.5, color='#BDC3C7', linestyle='--', alpha=0.7)
    
    ax.scatter(x_score, y_score, color='#E74C3C', s=250, zorder=5, edgecolors='white', linewidth=2)
    
    ax.set_xlabel(x_label, fontsize=11, color='#34495E')
    ax.set_ylabel(y_label, fontsize=11, color='#34495E')
    ax.set_title(title, fontsize=14, fontweight='bold', color='#2C3E50', pad=15)
    
    ax.text(1, 6, y_min, ha='left', va='center', rotation=90, color='#95A5A6', fontsize=10)
    ax.text(1, 19, y_max, ha='left', va='center', rotation=90, color='#95A5A6', fontsize=10)
    ax.text(6, 1, x_min, ha='center', va='bottom', color='#95A5A6', fontsize=10)
    ax.text(19, 1, x_max, ha='center', va='bottom', color='#95A5A6', fontsize=10)
    
    rect = patches.Rectangle((12.5, 12.5), 12.5, 12.5, linewidth=0, edgecolor='none', facecolor='#F0F2F6', alpha=0.5)
    ax.add_patch(rect)

# --- 免責事項 ---
st.markdown("""
<div class="disclaimer-box">
    <span class="disclaimer-title">【本ツールの位置づけ】</span>
    本アプリケーションは、書籍『YOUR TIME ユア・タイム』（鈴木 祐 著）で紹介されている理論を参考に、
    多数文献及び独自の見解を付加し、Dirbato社員向けの提供を目的として構築された<strong>非公式のプロトタイプ</strong>です。<br>
    設問ロジックや診断結果は本アプリケーション向けに独自に再構成されており、原著の正式な診断とは異なります。<br>
    また、本結果は医学的な診断を提供するものではなく、各人にマッチする可能性の高い戦略仮説を提示するものです。
</div>
""", unsafe_allow_html=True)

# --- タイトル ---
st.title("時間感覚テスト")
st.caption("認知科学とデータに基づく、コンサルタントのための時間感覚最適化")

# --- URLから復元された場合の表示 ---
if restored_from_url:
    st.markdown("""
    <div class="restored-notice">
        <strong>保存された結果を表示しています</strong><br>
        新しく診断を受ける場合は、下のフォームから回答してください。
    </div>
    """, unsafe_allow_html=True)
    
    show_restored_results = True
else:
    show_restored_results = False

# --- 設問データ ---
questions = {
    "expected_intensity": [
        "Q1. 今の行動が、5年後や10年後の未来にどう繋がるかをイメージするのが得意だ。",
        "Q2. 目の前の楽しさよりも、将来起こりうるリスクの方に自然と意識が向く。",
        "Q3. 将来のことを考えると、今の楽しみが色褪せて感じることがある。",
        "Q4. 「今これをやらなければ、将来必ず後悔する」という観点で物事を見ることが多い。",
        "Q5. 楽しい時間を過ごしている最中でも、つい「次にやるべきこと」や「後の予定」を考えてしまう。"
    ],
    "expected_quantity": [
        "Q6. スケジュール帳に空白があると、そこに何か予定を入れたくなる、あるいは入れてしまう。",
        "Q7. ひとつの作業をしている最中に、他の複数の「やらなければならないこと」が頭に浮かんでくる。",
        "Q8. 全てのタスクが「今すぐやるべき重要事項」に見えてしまい、どれも捨てがたいと感じる。",
        "Q9. やりたいこと・やるべきことが頭の中で次々と湧いてきて、整理が追いつかない。",
        "Q10. 長期の目標よりも、数時間〜数日以内の「こなすべき用事」で頭がいっぱいだ。"
    ],
    "recalled_accuracy": [
        "Q11. 過去の経験に基づき、「意外と時間がかかるかもしれない」とバッファ（余裕）を持たせる癖がある。",
        "Q12. 作業時間を見積もるとき、過去に実際にかかった時間を参考にする。",
        "Q13. 計画を立てる際に、障害や不測の事態を必ず考える。",
        "Q14. 過去に自分がどれくらいのスピードで作業できたか、具体的に思い出すことができる。",
        "Q15. 作業を始める前に、過去の類似タスクにおける失敗パターンをシミュレーションする。"
    ],
    "recalled_positivity": [
        "Q16. 過去の自分の判断や行動は、今の自分にとってプラスになっていると思う。",
        "Q17. 「自分は時間を有効に使ってきた人間だ」という自信がある。",
        "Q18. 過去の失敗を思い出しても、「あれはあれで良い経験だった」と意味づけできる。",
        "Q19. 過去の経験を振り返ると、困難な状況でも何とか乗り越えてきたと思える。",
        "Q20. 作業前に「これは自分には無理だろう」と思うことはない。"
    ]
}

# --- 職位選択肢 ---
grades = [
    "回答しない",
    "アナリスト",
    "コンサルタント",
    "シニアコンサルタント",
    "マネージャー",
    "アーキテクト",
    "シニアマネージャー",
    "シニアアーキテクト",
    "パートナー"
]

# --- フォーム作成 ---
options = ["全く当てはまらない", "あまり当てはまらない", "どちらともいえない", "やや当てはまる", "完全に当てはまる"]
option_values = {options[0]: 1, options[1]: 2, options[2]: 3, options[3]: 4, options[4]: 5}

with st.form("diagnosis_form"):
    st.header("Section 1: 未来の視点（Future Perspective）")
    st.info("未来に対する「予期」の傾向を分析します")
    
    st.subheader("Part A: 予期の濃さ（Intensity）")
    q1_score = st.radio(questions["expected_intensity"][0], options, horizontal=True, key="q1")
    q2_score = st.radio(questions["expected_intensity"][1], options, horizontal=True, key="q2")
    q3_score = st.radio(questions["expected_intensity"][2], options, horizontal=True, key="q3")
    q4_score = st.radio(questions["expected_intensity"][3], options, horizontal=True, key="q4")
    q5_score = st.radio(questions["expected_intensity"][4], options, horizontal=True, key="q5")
    
    st.markdown("---")
    st.subheader("Part B: 予期の量（Quantity）")
    q6_score = st.radio(questions["expected_quantity"][0], options, horizontal=True, key="q6")
    q7_score = st.radio(questions["expected_quantity"][1], options, horizontal=True, key="q7")
    q8_score = st.radio(questions["expected_quantity"][2], options, horizontal=True, key="q8")
    q9_score = st.radio(questions["expected_quantity"][3], options, horizontal=True, key="q9")
    q10_score = st.radio(questions["expected_quantity"][4], options, horizontal=True, key="q10")

    st.header("Section 2: 過去の視点（Past Perspective）")
    st.info("過去に対する「想起」の傾向を分析します")
    
    st.subheader("Part C: 想起の正確性（Accuracy）")
    q11_score = st.radio(questions["recalled_accuracy"][0], options, horizontal=True, key="q11")
    q12_score = st.radio(questions["recalled_accuracy"][1], options, horizontal=True, key="q12")
    q13_score = st.radio(questions["recalled_accuracy"][2], options, horizontal=True, key="q13")
    q14_score = st.radio(questions["recalled_accuracy"][3], options, horizontal=True, key="q14")
    q15_score = st.radio(questions["recalled_accuracy"][4], options, horizontal=True, key="q15")

    st.markdown("---")
    st.subheader("Part D: 想起の肯定度（Positivity）")
    q16_score = st.radio(questions["recalled_positivity"][0], options, horizontal=True, key="q16")
    q17_score = st.radio(questions["recalled_positivity"][1], options, horizontal=True, key="q17")
    q18_score = st.radio(questions["recalled_positivity"][2], options, horizontal=True, key="q18")
    q19_score = st.radio(questions["recalled_positivity"][3], options, horizontal=True, key="q19")
    q20_score = st.radio(questions["recalled_positivity"][4], options, horizontal=True, key="q20")

    st.markdown("---")
    st.header("オプション設定")
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        user_nickname = st.text_input("ニックネーム（任意）", placeholder="例：タナカ", help="結果の識別用です。空欄でも構いません。")
    with col_opt2:
        user_grade = st.selectbox("職位（任意）", grades, help="匿名での傾向分析に使用します。")
    
    data_consent = st.checkbox(
        "回答結果を匿名で蓄積し、全体傾向の比較表示に使用することに同意します",
        help="同意しない場合も診断結果は表示されますが、データは保存されず、全体比較も表示されません。"
    )

    submitted = st.form_submit_button("診断を実行", type="primary")

# --- 結果表示関数 ---
def display_results(s_exp_int, s_exp_qty, s_rec_acc, s_rec_pos, is_restored=False, show_comparison=True):
    """結果を表示する共通関数"""
    
    all_responses = pd.DataFrame()
    percentiles = {}
    total_responses = 0
    
    if show_comparison:
        all_responses = load_all_responses()
        if not all_responses.empty and len(all_responses) >= 5:
            total_responses = len(all_responses)
            if 's_exp_int' in all_responses.columns:
                percentiles['exp_int'] = calculate_percentile(s_exp_int, pd.to_numeric(all_responses['s_exp_int'], errors='coerce').dropna().values)
            if 's_exp_qty' in all_responses.columns:
                percentiles['exp_qty'] = calculate_percentile(s_exp_qty, pd.to_numeric(all_responses['s_exp_qty'], errors='coerce').dropna().values)
            if 's_rec_acc' in all_responses.columns:
                percentiles['rec_acc'] = calculate_percentile(s_rec_acc, pd.to_numeric(all_responses['s_rec_acc'], errors='coerce').dropna().values)
            if 's_rec_pos' in all_responses.columns:
                percentiles['rec_pos'] = calculate_percentile(s_rec_pos, pd.to_numeric(all_responses['s_rec_pos'], errors='coerce').dropna().values)

    # --- 診断サマリの判定（日本語版：画面表示用） ---
    summary_future = []
    if s_exp_int <= 12: summary_future.append("予期が薄い")
    if s_exp_int >= 13: summary_future.append("予期が濃い")
    if s_exp_qty >= 13: summary_future.append("予期が多い")
    if s_exp_qty <= 12: summary_future.append("予期が少ない")

    summary_past = []
    if s_rec_acc <= 12: summary_past.append("見積もりが曖昧")
    if s_rec_acc >= 13: summary_past.append("見積もりが正確")
    if s_rec_pos <= 12: summary_past.append("過去に否定的")
    if s_rec_pos >= 13: summary_past.append("過去に肯定的")

    # --- 診断サマリ（英語版：画像出力用） ---
    summary_future_en = []
    if s_exp_int <= 12: summary_future_en.append("Weak Expectation")
    if s_exp_int >= 13: summary_future_en.append("Strong Expectation")
    if s_exp_qty >= 13: summary_future_en.append("High Quantity")
    if s_exp_qty <= 12: summary_future_en.append("Low Quantity")

    summary_past_en = []
    if s_rec_acc <= 12: summary_past_en.append("Low Accuracy")
    if s_rec_acc >= 13: summary_past_en.append("High Accuracy")
    if s_rec_pos <= 12: summary_past_en.append("Negative Recall")
    if s_rec_pos >= 13: summary_past_en.append("Positive Recall")

    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">診断サマリ</div>
        <p class="summary-text"><strong>Future（未来）:</strong> {', '.join(summary_future)}</p>
        <p class="summary-text"><strong>Past（過去）:</strong> {', '.join(summary_past)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- 全体比較（パーセンタイル）の表示 ---
    if percentiles and total_responses >= 5:
        def get_position_description(pct, metric_type):
            """スコアの位置を中立的に説明"""
            if pct is None:
                return "N/A", ""
            
            position = f"{pct:.0f}%"
            
            if metric_type == "exp_int":
                if pct >= 70:
                    note = "将来への意識が高い傾向"
                elif pct <= 30:
                    note = "現在志向の傾向"
                else:
                    note = "バランス型"
            elif metric_type == "exp_qty":
                if pct >= 70:
                    note = "多くの予定を抱える傾向"
                elif pct <= 30:
                    note = "集中型の傾向"
                else:
                    note = "バランス型"
            elif metric_type == "rec_acc":
                if pct >= 70:
                    note = "見積もり精度が高い傾向"
                elif pct <= 30:
                    note = "楽観的な見積もりの傾向"
                else:
                    note = "バランス型"
            elif metric_type == "rec_pos":
                if pct >= 70:
                    note = "過去を肯定的に捉える傾向"
                elif pct <= 30:
                    note = "過去に厳しい傾向"
                else:
                    note = "バランス型"
            else:
                note = ""
            
            return position, note
        
        exp_int_pos, exp_int_note = get_position_description(percentiles.get('exp_int'), 'exp_int')
        exp_qty_pos, exp_qty_note = get_position_description(percentiles.get('exp_qty'), 'exp_qty')
        rec_acc_pos, rec_acc_note = get_position_description(percentiles.get('rec_acc'), 'rec_acc')
        rec_pos_pos, rec_pos_note = get_position_description(percentiles.get('rec_pos'), 'rec_pos')
        
        st.markdown(f"""
        <div class="percentile-box">
            <div class="percentile-title">全体比較（回答者 {total_responses} 名中の分布位置）</div>
            <table style="width:100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid rgba(100,100,255,0.3);">
                    <th style="text-align:left; padding:8px;">指標</th>
                    <th style="text-align:center; padding:8px;">スコア</th>
                    <th style="text-align:center; padding:8px;">パーセンタイル</th>
                    <th style="text-align:left; padding:8px;">傾向</th>
                </tr>
                <tr>
                    <td style="padding:8px;">予期の濃さ</td>
                    <td style="text-align:center; padding:8px;">{s_exp_int}/25</td>
                    <td style="text-align:center; padding:8px;">{exp_int_pos}</td>
                    <td style="padding:8px; font-size:0.85rem; opacity:0.8;">{exp_int_note}</td>
                </tr>
                <tr>
                    <td style="padding:8px;">予期の量</td>
                    <td style="text-align:center; padding:8px;">{s_exp_qty}/25</td>
                    <td style="text-align:center; padding:8px;">{exp_qty_pos}</td>
                    <td style="padding:8px; font-size:0.85rem; opacity:0.8;">{exp_qty_note}</td>
                </tr>
                <tr>
                    <td style="padding:8px;">想起の正確性</td>
                    <td style="text-align:center; padding:8px;">{s_rec_acc}/25</td>
                    <td style="text-align:center; padding:8px;">{rec_acc_pos}</td>
                    <td style="padding:8px; font-size:0.85rem; opacity:0.8;">{rec_acc_note}</td>
                </tr>
                <tr>
                    <td style="padding:8px;">想起の肯定度</td>
                    <td style="text-align:center; padding:8px;">{s_rec_pos}/25</td>
                    <td style="text-align:center; padding:8px;">{rec_pos_pos}</td>
                    <td style="padding:8px; font-size:0.85rem; opacity:0.8;">{rec_pos_note}</td>
                </tr>
            </table>
            <p style="font-size:0.8rem; margin-top:10px; opacity:0.7;">
                パーセンタイルは「あなたより低いスコアの回答者の割合」を示します。
                これらの指標に良し悪しはなく、異なる認知傾向を表しています。
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif show_comparison and total_responses < 5:
        st.info(f"全体比較は回答者が5名以上になると表示されます（現在: {total_responses}名）")

    # --- チャート描画（英語版・文字化け防止） ---
    def plot_matrix(x_score, y_score, x_label, y_label, title, x_min, x_max, y_min, y_max, all_x=None, all_y=None):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(0, 25)
        ax.set_ylim(0, 25)
        ax.axvline(x=12.5, color='#BDC3C7', linestyle='--', alpha=0.7)
        ax.axhline(y=12.5, color='#BDC3C7', linestyle='--', alpha=0.7)
        
        if all_x is not None and all_y is not None and len(all_x) > 0:
            ax.scatter(all_x, all_y, color='#BDC3C7', s=50, alpha=0.3, zorder=3, label='Others')
        
        ax.scatter(x_score, y_score, color='#E74C3C', s=250, zorder=5, edgecolors='white', linewidth=2, label='You')
        
        ax.set_xlabel(x_label, fontsize=11, color='#34495E')
        ax.set_ylabel(y_label, fontsize=11, color='#34495E')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#2C3E50', pad=15)
        ax.text(1, 6, y_min, ha='left', va='center', rotation=90, color='#95A5A6', fontsize=10)
        ax.text(1, 19, y_max, ha='left', va='center', rotation=90, color='#95A5A6', fontsize=10)
        ax.text(6, 1, x_min, ha='center', va='bottom', color='#95A5A6', fontsize=10)
        ax.text(19, 1, x_max, ha='center', va='bottom', color='#95A5A6', fontsize=10)
        rect = patches.Rectangle((12.5, 12.5), 12.5, 12.5, linewidth=0, edgecolor='none', facecolor='#F0F2F6', alpha=0.5)
        ax.add_patch(rect)
        
        if all_x is not None and len(all_x) > 0:
            ax.legend(loc='upper right', fontsize=9)
        
        return fig

    all_exp_qty = pd.to_numeric(all_responses['s_exp_qty'], errors='coerce').dropna().values if not all_responses.empty and 's_exp_qty' in all_responses.columns else None
    all_exp_int = pd.to_numeric(all_responses['s_exp_int'], errors='coerce').dropna().values if not all_responses.empty and 's_exp_int' in all_responses.columns else None
    all_rec_pos = pd.to_numeric(all_responses['s_rec_pos'], errors='coerce').dropna().values if not all_responses.empty and 's_rec_pos' in all_responses.columns else None
    all_rec_acc = pd.to_numeric(all_responses['s_rec_acc'], errors='coerce').dropna().values if not all_responses.empty and 's_rec_acc' in all_responses.columns else None

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Future（未来の視点）**")
        fig1 = plot_matrix(s_exp_qty, s_exp_int, "Quantity", "Intensity", 
                          "Future Matrix", "Low", "High", "Weak", "Strong",
                          all_exp_qty, all_exp_int)
        st.pyplot(fig1)
    with col2:
        st.markdown("**Past（過去の視点）**")
        fig2 = plot_matrix(s_rec_pos, s_rec_acc, "Positivity", "Accuracy", 
                          "Past Matrix", "Negative", "Positive", "Low", "High",
                          all_rec_pos, all_rec_acc)
        st.pyplot(fig2)

    # --- 結果保存セクション ---
    st.markdown("---")
    st.markdown("""
    <div class="save-section">
        <strong>結果を保存する</strong><br>
        <span style="font-size:0.9rem; opacity:0.8;">以下の方法で結果を保存できます。再度確認したい場合にご利用ください。</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_save1, col_save2, col_save3 = st.columns(3)
    
    with col_save1:
        summary_text = generate_summary_text(s_exp_int, s_exp_qty, s_rec_acc, s_rec_pos, summary_future, summary_past)
        st.text_area("テキストサマリ", summary_text, height=200, help="コピーしてSlackやメモアプリに貼り付けられます")
    
    with col_save2:
        buf = generate_result_image_with_summary(s_exp_int, s_exp_qty, s_rec_acc, s_rec_pos, summary_future_en, summary_past_en)
        
        st.download_button(
            label="結果画像をダウンロード",
            data=buf,
            file_name=f"time_perception_result_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
            mime="image/png",
            help="サマリ・グラフ・推奨戦略を含む画像をダウンロードできます"
        )
    
    with col_save3:
        result_url = generate_result_url(s_exp_int, s_exp_qty, s_rec_acc, s_rec_pos)
        st.text_input("結果URL（ブックマーク用）", result_url, help="このURLをブックマークすると、いつでも結果を見返せます")

    # --- Strategic Recommendations ---
    st.markdown("---")
    st.header("推奨戦略（Strategic Recommendations）")
    st.info("あなたの時間感覚特性に基づいて導き出された戦略を提示します。各項目をクリックして詳細を確認してください。")

    recommendations = []
    positive_messages = []

    # 1. 予期が薄い (Weak Expectation)
    if s_exp_int <= 12:
        recommendations.append({
            "title": "Future Connection - 未来との接続強化",
            "reason": "未来の報酬をリアルに感じにくく、目先の誘惑に流されやすい状態です。これは「怠惰」ではなく、脳が遠くの未来を認識しにくい特性です。対策は、未来を強制的に「今」に引き寄せることです。",
            "methods": [
                {
                    "name": "If-Then Planning（実行意図）",
                    "how_to": "「もしXが起きたら、Yをする」という形式で行動ルールを事前に決めてください。\n\n【具体例】\n- 「もしPCを開いたら、最初にメールではなく企画書ファイルを開く」\n- 「もし昼食後にデスクに戻ったら、まず5分だけ報告書を書く」\n- 「もし電車に乗ったら、SNSではなく電子書籍を開く」",
                    "tips": "ニューヨーク大学の研究で、この方法を使うと目標達成率が約2倍になることが示されています。脳は「もし〜なら」という条件を自動トリガーとして認識するため、意志力に頼らず行動を開始できます。",
                    "check": "1週間後、設定したIf-Thenルールを実行できた回数を数えてください。5回以上実行できていれば定着し始めています。"
                },
                {
                    "name": "Task Unpacking（タスクの極小分解）",
                    "how_to": "気の進まない大きなタスクを、これ以上分解できないレベルまで細かく分解してください。\n\n【分解例：企画書作成】\n1. ファイルを新規作成する（1分）\n2. タイトルを入力する（1分）\n3. 目次の見出しを3つ書く（3分）\n4. 最初のセクションに1文だけ書く（2分）\n\n最初の1だけを目標にしてください。",
                    "tips": "脳は「大きな塊」を見ると恐怖や面倒さを感じますが、「ファイルを開く」だけなら抵抗なく実行できます。一度始めると継続しやすくなる傾向があります。",
                    "check": "分解したタスクのうち、最初の1つを実行できたかを確認してください。それができれば成功です。"
                },
                {
                    "name": "Time Boxing（時間の箱詰め）",
                    "how_to": "ToDoリストをやめ、全てのタスクをカレンダー上の「予定」としてブロックしてください。\n\n【手順】\n1. Google CalendarまたはOutlookを開く\n2. タスクを「14:00-14:30 企画書の目次を作る」のように開始・終了時刻付きで登録\n3. 通知を5分前に設定\n4. その時間が来たら、会議と同じように必ず着手する",
                    "tips": "「いつかやる」というタスクは永遠に先送りされがちです。カレンダーに入れることで「会議」と同じ強制力を持たせられます。",
                    "check": "1週間後、カレンダーに入れたタスクのうち予定通り着手できた割合を確認してください。50%以上なら良好です。"
                }
            ]
        })

    # 2. 予期が濃い (Strong Expectation)
    if s_exp_int >= 13:
        recommendations.append({
            "title": "Pressure Release - プレッシャーの解放",
            "reason": "未来のリスクや責任を重く見積もる傾向があり、プレッシャーで動けなくなったり、燃え尽きるリスクがあります。「止まる技術」と「完璧主義の手放し」が処方箋です。",
            "methods": [
                {
                    "name": "Pomodoro Technique（強制休憩サイクル）",
                    "how_to": "25分作業→5分休憩を1セットとし、4セット後に15〜30分の長い休憩を取ってください。\n\n【手順】\n1. タイマーアプリ（Forest, Focus To-Do等）をインストール\n2. 25分にセット\n3. タイマーが鳴るまで1つのタスクだけに集中\n4. 鳴ったら必ず手を止めて休憩（これが最重要）\n5. 休憩中は立ち上がる、窓の外を見る、ストレッチする",
                    "tips": "人間の集中力の限界は20〜30分とされています。あなたは「止まれない」タイプの可能性が高いので、タイマーで強制的に休憩を入れることが重要です。",
                    "check": "1日に何ポモドーロ（25分セット）完了できたかを記録してください。"
                },
                {
                    "name": "80% Completion Rule（8割完成主義）",
                    "how_to": "最初から100点を目指さず、「2割の時間で80点の出来」を目指してアウトプットしてください。\n\n【実践法】\n1. 作業開始前に「今回の80点ライン」を定義する\n   例：図表なし・箇条書きでOK・誤字脱字は後で直す\n2. その基準を満たしたら即座に提出/共有\n3. フィードバックをもらってから残り20%を詰める",
                    "tips": "時間をかけて100点を目指しても、方向性が違えば全て無駄になります。素早く80点を作り、フィードバックをもらうサイクルを回す方が、結果的に高品質な成果物になります。",
                    "check": "初回提出までの時間が短縮されたか、手戻りの回数が減ったかを確認してください。"
                },
                {
                    "name": "Pre-commitment（強制休暇）",
                    "how_to": "3ヶ月以上先のスケジュールに、キャンセルすると金銭的痛みを伴う休暇を入れてください。\n\n【手順】\n1. 今すぐカレンダーを開き、3ヶ月後の週末を選ぶ\n2. 航空券・ホテル・レストランなど、キャンセル料が発生する予約を入れる\n3. チームに休暇予定を共有し、外堀を埋める",
                    "tips": "意志力だけで休むことは困難です。「仕事が落ち着いたら休む」という日は来ません。環境側から強制的に休みを作り出すことが唯一の解決策です。",
                    "check": "予約した休暇を実際に取得できたかを確認してください。"
                }
            ]
        })

    # 3. 予期が多い (High Quantity)
    if s_exp_qty >= 13:
        recommendations.append({
            "title": "Mental Declutter - 思考の整理整頓",
            "reason": "やるべきことが多すぎて、脳のワーキングメモリがパンクしている可能性があります。常に何かに追われている感覚があり、一つ一つの質が低下しがちです。「頭の外に出す」と「捨てる」が鍵です。",
            "methods": [
                {
                    "name": "Brain Dump（思考の外部化）",
                    "how_to": "頭の中にある「やるべきこと」「気になること」を全て書き出してください。\n\n【手順】\n1. タイマーを15分にセット\n2. 紙またはデジタルツールに、思いつく限りのタスク・心配事・アイデアを書き出す（質は問わない、とにかく全部）\n3. 書き出したら、以下の3つに分類：\n   - 今週やる\n   - いつかやる（別リストに移動）\n   - やらない（削除）",
                    "tips": "脳は「覚えておかなければ」という情報でワーキングメモリを消費します。外部に書き出すことで、脳のメモリを解放し、目の前のことに集中できるようになります。週に1回の実施を推奨します。",
                    "check": "ブレインダンプ後に「頭がスッキリした感覚」があるかを確認してください。"
                },
                {
                    "name": "Eisenhower Matrix（優先順位の強制決定）",
                    "how_to": "タスクを「緊急/非緊急」×「重要/非重要」の4象限に分類し、捨てる判断を強制してください。\n\n【4象限の対処法】\n1. 緊急かつ重要 → 今すぐ自分でやる\n2. 緊急でないが重要 → スケジュールに入れる（最優先で時間確保）\n3. 緊急だが重要でない → 誰かに任せる or 断る\n4. 緊急でも重要でもない → 削除する\n\n特に3,4を意識的に増やしてください。",
                    "tips": "「緊急だが重要でない」タスクに時間を取られていませんか？メールの即レス、突発的な依頼など、本当に自分がやるべきか問い直してください。",
                    "check": "1週間のタスクを振り返り、4象限のどこに時間を使っていたかを可視化してください。「重要だが緊急でない」の割合を増やすことが目標です。"
                },
                {
                    "name": "Calendar is King（時間の有限化）",
                    "how_to": "ToDoリストを廃止し、全てのタスクをカレンダーに入れてください。\n\n【ルール】\n1. カレンダーの枠に入り切らないタスクは「物理的に不可能」として来週以降に回す\n2. 「空白の時間」も予定として確保する（バッファタイム）\n3. 1日の最後に翌日のカレンダーを確認し、現実的かチェック\n4. 入り切らない場合は、何かを削除または移動する",
                    "tips": "ToDoリストは無限に増えますが、時間は有限です。カレンダーという「有限の箱」を使うことで、強制的に「やらないこと」を決められます。",
                    "check": "1週間後、カレンダー通りに1日を終えられた日が何日あったかを確認してください。"
                }
            ]
        })

    # 4. 予期が少ない (Low Quantity) - 強みとして活かす
    if s_exp_qty <= 12:
        recommendations.append({
            "title": "Deep Focus - 深い集中の活用",
            "reason": "予期の量が少なく、目の前のことに没頭できる良好な状態です。この「一点集中」の才能を最大限に活かし、成果の質を高めるための環境設計を行いましょう。",
            "methods": [
                {
                    "name": "Deep Work Block（集中時間の確保）",
                    "how_to": "1日の中に「中断されない集中時間」を90分以上確保してください。\n\n【手順】\n1. カレンダーに「Deep Work」として90分のブロックを予約\n2. その時間は通知をOFF、メール・Slackを閉じる\n3. 可能なら場所も変える（会議室、カフェ等）\n4. この時間は最も重要な「思考系タスク」だけに使う\n   例：企画立案、戦略策定、執筆、設計",
                    "tips": "知識労働者の成果の大部分は「深い集中状態」で生み出されます。浅い作業（メール、チャット）に分断されない時間を意図的に作ることが、あなたの強みを最大化します。",
                    "check": "Deep Work中に生み出したアウトプットの量・質を記録し、通常時と比較してください。"
                },
                {
                    "name": "Flow State Optimization（フロー状態の最適化）",
                    "how_to": "「没頭できる状態」を意図的に作り出してください。\n\n【フローに入るための3条件】\n1. 明確なゴールがある（「今日はここまで終わらせる」を1文で定義）\n2. 即座にフィードバックが得られる（進捗を30分ごとに確認）\n3. 難易度が適切（簡単すぎず難しすぎない）\n\n【実践】タスク開始前に「今日のゴール」を付箋に書いてモニターに貼る",
                    "tips": "フロー状態（ゾーン）に入ると、時間の感覚がなくなり、高い生産性と充実感が得られます。あなたは既にこの状態に入りやすい素養があります。条件を整えることで、より頻繁にフロー状態に入れます。",
                    "check": "「時間を忘れて没頭できた」経験が週に何回あったかを記録してください。"
                }
            ]
        })

    # 5. 想起の正確性が低い (Low Recall Accuracy)
    if s_rec_acc <= 12:
        recommendations.append({
            "title": "Estimation Calibration - 見積もりの校正",
            "reason": "過去の経験から時間を正しく見積もれておらず、「計画錯誤（楽観的な見積もり）」に陥りやすい傾向があります。自分の「感覚」ではなく、「データ」と「仕組み」で補正することが必要です。",
            "methods": [
                {
                    "name": "Pre-mortem Thinking（事前検死）",
                    "how_to": "プロジェクト開始前に「失敗した未来」を想像し、その原因を列挙してください。\n\n【手順】\n1. 「このプロジェクトは完全に失敗した」と仮定する\n2. 「なぜ失敗したのか？」を5つ以上書き出す\n   例：クライアントの要望が途中で変わった、他の案件が割り込んだ、技術的な問題が発生した\n3. それぞれの原因に対する予防策を考える\n4. 見積もり時間にその予防策や対応の時間を加算する",
                    "tips": "ノーベル賞心理学者ダニエル・カーネマンが推奨する手法です。「うまくいく前提」ではなく「失敗する前提」で計画を立てることで、計画錯誤を大幅に軽減できます。",
                    "check": "プレモータムで挙げた失敗原因が実際に発生したかを振り返り、予測精度を確認してください。"
                },
                {
                    "name": "Time Log（実績の記録と比較）",
                    "how_to": "1週間、全ての作業時間を記録し、見積もりとの差を分析してください。\n\n【手順】\n1. Toggl, Clockify, またはスプレッドシートを用意\n2. 作業を開始したら記録開始、終了したら記録終了\n3. 各タスクに「見積もり時間」も記入\n4. 1週間後、見積もりと実績の差を計算\n5. 差が大きかったタスクの傾向を把握（例：会議は常に30%オーバー）\n6. 次回から、その傾向を見積もりに反映する",
                    "tips": "多くの人は「会議」「メール対応」「割り込み」に想像以上の時間を取られています。記録することで初めて、時間の使い方の実態が見えてきます。",
                    "check": "1週間の記録を見て、「思ったより時間がかかったタスク」のパターンを3つ特定してください。"
                },
                {
                    "name": "1.5x Rule（バッファの強制適用）",
                    "how_to": "見積もりを出す際、直感した時間を自動的に1.5倍〜2倍にしてください。\n\n【適用例】\n- 「1時間で終わる」→ 1.5時間で見積もる\n- 「3日で終わる」→ 5日で見積もる\n- 「今週中に」→ 来週前半までに\n\nこれをルールとして機械的に適用してください。",
                    "tips": "人間には「トラブルなくスムーズにいった場合の最短時間」を見積もってしまう傾向があります。1.5倍にしてようやく「現実的なライン」になります。余った時間は次のタスクに使えばよいだけです。",
                    "check": "1.5倍ルールを適用した見積もりが、実績とどれくらい近かったかを確認してください。"
                }
            ]
        })

    # 6. 想起の正確性が高い (High Recall Accuracy) - 肯定メッセージのみ
    if s_rec_acc >= 13:
        positive_messages.append({
            "title": "想起の正確性：良好",
            "message": "過去の経験から時間を正確に見積もる能力が高い状態です。この強みを維持しながら、他の領域の改善に集中してください。見積もり精度を維持するために、引き続き過去の実績を参照する習慣を続けることを推奨します。"
        })

    # 7. 想起が肯定的で正確性が低い (Positive but Low Accuracy)
    if s_rec_pos >= 13 and s_rec_acc <= 12:
        recommendations.append({
            "title": "Optimism Calibration - 楽観の校正",
            "reason": "「なんとかなる」という自信が強い一方で、見積もりの精度が低い傾向があります。この組み合わせは「計画倒れ」を繰り返すリスクがあります。ポジティブさは維持しつつ、計画段階では意図的に「冷静な視点」を入れる必要があります。",
            "methods": [
                {
                    "name": "10-10-10 Test（3つの時間軸テスト）",
                    "how_to": "決断や見積もりをする前に、3つの時間軸で自問してください。\n\n【質問】\n- 10分後の自分はこの判断をどう思うか？\n- 10ヶ月後の自分はこの判断をどう思うか？\n- 10年後の自分はこの判断をどう思うか？\n\n【例】「今日は疲れたから明日やろう」\n- 10分後：楽になる\n- 10ヶ月後：先延ばし癖がついて成果が出ない\n- 10年後：成長機会を逃し続けた後悔",
                    "tips": "短期的な楽観と長期的な現実を天秤にかけることで、バランスの取れた判断ができます。",
                    "check": "重要な判断の前にこのテストを実施し、判断が変わったケースを記録してください。"
                },
                {
                    "name": "Environment Design（環境設計）",
                    "how_to": "計画が崩れた際、実際に何をしていたかを正直に記録し、その誘惑を物理的に遮断してください。\n\n【記録フォーマット】\n- 計画：14時から企画書作成\n- 実際：SNSを見ていた\n- 誘惑のトリガー：スマホが視界に入った\n\n【環境設計】\n- スマホを別室に置く\n- SNSアプリを削除する\n- 作業場所を変える（カフェ、会議室）",
                    "tips": "意志の力だけで誘惑に勝とうとしないでください。環境を変えることで、無意識の行動を防ぎやすくなります。",
                    "check": "誘惑を遮断した後、計画通りに進められた割合が増えたかを確認してください。"
                }
            ]
        })

    # 8. 想起が肯定的で正確性も高い (Positive and High Accuracy) - 肯定メッセージのみ
    if s_rec_pos >= 13 and s_rec_acc >= 13:
        positive_messages.append({
            "title": "想起のバランス：理想的",
            "message": "過去の経験を正確かつ肯定的に捉えられており、時間感覚において理想的なバランスです。この状態は、自己効力感が高く、かつ現実的な計画が立てられる最も生産的な状態です。現在の習慣を維持してください。余裕があれば、あなたのノウハウをチームに共有することで、組織全体の生産性向上に貢献できます。"
        })

    # 9. 想起が否定的 (Negative Recall)
    if s_rec_pos <= 12:
        recommendations.append({
            "title": "Confidence Building - 自信の構築",
            "reason": "過去の経験を否定的に捉える傾向があり、「自分には無理だ」「どうせ失敗する」と挑戦を避けがちになる可能性があります。必要なのは能力向上ではなく、「自分を責めるパターン」の解除と、小さな成功体験の積み重ねです。",
            "methods": [
                {
                    "name": "Self-Compassion（自分への思いやり）",
                    "how_to": "失敗したとき、自分を責める代わりに「親友に声をかけるように」自分に語りかけてください。\n\n【3つのステップ】\n1. 気づき：「今、自分は落ち込んでいる」と認識する\n2. 共通性：「失敗するのは人間として普通のこと。自分だけじゃない」と認める\n3. 優しさ：「よく頑張った。次に活かそう」と声をかける\n\n【実践のコツ】実際に声に出すか、紙に書くと効果的です。",
                    "tips": "心理学者クリスティン・ネフ博士の研究で、セルフコンパッションが高い人は失敗から立ち直りが早く、挑戦を恐れなくなることが示されています。自己批判は短期的にはモチベーションになりますが、長期的にはパフォーマンスを下げます。",
                    "check": "失敗した時の「自分への声かけ」が以前より優しくなっているかを観察してください。"
                },
                {
                    "name": "5-Minute Rule（5分ルール）",
                    "how_to": "気が進まないタスク、自信がないタスクも、まず「5分だけ」手をつけてください。\n\n【ルール】\n1. 「5分だけやる。無理なら止めてOK」と自分に宣言する\n2. タイマーを5分にセット\n3. 5分経ったら、続けるか止めるか選ぶ\n\n多くの場合、5分やると「もう少しやろうかな」という気持ちになります。",
                    "tips": "やる気は待っていても湧いてきません。行動することで後からやる気が出てくる傾向があります。最初の一歩を極限まで小さくすることで、「始められない」を克服できます。",
                    "check": "5分ルールを適用して着手できた日数を記録してください。"
                },
                {
                    "name": "Micro-Success Log（小さな成功の記録）",
                    "how_to": "毎日の終わりに「今日できたこと」を3つ書き出してください。\n\n【ルール】\n1. どんなに小さなことでもOK\n   例：「朝ちゃんと起きた」「メール1通返した」「会議に遅れず参加した」\n2. 「できなかったこと」は書かない（これが重要）\n3. 1週間続けたら、リストを見返す\n\n【ツール】紙のノート、またはスマホのメモアプリ",
                    "tips": "脳は「できなかったこと」を強く記憶する傾向があります（ネガティビティ・バイアス）。意識的に「できたこと」を記録することで、自己効力感が回復していきます。",
                    "check": "1週間後、リストを見返したときに「意外とできている」と感じられるかを確認してください。"
                }
            ]
        })

    # --- 結果表示 ---
    if positive_messages:
        for msg in positive_messages:
            st.markdown(f"""
            <div class="positive-box">
                <strong>{msg['title']}</strong><br>
                {msg['message']}
            </div>
            """, unsafe_allow_html=True)

    if recommendations:
        for rec in recommendations:
            with st.expander(f"{rec['title']}", expanded=False):
                st.markdown(f"**なぜ効果があるのか（Why This Works）**")
                st.info(rec['reason'])
                
                st.markdown("---")
                st.markdown("**推奨メソッド（Recommended Methods）**")
                
                for i, method in enumerate(rec['methods'], 1):
                    st.markdown(f"### {i}. {method['name']}")
                    
                    st.markdown("**やり方（How-To）**")
                    st.markdown(method['how_to'])
                    
                    st.markdown("**ポイント（Tips）**")
                    st.markdown(method['tips'])
                    
                    st.markdown("**効果確認（Check）**")
                    st.success(method['check'])
                    
                    if i < len(rec['methods']):
                        st.markdown("---")
    else:
        if not positive_messages:
            st.success("現在の時間感覚バランスは非常に良好です。現在の習慣を維持してください。")

    return summary_future, summary_past

# --- メイン処理 ---
if submitted:
    q_scores = [
        option_values[q1_score], option_values[q2_score], option_values[q3_score],
        option_values[q4_score], option_values[q5_score], option_values[q6_score],
        option_values[q7_score], option_values[q8_score], option_values[q9_score],
        option_values[q10_score], option_values[q11_score], option_values[q12_score],
        option_values[q13_score], option_values[q14_score], option_values[q15_score],
        option_values[q16_score], option_values[q17_score], option_values[q18_score],
        option_values[q19_score], option_values[q20_score]
    ]
    
    s_exp_int = sum(q_scores[0:5])
    s_exp_qty = sum(q_scores[5:10])
    s_rec_acc = sum(q_scores[10:15])
    s_rec_pos = sum(q_scores[15:20])
    
    if data_consent:
        user_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nickname": user_nickname if user_nickname else "",
            "grade": user_grade if user_grade != "回答しない" else "",
            "s_exp_int": s_exp_int,
            "s_exp_qty": s_exp_qty,
            "s_rec_acc": s_rec_acc,
            "s_rec_pos": s_rec_pos
        }
        
        save_success = save_response(user_data)
        if save_success:
            st.success("回答が保存されました。ご協力ありがとうございます。")
    
    st.markdown("---")
    st.header("診断結果")
    
    display_results(s_exp_int, s_exp_qty, s_rec_acc, s_rec_pos, 
                   is_restored=False, show_comparison=data_consent)

elif show_restored_results:
    st.markdown("---")
    st.header("診断結果（保存された結果）")
    
    display_results(
        restored_scores['s_exp_int'],
        restored_scores['s_exp_qty'],
        restored_scores['s_rec_acc'],
        restored_scores['s_rec_pos'],
        is_restored=True,
        show_comparison=True
    )

st.markdown("---")
st.caption("Developed for Dirbato Co., Ltd.")
