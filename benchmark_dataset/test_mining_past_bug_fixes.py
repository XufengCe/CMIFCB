import pytest
from mining_past_bug_fixes import extract_functions, extract_condition_raise_statements

original_string = """
    def _function1(a):
        if a:
            return 1
        raise OSError('error')
        
    def _function2(b):
        for i in range(10):
            if b:
                return 1
            raise OSError('error')
        if b:
            while b < 100:
                if b % 2 == 0 and b % 3 == 0:
                    raise OSError('error')

    def _handle_http_errors(response):
        \"\"\"
        Check for HTTP errors and raise
        OSError if relevant.

        Args:
            response (requests.Response):

        Returns:
            requests.Response: response
        \"\"\"
        code = response.status_code
        if type(code) is int:
            if 200 <= code < 400:
                # 1231564
                raise [code](response.reason)
            elif code in (403, 404):
                raise {403: _ObjectPermissionError,
                    404: _ObjectNotFoundError}[code](response.reason)
            else: raise OSError(response.reason)

            if code == 500:
                return 1
            raise OSError('error')

        if code == 503:
            raise _ServiceUnavailableError(response.reason)

        if not isinstance(node, yaml.MappingNode):
            msg = 'expected a mapping node, but found %s' % node.id
            raise yaml.constructor.ConstructorError(None, None, msg, node.start_mark)
"""

def test_extract_function():

    function_list = []
    function_list.extend(extract_functions(original_string))

    func = """
    def _function1(a):
        if a:
            return 1
        raise OSError('error')
    """

    func1 = """
    def _function2(b):
        for i in range(10):
            if b:
                return 1
            raise OSError('error')
        if b:
            while b < 100:
                if b % 2 == 0 and b % 3 == 0:
                    raise OSError('error')
    """

    func2 = """
    def _handle_http_errors(response):
        \"\"\"
        Check for HTTP errors and raise
        OSError if relevant.

        Args:
            response (requests.Response):

        Returns:
            requests.Response: response
        \"\"\"
        code = response.status_code
        if type(code) is int:
            if 200 <= code < 400:
                # 1231564
                raise [code](response.reason)
            elif code in (403, 404):
                raise {403: _ObjectPermissionError,
                    404: _ObjectNotFoundError}[code](response.reason)
            else: raise OSError(response.reason)

            if code == 500:
                return 1
            raise OSError('code is not 500')

        if code == 503:
            raise _ServiceUnavailableError(response.reason)

        if not isinstance(node, yaml.MappingNode):
            msg = 'expected a mapping node, but found %s' % node.id
            raise yaml.constructor.ConstructorError(None, None, msg, node.start_mark)
    """
    assert function_list == [func, func1, func2]


def test_extractor():
    condition_raise_statements = []
    c_m_1 = """ if not (a) : return 1 raise OSError('error') """
    condition_raise_statements.extend(extract_condition_raise_statements(func))
    assert condition_raise_statements == [c_m_1]

    condition_raise_statements = []
    c_m_2 = """ if b : return 1 raise OSError('error') """
    c_m_3 = """ if b % 2 == 0 and b % 3 == 0 : raise OSError('b is divisible by 2 and 3') """
    condition_raise_statements.extend(extract_condition_raise_statements(func1))
    assert condition_raise_statements == [c_m_2, c_m_3]


    condition_raise_statements = []
    c_m_4 = """ if 200 <= code < 400 : raise [code](response.reason) """
    c_m_5 = """ elif code in (403, 404) : raise {403: _ObjectPermissionError, 404: _ObjectNotFoundError}[code](response.reason) else : raise OSError(response.reason) """
    c_m_6 = """ else : raise OSError('error') """
    c_m_7 = """ if not (code == 500) : raise OSError('code is not 500') """
    c_m_8 = """ if code == 503 : raise _ServiceUnavailableError(response.reason) """
    c_m_9 = """ if not isinstance(node, yaml.MappingNode) : raise yaml.constructor.ConstructorError(None, None, msg, node.start_mark) """
    c_m_list = [c_m_4, c_m_5, c_m_6, c_m_7, c_m_8, c_m_9]
    extract_c_m(c_m_list, original_string)

