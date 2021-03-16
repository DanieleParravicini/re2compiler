#! python re2compiler.py -d="a(b|c)*" 
import importlib 
import config
import optimization

def save_dotty(fout):
	def save_dotty_action(x):
		fout.write( x.dotty_str() )

	return save_dotty_action

def compile(inputfile=None,data=None, o=None, 
			dotast=None, dotir=None, dotcode=None, 
			O1=None, no_postfix=False, no_prefix=False,
			backend="re2coprocessor", frontend="pythonre"):
	
	#programmatically import compiler frontend and backend
	frontend = importlib.import_module("frontend_"+frontend)
	backend  = importlib.import_module("backend_"+backend)
	
	if inputfile :
		with open(inputfile,'r') as f:
			data= f.read()
			print('read', data)
	elif data is None:
		data 	= input('enter the regular expression> ')  
	ir = frontend.to_ir(data=data, no_postfix=no_postfix, no_prefix=no_prefix, dotast=dotast )
	if(dotir is not None):
		with open(dotir, 'w', encoding="utf-8") as f:
			f.write('digraph{\n')
			ir.navigate(save_dotty(f))
			f.write('\n}')
	#middle end: source and target language independent optimization passes
	ir = optimization.eliminate_nops(ir)
	if(dotir is not None):
		with open(dotir, 'w', encoding="utf-8") as f:
			f.write('digraph{\n')
			ir.navigate(save_dotty(f))
			f.write('\n}')
	#if necessary
	if O1:
		ir = optimization.merge_redundant_parallel(ir)
		ir = optimization.simplify_jumps(ir)
		ir = optimization.enhance_splits(ir)
	#check for harmful code behaviour exception in case
	_ = optimization.check_infinite_loops(ir)

	if(dotir is not None):
		with open(dotir, 'w', encoding="utf-8") as f:
			f.write('digraph{\n')
			ir.navigate(save_dotty(f))
			f.write('\n}')

	o_content  = backend.to_code(ir, dotcode=dotcode, o=o, O1=O1)
	
	return o_content


if __name__ == "__main__":
	import argparse

	arg_parser = argparse.ArgumentParser(description='compile a regular expression into code that can be executed by re2coprocessor(https://github.com/DanieleParravicini/regex_coprocessor).')
	arg_parser.add_argument('inputfile'		    , type=str, help='input file containing the regular expression.'																			, default=None, nargs='?')
	arg_parser.add_argument('-data'		    	, type=str, help='allows to pass the input string representing the regular expression directly via parameter .'								, default=None, nargs='?')
	arg_parser.add_argument('-no_postfix'		, 			help='requires that regular expression ends with the end of the string. Equivalent to <your_regex>$'											    , default=False, action='store_true')
	arg_parser.add_argument('-no_prefix'     	, 			help='do not pose any constraint on where the regular expression starts matching the string. Corresponds to .*<your_regex> or ^<your_regex>'	    , default=False, action='store_true')	
	arg_parser.add_argument('-dotast'			, type=str, help='save abstract syntax tree representation using dot format in the given file.'												, default=None)
	arg_parser.add_argument('-dotir'		    , type=str, help='save ir representation using dot format in the given file.'																, default=None)
	arg_parser.add_argument('-dotcode'			, type=str, help='save a code representation using dot format in the given file.'															, default=None)
	arg_parser.add_argument('-o'			    , type=str, help='output file containing the code that represent the regular expression.'													, default='a.out', nargs='?')
	arg_parser.add_argument('-O1'			    , 			help='perform simple optimizations'																								, default=False, action='store_true')
	arg_parser.add_argument('-backend'			, type=str, help=f'request to use a certain compiler backend. Default={config.backend}'														, default=config.backend)
	arg_parser.add_argument('-frontend'			, type=str, help=f'request to use a certain compiler backfrontend. Default={config.frontend}'												, default=config.frontend)
	
	args = arg_parser.parse_args()
	
	compile(**args.__dict__)

	
	
			


	

