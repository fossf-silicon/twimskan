

def do_repl(code: str, iris):
    print('repling', code)
    code.replace('<br>', '\n')
    code.replace('&nbsp;', ' ')
    try:
            _return = str(eval(code, globals(), iris.locals)).strip('<>')
            return f">>> {code}\n{_return}"

    except SyntaxError:
        try:
            # code = code.replace('\r', '')
            # if not g_imprtd:
            #     exec(compile('globals().update(iris.locals)', 'input', 'single'), globals(), locals())
            #     g_imprtd = True
            # _code = compile(code , '<string>', 'single')
            exec(compile(code, 'input', 'single'), globals(), iris.locals)
            # exec(compile('globals().update(locals())', 'input', 'single'), globals(), iris.locals())
            # exec(_code, globals(), locals())
            return f">>> {code}"
        except Exception as e:
            return f">>> {code}\n{e}"


    except Exception as e:
        return f">>> {code}\n{e}"