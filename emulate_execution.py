import re2compiler
import ir_python
import timeit
import time
from   itertools import chain
from   golden_model import get_golden_model_result


def peek_up_to_n(generator, n):
	return (x for _ , x in zip(range(n), generator))
def _compile(regex_string, double_check =True, no_prefix=False, no_postfix=False, O1=True, debug=False ):
	code	       = re2compiler.compile(data=regex_string, no_prefix=no_prefix, no_postfix=no_postfix,
		O1=O1, backend="python")
	return code

def move_exe_res_in_list_instr_per_char(cur_res_exec, list_instr_per_char, debug=False ):
	num_char_in_flight = len(list_instr_per_char)
	if debug:
		print('num char in flight',num_char_in_flight)
		for instr in cur_res_exec:
				print('instr:', instr,' moved to list ',instr.cur_char_index % num_char_in_flight)
		
	for i in range(num_char_in_flight):

		instr_for_char_i = [ instr for instr in cur_res_exec if ( instr.cur_char_index % num_char_in_flight == i ) ]
		if debug:
			print("put", instr_for_char_i, "to list", i , "esim")
		list_instr_per_char[i] = chain(list_instr_per_char[i], instr_for_char_i)

def peek_up_to_n_from_list_instr_per_char(cur_char, list_instr_per_char, n, debug = False):
	num_char_in_flight = len(list_instr_per_char)
	list_that_be_executed = []

	for i in range(cur_char, cur_char+num_char_in_flight-1):
		if debug:
			print('add list', i%num_char_in_flight, 'to list of executable')
		list_that_be_executed.append( list_instr_per_char[i%num_char_in_flight])
	return peek_up_to_n(chain(* list_that_be_executed ), n)

def _run(code, string, debug=False ):
	if not isinstance(string,bytes):
		string = bytes(string,'utf-8','ignore')
	string_null_ter         = string +b'\0'
	cur_res_exec            = list(code.execute(string_null_ter, cur_char_index=0))
	cur_char                = 0
	n_core                  = 2
	cc                      = 1
	instruction_issued      = 1 + len(cur_res_exec)
	instruction_completed   = 1 + 0


	#n_core set the number of execution unit available at each clock cycle.
	#cc keeps track of the number of elapsed clock cycles.
	if(debug):
		print(f'@ 0 [@ [{ bytes([string[0]])}]' , string[1:] if len(string)>1 else "",' ran: ',  code)
		print('@',cc,' added :',cur_res_exec )

	num_char_in_flight      = 2
	assert num_char_in_flight > 1, "There should be at least 2 lists 1 for current and 1 for next"
	list_instr_per_char    = [[] for i in range(num_char_in_flight)]
	
	
	while( instruction_issued > instruction_completed and ir_python.Accepted not in cur_res_exec ):
		#concatenate list_execution with result of current execution 
		move_exe_res_in_list_instr_per_char(cur_res_exec, list_instr_per_char, debug)
		elem_to_be_executed = list(peek_up_to_n_from_list_instr_per_char(cur_char, list_instr_per_char, n_core, debug))
		#check whether to move to next char
		continuation_of_cur_char = [ i for i in elem_to_be_executed if i.cur_char_index == cur_char]
		if len(continuation_of_cur_char) == 0:
			cur_char += 1
			if debug:
				print('@ cc moved to next char')

		cc+=1
		cur_res_exec            = []
		#take up to n_core elements from list_execution
		for e in elem_to_be_executed:
			cur_res_exec            += e.execute()
			instruction_completed   += 1

		instruction_issued += len(cur_res_exec)

		if debug:
			print('@', cc, 'ran: ', elem_to_be_executed)
			print('@', cc, 'added :',cur_res_exec )
			input()


	res = ir_python.Accepted in cur_res_exec
	return res,cc

def _run_asap(code, string, debug=False ):
	if not isinstance(string,bytes):
		string = bytes(string,'utf-8','ignore')
	string_null_ter= string +b'\0'
	list_execution = code.execute(string_null_ter, cur_char_index=0)
	cur_res_exec   = list_execution
	#list_execution is a generator it contains execution point up to 
	# a certain clock cycle in the form of an instance of Continuation class.
	# To continue execution it's enough to recall the only object method execute().
	#   no params are needed as continuation keeps track of the string and the current 
	#   char index inside the object itself. 
	# A specific singleton (ir_python.Accepted) is returned by execute method instead
	# of a regular continuation in case of successful acceptance.
	# Since list_execution is a generator we can't test for presence of ir_python.Accepted,
	# to do this it's enough to keep in a small list the result of current execution step
	n_core         = 2
	cc             = 1
	#n_core set the number of execution unit available at each clock cycle.
	#cc keeps track of the number of elapsed clock cycles.
	if(debug):
		print(f'@ 0 [@ [{ bytes([string[0]])}]' , string[1:] if len(string)>1 else ""," ran: ", code)
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
			print('@',cc,' run :'  ,elem_to_be_executed )
			print('@',cc,' added :',cur_res_exec )


	res = ir_python.Accepted in cur_res_exec
	return res,cc

def compile_and_run(regex_string, string, double_check =True, no_prefix=False, no_postfix=False, O1=True, debug=False, frontend='pythonre'):

	code	       = _compile(regex_string=regex_string, double_check=double_check, no_prefix=no_prefix,
						no_postfix=no_postfix, O1=O1, debug=debug)
	res ,cc        = _run(code=code, string=string, debug=debug) 

	if debug:
		if(res):
			print("ACCEPTED in",cc, "clock cycle"+"s" if not cc == 1 else '')
		else:
			print("NOT ACCEPTED in", cc, "clock cycle"+ "s" if not cc == 1 else '')
	
	#it's possible to require a double check against a golden model (python re)
	if double_check:
		import golden_model
		golden_model_res = golden_model.get_golden_model_result(regex_string, string, no_prefix=no_prefix, no_postfix=no_postfix,frontend=frontend)

		assert golden_model_res == res, f'Mismatch between golden model {golden_model_res} and regex coprocessor {res}!'
		if debug:
			print('golden model agrees')
			
	return res, cc

def compile_and_run_asap(regex_string, string, double_check =True, no_prefix=False, no_postfix=False, O1=True, debug=False, frontend='pythonre' ):

	code	       = _compile(regex_string=regex_string, double_check=double_check, no_prefix=no_prefix,
						no_postfix=no_postfix, O1=O1, debug=debug)
	res ,cc        = _run_asap(code=code, string=string, debug=debug) 

	if debug:
		if(res):
			print("ACCEPTED in",cc, "clock cycle"+"s" if not cc == 1 else '')
		else:
			print("NOT ACCEPTED in", cc, "clock cycle"+ "s" if not cc == 1 else '')
	
	#it's possible to require a double check against a golden model (python re)
	if double_check:
		import golden_model
		golden_model_res = golden_model.get_golden_model_result(regex_string, string, no_prefix=no_prefix, no_postfix=no_postfix,frontend=frontend)

		assert golden_model_res == res, f'Mismatch between golden model {golden_model_res} and regex coprocessor {res}!'
		if debug:
			print('golden model agrees')
			
	return res, cc

def time_no_postfix(regex_string, string, debug=False, perf_counter=False):
	if perf_counter:
		timer = time.perf_counter
	else:
		timer = time.process_time
	secs = timeit.repeat(f"res = _run_asap(code=code, string='{string}')"  , f"code = _compile(regex_string='{regex_string}', no_prefix=False,no_postfix=True, O1=True, debug=False)", timer=timer ,number=number_of_batch , repeat=repeat,  globals=globals())
	
	return min(secs)/number_of_batch*to_ns

def time_match(regex_string, string, debug=False, perf_counter=False):
	if perf_counter:
		timer = time.perf_counter
	else:
		timer = time.process_time
	secs = timeit.repeat(f"res = _run_asap(code=code, string='{string}')" , f"code = _compile(regex_string='{regex_string}', no_prefix=False,no_postfix=False, O1=True, debug=False)", timer=timer ,number=number_of_batch , repeat=repeat,  globals=globals())
	
	return min(secs)/number_of_batch*to_ns

def time_no_prefix_match(regex_string, string, debug=False, perf_counter=False):
	if perf_counter:
		timer = time.perf_counter
	else:
		timer = time.process_time
	secs = timeit.repeat(f"res = _run_asap(code=code, string='{string}')"  , f"code = _compile(regex_string='{regex_string}', no_prefix=True,no_postfix=False, O1=True, debug=False)", timer=timer ,number=number_of_batch , repeat=repeat,  globals=globals())
	
	return min(secs)/number_of_batch*to_ns

def cc_asap_no_postfix(regex_string, string, debug=False):
	res, cc = compile_and_run_asap(regex_string=regex_string, string=string,
							 no_prefix=False, no_postfix=True, double_check=True, O1=True, debug=debug)
	return cc

def cc_asap_match(regex_string, string, debug=False):
	res, cc = compile_and_run_asap(regex_string=regex_string, string=string,
							 no_prefix=False, no_postfix=False, double_check=True, O1=True, debug=debug)
	return cc

def cc_asap_no_prefix_match(regex_string, string, debug=False):
	res, cc = compile_and_run_asap(regex_string=regex_string, string=string,
							 no_prefix=True, no_postfix=False, double_check=True, O1=True, debug=debug)
	return cc

def cc_no_postfix(regex_string, string, debug=False):
	res, cc = compile_and_run(regex_string=regex_string, string=string,
							 no_prefix=False, no_postfix=True, double_check=True, O1=True, debug=debug)
	return cc

def cc_match(regex_string, string, debug=False):
	res, cc = compile_and_run(regex_string=regex_string, string=string,
							 no_prefix=False, no_postfix=False, double_check=True, O1=True, debug=debug)
	return cc

def cc_no_prefix_match(regex_string, string, debug=False):
	res, cc = compile_and_run(regex_string=regex_string, string=string,
							 no_prefix=True, no_postfix=False, double_check=True, O1=True, debug=debug)
	return cc

repeat          = 20
number_of_batch = 1_000
to_ns           = 1_000_000_000



if __name__ == "__main__":

	debug   = False
	double_check = False

	#regex   = "((R|K|X)(...?)?(D|B|E|Z|X)(...?)?(Y|X))|(.(G|X)(R|K|X)(R|K|X))|((S|T|X).(R|K|X))"
	#string  = "MYKMYFLKDQKFSLSGTIRINDKTQSEYGSVWCPGLSITGLHHDAIDHNMFEEMETEIIEYLGPWVQAEYRRIKG"
	#res,cc  = compile_and_run_asap(regex, string, no_prefix=True,
	#              no_postfix=False, double_check=double_check, debug=True )
	#print('cc taken', cc)

	
	regex   = "(a(b|c|d)e*)+"
	#test acceptance full
	string  = "abacad"
	res,cc     = compile_and_run_asap(regex, string, no_prefix=True,
				  no_postfix=True, double_check=double_check, debug=debug )
	assert res
	print('cc taken', cc)
	input("passed")
	#test acceptance no_prefix
	string  = "abacadzzz"
	res,cc  = compile_and_run_asap(regex, string, no_prefix=True,
				  no_postfix=False, double_check=double_check, debug=debug )   
	assert res  
	print('cc taken', cc)
	input("passed")

	#test acceptance prefix
	string  = "zzzzabacad"
	res,cc  = compile_and_run_asap(regex, string, no_prefix=False,
				  no_postfix=True, double_check=double_check, debug=debug )
	
	print('cc taken', cc)
	input("passed")

	#test acceptance prefix, suffix
	string  = "zzzzabacadzzzzzz"
	res,cc  = compile_and_run_asap(regex, string, no_prefix=False,
				  no_postfix=False, double_check=double_check, debug=debug )
	assert res  
	print('cc taken', cc)
	input("passed")

	#test no-acceptance full
	string  = "abacadzzzz"
	res, cc = compile_and_run_asap(regex, string, no_prefix=True,
				  no_postfix=True, double_check=double_check, debug=debug )
	assert not res  
	print('cc taken', cc)
	input("passed")

	#test no-acceptance no_prefix
	string  = "azzzzacad"
	res, cc = compile_and_run_asap(regex, string, no_prefix=True,
				  no_postfix=False, double_check=double_check, debug=debug )
	assert not res  
	print('cc taken', cc)
	input("passed")

	#test no-acceptance prefix
	string  = "azzzzbazcazdzzzzz"
	res,cc  = compile_and_run_asap(regex, string, no_prefix=False,
				  no_postfix=False, double_check=double_check, debug=debug )
	assert not res  
	print('cc taken', cc)
	input("passed")
	
	t = time_no_postfix(regex, "abababababac")
	print('minimum time', t, 'ns')
	
	