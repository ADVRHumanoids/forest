import functools
import textwrap

# this is opened in main
log_file = None

class ProgressReporter:

    # recursive function call counter
    call_count = 0

    @classmethod
    def count_calls(cls, fn):
        """
        Decorator that counts the number of recursive function calls.
        This is meant to be applied to the install function
        """
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            cls.call_count += 1
            ret = fn(*args, **kwargs)
            cls.call_count -= 1
            return ret
    
        return wrapper

    @classmethod
    def print(cls, pkg, text, **kwargs):
        indent = '..' * (cls.call_count - 1)
        fmt_text = f'[{pkg}] {text}'
        fmt_text = textwrap.indent(text=fmt_text, prefix=indent)
        print(fmt_text, **kwargs)

    
    @classmethod
    def get_print_fn(cls, pkg):
        return functools.partial(cls.print, pkg)