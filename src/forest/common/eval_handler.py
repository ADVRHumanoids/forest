import os
from forest.common import proc_utils
from forest.common import config_handler
import inspect
from typing import List

class EvalHandler:

    _instance = None

    # modes are strings that are used to conditionally add cmake args
    # (and possibly other things, too!)
    modes = set()

    class Locals:

        def __init__(self) -> None:
            self.ubuntu_release = float(proc_utils.get_output('lsb_release -rs'.split(' ')))
            self.shell = EvalHandler.Locals.shell
            self.env = EvalHandler.Locals.env
            self.config = config_handler.ConfigHandler.instance()
            self.mode = EvalHandler.Locals.mode

        @staticmethod
        def mode(mode: str) -> bool:
            return mode in EvalHandler.modes

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

    def eval_string(self, code: str, ret_type=str, default=None, throw_on_failure=True):
        try:
            ret = ret_type(eval(code, None, self.locals.__dict__))
            if proc_utils.call_process_verbose:
                print(f'{code} evaluated to {ret}')
            return ret
        except BaseException as e:
            if proc_utils.call_process_verbose:
                print(f'failed to evaluate "{code}" to {ret_type} with error "{str(e)}"')
            if throw_on_failure:
                raise e
            return default

    def eval_condition(self, code: str):
        if isinstance(code, bool):
            return code
        return self.eval_string(code=code, ret_type=bool, default=False, throw_on_failure=False)

    def format_string(self, text: str, locals=None) -> str:
        if locals is None:
            locals = dict()
        ret = text.format(**self.locals.__dict__, **locals)
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
            if k in EvalHandler.modes:
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

        
    def process_string(self, text: str, locals=None, shell=True) -> str:
        """
        Process a string through a pipeline of operations as follows.
        a) if the input text is in the form ${code}, we evaluate code via
           the interpreter with given locals, and return
        b) otherwise, we first echo the input text via the shell,
           and then apply {} formatting with given locals.

        Args:
            text (str): input string
            locals (Dict[str, -], optional): A dictionary with variables used for string formatting. Defaults to None.
            shell (bool, optional): Enable parsing via the shell. Defaults to True.

        Returns:
            str: the processed string
        """

        # check if text is in the form ${code}
        is_expression = len(text) >= 3 and text[0:2] == '${' and text[-1] == '}'
        if is_expression:
            return self.eval_string(text[2:-1])
        
        # otherwise echo through the shell and then apply format rules
        ret = str(text)

        if shell:
            ret = EvalHandler.echo(ret)

        ret = self.format_string(ret, locals)
        
        return ret
