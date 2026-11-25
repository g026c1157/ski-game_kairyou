"""ASCIIスキー：リアルタイム入力とスクロールを学ぶ教材。Windows端末用。"""
import os
import random
import sys
import time

WIDTH = 29
HEIGHT = 16
START_INTERVAL = 0.32
MIN_INTERVAL = 0.085


def get_key():
    """Windowsの非ブロッキングキー入力。通常のターミナルで動作させる。"""
    import msvcrt
    if not msvcrt.kbhit():
        return None
    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        special = msvcrt.getwch()
        if special == "K":
            return "left"
        if special == "M":
            return "right"
        if special == "H":  #追加:上矢印キー
            return "up"
        return None
    return key.lower()


def start_game():
    return {"player_x": WIDTH // 2, "direction": 1, "distance": 0,
            "speed": START_INTERVAL, "alive": True, "running": False,
            "field": [" " * WIDTH for _ in range(HEIGHT)], "score": 0,
            "boost_timer": 0, #追加:加速の残りターン数
            "jump_timer": 0, #追加:ジャンプの残りターン数
            "star_timer": 0  #追加:無敵の残りターン数
            }


def make_row(distance):
    """障害物のある新しい行を作る。A=木、*=崖。"""
    row = [" "] * WIDTH
    chance = min(0.36, 0.10 + distance / 800)
    if random.random() < chance:
        row[random.randrange(WIDTH)] = random.choice(("A", "A", "*"))
    if random.random() < chance / 3:
        pos = random.randrange(WIDTH)
        if row[pos] == " ":
            row[pos] = "A"

    #追加:横幅10〜15マスのクレバス（=）を作る
    if random.random() < chance / 4:
        w = random.randint(10, 15)
        start = random.randrange(WIDTH - w + 1)
        for i in range(start, start + w):
            row[i] = "="

    #追加:無敵スター（$）を1つ置く
    if random.random() < 0.02:
        pos = random.randrange(WIDTH)
        if row[pos] == " ":
            row[pos] = "$"

    return "".join(row)


def update_game(game):
    if not game["running"] or not game["alive"]:
        return
    # プレイヤーは左右どちらかへ滑り続ける。方向を切り替えて回避する。
    nx = game["player_x"] + game["direction"]
    if nx < 0 or nx >= WIDTH:
        game["alive"] = False
        return
    
    #追加:加速タイマーのカウントダウン
    if game["boost_timer"] > 0:
        game["boost_timer"] -= 1

    #追加:ジャンプタイマーのカウントダウン
    if game["jump_timer"] > 0:
        game["jump_timer"] -= 1

    game["player_x"] = nx
    game["field"].pop()
    game["field"].insert(0, make_row(game["distance"]))
    game["distance"] += 1
    game["score"] = game["distance"] * 10

    #追加:基本速度を計算し、加速中だけ待ち時間を半分にする
    base_speed = max(MIN_INTERVAL, START_INTERVAL - game["distance"] * 0.001)
    #変更
    game["speed"] = base_speed * 0.5 if game["boost_timer"] > 0 else base_speed

    #変更:木(A)はジャンプ不可、崖(*)はジャンプ中(jump_timer > 0)なら飛び越えられる
    #追加:クレバス（=）もジャンプ中なら飛び越えられるようにする
    cell = game["field"][HEIGHT - 1][game["player_x"]]
    if cell == "A" or (cell in ("*", "=") and game["jump_timer"] == 0):
        game["alive"] = False


def draw_game(game):
    # ANSIのカーソル移動で画面を上書きする。Windows Terminal/VS Code推奨。
    sys.stdout.write("\x1b[H")
    print("=== ASCII SKI ===".ljust(WIDTH + 2))
    for y in range(HEIGHT):
        line = list(game["field"][y])
        if y == HEIGHT - 1:

            #変更:ジャンプ中は「^」、加速中は「V」、通常は「O」にする
            if game["jump_timer"] > 0:
                player_char = "^"
            elif game["boost_timer"] > 0:
                player_char = "V"
            else:
                player_char = "O"
            line[game["player_x"]] = player_char if game["alive"] else "X"
        print("|" + "".join(line) + "|")
    
    print("+" + "-" * WIDTH + "+")
    print(f"距離 {game['distance']:<5} 得点 {game['score']:<6} 速度 {1/game['speed']:.1f}行/秒    ")
    status = ("ゲームオーバー [R]でリスタート" if not game["alive"]
              else "滑走中" if game["running"] else "[Space]でスタート")
    print(status.ljust(WIDTH + 22))

    #追加:加速機能の操作説明を表示
    #追加:ジャンプ機能の操作説明を表示
    print("W/↑: 加速  J/Enter: ジャンプ  ← →: 方向変更  Space: 開始/停止  R: 再開  Q: 終了".ljust(WIDTH + 22))
    sys.stdout.flush()


def main():
    if os.name != "nt":
        print("この版のスキーゲームはWindowsのVS Codeターミナル用です。")
        return
    # Windows 10/11のVS Code内蔵ターミナルを想定
    os.system("")
    game = start_game()
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            key = get_key()
            if key in ("q", "\x1b"):
                break
            if key == "r":
                game = start_game()
            elif key == " ":
                if game["alive"]:
                    game["running"] = not game["running"]
            elif key in ("left", "a"):
                game["direction"] = -1
            elif key in ("right", "d"):
                game["direction"] = 1
   
            #追加:Wまたは↑が押されたら加速開始
            elif key in ("up", "w") and game["running"] and game["alive"]:
                game["boost_timer"] = 3

            #追加:JまたはEnterが押されたらジャンプ開始
            elif key in ("j", "\r") and game["running"] and game["alive"]:
                if game["jump_timer"] == 0:
                    game["jump_timer"] = 3
     
            if game["running"]:
                update_game(game)
            draw_game(game)
            time.sleep(game["speed"] if game["running"] else 0.08)
    finally:
        sys.stdout.write("\x1b[?25h\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()