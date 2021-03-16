def get_golden_model_result(regex_str, string, no_prefix=True,no_postfix=False,frontend='pythonre'):
    from helper import pcre_to_python, normalize_regex_input

    tmp_string = str(regex_str)
    if frontend == 'pcre':
        tmp_string = pcre_to_python(tmp_string)
    tmp_string = normalize_regex_input(tmp_string)

    if no_prefix and tmp_string[0:1] !='^(':
        tmp_string = '^('+ tmp_string + ')'

    if no_postfix and tmp_string[-2:] !=')$':
        tmp_string = '(' + tmp_string + ')$'
    
    if isinstance(tmp_string, str):
        tmp_string = bytes(tmp_string,'utf-8')

    if isinstance(string, str):
        string = bytes(string,'utf-8')

    import re
    regex_tmp            = re.compile(tmp_string)
    golden_model_res = not(regex_tmp.search(string) is None)

    return golden_model_res