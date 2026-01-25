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
        strategies.append("- Sustainable Pace")
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

# --- 設問データ（改訂版） ---
questions = {
    "expected_intensity": [
        "Q1. 普段から、1年後や5年後の自分の状況を具体的な映像としてイメージできる。",
        "Q2. 今日の行動が将来にどう影響するかを、日常的に意識している。",
        "Q3. 来月の予定について考えると、それがすぐ目の前に迫っているように感じる。",
        "Q4. 将来の楽しみな予定を考えると、今からワクワクした気持ちになる。",
        "Q5. 数年先の目標に向けた行動を、今日から始めることに抵抗がない。"
    ],
    "expected_quantity": [
        "Q6. 普段、頭の中に「やらなければならないこと」が5つ以上同時に浮かんでいる。",
        "Q7. 一つの作業に集中していても、別のタスクのことが頭をよぎることが多い。",
        "Q8. 予定のない空き時間ができると、何か予定を入れたくなる。",
        "Q9. 今週中にやるべきことを全て挙げようとすると、10個以上は思いつく。",
        "Q10. 複数のプロジェクトや予定を同時に抱えている状態が普通だと感じる。"
    ],
    "recalled_accuracy": [
        "Q11. 作業時間を見積もるとき、過去に同様の作業にかかった実際の時間を思い出して参考にする。",
        "Q12. 過去に見積もりが外れた経験を覚えており、その原因を説明できる。",
        "Q13. 自分の作業スピードについて、「このタスクなら何分」という感覚を持っている。",
        "Q14. 計画を立てるとき、「予定通りにいかなかった過去のケース」を具体的に思い浮かべる。",
        "Q15. 見積もり時間と実際にかかった時間を比較・記録したことがある。"
    ],
    "recalled_positivity": [
        "Q16. 振り返ると、自分は時間を概ね有意義に使ってきたと感じる。",
        "Q17. 過去に費やした時間の中で、「無駄だった」と後悔することは少ない。",
        "Q18. うまくいかなかった経験も、振り返れば学びがあったと思える。",
        "Q19. 過去の自分の判断は、その時点では妥当なものだったと思うことが多い。",
        "Q20. 以前取り組んだ仕事やプロジェクトを思い出すと、達成感を感じることが多い。"
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
    st.caption("未来の出来事がどれだけ心理的にリアルに、近く感じられるかを測定します")
    q1_score = st.radio(questions["expected_intensity"][0], options, horizontal=True, key="q1")
    q2_score = st.radio(questions["expected_intensity"][1], options, horizontal=True, key="q2")
    q3_score = st.radio(questions["expected_intensity"][2], options, horizontal=True, key="q3")
    q4_score = st.radio(questions["expected_intensity"][3], options, horizontal=True, key="q4")
    q5_score = st.radio(questions["expected_intensity"][4], options, horizontal=True, key="q5")
    
    st.markdown("---")
    st.subheader("Part B: 予期の量（Quantity）")
    st.caption("頭の中に同時に存在するタスク・予定・心配事の数を測定します")
    q6_score = st.radio(questions["expected_quantity"][0], options, horizontal=True, key="q6")
    q7_score = st.radio(questions["expected_quantity"][1], options, horizontal=True, key="q7")
    q8_score = st.radio(questions["expected_quantity"][2], options, horizontal=True, key="q8")
    q9_score = st.radio(questions["expected_quantity"][3], options, horizontal=True, key="q9")
    q10_score = st.radio(questions["expected_quantity"][4], options, horizontal=True, key="q10")

    st.header("Section 2: 過去の視点（Past Perspective）")
    st.info("過去に対する「想起」の傾向を分析します")
    
    st.subheader("Part C: 想起の正確性（Accuracy）")
    st.caption("過去の経験を参照して時間や労力を現実的に見積もる習慣を測定します")
    q11_score = st.radio(questions["recalled_accuracy"][0], options, horizontal=True, key="q11")
    q12_score = st.radio(questions["recalled_accuracy"][1], options, horizontal=True, key="q12")
    q13_score = st.radio(questions["recalled_accuracy"][2], options, horizontal=True, key="q13")
    q14_score = st.radio(questions["recalled_accuracy"][3], options, horizontal=True, key="q14")
    q15_score = st.radio(questions["recalled_accuracy"][4], options, horizontal=True, key="q15")

    st.markdown("---")
    st.subheader("Part D: 想起の肯定度（Positivity）")
    st.caption("過去の経験や自分の時間の使い方をどの程度肯定的に評価しているかを測定します")
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
    st.info("あなたの時間感覚特性に基づいて導き出された戦略を提示します。⭐マークは特に推奨する戦略です。")

    recommendations = []
    positive_messages = []

    # 1. 予期が薄い (Weak Expectation) - Intensity ≤ 12
    if s_exp_int <= 12:
        recommendations.append({
            "title": "Future Connection - 未来との接続強化",
            "connection": f"あなたの「予期の濃さ」スコアは {s_exp_int}/25 でした。これは、未来の出来事が心理的に「遠く」感じられ、今の行動と将来の結果が結びつきにくい状態を示しています。",
            "reason": "未来が遠く感じられると、目先の誘惑に流されやすくなります。これは意志の弱さではなく、脳が「遠くの報酬」を過小評価する傾向によるものです。対策は、未来を「今ここ」に引き寄せる技法を使うことです。",
            "methods": [
                {
                    "name": "ビジョン・エクササイズ",
                    "priority": "recommended",
                    "time_required": "1分/回",
                    "how_to": "作業を始める前に、以下のステップを実行してください。\n\n【手順】\n1. 椅子に座り、目を閉じる\n2. 深呼吸を3回する\n3. 「この作業が終わった瞬間の自分」を30秒間イメージする\n   - どんな気持ちか？\n   - 誰に報告しているか？\n   - 何が見えているか？\n4. 目を開けて作業を開始する",
                    "tips": "脳は「鮮明にイメージできるもの」を「近い」と認識します。納期直前の自分を先に体験することで、未来が心理的に近づき、行動を起こしやすくなります。",
                    "check": "1週間、毎日1回実施し、作業への着手がスムーズになったか確認してください。",
                    "first_step": "今日の最初のタスクを始める前に、目を閉じて「それが終わった瞬間の自分」を30秒だけ想像してください。"
                },
                {
                    "name": "デイリー・メトリクス",
                    "priority": "standard",
                    "time_required": "5分/日",
                    "how_to": "長期目標を「今日やる1つの行動」に分解してください。\n\n【手順】\n1. 長期目標を書き出す（例：3ヶ月後に資格を取る）\n2. 「今週やること」を1つ決める（例：テキスト第1章を読む）\n3. 「今日やること」を1つ決める（例：テキストを10ページ読む）\n4. 朝、その「今日やること」をカレンダーに入れる\n5. 夜、できたかどうかだけをチェックする",
                    "tips": "「3ヶ月後の目標」は遠すぎて行動に繋がりません。「今日の10ページ」なら具体的で、達成感も得られます。長期目標を日単位に変換することで、毎日小さな前進を実感できます。",
                    "check": "1週間後、「今日やること」を何日達成できたかカウントしてください。5日以上なら良好です。",
                    "first_step": "今抱えている最も大きな目標を1つ選び、「今日できる最小の1歩」を付箋に書いてモニターに貼ってください。"
                },
                {
                    "name": "タイムボクシング",
                    "priority": "standard",
                    "time_required": "10分/日",
                    "how_to": "ToDoリストをやめ、全てのタスクをカレンダー上の「時間枠」として予約してください。\n\n【手順】\n1. Google CalendarまたはOutlookを開く\n2. 今日やるべきタスクを「14:00-14:30 企画書の目次を作る」のように登録\n3. 通知を5分前に設定\n4. その時間が来たら、会議と同じように必ず着手する\n5. 時間内に終わらなくても、次の予定に移る（続きは別枠で予約）",
                    "tips": "「いつかやる」は永遠に来ません。カレンダーに入れることで「会議」と同じ強制力が生まれます。時間内に終わらなくても、「着手した」という事実が重要です。",
                    "check": "1週間後、カレンダーに入れたタスクのうち「着手できた」割合を確認してください。50%以上なら成功です。",
                    "first_step": "明日の午前中に「30分だけ」の作業枠を1つカレンダーに入れてください。"
                },
                {
                    "name": "アンパッキング（タスク分解）",
                    "priority": "standard",
                    "time_required": "5分/回",
                    "how_to": "大きなタスクを「これ以上分解できない」レベルまで細かくしてください。\n\n【分解例：企画書作成】\n1. ファイルを新規作成する（1分）\n2. タイトルを入力する（1分）\n3. 目次の見出しを3つ書く（3分）\n4. 最初のセクションに1文だけ書く（2分）\n\n【ルール】各ステップは5分以内で完了できるサイズにする",
                    "tips": "脳は「大きな塊」を見ると恐怖や面倒さを感じます。「ファイルを開く」だけなら抵抗なく実行できます。最初の1ステップだけを目標にしてください。",
                    "check": "分解した最初の1ステップを実行できたら成功です。",
                    "first_step": "今最も先延ばしにしているタスクを1つ選び、「最初の5分でやること」だけを紙に書いてください。"
                },
                {
                    "name": "ロールレタリング",
                    "priority": "advanced",
                    "time_required": "30分/回",
                    "how_to": "3年後の自分に手紙を書き、その返信を書いてください。\n\n【手順】\n1. 便箋またはWordを用意\n2. 「3年後の自分へ」という手紙を書く\n   - 今の悩み、目標、不安を正直に書く\n   - 「あなたは今どうなっていますか？」と問いかける\n3. 次に「3年後の自分から今の自分へ」の返信を書く\n   - 3年後の視点で、今の自分にアドバイスする\n   - 「あの時〇〇しておいてよかった」と書いてみる",
                    "tips": "未来の自分との対話を通じて、「今の行動が未来を作る」という実感が得られます。月に1回程度の実施を推奨します。",
                    "check": "手紙を書いた後、「未来のために今日やるべきこと」が1つ浮かんだら成功です。",
                    "first_step": "週末に30分の時間を確保し、「3年後の自分」に向けて今の正直な気持ちを書いてみてください。"
                }
            ]
        })

    # 2. 予期が濃い (Strong Expectation) - Intensity ≥ 13
    if s_exp_int >= 13:
        recommendations.append({
            "title": "Sustainable Pace - 持続可能なペースの構築",
            "connection": f"あなたの「予期の濃さ」スコアは {s_exp_int}/25 でした。これは、未来の責任や締切を強くリアルに感じており、常に「やらなければ」というプレッシャーを抱えやすい状態を示しています。",
            "reason": "未来が濃く感じられると、休むことに罪悪感を覚え、結果として燃え尽きるリスクが高まります。問題は「休む能力」の欠如です。意志の力ではなく、「休まざるを得ない仕組み」を作ることが解決策です。",
            "methods": [
                {
                    "name": "リマインディング（10年後の後悔テスト）",
                    "priority": "recommended",
                    "time_required": "5分/回",
                    "how_to": "休暇を取るか迷ったとき、以下の質問を自分に投げかけてください。\n\n【質問】\n「この休暇を取らなかったとして、10年後の自分はどう思うだろうか？」\n\n【具体例】\n- 「家族旅行をキャンセルして仕事を優先した10年後の自分」\n- 「体調を崩すまで働き続けた10年後の自分」\n- 「趣味の時間を全て仕事に充てた10年後の自分」\n\n10年後に後悔しそうなら、その休暇は取るべきです。",
                    "tips": "目の前の仕事は緊急に見えますが、10年後には大半が思い出せません。一方、休暇の思い出や健康は10年後も残ります。時間軸を伸ばすことで、正しい判断がしやすくなります。",
                    "check": "次に休暇を迷ったとき、この質問を使って判断してください。",
                    "first_step": "今週末の予定を確認し、「仕事を入れようとしている時間」があれば、10年後の後悔テストを適用してください。"
                },
                {
                    "name": "プレコミットメント（強制休暇予約）",
                    "priority": "recommended",
                    "time_required": "30分/回",
                    "how_to": "3ヶ月以上先に、キャンセルすると損失が発生する休暇を予約してください。\n\n【手順】\n1. 今すぐカレンダーを開き、3ヶ月後の週末を選ぶ\n2. 以下のいずれかを予約する（キャンセル料が発生するもの）\n   - 航空券（LCCでも可）\n   - ホテル（キャンセル不可プラン）\n   - レストラン（コース予約）\n   - イベントチケット\n3. チームに休暇予定を共有し、カレンダーをブロックする",
                    "tips": "「仕事が落ち着いたら休む」という日は来ません。キャンセル料という「損失」を設定することで、休暇を守る強制力が生まれます。これは意志の弱さではなく、人間の損失回避傾向を利用した合理的な戦略です。",
                    "check": "予約した休暇を実際に取得できたかを確認してください。",
                    "first_step": "今日中に、3ヶ月後の1日に「キャンセル料が発生する予約」を1つ入れてください。"
                },
                {
                    "name": "機能的アリバイ",
                    "priority": "standard",
                    "time_required": "5分/回",
                    "how_to": "休暇を取る際に、自分を納得させる「理由」を用意してください。\n\n【効果的なアリバイ例】\n- 「今週は〇〇を達成したから、休む権利がある」（努力の報酬）\n- 「この休暇は早割で30%オフだから、経済的に合理的」（金銭的メリット）\n- 「休むことで来週の生産性が上がるから、投資として正しい」（ROI思考）\n- 「健康診断の結果が良くなかったから、休息は必須」（健康上の理由）",
                    "tips": "休むことに罪悪感を覚える人は、「正当な理由」があると休みやすくなります。理由は後付けでも構いません。大切なのは、自分の脳を説得することです。",
                    "check": "次に休暇を取るとき、事前に「なぜ休むのか」の理由を1つ用意してください。",
                    "first_step": "直近で「休みたいけど休めなかった」経験を思い出し、どんな「アリバイ」があれば休めたか考えてください。"
                },
                {
                    "name": "ビジュアライズ（1年後の自分）",
                    "priority": "standard",
                    "time_required": "10分/回",
                    "how_to": "1年後の自分を、以下の3つの観点で具体的に想像してください。\n\n【観点】\n1. 健康：体重、睡眠、疲労度はどうなっている？\n2. 人間関係：家族、友人、同僚との関係はどうなっている？\n3. 仕事：成果、評価、やりがいはどうなっている？\n\n【手順】\n- 紙に3つの観点を書く\n- 「今のペースを続けた場合」の1年後を書く\n- 「適切に休んだ場合」の1年後を書く\n- 2つを比較する",
                    "tips": "「今のペースを続けた1年後」を具体的に想像すると、多くの場合、持続不可能であることに気づきます。この気づきが、休息の重要性を実感させます。",
                    "check": "2つのシナリオを比較して、「休息の価値」を実感できたかを確認してください。",
                    "first_step": "今日の夜、5分だけ時間を取り、「今のペースを1年続けたらどうなるか」を紙に書いてください。"
                },
                {
                    "name": "80%完成主義",
                    "priority": "advanced",
                    "time_required": "5分/回",
                    "how_to": "作業開始前に「今回の80点ライン」を定義し、それを満たしたら完了としてください。\n\n【80点ラインの例】\n- 企画書：図表なし、箇条書きでOK、誤字脱字は後で修正\n- プレゼン資料：デザインは後回し、内容の骨子が伝われば可\n- メール：完璧な文章でなくても、意図が伝われば送信\n\n【手順】\n1. 作業開始前に「今回の80点ライン」を1文で書く\n2. その基準を満たしたら、即座に提出/共有\n3. フィードバックを受けてから残り20%を詰める",
                    "tips": "100点を目指して時間をかけても、方向性が違えば全て無駄になります。80点で早く出し、フィードバックを得るサイクルの方が、結果的に高品質になります。",
                    "check": "初回提出までの時間が短縮されたか、手戻りが減ったかを確認してください。",
                    "first_step": "次のタスクを始める前に、「どこまでできたら一旦完了とするか」を付箋に書いてください。"
                }
            ]
        })

    # 3. 予期が多い (High Quantity) - Quantity ≥ 13
    if s_exp_qty >= 13:
        recommendations.append({
            "title": "Mental Declutter - 思考の整理整頓",
            "connection": f"あなたの「予期の量」スコアは {s_exp_qty}/25 でした。これは、頭の中に多くのタスクや予定が同時に存在し、常に「やるべきこと」に追われている感覚がある状態を示しています。",
            "reason": "頭の中のタスクが多すぎると、脳のワーキングメモリがパンクし、一つ一つの作業の質が低下します。解決策は「頭の外に出す」ことと「やらないことを決める」ことです。",
            "methods": [
                {
                    "name": "SSCエクササイズ",
                    "priority": "recommended",
                    "time_required": "15分/週",
                    "how_to": "全てのタスクを「Stop（やめる）」「Shrink（減らす）」「Continue（続ける）」に分類してください。\n\n【手順】\n1. 現在抱えている全タスクをリストアップする\n2. 各タスクを以下の基準で分類する：\n   - Stop：やめても影響が小さいもの → 削除または断る\n   - Shrink：頻度や品質を下げられるもの → 隔週にする、簡略化する\n   - Continue：維持すべきもの → そのまま継続\n3. Stop/Shrinkに分類したものを実際にやめる/減らす",
                    "tips": "「全部大事」と思いがちですが、実際にやめてみると影響がないことが多いです。「やめる」判断を先にすることで、本当に重要なことに集中できます。",
                    "check": "1週間後、Stop/Shrinkに分類したタスクを実際に削減できたかを確認してください。",
                    "first_step": "今抱えているタスクを5つ書き出し、1つだけ「やめる」または「減らす」ものを選んでください。"
                },
                {
                    "name": "ブレインダンプ",
                    "priority": "recommended",
                    "time_required": "15分/週",
                    "how_to": "頭の中にある全てを紙に書き出してください。\n\n【手順】\n1. タイマーを15分にセット\n2. 紙またはデジタルツールに、思いつく限りのタスク・心配事・アイデアを書き出す\n   - 質は問わない、とにかく全部出す\n   - 「牛乳を買う」から「キャリアプラン」まで全て\n3. 書き出したら、以下の3つに分類：\n   - 今週やる → カレンダーに入れる\n   - いつかやる → 別リストに移動\n   - やらない → 削除",
                    "tips": "脳は「覚えておかなければ」という情報でワーキングメモリを消費します。外部に書き出すだけで、頭がスッキリし、目の前のことに集中できます。週1回の実施を推奨します。",
                    "check": "ブレインダンプ後に「頭が軽くなった」感覚があるかを確認してください。",
                    "first_step": "今すぐ5分だけ時間を取り、頭の中にある「気になっていること」を10個書き出してください。"
                },
                {
                    "name": "ポモドーロ・テクニック",
                    "priority": "standard",
                    "time_required": "即時開始可",
                    "how_to": "25分作業→5分休憩のサイクルで作業してください。\n\n【手順】\n1. タイマーアプリ（Forest, Focus To-Do等）をインストール\n2. 取り組むタスクを1つ決める\n3. タイマーを25分にセット\n4. タイマーが鳴るまで、そのタスクだけに集中（他のことは全て無視）\n5. 鳴ったら必ず手を止めて5分休憩\n6. 4セット終わったら15-30分の長い休憩",
                    "tips": "「25分だけ」と区切ることで、複数のタスクが頭をよぎっても「後で」と先送りできます。脳が「今はこれだけ」と認識することで、集中力が維持されます。",
                    "check": "1日に何ポモドーロ完了できたかを記録してください。",
                    "first_step": "スマホにタイマーアプリをインストールし、次のタスクで25分タイマーを試してください。"
                },
                {
                    "name": "障害プランニング",
                    "priority": "standard",
                    "time_required": "10分/回",
                    "how_to": "プロジェクト開始前に、想定される障害と対策をリストアップしてください。\n\n【手順】\n1. これから取り組むプロジェクト/タスクを1つ選ぶ\n2. 「うまくいかない可能性があること」を5つ書き出す\n   例：クライアントの要望変更、他案件の割り込み、技術的問題、体調不良、情報不足\n3. 各障害に対する「対策」を書く\n   例：「要望変更」→ 事前に変更可能な範囲を合意しておく\n4. 対策を実行する時間を見積もりに加える",
                    "tips": "事前に障害を想定しておくと、実際に発生したときのパニックが軽減されます。「想定内」になることで、冷静に対処できます。",
                    "check": "プランニングで挙げた障害が実際に発生したか、対策が機能したかを振り返ってください。",
                    "first_step": "今抱えている最も大きなプロジェクトについて、「うまくいかないかもしれないこと」を3つ書き出してください。"
                },
                {
                    "name": "エンゲージメント速度を上げる",
                    "priority": "standard",
                    "time_required": "5分/日",
                    "how_to": "毎朝、「今日最も重要な3つ」を選び、それだけに集中する意思を確認してください。\n\n【手順】\n1. 朝、仕事を始める前に5分確保\n2. 今日やることを全てリストアップ\n3. その中から「今日絶対にやる3つ」を選ぶ\n4. その3つを紙に書き、目の前に置く\n5. 他のタスクは「今日やらなくても大丈夫」と自分に言い聞かせる",
                    "tips": "人間は1日に重要なことを3つ以上こなすことが難しいとされています。「3つだけ」に絞ることで、分散していた注意を集中させられます。",
                    "check": "夕方、選んだ3つを完了できたかを確認してください。2つ以上できていれば成功です。",
                    "first_step": "明日の朝、仕事を始める前に「今日絶対にやる3つ」を付箋に書いてください。"
                },
                {
                    "name": "カレンダー・イズ・キング",
                    "priority": "advanced",
                    "time_required": "15分/日",
                    "how_to": "ToDoリストを廃止し、全てのタスクをカレンダーの時間枠として管理してください。\n\n【ルール】\n1. タスクは全て「開始時刻-終了時刻」を持つ予定として登録\n2. カレンダーに入り切らないタスクは「今日はやらない」と決める\n3. 「空白の時間」もバッファとして予定化する\n4. 1日の最後に翌日のカレンダーを確認し、現実的かチェック",
                    "tips": "ToDoリストは無限に増えますが、1日は24時間しかありません。カレンダーという「有限の箱」を使うことで、「やらないこと」を強制的に決められます。",
                    "check": "1週間後、カレンダー通りに1日を終えられた日が何日あったかを確認してください。",
                    "first_step": "今日の残りの時間を全てカレンダーにブロックし、入り切らないタスクを明日以降に移動してください。"
                }
            ]
        })

    # 4. 予期が少ない (Low Quantity) - Quantity ≤ 12
    if s_exp_qty <= 12:
        recommendations.append({
            "title": "Deep Focus - 集中力の活用",
            "connection": f"あなたの「予期の量」スコアは {s_exp_qty}/25 でした。これは、頭の中が比較的整理されており、目の前のことに集中しやすい状態を示しています。",
            "reason": "これは強みです。多くの人が「タスクが多すぎる」問題に悩む中、あなたは一点集中の素養があります。この特性を活かし、深い集中状態（フロー）を意図的に作り出すことで、成果の質を最大化できます。",
            "methods": [
                {
                    "name": "ディープワーク・ブロック",
                    "priority": "recommended",
                    "time_required": "5分/日（設定）",
                    "how_to": "カレンダーに「中断されない集中時間」を90分以上ブロックしてください。\n\n【手順】\n1. カレンダーに「Deep Work」として90分の予定を作成\n2. その時間は：\n   - 通知を全てOFF\n   - メール・Slackを閉じる\n   - 可能なら場所を変える（会議室、カフェ等）\n3. この時間は「思考系タスク」だけに使う\n   例：企画立案、戦略策定、執筆、設計\n4. 雑務（メール、事務作業）は別の時間にまとめる",
                    "tips": "知識労働者の価値ある成果の大部分は「深い集中状態」で生み出されます。あなたは既にこの状態に入りやすい素養があります。環境を整えることで、その強みを最大化できます。",
                    "check": "Deep Work中に生み出したアウトプットの量・質を記録し、通常時と比較してください。",
                    "first_step": "明日のカレンダーに「90分の集中時間」を1つブロックし、その間に取り組むタスクを1つ決めてください。"
                },
                {
                    "name": "シングルタスク宣言",
                    "priority": "standard",
                    "time_required": "10秒/回",
                    "how_to": "作業を始める前に「今からこれだけやる」と声に出してください。\n\n【手順】\n1. 取り組むタスクを1つ決める\n2. 「今から30分、〇〇だけをやる」と声に出す（または心の中で宣言）\n3. 他のことが気になったら「それは後で」と言い聞かせる\n4. 宣言した時間が終わったら、次のタスクに移る",
                    "tips": "声に出すことで、脳に「今はこれだけ」という指令が明確に伝わります。マルチタスクの誘惑を防ぐシンプルな方法です。",
                    "check": "宣言した時間内、そのタスクだけに集中できたかを確認してください。",
                    "first_step": "次のタスクを始める前に、「今から〇〇だけやる」と声に出してみてください。"
                },
                {
                    "name": "フロー条件の整備",
                    "priority": "standard",
                    "time_required": "5分/回",
                    "how_to": "フロー状態（没頭状態）に入るための3条件を事前に確認してください。\n\n【3条件のチェックリスト】\n1. ゴールは明確か？\n   → 「今日はここまで終わらせる」を1文で書く\n2. フィードバックは即座に得られるか？\n   → 30分ごとに進捗を確認する仕組みを作る\n3. 難易度は適切か？\n   → 簡単すぎず難しすぎない、「少し背伸び」レベルか確認",
                    "tips": "フロー状態に入ると、時間の感覚がなくなり、高い生産性と充実感が得られます。3条件を意識的に整えることで、フローに入る確率が上がります。",
                    "check": "「時間を忘れて没頭できた」経験が週に何回あったかを記録してください。",
                    "first_step": "次の重要なタスクを始める前に、3条件のチェックリストを確認してください。"
                }
            ]
        })

    # 5. 想起の正確性が低い (Low Recall Accuracy) - Accuracy ≤ 12
    if s_rec_acc <= 12:
        recommendations.append({
            "title": "Estimation Calibration - 見積もりの校正",
            "connection": f"あなたの「想起の正確性」スコアは {s_rec_acc}/25 でした。これは、過去の経験を参照して時間を見積もる習慣が弱く、「計画錯誤（楽観的すぎる見積もり）」に陥りやすい状態を示しています。",
            "reason": "見積もりが甘いと、常に締切に追われ、信頼を損ない、ストレスが増大します。解決策は、自分の「感覚」ではなく「データ」に基づいて見積もることです。",
            "methods": [
                {
                    "name": "ごまかし率の計算",
                    "priority": "recommended",
                    "time_required": "5分/回",
                    "how_to": "タスク完了後に「ごまかし率」を計算し、次回の見積もりに反映してください。\n\n【計算式】\nごまかし率 = 実際にかかった時間 ÷ 見積もった時間\n\n【例】\n- 見積もり：2時間 → 実際：3時間 → ごまかし率：1.5\n- 見積もり：1日 → 実際：2日 → ごまかし率：2.0\n\n【使い方】\n次回の見積もり = 直感の見積もり × 自分のごまかし率",
                    "tips": "多くの人のごまかし率は1.5〜2.0です。自分の傾向を数値で把握することで、「また甘く見積もっていないか」を客観的にチェックできます。",
                    "check": "3つ以上のタスクでごまかし率を計算し、自分の平均値を把握してください。",
                    "first_step": "直近で完了したタスクについて、「見積もり時間」と「実際の時間」を思い出し、ごまかし率を計算してください。"
                },
                {
                    "name": "タイムログ",
                    "priority": "recommended",
                    "time_required": "継続（1分/回）",
                    "how_to": "1週間、全ての作業時間を記録してください。\n\n【手順】\n1. Toggl, Clockify, またはスプレッドシートを用意\n2. 作業を開始したら記録開始、終了したら記録終了\n3. 各タスクに「見積もり時間」も記入\n4. 1週間後、見積もりと実績の差を計算\n5. 差が大きかったタスクの傾向を把握\n\n【記録項目】\n- タスク名\n- 開始時刻\n- 終了時刻\n- 見積もり時間\n- 実際の時間\n- 差分",
                    "tips": "記録することで「会議」「メール」「割り込み」に想像以上の時間を取られていることが見えてきます。自分の時間の使い方を客観視する第一歩です。",
                    "check": "1週間の記録を見て、「思ったより時間がかかったタスク」のパターンを3つ特定してください。",
                    "first_step": "今日から、主要なタスク3つだけでも開始・終了時刻を記録してください。"
                },
                {
                    "name": "他人に見積もってもらう",
                    "priority": "standard",
                    "time_required": "2分/回",
                    "how_to": "自分の作業の所要時間を、同僚や上司に推測してもらってください。\n\n【手順】\n1. これから取り組むタスクを同僚に説明する\n2. 「これ、どのくらいかかると思う？」と聞く\n3. 自分の見積もりと比較する\n4. 差が大きい場合、その理由を話し合う\n\n【質問例】\n- 「この資料作成、何時間くらいかかると思う？」\n- 「このプロジェクト、何日くらい見ておくべき？」",
                    "tips": "自分のタスクは「簡単に見える」傾向がありますが、他人から見ると「大変そう」に見えることが多いです。第三者の視点を借りることで、見積もりの偏りを補正できます。",
                    "check": "他人の見積もりと自分の見積もり、どちらが実際に近かったかを確認してください。",
                    "first_step": "今日取り組むタスクについて、同僚に「どのくらいかかると思う？」と聞いてみてください。"
                },
                {
                    "name": "1.5倍ルール",
                    "priority": "standard",
                    "time_required": "即時適用",
                    "how_to": "見積もりを出す際、直感した時間を自動的に1.5倍にしてください。\n\n【適用例】\n- 「1時間で終わる」→ 1.5時間で見積もる\n- 「3日で終わる」→ 5日で見積もる\n- 「今週中に」→ 来週前半までに\n\nこれを例外なくルールとして適用してください。",
                    "tips": "人間は「全てがスムーズにいった場合の最短時間」を見積もる傾向があります。1.5倍にしてようやく「現実的なライン」になります。余った時間は次のタスクに使えば無駄になりません。",
                    "check": "1.5倍ルールを適用した見積もりが、実績とどれくらい近かったかを確認してください。",
                    "first_step": "次の見積もりを求められたとき、頭に浮かんだ時間を1.5倍にして回答してください。"
                },
                {
                    "name": "プレモータム（事前検死）",
                    "priority": "standard",
                    "time_required": "10分/回",
                    "how_to": "プロジェクト開始前に「失敗した未来」を想像し、その原因を列挙してください。\n\n【手順】\n1. 「このプロジェクトは完全に失敗した」と仮定する\n2. 「なぜ失敗したのか？」を5つ以上書き出す\n3. それぞれの原因に対する予防策を考える\n4. 予防策の実行時間を見積もりに加算する",
                    "tips": "ダニエル・カーネマンが推奨する手法です。「うまくいく前提」ではなく「失敗する前提」で計画を立てることで、計画錯誤を大幅に軽減できます。",
                    "check": "プレモータムで挙げた失敗原因が実際に発生したかを振り返ってください。",
                    "first_step": "今抱えている最も大きなプロジェクトについて、「失敗する原因」を3つ書き出してください。"
                },
                {
                    "name": "コピー・プロンプト",
                    "priority": "advanced",
                    "time_required": "10分/週",
                    "how_to": "時間管理が上手い人のやり方を1つ選び、真似してください。\n\n【手順】\n1. チーム内で「時間管理が上手い」と思う人を1人選ぶ\n2. その人に「どうやって見積もりをしているか」を聞く\n3. その手法を1つだけ選び、1週間試してみる\n4. 効果があれば継続、なければ別の手法を試す",
                    "tips": "自分で一から方法を考えるより、上手くいっている人の方法を真似る方が効率的です。「守破離」の「守」として、まず真似ることから始めてください。",
                    "check": "真似した手法が自分に合っているかを1週間後に評価してください。",
                    "first_step": "チーム内で「時間の使い方が上手い」と思う人を1人思い浮かべ、その人のどこを真似できそうか考えてください。"
                }
            ]
        })

    # 6. 想起の正確性が高い (High Recall Accuracy) - Accuracy ≥ 13
    if s_rec_acc >= 13:
        positive_messages.append({
            "title": "想起の正確性：良好",
            "message": f"あなたの「想起の正確性」スコアは {s_rec_acc}/25 でした。これは、過去の経験を参照して現実的な見積もりを行う能力が高いことを示しています。この強みを維持するために、引き続き以下を意識してください。",
            "maintenance_tips": [
                "月に1回、見積もりと実績の差を振り返る習慣を維持する",
                "新しいタイプのタスクに取り組む際は、意識的に過去の類似経験を参照する",
                "チームメンバーの見積もりをレビューする際に、あなたの視点を共有する"
            ]
        })

    # 7. 想起が肯定的で正確性が低い (Positive but Low Accuracy)
    if s_rec_pos >= 13 and s_rec_acc <= 12:
        recommendations.append({
            "title": "Optimism Calibration - 楽観の校正",
            "connection": f"あなたは「想起の肯定度」が高く（{s_rec_pos}/25）、「想起の正確性」が低い（{s_rec_acc}/25）状態です。これは、過去を肯定的に捉える一方で、見積もりの精度が低い傾向を示しています。",
            "reason": "「なんとかなる」という楽観は強みですが、見積もりが甘いと「計画倒れ」を繰り返すリスクがあります。ポジティブさは維持しつつ、計画段階では意図的に「冷静な視点」を入れる必要があります。",
            "methods": [
                {
                    "name": "誘惑日記",
                    "priority": "recommended",
                    "time_required": "3分/日",
                    "how_to": "その日「誘惑に負けた体験」を1〜2行だけメモしてください。\n\n【記録フォーマット】\n- 日付：\n- 計画していたこと：\n- 実際にやったこと：\n- 誘惑のトリガー：\n\n【例】\n- 日付：1/25\n- 計画：14時から企画書作成\n- 実際：SNSを30分見ていた\n- トリガー：スマホの通知",
                    "tips": "「なんとかなる」と思っていても、実際には誘惑に負けていることが多いです。記録することで、自分の「弱点パターン」が見えてきます。責めるためではなく、対策を立てるための記録です。",
                    "check": "1週間後、記録を見返して「誘惑に負けやすいパターン」を3つ特定してください。",
                    "first_step": "今日の終わりに、「計画通りにいかなかったこと」を1つだけメモしてください。"
                },
                {
                    "name": "ごまかし率の計算",
                    "priority": "recommended",
                    "time_required": "5分/回",
                    "how_to": "タスク完了後に「ごまかし率」を計算し、次回の見積もりに反映してください。\n\n【計算式】\nごまかし率 = 実際にかかった時間 ÷ 見積もった時間\n\n自分の楽観度を数値化することで、「どれくらい甘く見積もる傾向があるか」を客観視できます。",
                    "tips": "楽観的な人ほど、ごまかし率が高い傾向があります。自分の数値を知ることで、「また楽観的になっていないか」をチェックできます。",
                    "check": "自分のごまかし率を把握し、次回の見積もりに反映してください。",
                    "first_step": "直近で完了したタスクのごまかし率を計算してください。"
                },
                {
                    "name": "10-10-10テスト",
                    "priority": "standard",
                    "time_required": "3分/回",
                    "how_to": "決断や見積もりをする前に、3つの時間軸で自問してください。\n\n【質問】\n- 10分後の自分はこの判断をどう思うか？\n- 10ヶ月後の自分はこの判断をどう思うか？\n- 10年後の自分はこの判断をどう思うか？",
                    "tips": "楽観的な判断は「10分後」には心地よいですが、「10ヶ月後」には後悔することが多いです。時間軸を伸ばすことで、冷静な判断がしやすくなります。",
                    "check": "重要な判断の前にこのテストを実施し、判断が変わったケースを記録してください。",
                    "first_step": "次に「まあ大丈夫だろう」と思ったとき、10ヶ月後の自分がどう思うかを考えてください。"
                },
                {
                    "name": "環境設計",
                    "priority": "standard",
                    "time_required": "10分/回",
                    "how_to": "誘惑のトリガーを物理的に遮断してください。\n\n【よくあるトリガーと対策】\n- スマホ → 別室に置く、通知OFF、アプリ削除\n- SNS → ブロックアプリ（Freedom等）を使用\n- メール → 特定の時間以外は閉じる\n- 同僚の話しかけ → ヘッドホン着用、場所移動",
                    "tips": "意志の力だけで誘惑に勝とうとしないでください。環境を変える方が、はるかに効果的で持続可能です。",
                    "check": "誘惑を遮断した後、計画通りに進められた割合が増えたかを確認してください。",
                    "first_step": "誘惑日記で特定した「トリガー」を1つ選び、物理的に遮断する方法を試してください。"
                },
                {
                    "name": "想起リライティング",
                    "priority": "advanced",
                    "time_required": "15分/回",
                    "how_to": "過去の失敗を思い出し、「対策を講じた自分」を想像してください。\n\n【手順】\n1. 過去の「計画倒れ」を1つ思い出す\n2. 「なぜ失敗したか」を書き出す\n3. 「どうすれば防げたか」の対策を考える\n4. 「対策を講じて成功した自分」を具体的に想像する\n5. その対策を次回の計画に組み込む",
                    "tips": "過去の失敗を「教訓」として書き換えることで、同じパターンを繰り返さなくなります。失敗を責めるのではなく、学びに変換する作業です。",
                    "check": "リライティングした対策を、次の計画に実際に組み込めたかを確認してください。",
                    "first_step": "直近の「計画倒れ」を1つ思い出し、「どうすれば防げたか」を1つ書いてください。"
                }
            ]
        })

    # 8. 想起が肯定的で正確性も高い (Positive and High Accuracy)
    if s_rec_pos >= 13 and s_rec_acc >= 13:
        positive_messages.append({
            "title": "想起のバランス：理想的",
            "message": f"あなたは「想起の肯定度」（{s_rec_pos}/25）と「想起の正確性」（{s_rec_acc}/25）の両方が高い、理想的なバランスです。これは、過去を肯定的に捉えながらも現実的な見積もりができる状態であり、高い自己効力感と実行力を兼ね備えています。",
            "maintenance_tips": [
                "この良好な状態を維持するために、定期的に時間の使い方を振り返る習慣を続ける",
                "余裕があれば、チームメンバーの時間管理をサポートする役割を担う",
                "新しいチャレンジに積極的に取り組み、成功体験をさらに積み重ねる"
            ]
        })

    # 9. 想起が否定的 (Negative Recall) - Positivity ≤ 12
    if s_rec_pos <= 12:
        recommendations.append({
            "title": "Confidence Building - 自信の構築",
            "connection": f"あなたの「想起の肯定度」スコアは {s_rec_pos}/25 でした。これは、過去の経験や時間の使い方を否定的に評価する傾向があることを示しています。",
            "reason": "過去を否定的に捉えていると、「どうせ自分には無理」「また失敗する」と感じ、新しい挑戦を避けがちになります。必要なのは能力向上ではなく、「自分を責めるパターン」の解除と、小さな成功体験の積み重ねです。",
            "methods": [
                {
                    "name": "ネガティブ想起改善シート",
                    "priority": "recommended",
                    "time_required": "5分/回",
                    "how_to": "タスクの「予想」と「実際」を比較記録してください。\n\n【記録フォーマット】\n| 項目 | 予想 | 実際 |\n|-----|-----|-----|\n| 困難度（1-10） | | |\n| 満足度（1-10） | | |\n| かかった時間 | | |\n\n【手順】\n1. タスク開始前に「困難度」「満足度」「時間」を予想\n2. タスク完了後に「実際」を記録\n3. 予想と実際の差を確認",
                    "tips": "否定的な人は「思ったより大変だった」と感じがちですが、実際に記録すると「思ったより簡単だった」「思ったより満足できた」ことが多いです。データで認知の歪みを修正できます。",
                    "check": "5回以上記録し、「予想より実際の方が良かった」ケースが何割あったかを確認してください。",
                    "first_step": "今日取り組むタスク1つについて、開始前に「困難度」を1-10で予想し、完了後に実際の困難度を記録してください。"
                },
                {
                    "name": "マイクロ・サクセス",
                    "priority": "recommended",
                    "time_required": "5分/日",
                    "how_to": "1日の終わりに「今日できたこと」を3つ書き出してください。\n\n【ルール】\n1. どんなに小さなことでもOK\n   例：「朝起きた」「メール1通返した」「会議に参加した」\n2. 「できなかったこと」は書かない（これが重要）\n3. 各項目に「それによって得られたメリット」も1行追加\n\n【記録例】\n- できたこと：朝9時に出社した\n- メリット：午前中に集中して作業できた",
                    "tips": "脳は「できなかったこと」を強く記憶します（ネガティビティ・バイアス）。意識的に「できたこと」を記録することで、自己認識のバランスを取り戻せます。",
                    "check": "1週間後、リストを見返したときに「意外とできている」と感じられるかを確認してください。",
                    "first_step": "今日の終わりに、「今日できたこと」を3つ、どんなに小さなことでも書いてください。"
                },
                {
                    "name": "5分ルール",
                    "priority": "standard",
                    "time_required": "即時適用",
                    "how_to": "気が進まないタスクも、まず「5分だけ」手をつけてください。\n\n【手順】\n1. 「5分だけやる。無理なら止めてOK」と自分に宣言\n2. タイマーを5分にセット\n3. 5分経ったら、続けるか止めるか選ぶ\n\n多くの場合、5分やると「もう少しやろうかな」という気持ちになります。",
                    "tips": "やる気は「行動の後」に湧いてきます。最初の一歩を極限まで小さくすることで、「始められない」を克服できます。5分で止めても、「やった」という事実が自信になります。",
                    "check": "5分ルールを適用して着手できた日数を記録してください。",
                    "first_step": "今最も気が進まないタスクに、「5分だけ」手をつけてください。"
                },
                {
                    "name": "アドバイス法",
                    "priority": "standard",
                    "time_required": "10分/回",
                    "how_to": "同じ悩みを持つ人にアドバイスするつもりで、自分の問題を考えてください。\n\n【手順】\n1. 自分が抱えている問題を書き出す\n2. 「同じ問題を持つ後輩が相談に来た」と想定する\n3. その後輩に何とアドバイスするかを書く\n4. そのアドバイスを自分に適用する",
                    "tips": "人は自分に対しては厳しく、他人に対しては優しくなる傾向があります。「他人へのアドバイス」という形式にすることで、自分への優しさを引き出せます。",
                    "check": "アドバイスした内容を、実際に自分で試せたかを確認してください。",
                    "first_step": "今抱えている悩みを1つ選び、「後輩にどうアドバイスするか」を考えてください。"
                },
                {
                    "name": "リフレクション（成功体験の分析）",
                    "priority": "standard",
                    "time_required": "15分/回",
                    "how_to": "過去の成功体験を1つ選び、なぜ成功したかを分析してください。\n\n【手順】\n1. 過去の成功体験を1つ思い出す（どんなに小さくてもOK）\n2. 「なぜ成功したか」の要因を3つ書き出す\n3. その要因を、今の課題に活かせないか考える\n4. 具体的な行動を1つ決める",
                    "tips": "失敗ばかり思い出しがちですが、成功体験も必ずあります。成功の要因を分析することで、「自分にもできる」という自信が回復します。",
                    "check": "分析した成功要因を、新しい課題に1つ適用できたかを確認してください。",
                    "first_step": "過去1年で「うまくいった」と思える経験を1つ思い出し、なぜうまくいったかを1行で書いてください。"
                },
                {
                    "name": "セルフ・コンパッション",
                    "priority": "advanced",
                    "time_required": "3分/回",
                    "how_to": "失敗したとき、自分を責める代わりに「親友に声をかけるように」自分に語りかけてください。\n\n【3つのステップ】\n1. 気づき：「今、自分は落ち込んでいる」と認識する\n2. 共通性：「失敗するのは人間として普通。自分だけじゃない」と認める\n3. 優しさ：「よく頑張った。次に活かそう」と声をかける\n\n実際に声に出すか、紙に書くと効果的です。",
                    "tips": "自己批判は短期的にはモチベーションになりますが、長期的にはパフォーマンスを下げます。クリスティン・ネフ博士の研究で、セルフコンパッションが高い人は失敗から立ち直りが早いことが示されています。",
                    "check": "失敗した時の「自分への声かけ」が以前より優しくなっているかを観察してください。",
                    "first_step": "次に何かうまくいかなかったとき、「親友だったら何と声をかけるか」を考えてみてください。"
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
            
            if 'maintenance_tips' in msg:
                st.markdown("**維持・発展のためのヒント：**")
                for tip in msg['maintenance_tips']:
                    st.markdown(f"- {tip}")

    if recommendations:
        for rec in recommendations:
            with st.expander(f"{rec['title']}", expanded=False):
                # 設問との接続を表示
                st.markdown(f"**あなたの傾向（Your Pattern）**")
                st.info(rec['connection'])
                
                st.markdown(f"**なぜ効果があるのか（Why This Works）**")
                st.markdown(rec['reason'])
                
                st.markdown("---")
                st.markdown("**推奨メソッド（Recommended Methods）**")
                
                for i, method in enumerate(rec['methods'], 1):
                    # 優先度に応じたマーク
                    if method.get('priority') == 'recommended':
                        st.markdown(f"### ⭐ {i}. {method['name']}（推奨）")
                    elif method.get('priority') == 'advanced':
                        st.markdown(f"### {i}. {method['name']}（発展）")
                    else:
                        st.markdown(f"### {i}. {method['name']}")
                    
                    # 所要時間
                    st.caption(f"所要時間: {method['time_required']}")
                    
                    st.markdown("**やり方（How-To）**")
                    st.markdown(method['how_to'])
                    
                    st.markdown("**ポイント（Tips）**")
                    st.markdown(method['tips'])
                    
                    st.markdown("**効果確認（Check）**")
                    st.markdown(method['check'])
                    
                    # 今日やること（First Step）を強調表示
                    st.markdown("**今日やること（First Step）**")
                    st.success(method['first_step'])
                    
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
