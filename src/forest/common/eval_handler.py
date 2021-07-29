import sys, os
from forest.common import proc_utils
import inspect

class EvalHandler:

    _instance = None

    class Locals:

        def __init__(self) -> None:
            self.ubuntu_release = float(proc_utils.get_output('lsb_release -rs'.split(' ')))
            self.shell = EvalHandler.Locals.shell
            self.env = EvalHandler.Locals.env

        @staticmethod
        def shell(cmd: str) -> str:
            ret = proc_utils.get_output(args=[cmd], shell=True)
            if ret is None:
                return ''
            else:
                return ret

        @staticmethod
        def env(key: str) -> str:
            return os.environ.get(key, '')
    
    
    def __init__(self) -> None:
        self.locals = EvalHandler.Locals()

    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def print_available_locals(cls):

        print('{:20s} {}'.format('name', 'type'))
        print('{:20s} {}'.format('----', '----'))
        
        for k, v in cls.instance().locals.__dict__.items():

            if callable(v):
                descr = f'function{inspect.signature(v)}'
            else:
                descr = type(v).__name__
            
            print('{:20s} {}'.format(k, descr))

    
    def eval_condition(self, code: str):
        try:
            eval_out = eval(code, None, self.locals.__dict__)
        except Exception:
            return False

        if isinstance(eval_out, bool):
            return eval_out
        else:
            print(f'condition "{code}" evaluates to {type(eval_out)} instead of bool', 
                dest=sys.stderr)
            return False
