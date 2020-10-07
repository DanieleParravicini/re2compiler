import re2compiler
import ir_python
import timeit
import time
from   itertools import chain


def peek_up_to_n(generator, n):
    return (x for _ , x in zip(range(n), generator))
def _compile(regex_string, double_check =True, allow_prefix=True, full_match=False, O1=True, debug=False ):
    code	       = re2compiler.compile(data=regex_string, allow_prefix=allow_prefix, full_match=full_match,
        O1=O1, backend="python")
    return code

def _run(code, string, debug=False ):
    string_null_ter= string +'\0'
    list_execution = code.execute(string_null_ter, cur_char_index=0)
    cur_res_exec   = list_execution
    #list_execution is a generator it contains execution point up to 
    # a certain clock cycle in the form of an instance of Continuation class.
    # To continue execution it's enough to recall the only object method execute().
    #   no params are needed as continuation keeps track of the string and the current 
    #   char index inside the object itself. 
    # A specific singleton (ir_python.Accepted) is returned by execute method instead
    # of a regular continuation in case of succesful acceptance.
    # Since list_execution is a generator we can't test for presence of ir_python.Accepted,
    # to do this it's enough to keep in a small list the result of current execution step
    n_core         = 4
    cc             = 1
    #n_core set the number of execution unit available at each clock cycle.
    #cc keeps track of the number of elapsed clock cycles.
    if(debug):
        print(f'@ 0 [@ [{ string[0]}]' , string[1:] if len(string)>1 else "", code)
        print('@',cc,' added :',cur_res_exec )
    elem_to_be_executed = list(peek_up_to_n(list_execution, n_core))
    while( elem_to_be_executed and ir_python.Accepted not in cur_res_exec ):
        
        
        cc+=1
        cur_res_exec            = []
        #take up to n_core elements from list_execution
        for e in elem_to_be_executed:
            cur_res_exec += e.execute()
        
        #concatenate list_execution with result of current execution 
        list_execution = chain(list_execution, cur_res_exec)
        #peek elems for next iteration
        elem_to_be_executed = list(peek_up_to_n(list_execution, n_core))
        if debug:
            print('@',cc,' added :',cur_res_exec )


    res = ir_python.Accepted in cur_res_exec
    return res,cc

def compile_and_run(regex_string, string, double_check =True, allow_prefix=True, full_match=False, O1=True, debug=False ):

    code	       = _compile(regex_string=regex_string, double_check=double_check, allow_prefix=allow_prefix,
                        full_match=full_match, O1=O1, debug=debug)
    res ,cc        = _run(code=code, string=string, debug=debug) 

    if debug:
        if(res):
            print("ACCEPTED in",cc, "clock cycle"+"s" if not cc == 1 else '')
        else:
            print("NOT ACCEPTED in", cc, "clock cycle"+ "s" if not cc == 1 else '')
    
    #it's possible to require a double check against a golden model (python re)
    if double_check:
        import re
        regex            = re.compile(regex_string)
        if full_match:
            golden_model_res = not(regex.fullmatch(string, pos=0) is None)
        elif allow_prefix:
            golden_model_res = not(regex.search(string, pos=0) is None)
        else:
            golden_model_res = not(regex.match(string, pos=0) is None)
        assert golden_model_res == res, f'Mismatch between golden model {golden_model_res} and regex coprocessor {res}!'
        if debug:
            print('golden model agrees')
            
    return res

def time_full_match(regex_string, string, debug=False, perf_counter=False):
    if perf_counter:
        timer = time.perf_counter
    else:
        timer = time.process_time
    secs = timeit.repeat(f"res = _run(code=code, string='{string}')"  , f"code = _compile(regex_string='{regex_string}', allow_prefix=False,full_match=True, O1=True, debug=False)", timer=timer ,number=number_of_batch , repeat=repeat,  globals=globals())
    
    return min(secs)/number_of_batch*to_ns

def time_match(regex_string, string, debug=False, perf_counter=False):
    if perf_counter:
        timer = time.perf_counter
    else:
        timer = time.process_time
    secs = timeit.repeat(f"res = _run(code=code, string='{string}')" , f"code = _compile(regex_string='{regex_string}', allow_prefix=False,full_match=False, O1=True, debug=False)", timer=timer ,number=number_of_batch , repeat=repeat,  globals=globals())
    
    return min(secs)/number_of_batch*to_ns

def time_allow_prefix_match(regex_string, string, debug=False, perf_counter=False):
    if perf_counter:
        timer = time.perf_counter
    else:
        timer = time.process_time
    secs = timeit.repeat(f"res = _run(code=code, string='{string}')"  , f"code = _compile(regex_string='{regex_string}', allow_prefix=True,full_match=False, O1=True, debug=False)", timer=timer ,number=number_of_batch , repeat=repeat,  globals=globals())
    
    return min(secs)/number_of_batch*to_ns

repeat          = 20
number_of_batch = 1_000
to_ns           = 1_000_000_000


if __name__ == "__main__":
    debug   = False
    double_check = False
    regex   = "(a(b|c|d)e*)+"
    #test acceptance full
    string  = "abacad"
    res     = compile_and_run(regex, string, allow_prefix=False,
                  full_match=True, double_check=double_check, debug=debug )
    assert res
    input("passed")
    #test acceptance no_prefix
    string  = "abacadzzz"
    res     = compile_and_run(regex, string, allow_prefix=False,
                  full_match=False, double_check=double_check, debug=debug )   
    assert res  
    
    input("passed")
    #test acceptance prefix
    string  = "zzzzabacadzzzzz"
    res     = compile_and_run(regex, string, allow_prefix=True,
                  full_match=False, double_check=double_check, debug=True )
    assert res  
    
    input("passed")
    #test no-acceptance full
    string  = "abacadzzzz"
    res     = compile_and_run(regex, string, allow_prefix=False,
                  full_match=True, double_check=double_check, debug=debug )
    assert not res  
    
    input("passed")
    #test no-acceptance no_prefix
    string  = "azzzzacad"
    res     = compile_and_run(regex, string, allow_prefix=False,
                  full_match=False, double_check=double_check, debug=debug )
    assert not res  
    
    input("passed")
    #test no-acceptance prefix
    string  = "azzzzbazcazdzzzzz"
    res     = compile_and_run(regex, string, allow_prefix=True,
                  full_match=False, double_check=double_check, debug=debug )
    assert not res  
    input("passed")
    
    t = time_full_match(regex, "abababababac")
    print('minimum time', t, 'ns')