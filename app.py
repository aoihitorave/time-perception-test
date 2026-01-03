import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- ページ設定 ---
st.set_page_config(page_title="Time Perception Analysis", layout="centered")

# --- スタイル調整 (CSS) ---
st.markdown("""
<style>
    /* 全体のフォント定義 */
    body { font-family: 'Helvetica Neue', Arial, sans-serif; }
    
    /* 免責事項のデザイン */
    .disclaimer-box {
        background-color: #262730;
        color: #FAFAFA;
        padding: 15px;
        border-left: 5px solid #FF4B4B;
        border-radius: 4px;
        margin-bottom: 25px;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    .disclaimer-title {
        font-weight: bold;
        color: #FF4B4B;
        display: block;
        margin-bottom: 5px;
    }
    
    /* 診断サマリボックス */
    .summary-box {
        background-color: #F0F2F6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #E6E9EF;
    }
    .summary-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2C3E50;
        margin-bottom: 10px;
    }
    .summary-tag {
        background-color: #FF4B4B;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: bold;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 免責事項 ---
st.markdown("""
<div class="disclaimer-box">
    <span class="disclaimer-title">【免責事項・本ツールの位置づけ】</span>
    本アプリケーションは、書籍『YOUR TIME ユア・タイム』（鈴木 祐 著）で紹介されている理論を参考に、
    独自の見解を付加し一定の母集団向けの提供を目的として構築された<strong>非公式のプロトタイプ</strong>です。<br>
    設問ロジックや診断結果は本アプリケーション向けに独自に再構成されており、原著の正式な診断とは異なります。<br>
    また、本結果は医学的な診断を提供するものではなく、各人にマッチする可能性の高い時間術の仮説を提示するものです。
</div>
""", unsafe_allow_html=True)

# --- タイトル ---
st.title("Time Perception Analysis")
st.caption("認知科学的アプローチによる時間感覚の特性分析")

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
    st.info("未来に対する「予期」の傾向を分析します")
    
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
    st.info("過去に対する「想起」の傾向を分析します")
    
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

    submitted = st.form_submit_button("Run Analysis (分析実行)", type="primary")

# --- 集計と結果表示ロジック ---
if submitted:
    s_exp_int = sum([option_values[x] for x in [q1_score, q2_score, q3_score, q4_score, q5_score]])
    s_exp_qty = sum([option_values[x] for x in [q6_score, q7_score, q8_score, q9_score, q10_score]])
    s_rec_acc = sum([option_values[x] for x in [q11_score, q12_score, q13_score, q14_score, q15_score]])
    s_rec_pos = sum([option_values[x] for x in [q16_score, q17_score, q18_score, q19_score, q20_score]])

    st.markdown("---")
    st.header("Analysis Result")

    # --- 診断サマリの判定 ---
    summary_future = []
    if s_exp_int <= 12: summary_future.append("予期が薄い (Weak)")
    if s_exp_int >= 13: summary_future.append("予期が濃い (Strong)")
    if s_exp_qty >= 13: summary_future.append("予期が多い (High)")
    if s_exp_qty <= 12: summary_future.append("予期が少ない (Low)")

    summary_past = []
    if s_rec_acc <= 12: summary_past.append("見積もりが甘い (Low Accuracy)")
    if s_rec_acc >= 13: summary_past.append("見積もりが正確 (High Accuracy)")
    if s_rec_pos <= 12: summary_past.append("否定的 (Negative)")
    if s_rec_pos >= 13: summary_past.append("肯定的 (Positive)")

    # サマリ表示
    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">📊 診断サマリ</div>
        <p><strong>Future Perspective (未来):</strong> {', '.join(summary_future)}</p>
        <p><strong>Past Perspective (過去):</strong> {', '.join(summary_past)}</p>
    </div>
    """, unsafe_allow_html=True)


    # --- チャート描画 (英語表記のみにして文字化け回避) ---
    def plot_matrix(x_score, y_score, x_label, y_label, title, x_min, x_max, y_min, y_max):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(0, 25)
        ax.set_ylim(0, 25)
        ax.axvline(x=12.5, color='#BDC3C7', linestyle='--', alpha=0.7)
        ax.axhline(y=12.5, color='#BDC3C7', linestyle='--', alpha=0.7)
        ax.scatter(x_score, y_score, color='#E74C3C', s=250, zorder=5, edgecolors='white', linewidth=2)
        
        ax.set_xlabel(x_label, fontsize=11, color='#34495E')
        ax.set_ylabel(y_label, fontsize=11, color='#34495E')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#2C3E50', pad=15)
        
        # 英語ラベル (文字化けしない)
        plt.text(1, 12.5, y_min, ha='left', va='center', rotation=90, color='#95A5A6', fontsize=10)
        plt.text(1, 13, y_max, ha='left', va='center', rotation=90, color='#95A5A6', fontsize=10)
        plt.text(12.5, 1, x_min, ha='center', va='bottom', color='#95A5A6', fontsize=10)
        plt.text(13, 1, x_max, ha='center', va='bottom', color='#95A5A6', fontsize=10)

        rect = patches.Rectangle((12.5, 12.5), 12.5, 12.5, linewidth=0, edgecolor='none', facecolor='#F0F2F6', alpha=0.5)
        ax.add_patch(rect)
        st.pyplot(fig)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Future Perspective (予期)**")
        st.markdown(f"予期の濃さ: **{s_exp_int}** / 25")
        st.markdown(f"予期の多さ: **{s_exp_qty}** / 25")
        plot_matrix(
            s_exp_qty, s_exp_int, 
            "Quantity (Expected)", "Intensity (Expected)", 
            "Future Matrix", 
            "Low", "High", "Weak", "Strong"
        )

    with col2:
        st.markdown(f"**Past Perspective (想起)**")
        st.markdown(f"想起の正確性: **{s_rec_acc}** / 25")
        st.markdown(f"想起の肯定度: **{s_rec_pos}** / 25")
        plot_matrix(
            s_rec_pos, s_rec_acc, 
            "Positivity (Recalled)", "Accuracy (Recalled)", 
            "Past Matrix", 
            "Negative", "Positive", "Error", "Correct"
        )

    # --- Recommendations Logic ---
    st.markdown("---")
    st.header("Strategic Recommendations")
    st.info("診断結果に基づき、あなたに適した戦略を抽出しました。")

    recommendations = []

    # 1. 予期が薄すぎる
    if s_exp_int <= 12:
        recommendations.append({
            "title": "Strategy: Future Connection (未来との接続強化)",
            "reason": f"あなたの「予期の濃さ」スコアは {s_exp_int} (基準値12以下) です。これは未来の利益よりも目の前の利益を優先しやすく、結果として「先延ばし」が起きやすい傾向を示しています。未来の自分をリアルに感じるための対策が有効です。",
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
                }
            ]
        })

    # 2. 予期が濃すぎる
    if s_exp_int >= 13:
        recommendations.append({
            "title": "Strategy: Anxiety Management (予期不安の管理)",
            "reason": f"あなたの「予期の濃さ」スコアは {s_exp_int} (基準値13以上) です。これは未来のリスクや責任を強く感じすぎている状態です。真面目さが裏目に出てプレッシャーになり、逆に動けなくなる可能性があるため、意図的な休息が必要です。",
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
                }
            ]
        })

    # 3. 予期が多すぎる
    if s_exp_qty >= 13:
        recommendations.append({
            "title": "Strategy: Bandwidth Optimization (脳内帯域の解放)",
            "reason": f"あなたの「予期の多さ」スコアは {s_exp_qty} (基準値13以上) です。これは常に複数のタスクが頭を占拠しており、脳のメモリ（帯域）が不足している状態です。マルチタスクを防ぎ、タスクを外部化することが重要です。",
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
                }
            ]
        })

    # 4. 想起の誤りが大きい
    if s_rec_acc <= 12:
        recommendations.append({
            "title": "Strategy: Calibration (見積もりの補正)",
            "reason": f"あなたの「想起の正確性」スコアは {s_rec_acc} (基準値12以下) です。これは過去にかかった時間を短く見積もる「計画錯誤」の傾向があります。自分の感覚を疑い、客観的なデータや他者の視点を取り入れる必要があります。",
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
            "reason": f"あなたの「想起の肯定度」は高く({s_rec_pos})、一方で「正確性」が低い({s_rec_acc})状態です。これは「なんとかなる」という楽観バイアスが強く、リスクを見落としがちであることを示唆しています。",
            "methods": [
                {
                    "name": "Temptation Diary (誘惑日記)",
                    "how_to": "計画が崩れた際、その原因となった「誘惑（スマホ、雑談など）」を記録する。",
                    "tips": "自分が何に弱いかを把握し、次回の計画時にその誘惑対策を盛り込む。"
                },
                {
                    "name": "Fudge Ratio (ごまかし率の計算)",
                    "how_to": "過去のタスクで「予定時間」と「実際にかかった時間」を割り算し、自分の「サバ読み係数（例：1.5倍）」を算出する。",
                    "tips": "次の見積もり時は、何も考えずにその係数を掛ける。自分の感覚を信じず、係数を信じる。"
                }
            ]
        })

    # 6. 想起が否定的すぎる
    if s_rec_pos <= 12:
        recommendations.append({
            "title": "Strategy: Self-Efficacy (自己効力感の向上)",
            "reason": f"あなたの「想起の肯定度」スコアは {s_rec_pos} (基準値12以下) です。これは過去の失敗にとらわれ、「自分には無理だ」と挑戦を避けたり、過度に慎重になっている可能性があります。小さな成功体験を認識させることが鍵です。",
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
                    "name": "Reflection (リフレクション)",
                    "how_to": "過去の成功体験を分析し、なぜうまくいったのかその要因を言語化して、次のタスクに活かす。",
                    "tips": "「運が良かった」ではなく「自分の行動の何が良かったか」にフォーカスする。"
                }
            ]
        })

    # 結果表示ループ (折りたたみ・階層化)
    if not recommendations:
        st.success("Balance is optimal. 現在の時間感覚バランスは非常に良好です。今の習慣を継続してください。")
    else:
        for rec in recommendations:
            with st.expander(f"{rec['title']}", expanded=False):
                # Reasonを追加
                st.info(f"💡 **Reason (なぜこの対策か):** \n{rec['reason']}")
                
                for method in rec['methods']:
                    st.markdown("---")
                    st.markdown(f"#### 🛠 {method['name']}")
                    st.markdown(f"**How-To (やり方):**  \n{method['how_to']}")
                    st.markdown(f"**Tips (コツ):** {method['tips']}")

    st.markdown("---")
    st.caption("Reference: 『YOUR TIME ユア・タイム』(鈴木 祐 著)")
