import sys
from forest.common import proc_utils

class EvalHandler:

    _instance = None

    class Locals:

        def __init__(self) -> None:
            self.ubuntu_release = float(proc_utils.get_output('lsb_release -rs'.split(' ')))

    
    def __init__(self) -> None:
        self.locals = EvalHandler.Locals()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    
    def eval_condition(self, code: str):
        eval_out = eval(code, None, self.locals.__dict__)
        if isinstance(eval_out, bool):
            return eval_out
        else:
            print(f'condition "{code}" evaluates to {type(eval_out)} instead of bool', 
                dest=sys.stderr)
            return False
