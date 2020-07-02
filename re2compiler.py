import ply.yacc as yacc
import re2lexer
import ir
import optimization
tokens = re2lexer.tokens

#grammar structure obtained from https://pubs.opengroup.org/onlinepubs/000095399/basedefs/xbd_chap09.html
								
def p_regex(p):
	'regex : alternative '
	p[0] = ir.whole_regexp(p[1])

def p_alternative(p):
	'''alternative 	: alternative OR concatenation 
					| concatenation'''
	if(len(p) >= 4):
		if isinstance( p[1] , ir.alternative):
			p[1].append(p[3])
			p[0] = p[1]
		else:
			p[0] = ir.alternative(p[1],p[3])
		
	else:
		p[0] = p[1]

def p_concatenation(p):
	'''concatenation 	: concatenation repetition 
						| repetition'''
	if(len(p) >= 3):
		if isinstance( p[1] , ir.concatenation):
			p[1].append(p[2])
			p[0] = p[1]
		else:
			p[0] = ir.concatenation(p[1],p[2])
	else:
		p[0] = p[1]

def p_repetition(p):
	'''repetition 	: subexpr TIMES 
				  	| subexpr PLUS 
					| subexpr OPT  
					| subexpr '''
	if(len(p) >= 3):
		if( p[2] == '*'):
			p[0] = ir.any_repetition(p[1])
		elif(p[2] == '+'):
			p[0] = ir.more_than_one_repetition(p[1])
		elif(p[2] == '?'):
			p[0] = ir.optional_repetition(p[1])
	else:
		p[0] = p[1]
		
	pass

def p_subexpr(p):
	'''subexpr 	: LPAR alternative RPAR 
				| CHAR
				| HEXA
				| WHITESPACE
				| ANYCHAR'''
	#access lexer object through
	#p.slice[i]
	#print('try',p.slice[1], p[1])
	if 	 p.slice[1].type == 'LPAR' :
		p[0] = p[2]
	elif p.slice[1].type == 'WHITESPACE':
		#from https://docs.python.org/3.8/library/re.html
		#For Unicode (str) patterns:
		#Matches Unicode whitespace characters (which includes [ \t\n\r\f\v], and also many other characters, 
		# for example the non-breaking spaces mandated by typography rules in many languages). 
		#If the ASCII flag is used, only [ \t\n\r\f\v] is matched.
		#
		#or 8-bit (bytes) patterns:
		#Matches characters considered whitespace in the ASCII character set; this is equivalent to [ \t\n\r\f\v].
		#	 and https://docs.microsoft.com/en-us/cpp/c-language/escape-sequences?view=vs-2019
		p[0] = ir.alternative(	ir.match_character(' '),
							  	ir.match_character('\t'),
							   	ir.match_character('\n'),
							   	ir.match_character('\r'),
							   	ir.match_character('\f'),
							   	ir.match_character('\v'))
	elif p.slice[1].type == 'ANYCHAR':
		print('test')
		p[0] = ir.any_character()
	else:
		p[0] = ir.match_character(p[1])
	
# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!", p)

# Build the parser
frontend	= yacc.yacc()

def save_dotty(fout):
	def save_dotty_action(x):
		fout.write( x.dotty_str() )

	return save_dotty_action

def compile(inputfile=None,data=None, o=None, dotast=None, dotirlowered=None, dotcode=None, O1=None, full_match=False):
	
	if inputfile :
		with open(inputfile,'r') as f:
			data= f.read()
			print('read', data)
	elif data is None:
		data 	= input('enter the regular expression> ')  
	
	ast 		= frontend.parse(data)

	if(full_match): #by default regex_code accept even partial match
		ast.set_accept_partial(False)

	if(dotast is not None):
		dot_file_content 	= ast.dotty_str()
		with open(dotast, 'w', encoding="utf-8") as f:
			f.write(dot_file_content)

	lowered_ir = ast.lower()
	lowered_ir = optimization.eliminate_nops(lowered_ir)
	if O1:
		lowered_ir = optimization.simplify_jumps(lowered_ir)
		lowered_ir = optimization.enhance_splits(lowered_ir)
	
	_ = optimization.check_infinite_loops(lowered_ir)


	if(dotirlowered is not None):
		with open(dotirlowered, 'w', encoding="utf-8") as f:
			f.write('digraph{\n')
			lowered_ir.navigate(save_dotty(f))
			f.write('\n}')

	list_istr = lowered_ir.code_gen()
	if O1:
		list_istr = optimization.simplify_jumps_backend(list_istr)
	
	if(dotcode is not None):
		with open(dotcode, 'w', encoding="utf-8") as f:
			dot_content = 'digraph {\n'+"".join([instr.dotty_str() for instr in list_istr ])+'}'
			f.write(dot_content)

	ocontent = "".join([instr.code() for instr in list_istr ])
	if(o is not None):
		with open(o, 'w', encoding="utf-8") as f:
			f.write(ocontent)
	
	return ocontent


if __name__ == "__main__":
	import argparse

	arg_parser = argparse.ArgumentParser(description='compile a regular expression into code that can be executed by re2coprocessor(https://github.com/DanieleParravicini/regex_coprocessor).')
	arg_parser.add_argument('inputfile'		    , type=str, help='input file containing the regular expression.'													, default=None, nargs='?')
	arg_parser.add_argument('-full_match'	    , 			help='requires that regular expression matches the entire string'										, default=False, action='store_true')
	arg_parser.add_argument('-data'		    	, type=str, help='allows to pass the input string representing the regular expression directly via parameter .'		, default=None, nargs='?')
	arg_parser.add_argument('-dotast'			, type=str, help='save abstract syntax tree representation using dot format in the given file.'						, default=None)
	arg_parser.add_argument('-dotirlowered'		, type=str, help='save ir representation using dot format in the given file.'										, default=None)
	arg_parser.add_argument('-dotcode'			, type=str, help='save a code representatio using dot format in the given file.'									, default=None)
	arg_parser.add_argument('-o'			    , type=str, help='output file containing the code that represent the regular expression.'							, default='a.out', nargs='?')
	arg_parser.add_argument('-O1'			    , 			help='perform simple optimization'																		, default=False, action='store_true')
	
	args = arg_parser.parse_args()
	
	compile(**args.__dict__)

	
	
			


	

