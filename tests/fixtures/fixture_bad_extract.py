"""Module where a naive autofix would produce broken code.

The ``eval()`` call is flagged by the security analyzer (SEC001), but
removing it naively would eliminate the only code path that computes
``result``, breaking the return value.  The Verification Engine's
SyntaxVerifier must block any transform that introduces syntax errors
or new ``eval``/``exec`` calls.
"""


def dynamic_dispatch(expression, fallback=0):
    result = eval(expression)  # SEC001 — dangerous function
    if result is None:
        result = fallback
    return result


def build_query(table, columns):
    cols = ", ".join(columns)
    query = f"SELECT {cols} FROM {table}"  # noqa: S608 — intentional SQL pattern
    return query
