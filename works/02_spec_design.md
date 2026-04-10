システム設計者として、提示された要件定義書に基づき、エンジニアが即座に実装・テストに移行できるレベルまで詳細化した**「機能仕様書」**および**「詳細設計書」**を作成しました。

---

# 1. 機能仕様書 (Software Specification)

## 1.1 プログラム概要
本プログラムは、PythonおよびPygameを用いたブロック崩しゲームである。既存の実行時エラーを解消し、ゲームプレイの継続性を高めるための「リスタート機能」および、ゲームの難易度を動的に調整する「スコア連動型加速システム」を実装する。

## 1.2 機能詳細

### 1.2.1 実行時エラーの修正 (Delta Time 制御)
*   **機能内容**: フレームレート（FPS）の変動に依存せず、物理演算（移動速度）を一定に保つための時間差分（$\Delta t$）計算の修正。
*   **計算方式**: 
    *   前フレームのタイムスタンプと現フレームのタイムスタンプの差分を `dt` として算出。
    *   各オブジェクトの移動距離は `velocity * dt` と定義する。

### 1.2.2 スコア連動型加速システム
*   **機能内容**: スコアが一定の閾値に達した際、ボールの移動速度を増幅させる。
*   **発動条件**: スコアが $100, 200, 300, \dots$ の倍数に到達した瞬間。
*   **増幅ロジック**: 
    *   現在の移動ベクトル $\vec{V}_{new} = \vec{V}_{old} \times \text{ACCELERATION\_FACTOR}$
    *   増幅係数は定数として定義（初期値: 1.1）。
*   **制約事項**: 同一スコア内で毎フレーム加速が発生しないよう、スコアの更新検知ロジックを実装すること。

### 1.2.3 リスタート・レジューム機能
*   **機能内容**: `R` キー押下により、ゲームの状態を初期化して再開する。
*   **リセット対象**:
    *   スコア、現在の生存ブロック数。
    *   ボールの座標、移動ベクトル。
    *   パドルの座標。
    *   ブロックの配置（全復元）。
*   **トリガー**: `pygame.KEYDOWN` イベントにおける `K_r` の検知。

## 1.3 非機能要件
*   **保守性**: 全てのパラメータ（加速率、閾値、初期速度等）は `GameConfig` クラスまたは定数セクションに集約すること。
*   **安定性**: `dt` の計算において、万が一 `dt` が極端に大きな値（ウィンドウ移動等による一時停止後）になった場合でも、オブジェクトが画面外に飛散しないよう、`dt` の上限値（Cap）を設けること。

---

# 2. 詳細設計書 (Detailed Design)

## 2.1 クラス設計 (Class Design)

### 2.1.1 `GameConstants` (定数管理)
マジックナンバーを排除するための静的クラス。

| 定数名 | 型 | 値 (例) | 説明 |
| :--- | :--- | :--- | :--- |
| `ACCEL_FACTOR` | float | `1.1` | スコア更新時の速度倍率 |
| `SCORE_THRESHOLD` | int | `100` | 加速が発生するスコアの間隔 |
| `MAX_DT` | float | `0.1` | `dt` の最大許容値（スプタリング対策） |
| `PADDLE_SPEED` | float | `400` | パドルの移動速度 (px/s) |
| `BALL_START_SPEED`| float | `200` | 初期のボール速度 (px/s) |

### 2.1.2 `GameEngine` (メイン制御クラス)
ゲームのメインループ、状態管理、物理演算を担当。

*   **主要属性 (Attributes)**:
    *   `self.state`: `GameState` (Enum: `RUNNING`, `GAME_OVER`, `PAUSED`)
    *   `selfﻘ_score`: `int` (現在のスコア)
    *   `self.prev_score`: `int` (前フレームのスコア：加速判定用)
    *   `self.last_time`: `float` (前フレームの時刻)
*   **主要メソッド (Methods)**:
    *   `update(dt)`: 全オブジェクトの更新。`dt` を用いた移動計算。
    *   `handle_events()`: キー入力（`R`キー、移動キー）の処理。
    *   `check_score_logic()`: `score % 100 == 0` かつ `score != prev_score` の判定。
    *   `reset_game()`: 全オブジェクトの初期化。

## 2.2 アルゴリズム設計 (Algorithm)

### 2.2.1 デルタタイム計算と移動ロジック
```python
# 擬似コード
current_time = time.time()
dt = current_time - self.last_time
self.last_time = current_time

# 異常値対策 (dt Cap)
if dt > GameConstants.MAX_DT:
    dt = GameConstants.MAX_DT

# オブジェクトの移動 (フレームレートに依存しない)
position += velocity * dt
```

### 2.2.2 スコア連動型加速アルゴリズム
```python
# 擬似コード
def check_score_logic(self):
    # スコアが閾値の倍数に達し、かつ前フレームとは異なるスコアであることを確認
    if self.score > 0 and self.score % GameConstants.SCORE_THRESHOLD == 0:
        if self.score != self.prev_score:
            self.accelerate_ball()
    
    self.prev_score = self.score

def accelerate_ball(self):
    # ベクトルのスカラー倍
    self.ball.velocity *= GameConstants.ACCEL_FACTOR
```

### 2.2.3 リスタート処理シーケンス
`R` キー押下時の状態遷移図。

1.  `Input Event (K_R)` を検知。
2.  `GameEngine.reset_game()` を呼び出し。
3.  `score = 0`, `prev_score = 0` に初期化。
4.  `Ball.position` を初期座標へ。
5.  `Paddle.position` を初期座標へ。
6.  `BlockContainer.rebuild()` を実行（全ブロックを再生成）。
7.  `state = GameState.RUNNING` に変更。

## 2.3 データ構造 (Data Structure)

### 2.3.1 ゲーム状態管理 (Enum)
```python
class GameState(Enum):
    RUNNING = 1
    PAUSED = 2
    GAME_OVER = 3
```

## 2.4 画面インターフェース設計 (UI/UX)
*   **HUD (Heads-up Display)**:
    *   画面上部に `Score: {score}` を表示。
    *   （オプション）現在の倍率やレベルを表示。
*   **Game Over Screen**:
    *   「GAME OVER」のテキスト表示。
    *   「Press 'R' to Restart」のガイド表示。

---
**設計者注記:**
実装に際しては、`dt` の計算において `time.time()` を使用する場合、システムのクロック精度に注意してください。また、加速ロジックにおいて `self.score != self.prev_score` の比較を忘れると、`dt` が非常に小さいフレームで指数関数的な加速が発生するため、必ずスコアの「変化の瞬間」を捕捉する設計を遵守してください。