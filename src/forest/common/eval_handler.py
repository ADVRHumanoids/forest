import os
from forest.common import proc_utils
from forest.common import config_handler
from forest.common import package
import inspect
from string import Formatter
from typing import List

class EvalHandler:

    _instance = None

    class Locals:

        def __init__(self) -> None:
            self.ubuntu_release = float(proc_utils.get_output('lsb_release -rs'.split(' ')))
            self.shell = EvalHandler.Locals.shell
            self.env = EvalHandler.Locals.env
            self.config = config_handler.ConfigHandler.instance()

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
    def echo(cls, text: str) -> str:
        return proc_utils.get_output(args=['/bin/echo "' + text + '"'], shell=True)
        
    
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

    def eval_condition(self, code: str) -> bool:
        try:
            return bool(eval(code, None, self.locals.__dict__))
        except BaseException as e:
            if proc_utils.call_process_verbose:
                print(f'failed to evaluate "{code}" with error "{str(e)}"')
            return False

    def format_string(self, text: str) -> str:
        ret = text.format(**self.locals.__dict__)
        if proc_utils.call_process_verbose:
            print(f'formatted string "{text}" into "{ret}"')
        return ret


    def parse_conditional_dict(self, args_if) -> List[str]:

        args = list()

        # parse conditional cmake arguments
        eh = EvalHandler.instance()
        for k, v in args_if.items():

            add_arg = False

            # process key through the shell
            k = self.process_string(k)
            
            # check if key is an active mode, 
            # or is an expression returning True
            if k in package.Package.modes:
                add_arg = True
            elif eh.eval_condition(code=k):
                add_arg = True
            else:
                add_arg = False

            if not add_arg:
                continue

            # extend args with all conditional args
            if not isinstance(v, list):
                v = [v]
            
            args.extend(v)
        
        return args

        
    def process_string(self, text):
        ret = EvalHandler.echo(text)
        ret = self.format_string(ret)
        return ret
