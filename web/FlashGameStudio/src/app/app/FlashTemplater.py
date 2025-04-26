import ast
from RestrictedPython import compile_restricted
from base64 import b64encode, b64decode

GAME_TEMPLATE = """class GameName:
    def __init__(self):
        self.board = []
        self.gameover = False
        self.player1, self.player2, self.state = {},{},{'gameover':False}

    def play(self):
        while(True):
            self.player1, self.player2, self.state = self.tick()
            if(self.state['gameover']):
                break
        return "Your game works!"

    def tick(self):
        self.gameover = True
        return {},{},{'gameover':False}
"""

class FlashGameHelper:
    def gen_game_from_template(name):
        tree = ast.parse(GAME_TEMPLATE)
        tree.body[0].name = name
        return b64encode(ast.unparse(tree).encode()).decode()

    def test_game(code,game_name):
        try: 
            # Let's us declare classes in RestrictedPython
            exec_globals = globals().copy()
            exec_globals['__metaclass__'] = type
            exec_globals['__name__'] = "GameTemplate"
            # Using this because it should safely create the class
            safe_byte_code = compile_restricted(
                b64decode(code).decode(),
                filename='<inline code>',
                mode='exec',
            )
            exec(safe_byte_code,globals=exec_globals)
            # Trying to run the game breaks, will learn how to implement
            # this properly later, security comes first!!!
            safe_byte_code = compile_restricted(
                f'{game_name}().play()',
                filename='<inline code>',
                mode='exec',
            )
            exec(safe_byte_code,exec_globals)
            return "Game ran successfully."
        except Exception as e:
            return f"Game failed during testing."