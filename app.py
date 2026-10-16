import json
import os
import random
from datetime import datetime
import matplotlib.pyplot as plt

DATA_FILE = "study_data.json"
IMPORT_FILE = "import_data.txt"

def load_data():
    """学習データを読み込む"""
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_data(data):
    """学習データを保存する"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def step1_batch_import(data):
    """ステップ1：一括インプット機能（テキストファイルから読み込み）"""
    print("\n--- 【ステップ1】 一括学習データインプット ---")
    print(f"📁 作業ディレクトリにある '{IMPORT_FILE}' からデータを一括読み込みします。")
    print("【書き方のルール】")
    print("  1行につき 1問 を記入してください。")
    print("  フォーマット: 問題文 | 解答・解説 | カテゴリ")
    print("  例: IPアドレスとは何か？ | ネットワーク上の機器を識別する住所 | network\n")
    
    if not os.path.exists(IMPORT_FILE):
        # ファイルがない場合は空のひな形を作成する
        with open(IMPORT_FILE, "w", encoding="utf-8") as f:
            f.write("# ここに 問題文 | 解答 | カテゴリ を記述してください\n")
        print(f"⚠️ '{IMPORT_FILE}' が見つからなかったため、新しく作成しました。")
        print(f"このファイルにデータを書き込んでから、再度インプットを実行してください。")
        return data

    # ファイルの読み込み
    added_count = 0
    try:
        with open(IMPORT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            # コメント行や空行はスキップ
            if not line or line.startswith("#"):
                continue
            
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                question, answer, category = parts[0], parts[1], parts[2]
                
                new_item = {
                    "id": len(data) + 1,
                    "question": question,
                    "answer": answer,
                    "category": category,
                    "mastery_score": 0,      # 習熟度（0〜5）
                    "label": "要学習",       # ラベル
                    "last_reviewed": str(datetime.now().date())
                }
                data.append(new_item)
                added_count += 1
                
        save_data(data)
        print(f"✨ 成功！ {added_count} 件の問題を新しくインポートしました！")
        
    except Exception as e:
        print(f"❌ 読み込み中にエラーが発生しました: {e}")
        
    return data

def step2_and_3_test(data):
    """ステップ2＆3：テストの実施と回答分析・ラベルづけ"""
    if not data:
        print("\n⚠️ 登録されている問題がありません。まずはステップ1でデータをインポートしてください。")
        return data

    print("\n--- 【ステップ2】 定着度テスト（新規 ＋ 苦手・復習問題） ---")
    
    target_items = [item for item in data if item["mastery_score"] < 4]
    if not target_items:
        target_items = data 
    
    test_items = random.sample(target_items, min(len(target_items), 5))
    print(f"本日のテスト問題数: {len(test_items)}問\n")
    
    for idx, item in enumerate(test_items, 1):
        print(f"【Q{idx} [{item['category']}] (現在の習熟度: {item['mastery_score']}/5 | ラベル: {item['label']})】")
        print(f"問題: {item['question']}")
        
        input("👉 解答を頭の中で思い浮かべたら [Enter] キーを押してください...")
        print(f"【正解・解説】: {item['answer']}\n")
        
        print("今回の理解度を評価してください（0: 全く分からない、 3: 普通、 5: 完璧に理解）")
        try:
            score_input = int(input("評価 (0〜5): "))
            score_input = max(0, min(5, score_input))
        except ValueError:
            score_input = item["mastery_score"]
            
        item["mastery_score"] = score_input
        item["last_reviewed"] = str(datetime.now().date())
        
        if score_input <= 2:
            item["label"] = "要重点復習"
        elif score_input <= 4:
            item["label"] = "復習中"
        else:
            item["label"] = "マスター"
            
        print(f"  -> 更新完了！ [ラベル: {item['label']} / 習熟度: {item['mastery_score']}/5]\n")
        
    save_data(data)
    print("🎉 本日のテストが終了しました！データが更新されました。")
    return data

def step4_export_reports(data):
    """ステップ4：習熟度の数値化、グラフ化、Notion用ファイル作成"""
    if not data:
        print("\n⚠️ 出力するデータがありません。")
        return

    print("\n--- 【ステップ4】 学習レポート・見える化ファイルの作成 ---")
    
    total_questions = len(data)
    avg_score = sum(item["mastery_score"] for item in data) / total_questions if total_questions > 0 else 0
    
    categories = {}
    for item in data:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item["mastery_score"])
        
    cat_avg = {cat: sum(scores)/len(scores) for cat, scores in categories.items()}

    # 1. グラフの作成と保存
    if cat_avg:
        plt.figure(figsize=(8, 5))
        plt.bar(cat_avg.keys(), cat_avg.values(), color='skyblue')
        plt.ylim(0, 5)
        plt.xlabel('Category')
        plt.ylabel('Average Mastery Score (0-5)')
        plt.title('Learning Mastery by Category')
        plt.tight_layout()
        graph_filename = "mastery_chart.png"
        plt.savefig(graph_filename)
        plt.close()
        print(f"📊 グラフ画像を生成しました: {graph_filename}")

    # 2. Notion保存用Markdownファイルの作成
    md_filename = "notion_learning_report.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write("# 📈 学習進捗・定着度レポート\n\n")
        f.write(f"* **総登録問題数:** {total_questions}問\n")
        f.write(f"* **平均習熟度:** {avg_score:.2f} / 5.0\n")
        f.write(f"* **最終更新日:** {datetime.now().date()}\n\n")
        
        f.write("## 🔍 カテゴリ別平均習熟度\n")
        f.write("| カテゴリ | 平均習熟度 (0-5) |\n")
        f.write("| :--- | :---: |\n")
        for cat, score in cat_avg.items():
            f.write(f"| {cat} | {score:.2f} |\n")
            
        f.write("\n## 📝 問題別ステータス一覧\n")
        f.write("| ID | カテゴリ | 問題 | 習熟度 | ラベル |\n")
        f.write("| :---: | :--- | :--- | :---: | :--- |\n")
        for item in data:
            f.write(f"| {item['id']} | {item['category']} | {item['question']} | {item['mastery_score']} | {item['label']} |\n")

    print(f"📄 Notion保存用Markdownファイルを生成しました: {md_filename}")
    print("✅ ステップ4の出力が完了しました！")

def main():
    data = load_data()
    while True:
        print("\n==============================")
        print("🧠 文系大学生のためのIT学習支援プログラム")
        print("==============================")
        print("1. ステップ1: 一括インプット（import_data.txtから読み込み）")
        print("2. ステップ2＆3: 定着度テスト ＆ 分析・ラベルづけ")
        print("3. ステップ4: レポート・グラフ出力（Notion用）")
        print("4. 終了")
        
        choice = input("\nメニュー番号を選んでください (1〜4): ")
        
        if choice == '1':
            data = step1_batch_import(data)
        elif choice == '2':
            data = step2_and_3_test(data)
        elif choice == '3':
            step4_export_reports(data)
        elif choice == '4':
            print("お疲れ様でした！学習を続けましょう。")
            break
        else:
            print("⚠️ 1〜4の番号を入力してください。")

if __name__ == "__main__":
    main()