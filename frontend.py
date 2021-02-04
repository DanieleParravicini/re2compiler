from threading import main_thread
import re2lexer
import ply.yacc as yacc
import ast_refined
tokens = re2lexer.tokens
debug = False


#grammar structure obtained from https://pubs.opengroup.org/onlinepubs/000095399/basedefs/xbd_chap09.html
								
def p_regex(p):
	'regex : alternative '
	p[0] = ast_refined.whole_regexp(p[1])

def p_alternative(p):
	'''alternative 	: alternative OR concatenation 
					| concatenation'''
	if(len(p) >= 4):
		if isinstance( p[1] , ast_refined.alternative):
			p[1].append(p[3])
			p[0] = p[1]
		else:
			p[0] = ast_refined.alternative(p[1],p[3])
		
	else:
		p[0] = p[1]

def p_concatenation(p):
	'''concatenation 	: concatenation repetition 
						| repetition'''
	if(len(p) >= 3):
		if isinstance( p[1] , ast_refined.concatenation):
			p[1].append(p[2])
			p[0] = p[1]
		else:
			p[0] = ast_refined.concatenation(p[1],p[2])
	else:
		p[0] = p[1]

def p_repetition(p):
	'''repetition 	: subexpr TIMES 
				  	| subexpr PLUS 
					| subexpr OPT  
					| subexpr '''
	if(len(p) >= 3):
		if( p[2] == '*'):
			p[0] = ast_refined.any_repetition(p[1])
		elif(p[2] == '+'):
			p[0] = ast_refined.more_than_one_repetition(p[1])
		elif(p[2] == '?'):
			p[0] = ast_refined.optional_repetition(p[1])
	else:
		p[0] = p[1]
		
	pass

def p_subexpr(p):
	'''subexpr 	: LPAR alternative RPAR 
				| CHAR
				| HEXA
				| WHITESPACE
				| ANYCHAR
				| LSPAR HAT group RSPAR
				| LSPAR group RSPAR'''
	#access lexer object through
	#p.slice[i]
	if debug:
		print('try',p.slice[1], p[1])
	if 	 p.slice[1].type == 'LPAR' :
		# matched subexpr -> LPAR alternative RPAR so just pass up a reference to 
		#  the other ast 
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
		p[0] = ast_refined.alternative(	ast_refined.match_character(' '),
							  	ast_refined.match_character('\t'),
							   	ast_refined.match_character('\n'),
							   	ast_refined.match_character('\r'),
							   	ast_refined.match_character('\f'),
							   	ast_refined.match_character('\v'))
	elif p.slice[1].type == 'ANYCHAR':
		#match a '.'
		p[0] = ast_refined.any_character()
	elif p.slice[1].type == 'LSPAR' and p.slice[2].type == 'HAT' :
		# negative group
		list_possible_chars = [ c  for c in range(256) if c not in p[3] ]
		list_of_matches 	= [ ast_refined.match_character(c) for c in list_possible_chars]
		
		p[0] = ast_refined.alternative(*list_of_matches)
	elif p.slice[1].type == 'LSPAR':
		#positive group
		list_of_matches = [ ast_refined.match_character(c) for c in p[2]]
		p[0] = ast_refined.alternative(*list_of_matches)
	else:
		#CHAR
		p[0] = ast_refined.match_character(p[1])

def p_group(p):
	''' group 	:  CHAR MINUS CHAR group
				|  CHAR MINUS CHAR 
				|  CHAR group
				|  CHAR '''
	#group is a special subproduction that does not return an ast 
	#but a list of int representing chars in utf-8 is responsability of
	#other production to produce a valid ast.
	if  len(p) >= 4:
		#include MINUS
		#take high and low
		low  			= min(p[1], p[3])
		high 			= max(p[1], p[3])
		#produce a list of chars ranging from low to high (included)
		# NOTE: char is described by means of an int
		p[0] 			= [c for c in range(low,high+1)] 
		if len(p) > 4:
			# if we are in the case CHAR MINUS CHAR group
			# concatenate the list produced by the subrule group 
			p[0] 		= p[0] + p[4]

	elif p.slice[1].type == "CHAR":
		p[0] 			= [p[1]]
		
		if len(p) > 2:
			# if we are in the case CHAR group
			# concatenate the list produced by the subrule group 
			p[0] 		= p[0] + p[2]

	
# Error rule for syntax errors
def p_error(p):
	if p:
          print(f"Syntax error at line {p.lineno} col {p.lexpos} token { p.type}")
          line = p.lexer.lexdata.splitlines()[p.lineno-1]
          print(line)
          print(" "*(p.lexpos)+'^')
          # Just discard the token and tell the parser it's okay.
          #raise Exception(p)
	else:
          print("Syntax error at EOF")
	exit(-1)

# Build the parser
parser	= yacc.yacc()

def to_ir(data=None, full_match=False,allow_prefix=False,dotast=None):
	ast 		= parser.parse(data)

	if(full_match): 	#by default regex_code accepts a string even if the part matching the regex does not end at the end of the string
		ast.set_accept_partial(False)
	if(allow_prefix): 	#by default the start of the match in the string does not have to correspond with start of the string
		ast.set_ignore_prefix(True)
		
	if(dotast is not None):
		dot_file_content 	= ast.dotty_str()
		with open(dotast, 'w', encoding="utf-8") as f:
			f.write(dot_file_content)

	return ast.to_ir()

if __name__ == "__main__":
	data 		= '[^a-zA-Z]\\-'
	ast 		= parser.parse(data)

	dot_file_content 	= ast.dotty_str()
	with open('test.dot', 'w', encoding="utf-8") as f:
		f.write(dot_file_content)