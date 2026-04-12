システム設計者として、ご提示いただいた要件定義書に基づき、実装者が迷いなく、かつ「構文エラーの排除」と「機能の完全充足」を実現するための**「詳細仕様書」**および**「詳細設計書」**を作成いたしました。

このドキュメントは、実装時の単一の真実のソース（Single Source of Truth）として機能するように設計されています。

---

# 1. 詳細仕様書 (Software Specification)

## 1.1 プログラム概要
本プログラムは、PythonおよびPygameライブラリを用いた、高い応答性と視覚的一貫性を備えたブロック崩しゲームである。

## 1.2 機能要件
### 1.2.1 ゲームオブジェクト仕様
| オブジェクト | 形状/色 | 属性・挙動 |
| :--- | :--- | :--- |
| **ボール** | 白色の円 ($\circ$) | 物理移動（等速直線運動）。スコア100点ごとに速度ベクトルが増幅される。 |
| **バー (Paddle)** | 矩形 | 画面下部。左右矢印キーによる操作。画面外へ出ない制約。 |
| **ブロック** | 矩形 (5層) | 5つの異なる色。各層（レイヤー）が完全に消滅するとレベルアップ。 |

### 1.2.2 ゲームロジック仕様
* **レベルアップ・メカニズム:**
    * ブロックの全消去判定：全ブロックの「生存フラグ」が `False` になった際、`Level` を $+1$ し、新しいブロック配置を生成する。
* **難易度上昇（加速）メカニズム:**
    * 加速閾値：`Score % 100 == 0` かつ `Score > 0` のタイミング、またはスコアが100点増加した瞬間に、ボールの移動速度（$\Delta x, \Delta y$）を一定割合（例: $1.1$ 倍）増加させる。
* **ゲームオーバー・メカニズム:**
    * 判定条件：ボールの $y$ 座標 $\ge$ 画面下端（バーの範囲外）。
    * 状態遷移：`GameState` を `GAME_OVER` に遷移。
    * 継続表示：`GAME_OVER` 状態においても、描画ループは停止せず、既存のブロック、バー、スコア、レベルをすべて描画し続ける。
* **リトライ・メカニズム:**
    * `R` キー押下をトリガーとし、すべての変数（Score, Level, Ball pos, Block list）を初期状態にリセットする。

### 1.2.3 UI/UX 仕様
* **リアルタイム表示:**
    * `Score`: 画面左上に配置。
    * `Level`: 画面右端（`SCREEN_WIDTH` の末尾付近）に配置。
* **情報更新:** レベルアップ時およびスコア加算時に、即時、かつ視覚的に更新されること。

## 1.3 非機能要件（品質・エラー防止）
* **完全な構文的整合性:** PythonのSyntax標準に準拠。全角文字の混入、不適切な代入演算子の使用（Walrus operatorのクラス属性への適用など）を厳禁とする。
* **操作の低遅延:** ユーザー入力（`KEYDOWN`, `KEYUP`）をイベントキューから直接処理し、フレーム間の入力遅延を最小化する。

---

# 2. 詳細設計書 (Detailed Design Document)

## 2.1 クラス構成図 (Class Diagram)

### 2.1.1 `GameConstants` (定数管理クラス)
* **役割:** ゲーム全体で使用する不変の値（色、サイズ、速度、キー設定）を定義。
* **主な属性:**
    * `SCREEN_WIDTH`, `SCREEN_HEIGHT`
    * `PADDLE_SPEED`, `BALL_START_SPEED`
    * `COLOR_PALETTE` (5層分の色リスト)
    * `COLORS` (背景、ボール、文字の色)

### 2.1.2 `GameObject` (基底抽象クラス)
* **役割:** すべての動的オブジェクトの共通プロパティ（位置、描画メソッド）を定義。
* **メソッド:** `draw(surface)`

### 2.1.3 `Ball` (ボールクラス)
* **継承:** `GameObject`
* **属性:**
    * `pos`: `pygame.Vector2` (位置)
    * `vel`: `pygame.Vector2` (速度ベクトル)
    * `radius`: `float`
* **メソッド:**
    * `move()`: 速度に基づいた位置更新。
    * `check_wall_collision()`: 壁（左右・上）との衝突判定。
    * `increase_speed(factor)`: 速度の増幅。

### 2.1.4 `Paddle` (バークラス)
* **継承:** `GameObject`
* **属性:**
    * `rect`: `pygame.Rect` (位置とサイズ)
    * `speed`: `float`
* **メソッド:**
    * `update(keys)`: 左右矢印キーに基づいた移動処理。境界チェックを含む。

### 2.1.5 `Block` (ブロッククラス)
* **継承:** `GameObject`
* **属性:**
    * `rect`: `pygame.Rect`
    * `color`: `Color`
    * `is_alive`: `bool`
* **メソッド:**
    * `draw(surface)`: 生存している場合のみ描画。

### 2.1.6 `GameManager` (ゲーム制御メインクラス)
* **役割:** ゲームループ、状態管理、衝突判定、ルール実行の集約。
* **属性:**
    * `state`: `Enum` (PLAYING, GAME_OVER)
    * `score`: `int`
    * `level`: `int`
    * `entities`: `List[GameObject]` (Ball, Paddle, Blocksのリスト)
* **メソッド:**
    * `handle_events()`: キー入力、リトライ処理。
    * `update()`: 衝突判定、レベルアップ判定、加速判定。
    * `collision_logic()`: ボールとブロック、ボールとバーの衝突判定（数学的に正確な境界判定）。
    * `render()`: 全オブジェクトの描画、UI（Score/Level）の描画。
    * `reset()`: 全状態の初期化。

## 2.2 アルゴリズム・ロジック詳細

### 2.2.1 衝突判定アルゴリズム (Collision Logic)
ボールの `pos` (中心点) と `radius` を用いた `pygame.Rect.collidepoint` または `colliderect` を使用。
* **Ball vs Block:**
    1. `ball.rect.colliderect(block.rect)` が `True` かつ `block.is_hit == False` を確認。
    2. `block.is_alive = False` に設定。
    3. `ball.vel.y *= -1` (垂直方向の反転)。
    4. `score += 10`。
    5. 加速判定：`if score % 100 == 0: ball.increase_speed(1.1)`。
* **Ball vs Paddle:**
    1. `ball.rect.colliderect(paddle.rect)` が `True` かつ `ball.vel.y > 0`（下降中）を確認。
    2. `ball.vel.y *= -1`。

### 2.2.2 描画レイヤー設計 (Rendering Layer)
描画の順序（Z-order）を以下のように固定し、ゲームオーバー時でも要素が消えないように制御する。
1. **Background Layer:** 画面の塗りつぶし。
2. **Block Layer:** 生存している全ブロックの描画。
3. **Paddle Layer:** パドルの描画。
4. **Ball Layer:** ボールの描画。
5. **UI Layer:**
    * `Score` (左上)
    * `Level` (右上)
    * `GameOver Message` (中央：`state == GAME_OVER` の場合のみ)

## 2.3 実装時エラー防止チェックリスト (Developer Check-list)

* [ ] **Syntax Check:** `if` 文の末尾に `:` があるか？ 括弧 `()` は閉じられているか？
* [ ] **Zero-Width/Full-width Check:** コード内に全角スペースや全角記号（`．`, `，`）が混入していないか？
* [ ] **Variable Naming:** 変数名が数字から始まっていないか？ タイポ（`ball_pos` vs `bal_pos`）はないか？
* [ ] **Assignment Logic:** クラスの `__init__` 外で、`self.attr := value` のような代入式を不適切に使用していないか？（通常の `self.attr = value` を使用すること）
* [ ] **Boundary Logic:** パドルが画面の左端（$x < 0$）および右端（$x + width > SCREEN\_WIDTH$）を超えないよう、`clamp` 処理が行われているか？
* [ ] **Persistence Logic:** `GAME_OVER` 状態のとき、`update()` メソッド内での「ボールの移動」や「ブロックの消失」ロジックがスキップされる設計になっているか？（要素の描画は継続すること）

---
**設計完了**