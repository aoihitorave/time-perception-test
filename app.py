import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import os

# --- フォント設定 (Streamlit Cloud対応 / 日本語化) ---
def configure_japanese_font():
    # Noto Sans JPフォントをダウンロードして設定
    font_url = 'https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP-Regular.ttf'
    font_path = 'NotoSansJP-Regular.ttf'
    
    if not os.path.exists(font_path):
        import urllib.request
        try:
            urllib.request.urlretrieve(font_url, font_path)
        except Exception as e:
            st.error(f"Font download failed: {e}")
            return

    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'Noto Sans JP'

configure_japanese_font()
# --------------------------------------------------

# ページ設定
st.set_page_config(page_title="Time Perception Analysis", layout="centered")

# --- スタイル調整 (CSS) ---
st.markdown("""
<style>
    h1 { font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 700; color: #2C3E50; }
    h2, h3 { font-family: 'Helvetica Neue', Arial, sans-serif; color: #34495E; }
    .stMetric { background-color: #F8F9F9; padding: 15px; border-radius: 5px; border: 1px solid #E5E8E8; }
    .disclaimer { font-size: 0.8rem; color: #7F8C8D; background-color: #F2F3F4; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 免責事項 (Legal/Ethical Disclaimer) ---
st.markdown("""
<div class="disclaimer">
    <strong>【免責事項・本ツールの位置づけ】</strong><br>
    本アプリケーションは、書籍『YOUR TIME ユア・タイム』（鈴木 祐 著）で紹介されている理論を参考に、
    独自の見解を付加し一定の母集団向けの提供を目的として構築された<strong>非公式のプロトタイプ</strong>です。<br>
    設問ロジックや診断結果は本アプリケーション向けに独自に再構成されており、原著の正式な診断とは異なります。
    また、本結果は医学的な診断を提供するものではなく、各人にマッチする可能性の高い時間術の仮説を提示するものです。
</div>
""", unsafe_allow_html=True)

# --- タイトル ---
st.title("Time Perception Analysis")
st.markdown("認知科学的アプローチによる時間感覚の特性分析")

# --- 設問データ ---
questions = {
    "expected_intensity": [
        "Q1. 今の行動が、5年後や10年後の未来にどう繋がるかをイメージするのが得意だ。",
        "Q2. 目の前の楽しさよりも、将来起こりうるリスクの方に自然と意識が向く。",
        "Q3. 将来の幸福を達成するためなら、目先の幸福を犠牲にするのにも抵抗がない。",
        "Q4. 「今これをやらなければ、将来必ず後悔する」という観点で物事を見ることが多い。",
        "Q5. 楽しい時間を過ごしている最中でも、つい「次にやるべきこと」や「後の予定」を考えてしまう。"
    ],
    "expected_quantity": [
        "Q6. スケジュール帳に空白があると、そこに何か予定を入れたくなる、あるいは入れてしまう。",
        "Q7. ひとつの作業をしている最中に、他の複数の「やらなければならないこと」が頭に浮かんでくる。",
        "Q8. 全てのタスクが「今すぐやるべき重要事項」に見えてしまい、どれも捨てがたいと感じる。",
        "Q9. 常に「時間が足りない」「何かに追われている」という感覚がある。",
        "Q10. 長期の目標よりも、数時間〜数日以内の「こなすべき用事」で頭がいっぱいだ。"
    ],
    "recalled_accuracy": [
        "Q11. 過去の経験に基づき、「意外と時間がかかるかもしれない」とバッファ（余裕）を持たせる癖がある。",
        "Q12. 「自分ならもっと早くできるはずだ」という期待よりも、過去の実績タイムを信頼する。",
        "Q13. 計画を立てる際に、障害や不測の事態を必ず考える。",
        "Q14. 過去に自分がどれくらいのスピードで作業できたか、具体的に思い出すことができる。",
        "Q15. 作業を始める前に、過去の類似タスクにおける失敗パターンをシミュレーションする。"
    ],
    "recalled_positivity": [
        "Q16. 過去の自分の判断や行動は、今の自分にとってプラスになっていると思う。",
        "Q17. 「自分は時間を有効に使ってきた人間だ」という自信がある。",
        "Q18. 過去の失敗を思い出しても、「あれはあれで良い経験だった」と意味づけできる。",
        "Q19. 未知の課題に直面しても、「過去になんとかなったから今回も大丈夫だろう」と思える。",
        "Q20. 作業前に「これは自分には無理だろう」と思うことはない。"
    ]
}

# --- フォーム作成 ---
options = ["全く当てはまらない (1)", "あまり当てはまらない (2)", "どちらともいえない (3)", "やや当てはまる (4)", "完全に当てはまる (5)"]
option_values = {options[0]: 1, options[1]: 2, options[2]: 3, options[3]: 4, options[4]: 5}

with st.form("diagnosis_form"):
    st.header("Section 1: Future Perspective")
    st.caption("未来に対する「予期」の傾向を分析します")
    
    st.subheader("Part A: Intensity (予期の濃さ)")
    q1_score = st.radio(questions["expected_intensity"][0], options, horizontal=True)
    q2_score = st.radio(questions["expected_intensity"][1], options, horizontal=True)
    q3_score = st.radio(questions["expected_intensity"][2], options, horizontal=True)
    q4_score = st.radio(questions["expected_intensity"][3], options, horizontal=True)
    q5_score = st.radio(questions["expected_intensity"][4], options, horizontal=True)
    
    st.markdown("---")
    st.subheader("Part B: Quantity (予期の量)")
    q6_score = st.radio(questions["expected_quantity"][0], options, horizontal=True)
    q7_score = st.radio(questions["expected_quantity"][1], options, horizontal=True)
    q8_score = st.radio(questions["expected_quantity"][2], options, horizontal=True)
    q9_score = st.radio(questions["expected_quantity"][3], options, horizontal=True)
    q10_score = st.radio(questions["expected_quantity"][4], options, horizontal=True)

    st.header("Section 2: Past Perspective")
    st.caption("過去に対する「想起」の傾向を分析します")
    
    st.subheader("Part C: Accuracy (想起の正確性)")
    q11_score = st.radio(questions["recalled_accuracy"][0], options, horizontal=True)
    q12_score = st.radio(questions["recalled_accuracy"][1], options, horizontal=True)
    q13_score = st.radio(questions["recalled_accuracy"][2], options, horizontal=True)
    q14_score = st.radio(questions["recalled_accuracy"][3], options, horizontal=True)
    q15_score = st.radio(questions["recalled_accuracy"][4], options, horizontal=True)

    st.markdown("---")
    st.subheader("Part D: Positivity (想起の肯定度)")
    q16_score = st.radio(questions["recalled_positivity"][0], options, horizontal=True)
    q17_score = st.radio(questions["recalled_positivity"][1], options, horizontal=True)
    q18_score = st.radio(questions["recalled_positivity"][2], options, horizontal=True)
    q19_score = st.radio(questions["recalled_positivity"][3], options, horizontal=True)
    q20_score = st.radio(questions["recalled_positivity"][4], options, horizontal=True)

    submitted = st.form_submit_button("Run Analysis", type="primary")

# --- 集計と結果表示ロジック ---
if submitted:
    s_exp_int = sum([option_values[x] for x in [q1_score, q2_score, q3_score, q4_score, q5_score]])
    s_exp_qty = sum([option_values[x] for x in [q6_score, q7_score, q8_score, q9_score, q10_score]])
    s_rec_acc = sum([option_values[x] for x in [q11_score, q12_score, q13_score, q14_score, q15_score]])
    s_rec_pos = sum([option_values[x] for x in [q16_score, q17_score, q18_score, q19_score, q20_score]])

    st.markdown("---")
    st.header("Analysis Result")

    def plot_matrix(x_score, y_score, x_label, y_label, title, x_min_text, x_max_text, y_min_text, y_max_text):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(0, 25)
        ax.set_ylim(0, 25)
        ax.axvline(x=12.5, color='#BDC3C7', linestyle='--', alpha=0.7)
        ax.axhline(y=12.5, color='#BDC3C7', linestyle='--', alpha=0.7)
        ax.scatter(x_score, y_score, color='#E74C3C', s=250, zorder=5, edgecolors='white', linewidth=2)
        
        ax.set_xlabel(x_label, fontsize=12, color='#34495E')
        ax.set_ylabel(y_label, fontsize=12, color='#34495E')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#2C3E50')
        
        # テキスト配置
        plt.text(1, 12.5, y_min_text, ha='left', va='center', rotation=90, color='#7F8C8D', fontsize=10)
        plt.text(1, 13, y_max_text, ha='left', va='center', rotation=90, color='#7F8C8D', fontsize=10)
        plt.text(12.5, 1, x_min_text, ha='center', va='bottom', color='#7F8C8D', fontsize=10)
        plt.text(13, 1, x_max_text, ha='center', va='bottom', color='#7F8C8D', fontsize=10)

        # 背景色分け
        rect = patches.Rectangle((12.5, 12.5), 12.5, 12.5, linewidth=0, edgecolor='none', facecolor='#ECF0F1', alpha=0.5)
        ax.add_patch(rect)
        
        st.pyplot(fig)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Future Perspective")
        st.metric("予期の濃さ (Intensity)", f"{s_exp_int} / 25")
        st.metric("予期の多さ (Quantity)", f"{s_exp_qty} / 25")
        plot_matrix(
            s_exp_qty, s_exp_int, 
            "予期の多さ (Quantity)", "予期の濃さ (Intensity)", 
            "Future Matrix", 
            "少ない", "多い", "薄い", "濃い"
        )

    with col2:
        st.markdown("#### Past Perspective")
        st.metric("想起の正確性 (Accuracy)", f"{s_rec_acc} / 25")
        st.metric("想起の肯定度 (Positivity)", f"{s_rec_pos} / 25")
        plot_matrix(
            s_rec_pos, s_rec_acc, 
            "肯定度 (Positivity)", "正確性 (Accuracy)", 
            "Past Matrix", 
            "否定的", "肯定的", "誤り", "正しい"
        )

    # --- Recommendations Logic ---
    st.markdown("---")
    st.header("Strategic Recommendations")
    st.info("スコアに基づき、推奨される「認知ハック」と「具体的なアクション」を提示します。")

    recommendations = []

    # 1. 予期が薄すぎる
    if s_exp_int <= 12:
        recommendations.append({
            "title": "Strategy: Future Connection (未来との接続強化)",
            "problem": "「今」に集中するあまり、未来の利益を過小評価し、先延ばしが発生しやすい傾向があります。",
            "methods": [
                {
                    "name": "Time Boxing (タイムボクシング)",
                    "how_to": "Googleカレンダー等で、タスクの「開始」と「終了」時間をブロックし、その時間は絶対にその作業以外しないと決める。",
                    "tips": "「できればやる」ではなく「会議」のように扱うのがコツ。最初は30分単位から。終了アラームが鳴ったら途中でもやめることで、次回への着手欲求を高める。"
                },
                {
                    "name": "Unpacking (アンパッキング)",
                    "how_to": "「企画書作成」などの大きなタスクを、「ファイル作成」「目次案出し」「導入部執筆」など5分で終わるレベルまで分解してリスト化する。",
                    "tips": "面倒だと感じるのはタスクが大きすぎるから。分解すれば脳は「これならできる」と認識する。「最初の1歩」を極限まで小さくする。"
                },
                 {
                    "name": "Vision Exercise (ビジョン・エクササイズ)",
                    "how_to": "作業に取り掛かる前に深呼吸し、3年後や10年後の理想的な自分の姿を鮮明にイメージしてからタスクに向かう。",
                    "tips": "視覚的イメージだけでなく、その時の感情や周囲の音まで想像すると効果が高い。"
                },
                 {
                    "name": "Role Lettering (ロールレタリング)",
                    "how_to": "「3年後の自分」になりきって、現在の自分に向けた手紙を書く。逆に、現在の自分から未来の自分へ返信を書く。",
                    "tips": "未来の自分からの視点を持つことで、現在の行動の意義を再確認できる。"
                },
                 {
                    "name": "Daily Matrix (デイリー・マトリクス)",
                    "how_to": "長期プロジェクトであっても、その進捗管理を「日単位」で細かく刻んで管理する。",
                    "tips": "遠い締切を「今日のノルマ」に変換することで、切迫感を生み出し行動を促す。"
                }
            ]
        })

    # 2. 予期が濃すぎる
    if s_exp_int >= 13:
        recommendations.append({
            "title": "Strategy: Anxiety Management (予期不安の管理)",
            "problem": "未来のリスクを過大評価し、プレッシャーや不安を感じやすい傾向があります。休息が苦手なタイプです。",
            "methods": [
                {
                    "name": "Pre-commitment (プレコミットメント)",
                    "how_to": "数ヶ月先に「キャンセル不可能な休暇（航空券予約など）」や「遊びの予定」を先に入れてしまう。",
                    "tips": "意志の力で休むのは不可能と割り切る。環境によって強制的に休む状況を作る。キャンセル料が発生する予約が最も効果的。"
                },
                {
                    "name": "Functional Alibi (機能的アリバイ)",
                    "how_to": "「良い仕事をするために、今は脳を休めるメンテナンス業務が必要だ」と、休息に論理的な正当性を与える。",
                    "tips": "「サボる」ではなく「回復プロセス」と定義し直す。「努力した後」「金銭的に得をした時」などに休暇を計画すると罪悪感が減る。"
                },
                {
                    "name": "Reminding (リマインディング)",
                    "how_to": "不安に襲われた時、「この悩みについて、10年後の自分は後悔しているだろうか？」と自問する。",
                    "tips": "視点を長期的な未来に移すことで、目の前の小さなトラブルに対する過剰反応を鎮める。"
                },
                 {
                    "name": "Visualize (ビジュアライズ)",
                    "how_to": "1年後の自分がどうなっているか、ポジティブな側面だけでなく、細かい日常の風景まで想像する。",
                    "tips": "漠然とした不安を、具体的なイメージに置き換えることで対処可能にする。"
                }
            ]
        })

    # 3. 予期が多すぎる
    if s_exp_qty >= 13:
        recommendations.append({
            "title": "Strategy: Bandwidth Optimization (脳内帯域の解放)",
            "problem": "マルチタスク傾向があり、常に「何かに追われている」感覚によるパフォーマンス低下が懸念されます。",
            "methods": [
                {
                    "name": "SSC Exercise (選択と放棄)",
                    "how_to": "タスクを「Start（始める）」「Stop（やめる）」「Continue（続ける）」に分類し、特にStopを決める。",
                    "tips": "「価値の低い仕事」を特定し、勇気を持って捨てるか、他人に移譲するか、質を下げる許可を自分に出す。"
                },
                 {
                    "name": "Deliberate Planning (熟慮プランニング)",
                    "how_to": "「もし障害が起きたら、その時じっくり考えればいい」と事前に決め、今の不安を遮断する。",
                    "tips": "すべてのリスクを事前に潰すのは不可能と知る。トラブル発生時の「思考時間」をあらかじめスケジュールに確保しておく。"
                },
                {
                    "name": "If-Then Planning (障害プランニング)",
                    "how_to": "「もしXが起きたらYをする」というルールを事前に紙に書き出す。（例：もしメールが来たら、16時まで返信しない）",
                    "tips": "トラブル対応の意思決定コストをゼロにすることが目的。事前に決めておけば脳のメモリを使わない。"
                },
                {
                     "name": "Engagement Speed (エンゲージメント速度を上げる)",
                     "how_to": "重要な問題を3つだけ選び、それらに対する「集中の意思」を毎朝確認する。",
                     "tips": "あれもこれもと手を出す前に、トッププライオリティを明確に意識することで、雑多な予期をフィルタリングする。"
                }
            ]
        })

    # 4. 想起の誤りが大きい
    if s_rec_acc <= 12:
        recommendations.append({
            "title": "Strategy: Calibration (見積もりの補正)",
            "problem": "過去の所要時間を過小評価し、計画錯誤（楽観的な計画倒れ）に陥りやすい傾向があります。",
            "methods": [
                {
                    "name": "Time Log (タイムログ)",
                    "how_to": "朝起きてから寝るまで、何に何分使ったかを1週間記録する。スマホアプリ（Toggl等）やメモ帳を使用。",
                    "tips": "修正するためではなく「事実を知る」ためだけに行う。体感時間とのズレに驚くことが第一歩。"
                },
                {
                    "name": "Ask Others (他人に見積もってもらう)",
                    "how_to": "自分の作業時間を、同僚や友人に予測してもらう。",
                    "tips": "当事者よりも第三者の方が、バイアスなく客観的な時間を見積もれることが多い。"
                },
                {
                    "name": "Copy Prompt (コピー・プロンプト)",
                    "how_to": "自分と同じタスクをうまくこなしている人の手順や時間をそのまま真似る。",
                    "tips": "「自分流」にこだわらず、成功モデルをトレースすることで見積もりの精度を強制的に高める。"
                }
            ]
        })

    # 5. 想起が肯定的すぎる（楽観バイアス）
    if s_rec_pos >= 13 and s_rec_acc <= 12:
        recommendations.append({
            "title": "Strategy: Reality Check (現実的なリスク評価)",
            "problem": "根拠のない自信がリスクの見落としに繋がっている可能性があります。",
            "methods": [
                {
                    "name": "Time Log Advance (タイムログ・アドバンス分析)",
                    "how_to": "記録したタイムログを、「仕事」「家事」「移動」などに仕分けし、時間の使い方の傾向を分析して対策を立てる。",
                    "tips": "「何に時間を使っているか」を可視化することで、楽観的な思い込みをデータで修正する。"
                },
                {
                    "name": "Temptation Diary (誘惑日記)",
                    "how_to": "計画が崩れた際、その原因となった「誘惑（スマホ、雑談など）」を記録する。",
                    "tips": "自分が何に弱いかを把握し、次回の計画時にその誘惑対策を盛り込む。"
                },
                {
                    "name": "Fudge Ratio (ごまかし率の計算)",
                    "how_to": "過去のタスクで「予定時間」と「実際にかかった時間」を割り算し、自分の「サバ読み係数（例：1.5倍）」を算出する。",
                    "tips": "次の見積もり時は、何も考えずにその係数を掛ける。自分の感覚を信じず、係数を信じる。"
                },
                {
                    "name": "Recalled Rewriting (想起リライティング)",
                    "how_to": "過去の失敗を振り返り、「どうすれば防げたか」「次はどうするか」を考え、解決した自分を想像する。",
                    "tips": "単なる反省ではなく、未来の成功イメージに書き換えることで、学習効果を高める。"
                }
            ]
        })

    # 6. 想起が否定的すぎる
    if s_rec_pos <= 12:
        recommendations.append({
            "title": "Strategy: Self-Efficacy (自己効力感の向上)",
            "problem": "過去の失敗体験にとらわれ、新たな挑戦へのハードルが高くなっている状態です。",
            "methods": [
                {
                    "name": "Negative Simulation Check (ネガティブ想起改善シート)",
                    "how_to": "作業前に予想した「困難度(1-10)」と「満足度(1-10)」を記録し、作業後に「実際の数値」と比較する。",
                    "tips": "多くの場合「やる前の予想」より「やった後の現実」の方がマシであることにデータで気づく。"
                },
                {
                    "name": "Micro Success (マイクロ・サクセス)",
                    "how_to": "1日の終わりに、どんなに小さなことでも良いので「できたこと」や「得たメリット」を書き残す。",
                    "tips": "「朝起きられた」「メールを返した」レベルでOK。脳の「できないフィルター」を解除する。"
                },
                 {
                    "name": "Advice Method (アドバイス法)",
                    "how_to": "自分と同じ悩みを持つ架空の人物（または友人）に対して、どのようなアドバイスをするか考える。",
                    "tips": "自分のことだと否定的になるが、他人のことなら冷静かつ建設的な解決策が思い浮かぶ性質を利用する。"
                },
                {
                    "name": "Reflection (リフレクション)",
                    "how_to": "過去の成功体験を分析し、なぜうまくいったのかその要因を言語化して、次のタスクに活かす。",
                    "tips": "「運が良かった」ではなく「自分の行動の何が良かったか」にフォーカスする。"
                }
            ]
        })
    
    # 7. 体質改善（時間不足・追われる感覚の根本解決） - 全員向けオプション
    # 特定のスコア条件なしに、すべての人に役立つ可能性があるため、Expandersとして下部に配置するか、
    # あるいはスコアが悪かった場合に追加表示する形をとる。今回は「予期多」や「予期濃」の補助として表示。
    
    if s_exp_qty >= 13 or s_exp_int >= 13:
         recommendations.append({
            "title": "Strategy: Fundamental Improvement (時間感覚の体質改善)",
            "problem": "効率化を求めても時間が足りない、常に時間に追われる感覚が消えない場合の根本対策です。",
            "methods": [
                 {
                    "name": "Ikigai Chart (生きがいチャート)",
                    "how_to": "「楽しい」「必要とされる」「稼げる」「得意」の4つの円が重なる領域を探し、自分の活動をマッピングする。",
                    "tips": "時間の使い方が自分の価値観と一致していないと、いくら効率化しても満足感は得られない。"
                },
                {
                    "name": "Deep Reading (文学に親しむ)",
                    "how_to": "簡単に解釈できない純文学や詩を精読する時間を設ける。",
                    "tips": "「すぐに答えが出ない時間」に耐性をつけることで、効率化中毒から脳を解放する。"
                },
                {
                    "name": "Altruism (他人のために時間を使う)",
                    "how_to": "小さな親切（同僚の手伝い、寄付など）をまずは1週間続けてみる。",
                    "tips": "「他人に時間を使えるほど自分には時間がある」という感覚（時間的豊かさ）を脳に錯覚させる強力な方法。"
                },
                {
                     "name": "Boredom Training (退屈トレーニング)",
                     "how_to": "単純作業や、何もしない時間をあえて作り、スマホを見ずに1週間実行する。",
                     "tips": "「退屈」を回避しようとする衝動が、余計なタスク（予期）を生んでいることに気づく。"
                },
                 {
                     "name": "Event Time (イベントタイムで過ごす)",
                     "how_to": "時計を禁止し、「腹が減ったら食べる」「作業が終わったら次へ」という、自分の感覚に従って行動する日を作る。",
                     "tips": "時計時間（クロックタイム）の支配から離れ、本来の身体感覚を取り戻す。"
                 }
            ]
         })


    # 結果表示ループ
    if not recommendations:
        st.success("Balance is optimal. 現在の時間感覚バランスは非常に良好です。")
    else:
        for rec in recommendations:
            with st.container():
                st.markdown(f"### {rec['title']}")
                st.markdown(f"**課題:** {rec['problem']}")
                
                for method in rec['methods']:
                    with st.expander(f"実践技法: {method['name']}", expanded=True):
                        st.markdown(f"**How-To (やり方):** {method['how_to']}")
                        st.markdown(f"**Tips (コツ):** {method['tips']}")

    st.markdown("---")
    st.caption("Reference: 『YOUR TIME ユア・タイム』(鈴木 祐 著)")
