import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ページ設定
st.set_page_config(page_title="時間感覚タイプ診断", layout="centered")

# --- タイトルと導入 ---
st.title("⏱️ 時間感覚タイプ診断")
st.markdown("""
この診断は、認知科学に基づきあなたの「時間の捉え方」を分析するツールです。
以下の設問に直感で答えてください。（所要時間：約3分）

※本診断は仮説モデルに基づくプロトタイプであり、医学的な診断ではありません。
""")

# --- 設問データ（改定案） ---
questions = {
    "expected_intensity": [ # 予期：濃い・薄い (Q1-Q5)
        "Q1. 今の行動が、5年後や10年後の未来にどう繋がるかをイメージするのが得意だ。",
        "Q2. 目の前の楽しさよりも、将来起こりうるリスクの方に自然と意識が向く。",
        "Q3. 将来の幸福を達成するためなら、目先の幸福を犠牲にするのにも抵抗がない。",
        "Q4. 「今これをやらなければ、将来必ず後悔する」という観点で物事を見ることが多い。",
        "Q5. 楽しい時間を過ごしている最中でも、つい「次にやるべきこと」や「後の予定」を考えてしまう。"
    ],
    "expected_quantity": [ # 予期：多い・少ない (Q6-Q10)
        "Q6. スケジュール帳に空白があると、そこに何か予定を入れたくなる、あるいは入れてしまう。",
        "Q7. ひとつの作業をしている最中に、他の複数の「やらなければならないこと」が頭に浮かんでくる。",
        "Q8. 全てのタスクが「今すぐやるべき重要事項」に見えてしまい、どれも捨てがたいと感じる。",
        "Q9. 常に「時間が足りない」「何かに追われている」という感覚がある。",
        "Q10. 長期の目標よりも、数時間〜数日以内の「こなすべき用事」で頭がいっぱいだ。"
    ],
    "recalled_accuracy": [ # 想起：正しい・誤り (Q11-Q15)
        "Q11. 過去の経験に基づき、「意外と時間がかかるかもしれない」とバッファ（余裕）を持たせる癖がある。",
        "Q12. 「自分ならもっと早くできるはずだ」という期待よりも、過去の実績タイムを信頼する。",
        "Q13. 計画を立てる際に、障害や不測の事態を必ず考える。",
        "Q14. 過去に自分がどれくらいのスピードで作業できたか、具体的に思い出すことができる。",
        "Q15. 作業を始める前に、過去の類似タスクにおける失敗パターンをシミュレーションする。"
    ],
    "recalled_positivity": [ # 想起：肯定的・否定的 (Q16-Q20)
        "Q16. 過去の自分の判断や行動は、今の自分にとってプラスになっていると思う。",
        "Q17. 「自分は時間を有効に使ってきた人間だ」という自信がある。",
        "Q18. 過去の失敗を思い出しても、「あれはあれで良い経験だった」と意味づけできる。",
        "Q19. 未知の課題に直面しても、「過去になんとかなったから今回も大丈夫だろう」と思える。",
        "Q20. 作業前に「これは自分には無理だろう」と思うことはない。"
    ]
}

# --- フォーム作成 ---
scores = {}
options = ["全く当てはまらない (1)", "あまり当てはまらない (2)", "どちらともいえない (3)", "やや当てはまる (4)", "完全に当てはまる (5)"]
option_values = {options[0]: 1, options[1]: 2, options[2]: 3, options[3]: 4, options[4]: 5}

with st.form("diagnosis_form"):
    st.subheader("Section 1: 未来に対する感覚（予期）")
    
    st.markdown("**Part A**")
    q1_score = st.radio(questions["expected_intensity"][0], options, horizontal=True)
    q2_score = st.radio(questions["expected_intensity"][1], options, horizontal=True)
    q3_score = st.radio(questions["expected_intensity"][2], options, horizontal=True)
    q4_score = st.radio(questions["expected_intensity"][3], options, horizontal=True)
    q5_score = st.radio(questions["expected_intensity"][4], options, horizontal=True)
    
    st.markdown("---")
    st.markdown("**Part B**")
    q6_score = st.radio(questions["expected_quantity"][0], options, horizontal=True)
    q7_score = st.radio(questions["expected_quantity"][1], options, horizontal=True)
    q8_score = st.radio(questions["expected_quantity"][2], options, horizontal=True)
    q9_score = st.radio(questions["expected_quantity"][3], options, horizontal=True)
    q10_score = st.radio(questions["expected_quantity"][4], options, horizontal=True)

    st.subheader("Section 2: 過去に対する感覚（想起）")
    
    st.markdown("**Part C**")
    q11_score = st.radio(questions["recalled_accuracy"][0], options, horizontal=True)
    q12_score = st.radio(questions["recalled_accuracy"][1], options, horizontal=True)
    q13_score = st.radio(questions["recalled_accuracy"][2], options, horizontal=True)
    q14_score = st.radio(questions["recalled_accuracy"][3], options, horizontal=True)
    q15_score = st.radio(questions["recalled_accuracy"][4], options, horizontal=True)

    st.markdown("---")
    st.markdown("**Part D**")
    q16_score = st.radio(questions["recalled_positivity"][0], options, horizontal=True)
    q17_score = st.radio(questions["recalled_positivity"][1], options, horizontal=True)
    q18_score = st.radio(questions["recalled_positivity"][2], options, horizontal=True)
    q19_score = st.radio(questions["recalled_positivity"][3], options, horizontal=True)
    q20_score = st.radio(questions["recalled_positivity"][4], options, horizontal=True)

    submitted = st.form_submit_button("診断する")

# --- 集計と結果表示ロジック ---
if submitted:
    # スコア計算
    s_exp_int = sum([option_values[x] for x in [q1_score, q2_score, q3_score, q4_score, q5_score]])
    s_exp_qty = sum([option_values[x] for x in [q6_score, q7_score, q8_score, q9_score, q10_score]])
    s_rec_acc = sum([option_values[x] for x in [q11_score, q12_score, q13_score, q14_score, q15_score]])
    s_rec_pos = sum([option_values[x] for x in [q16_score, q17_score, q18_score, q19_score, q20_score]])

    st.markdown("---")
    st.header("📊 診断結果")

    # --- プロット関数 ---
    def plot_matrix(x_score, y_score, x_label, y_label, title, x_min_text, x_max_text, y_min_text, y_max_text):
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # 軸の設定 (0-25)
        ax.set_xlim(0, 25)
        ax.set_ylim(0, 25)
        
        # 中心線 (12.5)
        ax.axvline(x=12.5, color='gray', linestyle='--', alpha=0.5)
        ax.axhline(y=12.5, color='gray', linestyle='--', alpha=0.5)
        
        # プロット
        ax.scatter(x_score, y_score, color='#FF4B4B', s=200, zorder=5)
        
        # ラベル
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        
        # 象限のテキスト
        plt.text(1, 12.5, y_min_text, ha='left', va='center', rotation=90, color='gray') # Y軸下
        plt.text(1, 13, y_max_text, ha='left', va='center', rotation=90, color='gray') # Y軸上
        plt.text(12.5, 1, x_min_text, ha='center', va='bottom', color='gray') # X軸左
        plt.text(13, 1, x_max_text, ha='center', va='bottom', color='gray') # X軸右

        # 背景色分け（オプション）
        rect_high_high = patches.Rectangle((12.5, 12.5), 12.5, 12.5, linewidth=0, edgecolor='none', facecolor='#f0f2f6', alpha=0.5)
        ax.add_patch(rect_high_high)
        
        st.pyplot(fig)

    # --- カラム分けしてグラフ表示 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("＜予期＞の傾向")
        st.metric("予期の濃さ (Y)", f"{s_exp_int} / 25")
        st.metric("予期の多さ (X)", f"{s_exp_qty} / 25")
        plot_matrix(
            s_exp_qty, s_exp_int, 
            "予期の多さ", "予期の濃さ", 
            "予期マトリクス", 
            "少ない", "多い", "薄い", "濃い"
        )

    with col2:
        st.subheader("＜想起＞の傾向")
        st.metric("想起の正確性 (Y)", f"{s_rec_acc} / 25")
        st.metric("想起の肯定度 (X)", f"{s_rec_pos} / 25")
        plot_matrix(
            s_rec_pos, s_rec_acc, 
            "肯定的", "正確性", 
            "想起マトリクス", 
            "否定的", "肯定的", "誤り", "正しい"
        )

    # --- 対策ロジック ---
    st.markdown("---")
    st.header("💡 あなたへの処方箋（推奨される時間術）")
    st.info("スコアに基づいて、優先的に取り組むべきアプローチを提案します。")

    recommendations = []

    # 1. 予期が薄すぎる場合 (Y <= 12)
    if s_exp_int <= 12:
        recommendations.append({
            "type": "⚠️ 予期が薄すぎる（未来への接続が弱い）",
            "desc": "未来の重要性が現在よりも低く見積もられ、先延ばしが発生しやすい状態です。",
            "techniques": [
                "**タイムボクシング**: 作業時間をあらかじめ箱（ボックス）のように区切り、その中で強制的に終わらせる。",
                "**アンパッキング**: 巨大に見えるタスクを細かく分解し、着手へのハードルを下げる。",
                "**ビジョン・エクササイズ**: 締切直前の自分や、3年後の自分を鮮明に想像してから作業に入る。"
            ]
        })

    # 2. 予期が濃すぎる場合 (Y >= 13)
    if s_exp_int >= 13:
        recommendations.append({
            "type": "🛑 予期が濃すぎる（未来への不安が強い）",
            "desc": "将来のリスクや義務感を過剰に感じ、プレッシャーで動けなくなったり、休息が取れない状態です。",
            "techniques": [
                "**プレコミットメント**: 「キャンセルできない休暇」や「予定」を先に入れてしまい、休むことを強制する。",
                "**リマインディング**: 不安になったら「10年後にこの件で後悔しているか？」と問いかける。",
                "**機能的アリバイ**: 「仕事のために必要だから休むのだ」と、休息に正当な理由付けを行う。"
            ]
        })

    # 3. 予期が多すぎる場合 (X >= 13)
    if s_exp_qty >= 13:
        recommendations.append({
            "type": "🤯 予期が多すぎる（マルチタスク・容量超過）",
            "desc": "やるべきことが多すぎて脳の帯域が埋まり、常に何かに追われている感覚がある状態です。",
            "techniques": [
                "**SSCエクササイズ**: 価値の低い仕事を特定し、意図的に「捨てる」か「放置」する練習をする。",
                "**熟慮プランニング**: 「もし障害が起きたら、その時じっくり考えよう」と事前に決め、今の不安を遮断する。",
                "**障害プランニング (If-Then)**: 想定されるトラブルと、その時の対処法をリスト化し、脳のメモリを解放する。"
            ]
        })
    
    # 予期が少なすぎる場合のメッセージ（特になし、または良好）
    if s_exp_qty <= 12 and s_exp_int >= 13:
         recommendations.append({
            "type": "✅ 予期のリソース管理は良好",
            "desc": "適度な集中状態を保てています。ただし、タスク漏れがないか定期的な見直しは行いましょう。",
            "techniques": []
        })


    # 4. 想起の誤りが大きい場合 (Y <= 12)
    if s_rec_acc <= 12:
        recommendations.append({
            "type": "📉 想起の誤りが大きい（見積もりの甘さ）",
            "desc": "過去の所要時間を短く見積もる傾向があり、計画倒れになりやすい状態です。",
            "techniques": [
                "**タイムログ**: 1日の行動と時間を記録し、自分の「体感時間」と「実時間」のズレを自覚する。",
                "**他人に見積もってもらう**: 自分の作業時間を他人に予測してもらい、客観的な数値を取り入れる。",
                "**コピー・プロンプト**: 自分と同じタスクをうまくこなしている人の手順や時間をそのまま真似る。"
            ]
        })

    # 5. 想起が肯定的すぎる場合 (X >= 13) 
    # ※本によっては「楽観的すぎる」ことが計画錯誤に繋がる文脈もあるが、表ベースで対策を提示
    if s_rec_pos >= 13 and s_rec_acc <= 12: # 肯定的かつ誤りがある場合（楽観バイアス）
         recommendations.append({
            "type": "🌞 想起が肯定的すぎる（楽観バイアス）",
            "desc": "「なんとかなる」と考えがちで、リスクを見落とす可能性があります。",
            "techniques": [
                "**誘惑日記**: 計画が崩れた原因（誘惑）を記録し、自分が何に弱いかを把握する。",
                "**ごまかし率の計算**: （実際にかかった時間 ÷ 見積もり時間）を計算し、次回の見積もりに掛け算する係数を作る。"
            ]
        })

    # 6. 想起が否定的すぎる場合 (X <= 12)
    if s_rec_pos <= 12:
        recommendations.append({
            "type": "🌧️ 想起が否定的すぎる（自己効力感の低下）",
            "desc": "過去の失敗にとらわれ、「自分には無理だ」と挑戦を避けてしまう状態です。",
            "techniques": [
                "**ネガティブ想起改善シート**: 予想した「困難度」と実際の「困難度」を比較し、「案外なんとかなった」事実を確認する。",
                "**マイクロ・サクセス**: 1日の終わりに、どんなに小さなことでも良いので「できたこと」を書き残す。",
                "**リフレクション**: 過去の成功体験を分析し、なぜうまくいったのか（運ではなく実力）を言語化する。"
            ]
        })

    # --- 対策の表示 ---
    if not recommendations:
        st.success("🎉 バランスの取れた素晴らしい時間感覚をお持ちのようです！今の習慣を継続してください。")
    else:
        for rec in recommendations:
            if rec["techniques"]: # 対策がある場合のみ表示
                with st.expander(rec["type"], expanded=True):
                    st.write(rec["desc"])
                    st.markdown("##### 🔧 おすすめの技法")
                    for tech in rec["techniques"]:
                        st.markdown(f"- {tech}")

    st.markdown("---")
    st.caption("出典・参考文献: 『YOUR TIME ユア・タイム』(鈴木 祐 著)")
