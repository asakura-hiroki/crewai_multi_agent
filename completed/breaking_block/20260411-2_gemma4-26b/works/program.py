import tkinter as tk

class GameConstants:
    """ゲーム全体で使用する不変の値を定義する定数管理クラス"""
    SCREEN_WIDTH = 600
    SCREEN_HEIGHT = 400
    PADDLE_WIDTH = 100
    PADDLE_HEIGHT = 15
    PADDLE_SPEED = 20
    BALL_RADIUS = 8
    BALL_START_SPEED_X = 3
    BALL_START_SPEED_Y = -3
    BLOCK_COLS = 10
    BLOCK_ROWS = 5
    BLOCK_PADDING = 5
    BLOCK_WIDTH = 50
    BLOCK_HEIGHT = 20
    COLOR_PALETTE = ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF"]
    COLOR_BG = "#222222"
    COLOR_PADDLE = "#FFFFFF"
    COLOR_BALL = "#FFFFFF"
    COLOR_TEXT = "#FFFFFF"
    COLOR_GAME_OVER = "#FF0000"

class GameObject:
    """すべての動的オブジェクトの基底クラス"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, canvas):
        pass

class Ball(GameObject):
    """ボールの挙動を制御するクラス"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = GameConstants.BALL_RADIUS
        self.dx = GameConstants.BALL_START_SPEED_X
        self.dy = GameConstants.BALL_START_SPEED_Y

    def move(self):
        self.x = self.x + self.dx
        self.y = self.y + self.dy

    def check_wall_collision(self):
        # 左右の壁
        if self.x - self.radius <= 0 or self.x + self.radius >= GameConstants.SCREEN_WIDTH:
            self.dx = self.dx * -1
        # 上の壁
        if self.y - self.radius <= 0:
            self.dy = self.dy * -1

    def increase_speed(self, factor):
        self.dx = self.dx * factor
        self.dy = self.dy * factor

    def draw(self, canvas):
        canvas.create_oval(
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius,
            fill=GameConstants.COLOR_BALL, outline=""
        )

class Paddle(GameObject):
    """パドルの挙動を制御するクラス"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.width = GameConstants.PADDLE_WIDTH
        self.height = GameConstants.PADDLE_HEIGHT
        self.move_dir = 0  # -1: Left, 0: None, 1: Right

    def update(self):
        if self.move_dir == -1:
            self.x = self.x - GameConstants.PADDLE_SPEED
        elif self.move_dir == 1:
            self.x = self.x + GameConstants.PADDLE_SPEED
            
        # 画面外へ出ない制約 (Clamp)
        if self.x < 0:
            self.x = 0
        if self.x + self.width > GameConstants.SCREEN_WIDTH:
            self.x = GameConstants.SCREEN_WIDTH - self.width

    def draw(self, canvas):
        canvas.create_rectangle(
            self.x, self.y,
            self.x + self.width, self.y + self.height,
            fill=GameConstants.COLOR_PADDLE, outline=""
        )

class Block(GameObject):
    """ブロックの属性を管理するクラス"""
    def __init__(self, x, y, color):
        super().__init__(x, y)
        self.width = GameConstants.BLOCK_WIDTH
        self.height = GameConstants.BLOCK_HEIGHT
        self.color = color
        self.is_alive = True

    def draw(self, canvas):
        if self.is_alive:
            canvas.create_rectangle(
                self.x, self.y,
                self.x + self.width, self.y + self.height,
                fill=self.color, outline="#333330"
            )

class GameManager:
    """ゲームのメインロジックを制御するクラス"""
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(
            root, 
            width=GameConstants.SCREEN_WIDTH, 
            height=GameConstants.SCREEN_HEIGHT, 
            bg=GameConstants.COLOR_BG, 
            highlightthickness=0
        )
        self.canvas.pack()
        
        self.state = "PLAYING"
        self.score = 0
        self.level = 1
        
        self.blocks = []
        self.paddle = None
        selfasonic_ball = None # 用語整理: self.ball
        self.ball = None

        self.reset()
        
        # イベントバインド
        self.root.bind("<KeyPress>", self.handle_keypress)
        self.root.bind("<KeyRelease>", self.handle_keyrelease)
        self.root.bind("<r>", self.handle_reset_key)
        self.root.bind("<R>", self.handle_reset_key)

        self.game_loop()

    def reset(self):
        """全状態の初期化"""
        self.state = "PLAYING"
        self.score = 0
        self.level = 1
        
        self.paddle = Paddle(
            (GameConstants.SCREEN_WIDTH / 2) - (GameConstants.PADDLE_WIDTH / 2),
            GameConstants.SCREEN_HEIGHT - 30
        )
        self.ball = Ball(
            GameConstants.SCREEN_WIDTH / 2,
            GameConstants.SCREEN_HEIGHT - 50
        )
        self.generate_blocks()

    def generate_blocks(self):
        """レベルに応じたブロックの生成"""
        self.blocks = []
        total_padding = GameConstants.BLOCK_PADDING * (GameConstants.BLOCK_COLS - 1)
        # 中央寄せの計算
        total_content_width = (GameConstants.BLOCK_COLS * GameConstants.BLOCK_WIDTH) + total_padding
        start_x = (GameConstants.SCREEN_WIDTH - total_content_width) / 2
        
        for row in range(GameConstants.BLOCK_ROWS):
            color = GameConstants.COLOR_PALETTE[row % len(GameConstants.COLOR_PALETTE)]
            for col in range(GameConstants.BLOCK_COLS):
                bx = start_x + col * (GameConstants.BLOCK_WIDTH + GameConstants.BLOCK_PADDING)
                by = 50 + row * (GameConstants.BLOCK_HEIGHT + GameConstants.BLOCK_PADDING)
                self.blocks.append(Block(bx, by, color))

    def handle_keypress(self, event):
        if event.keysym == "Left":
            self.paddle.move_dir = -1
        elif event.keysym == "Right":
            self.paddle.move_dir = 1

    def handle_keyrelease(self, event):
        if event.keysym in ["Left", "Right"]:
            self.paddle.move_dir = 0

    def handle_reset_key(self, event):
        self.reset()

    def collision_logic(self):
        if self.state != "PLAYING":
            return

        # 1. Ball vs Walls
        self.ball.check_wall_collision()

        # 2. Ball vs Paddle
        if (self.ball.y + self.ball.radius >= self.paddle.y and 
            self.ball.y - self.ball.radius <= self.paddle.y + self.paddle.height):
            if (self.paddle.x <= self.ball.x <= self.ball.x <= self.paddle.x + self.paddle.width):
                if self.ball.dy > 0:
                    self.ball.dy = self.ball.dy * -1

        # 3. Ball vs Blocks
        for block in self.blocks:
            if block.is_alive:
                if (self.ball.x + self.ball.radius > block.x and 
                    self.ball.x - self.ball.radius < block.x + block.width and
                    self.ball.y + self.ball.radius > block.y and 
                    self.ball.y - self.ball.radius < block.y + block.height):
                    
                    block.is_alive = False
                    self.ball.dy = self.ball.dy * -1
                    self.score += 10
                    
                    # 加速判定
                    if self.score % 100 == 0 and self.score > 0:
                        self.ball.increase_speed(1.05)

        # 4. Check Level Up
        all_dead = True
        for block in self.blocks:
            if block.is_alive:
                all_dead = False
                break
        if all_dead:
            self.level += 1
            self.generate_blocks()

        # 5. Check Game Over
        if self.ball.y - self.ball.radius >= GameConstants.SCREEN_HEIGHT:
            self.state = "GAME_OVER"

    def update(self):
        if self.state == "PLAYING":
            self.ball.move()
            self.paddle.update()
            self.collision_logic()

    def render(self):
        self.canvas.delete("all")
        
        for block in self.blocks:
            block.draw(self.canvas)
            
        self.paddle.draw(self.canvas)
        self.ball.draw(self.canvas)
        
        self.canvas.create_text(
            20, 20, 
            text="Score: " + str(self.score), 
            fill=GameConstants.COLOR_TEXT, 
            anchor="nw", 
            font=("Arial", 14, "bold")
        )
        self.canvas.create_text(
            GameConstants.SCREEN_WIDTH - 20, 20, 
            text="Level: " + str(self.level), 
            fill=GameConstants.COLOR_TEXT, 
            anchor="ne", 
            font=("Arial", 14, "bold")
        )

        if self.state == "GAME_OVER":
            self.canvas.create_text(
                GameConstants.SCREEN_WIDTH / 2,
                GameConstants.SCREEN_HEIGHT / 2,
                text="GAME OVER",
                fill=GameConstants.COLOR_GAME_OVER,
                font=("Arial", 30, "bold"),
                justify="center"
            )
            self.canvas.create_text(
                GameConstants.SCREEN_WIDTH / 2,
                (GameConstants.SCREEN_HEIGHT / 2) + 40,
                text="Press 'R' to Retry",
                fill=GameConstants.COLOR_TEXT,
                font=("Arial", 14),
                justify="center"
            )

    def game_loop(self):
        self.update()
        self.render()
        self.root.after(16, self.game_loop)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Breakout - Tkinter Edition")
    root.resizable(False, False)
    app = GameManager(root)
    root.mainloop()