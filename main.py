#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# 2026/04/09
# タイトル：CrewAIを用いた開発チームエージェント
# 概要：
# ソフトウェア開発プロセスにおける担当登場人物をＡＩエージェントにして、
# それぞれの担当の役割を実施して成果物を作る仕組みを実験したかったので
# 作成しました。
#
# ・マネージャ、設計者、プログラマ、テスターを担当するエージェントが存在。
# ・各エージェントは、依頼者からの要望を基に各ドキュメントを作成。
# ・ドキュメントには、要件書、仕様書、設計書、試験仕様書、試験報告書を出力。
# ・各エージェントはこれらのドキュメントを基にプログラムを製造する。
# ・テスターは製造されたプログラムを仕様に基づいてテストしてフィードバック。
# ・バグ・不具合などの問題があれば自動で改善ループを行う。
# ・一通り完成した後は、人による確認やさらなる要望を出すことができる。
# ----------------------------------------------------------------------

import os
import re
from crewai import Agent, Crew, Process, Task, LLM

# --- テレメトリ表示を消す設定 ---
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# --- 設定エリア ---
MODEL = "ollama/gemma4:26b"
OLLAMA_URL = "http://192.168.1.64:11434"
ollama_llm = LLM(model=MODEL, base_url=OLLAMA_URL)
WORK_DIR = "works"

# --- 保存用関数の定義 ---

def save_01(output):
    save_to_file(output.raw, "01_requirements.md")

def save_02(output):
    save_to_file(output.raw, "02_spec_design.md")

def save_03(output):
    content = output.raw
    with open(f"{WORK_DIR}/03_program.md", "w", encoding="utf-8") as f:
        f.write(content)
    code_match = re.search(r"```python\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
    if code_match:
        pure_code = code_match.group(1).strip()
        with open(f"{WORK_DIR}/program.py", "w", encoding="utf-8") as f:
            f.write(pure_code)
        print(f"  [成果物保存] program.py")

def save_04(output):
    save_to_file(output.raw, "04_test_report.md")

def save_to_file(content, filename):
    os.makedirs(WORK_DIR, exist_ok=True)
    path = os.path.join(WORK_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [成果物保存] {path}")


# --- 開発ループの設定 ---
# 初期の要望
current_request = "ブロック崩しゲーム。Rキーで再開可能。100点ごとにボール加速。"

while True:
    print("\n" + "="*50)
    print(f"### 現在の要望: {current_request}")
    print("### マルチエージェント開発クルー始動...")
    print("="*50 + "\n")

    # エージェント定義（ループごとに最新の要望を反映）
    manager = Agent(
        role='プロジェクトマネージャー',
        goal=f'要望「{current_request}」に基づき、完璧な要件定義書を作成する',
        backstory='あなたは顧客の意図を汲み取り、技術者が実装可能な形に落とし込むプロです。',
        llm=ollama_llm, verbose=True
    )
    designer = Agent(role='システム設計者', goal='要件に基づき仕様書と設計書を作成', backstory='精密な設計を行います', llm=ollama_llm)
    programmer = Agent(role='シニア・プログラマー', goal='バグのない実装を行う', backstory='正確なコードを書きます', llm=ollama_llm)
    tester = Agent(role='QAエンジニア', goal='品質保証', backstory='厳格にテストします', llm=ollama_llm)

    # タスク定義
    task_req = Task(
        description=f'以下の要望を詳細な要件定義書にしてください：{current_request}',
        expected_output='要件定義書（Markdown）',
        agent=manager,
        callback=save_01
    )
    task_design = Task(
        description='要件定義書を元に詳細な仕様書と設計書を作成してください。',
        expected_output='仕様書・設計書（Markdown）',
        agent=designer,
        context=[task_req],
        callback=save_02
    )
    task_code = Task(
        description='設計に基づきtkinterで実装してください。:= は禁止、= のみ使用。',
        expected_output='```python で囲まれたソースコード。',
        agent=programmer,
        context=[task_design]
    )
    task_review_fix = Task(
        description='構文エラーがないか徹底チェックし、完成版コードを出力してください。',
        expected_output='修正済みの完全なPythonソースコード',
        agent=programmer,
        context=[task_code],
        callback=save_03
    )
    task_test = Task(
        description='コードと設計を比較しテスト報告書を作成してください。',
        expected_output='報告書（Markdown）',
        agent=tester,
        context=[task_review_fix, task_design],
        callback=save_04
    )

    # 実行
    dev_crew = Crew(
        agents=[manager, designer, programmer, tester],
        tasks=[task_req, task_design, task_code, task_review_fix, task_test],
        process=Process.sequential
    )

    try:
        dev_crew.kickoff()
        print("\n✅ 開発工程が一旦完了しました。")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        break

    # --- 人間による確認フェーズ ---
    print("\n" + "!"*50)
    print("works/program.py を実行して結果を確認してください。")
    print("! OKなら 'ok' と入力して終了してください。")
    print("! 修正が必要なら、具体的な指示を入力してください。")
    print("!"*50)

    feedback = input("フィードバックをどうぞ >> ")

    if feedback.lower() == 'ok':
        print("\n🎉 プロジェクトが承認されました！完了です。")
        break
    else:
        # フィードバックを次回の要望として更新
        print(f"\n🔄 修正依頼を受け付けました。次回の開発に反映します...")
        current_request = f"【前回の成果物への修正指示】{feedback}\n【元の基本要望】{current_request}"

