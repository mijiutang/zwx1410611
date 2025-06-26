import random


class Game:
    # 定义类属性, 保存历史最高分
    top_score = 0

    def __init__(self, name):
        self.play_name = name  # 实例属性

    # 静态方法
    @staticmethod
    def show_help():
        print('这是游戏的帮助信息')

    # 类方法
    @classmethod
    def show_top_score(cls):
        print(f'历史最高分为: {cls.top_score}')

    def start_game(self):
        print(f'玩家 {self.play_name} 开始游戏.....')
        score = random.randint(10, 100)  # 本次游戏得分
        print(f" 玩家 {self.play_name} 本次游戏得分为 {score}")
        if score > Game.top_score:
            Game.top_score = score


if __name__ == '__main__':
    Game.show_help()
    Game.show_top_score()
    player = Game('小王')
    player.start_game()
    Game.show_top_score()
    player.start_game()
    Game.show_top_score()



