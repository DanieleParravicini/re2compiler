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
			    | alternative LCPAR NUM RCPAR
				| alternative LCPAR NUM COMMA NUM RCPAR
				| CHAR
				| NUM
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
	elif len(p) > 2 and p.slice[2].type == 'LCPAR':
		if len(p) <= 5:
			#case alternative LCPAR NUM RCPAR
			
			n_rep = int(p[3])
			p[0] = ast_refined.bounded_num_repetition(p[1], min_num=n_rep,max_num=n_rep)
		else:
			#alternative LCPAR NUM COMMA NUM RCPAR
			
			n_min_rep = int(p[3])
			n_max_rep = int(p[5])
			p[0] = ast_refined.bounded_num_repetition(p[1], min_num=n_min_rep,max_num=n_max_rep)

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
	elif p.slice[1].type == 'NUM':
		p[0]   = from_num_to_concat(p[1])
	else:
		#CHAR 
		p[0] = ast_refined.match_character(p[1])

def p_group(p):
	''' group 	:  CHAR MINUS CHAR group
				|  CHAR MINUS CHAR 
				|  CHAR group
				|  CHAR 
				|  NUM MINUS NUM group
				|  NUM MINUS NUM 
				|  NUM group
				|  NUM'''
	#group is a special subproduction that does not return an ast 
	#but a list of int representing chars in utf-8 is responsability of
	#other production to produce a valid ast.
	if  len(p) >= 4:
		#include MINUS
		#take high and low
		extra = []
		if p.slice[1].type == 'NUM':
			
			extra = [c.encode('utf-8')[0] for c in p[1][:-1]]+[c.encode('utf-8')[0] for c in p[3][1:]]
			p[1]  = (p[1][-1].encode('utf-8')[0])
			p[3]  = (p[3][0].encode('utf-8')[0] )
		low  			= min(p[1], p[3])
		high 			= max(p[1], p[3])
		#produce a list of chars ranging from low to high (included)
		# NOTE: char is described by means of an int
		p[0] 			= [c for c in range(low,high+1)] + extra

		if len(p) > 4:
			# if we are in the case (CHAR|NUM) MINUS (CHAR|NUM) group
			# concatenate the list produced by the subrule group 
			p[0] 		= p[0] + p[4]

	elif p.slice[1].type in ["CHAR" , "NUM"] :
		if p.slice[1].type == 'NUM':
			p[0]			= [c for c in p[1]]
		else:
			p[0] 			= [p[1]]
		
		if len(p) > 2:
			# if we are in the case (CHAR|NUM) group
			# concatenate the list produced by the subrule group 
			p[0] 		= p[0] + p[2]

def from_num_to_concat(n_string):
	to_concat = []
	for c in n_string:
		to_concat.append(ast_refined.match_character(c))

	return ast_refined.concatenation(*to_concat)

	
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

def to_ir(data=None, no_postfix=False,no_prefix=False,dotast=None):
	#https://docs.python.org/3/library/re.html#regular-expression-syntax 
	#^ (Caret.) Matches the start of the string, and in MULTILINE mode also 
	# matches immediately after each newline.
	if data[0] == '^': 
		no_prefix	= True
		data  		= data[1:]
	
	#$
	#Matches the end of the string or just before the newline at the end of the 
	# string, and in MULTILINE mode also matches before a newline. foo matches both 
	# ‘foo’ and ‘foobar’, while the regular expression foo$ matches only ‘foo’. 
	if data[-1] == '$':
		no_postfix  = True	
		data  		= data[:-1]

	ast 		= parser.parse(data)

	#by default regex_code accepts a string even if the part matching the regex does not end at the end of the string
	ast.set_accept_partial(not no_postfix)
	#by default the start of the match in the string does not have to correspond with start of the string
	ast.set_ignore_prefix(not no_prefix)
		
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

	data 		= 'r12ax\\-'
	ast 		= parser.parse(data)

	dot_file_content 	= ast.dotty_str()
	with open('test.dot', 'w', encoding="utf-8") as f:
		f.write(dot_file_content)