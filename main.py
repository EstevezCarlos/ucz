from typing import Literal, Callable
import traceback
import sys

ERROR = sentinel('ERROR')

is_testing = False

Mode = Literal[
    'invalid',
    'expects',
    'circa',
    'raises',
]

__all__ = ['Case', 'Test']


class Test:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args: Case):
        f: dict[Mode, Callable] = {
            'expects': self.expects,
            'circa': self.circa,
            'raises': self.raises,
        }

        for case in args:
            f.get(case.mode, self.invalid)(case)

    def invalid(self):
        pass

    def using(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self

    # def expects(self, case:Case):
    #     code = self._get_code(case)
    #     try:
    #         result = self.func(*case.args, **case.kwargs)
    #     except Exception as exception:
    #         self._error(code, self.func, exception)
    #     if case.value != result:
    #         print(f"☠ {code} == {result} != {case.value}")
    #         sys.exit()
    #     else:
    #         print(f"✔ {code} == {case.value}")

    def expects(self, case: Case):
        code = self._get_code(case)
        result = self._try(code, case)
        if result is ERROR:
            return
        try:
            comparison = result == case.value
        except Exception:
            # WIP
            return self._exit()
        self._assert(
            '✔ {} == {}', '✖ {} == {} != {}', code, result, case, comparison
        )

    def circa(self, case: Case):
        code = self._get_code(case)
        result = self._try(code, case)
        if result is ERROR:
            return self._exit()
        try:
            comparison = abs(result - case.value) < case.epsilon
        except Exception:
            # WIP
            return self._exit()
        self._assert(
            '✔ {} ~~ {}', '✖ {} == {} !~ {}', code, result, case, comparison
        )

    def raises(self, case: Case):

        code = self._get_code(case)
        result = self._raisez(code, case)

        if isinstance(case.value, type) and issubclass(
            case.value, BaseException
        ):
            value_str = f'<{case.value.__name__}>'
        else:
            print(
                f'⚙ Case({code}).raises({case.value}) >>> {case.value} is not exception'
            )
            return self._exit()

        if result is ERROR:
            print(
                f'✖ {code} did not raise any exception, expected {value_str}'
            )
            return self._exit()

        if isinstance(result, type) and issubclass(result, BaseException):
            result_str = f'<{result.__name__}>'
        else:
            print(f'⚙ WTF?!')
            return self._exit()

        self._assert(
            '✔ {} raises ' + result_str,
            '✖ {} raises ' + result_str + ', expected ' + value_str,
            code,
            result,
            case,
            result == case.value,
        )

    def _exit(self):
        from sys import exit

        global is_testing
        if not is_testing:
            exit()

    def _try(self, code, case):
        try:
            return self.func(*case.args, **case.kwargs)
        except Exception as exception:
            prefix = f'{self.func.__qualname__}() '
            exception_str = str(exception)
            if prefix in exception_str:
                msg = f'{self.func.__name__}() {exception_str.removeprefix(prefix)}'
                print(f'⚙ {code} >>> {type(exception).__name__} - {msg}')
            else:
                frame = traceback.extract_tb(exception.__traceback__)[-1]
                print(
                    f'⚠ {code} >>> {type(exception).__name__} in line {frame.lineno}: {frame.line} >>> {exception_str}'
                )
            if not is_testing:
                sys.exit()
            else:
                return ERROR

    def _raisez(self, code, case):
        try:
            self.func(*case.args, **case.kwargs)
            return ERROR
        except Exception as exception:
            return type(exception)

    def _assert(
        self,
        success_template: str,
        fail_template: str,
        code: str,
        result,
        case: Case,
        comparison: bool,
    ):
        if not comparison:
            print(fail_template.format(code, result, case.value))
            if not is_testing:
                sys.exit()
            else:
                return ERROR
        else:
            print(success_template.format(code, case.value))

    def _get_code(self, case: Case):
        return f"{self.func.__name__}({', '.join(repr(elem) for elem in case.args)})"


class Case:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.value = None
        self.mode: Mode = 'invalid'
        self.epsilon = 1e-9

    def expects(self, value):
        self.value = value
        self.mode = 'expects'
        return self

    def circa(self, value, epsilon=1e-9):
        self.value = value
        self.mode = 'circa'
        self.epsilon = epsilon
        return self

    def raises(self, value: type[BaseException]):
        self.value = value
        self.mode = 'raises'
        return self


def selfTest():
    global is_testing
    is_testing = True

    def add(a, b):
        return a + b

    Test(add)(
        Case(3, 1).expects(4),
        Case(3, 1).expects(5),
        Case(3, 1, 0).expects(4),
        Case(3, '1').expects(4),
        Case(3.0, 1.0).circa(4.0),
        Case(3.0, 1.0).circa(4.5),
        Case(3.0, 1.0, 0).circa(4.0),
        Case(3.0, '1').circa(4.0),
        Case(3, '1').raises(TypeError),
        Case(3, '1').raises(ValueError),
        # Case(3, "1").raises(1),
        Case(3, 1).raises(TypeError),
    )


def main():
    global is_testing
    is_testing = False
    print('WIP')


if __name__ == '__main__':

    if 't' in sys.argv or 'test' in sys.argv:
        selfTest()
    else:
        main()
