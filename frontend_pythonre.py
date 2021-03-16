import ply.yacc as yacc
import ast_refined
import re2lexer
tokens = re2lexer.tokens
debug  = False
NUM_CHARS 			= 256
MAX_SEQUENTIAL_TEST = 64

#grammar structure obtained from https://pubs.opengroup.org/onlinepubs/000095399/basedefs/xbd_chap09.html
								
def p_regex(p):
	'regex : alternative '
	p[0] = ast_refined.whole_regexp(p[1])

def p_alternative(p):
	'''alternative 	: alternative OR concatenation  
					| alternative OR
					| concatenation'''
	if(len(p) >= 4):
		if (isinstance( p[1] , ast_refined.alternative) and 
		    isinstance(p[3], ast_refined.alternative)):
				for c in p[3].children:
					p[1].append(c)
		elif isinstance( p[1] , ast_refined.alternative):
			p[1].append(p[3])
			p[0] = p[1]
		elif isinstance( p[3] , ast_refined.alternative):
			p[3].append(p[1])
			p[0] = p[3]
		else:
			p[0] = ast_refined.alternative(p[1],p[3])
	elif(len(p) == 3):
		if isinstance( p[1] , ast_refined.alternative):
			p[1].append(ast_refined.epsilon_move())
			p[0] = p[1]
		else:
			p[0] = ast_refined.alternative(p[1],ast_refined.epsilon_move())
	else:
		p[0] = p[1]

def p_concatenation(p):
	'''concatenation 	: concatenation repetition 
						| repetition'''
	if(len(p) >= 3):
		if 	(isinstance( p[1] , ast_refined.concatenation) and
			 isinstance( p[2] , ast_refined.concatenation) ):
			for c in p[2].children:
				p[1].append(c)
			p[0] = p[1]
		elif isinstance( p[1] , ast_refined.concatenation) :
			p[1].append(p[2])
			p[0] = p[1]
		elif isinstance( p[2] , ast_refined.concatenation) :
			p[1] = ast_refined.concatenation(p[1])
			for c in p[2].children:
				p[1].append(c)
			p[0] = p[1]
		else:
			p[0] = ast_refined.concatenation(p[1],p[2])
	else:
		p[0] = p[1]

def p_repetition(p):
	'''repetition 	: subexpr TIMES 
				  	| subexpr PLUS 
					| subexpr OPT  
					| subexpr LCPAR NUM RCPAR
					| subexpr LCPAR COMMA NUM RCPAR
					| subexpr LCPAR NUM COMMA RCPAR
					| subexpr LCPAR NUM COMMA NUM RCPAR
					| subexpr '''
	#pay attention that even though some constructs are parsed by the grammar
	#they may be not suitable to run in the accel.
	if(len(p) == 3):
		if(  p[2] == '*'):
			p[0] = ast_refined.any_repetition(p[1])
		elif(p[2] == '+'):
			p[0] = ast_refined.more_than_one_repetition(p[1])
		elif(p[2] == '?'):
			p[0] = ast_refined.optional_repetition(p[1])	
	elif len(p) >= 5 and p.slice[2].type == 'LCPAR':
		
		if len(p) == 5:
			#case: alternative LCPAR NUM RCPAR regex{n}
			n_rep = int(p[3])
			p[0] = ast_refined.bounded_num_repetition(p[1], min_num=n_rep,max_num=n_rep)
		elif len(p) == 6 and p.slice[3].type == 'COMMA':
			#case: alternative LCPAR COMMA NUM RCPAR regex{,m}
			n_min_rep = 0
			n_max_rep = int(p[4])
			p[0] = ast_refined.bounded_num_repetition(p[1], min_num=n_min_rep,max_num=n_max_rep)
		elif len(p) == 6 and p.slice[4].type == 'COMMA':
			#case: alternative LCPAR NUM COMMA RCPAR regex{n,}
			n_min_rep = int(p[3])
			p[0] = ast_refined.min_bounded_num_repetition(p[1], min_num=n_min_rep)
		else:
			#case: alternative LCPAR NUM COMMA NUM RCPAR regex{n,m}
			n_min_rep = int(p[3])
			n_max_rep = int(p[5])
			p[0] = ast_refined.bounded_num_repetition(p[1], min_num=n_min_rep,max_num=n_max_rep)
	else:
		#case subexpression
		p[0] = p[1]

def p_subexpr(p):
	'''subexpr 	: LPAR alternative RPAR 
				| LSPAR HAT group RSPAR
				| LSPAR group RSPAR
				| terminal_sequence
				| metachar 
				| ANYCHAR
				| DOLLAR
				| MINUS
				'''
	
	if debug: #access lexer object through p.slice[i] example:
		print('try',p.slice[1], p[1])

	if 	 p.slice[1].type == 'LPAR' :
		# matched subexpr -> LPAR alternative RPAR so just pass up a reference to 
		#  the sub ast 
		p[0] = p[2]
	elif p.slice[1].type == 'LSPAR' and p.slice[2].type == 'HAT' :
		# negative group
		p[0] = match_negative_group(p[3])
	elif p.slice[1].type == 'LSPAR':
		#positive group
		p[0] = match_positive_group(p[2])
	elif p.slice[1].type == 'metachar':
		# metachar can be treated as a positive group of chars to be matched
		p[0] = match_positive_group(p[1])
	elif p.slice[1].type == 'ANYCHAR':
		#match a '.'
		p[0] = ast_refined.any_character()
	elif p.slice[1].type == 'DOLLAR':
		#match a '$'
		p[0] = ast_refined.end_of_string()
	else:
		#a terminal_sequence
		list_of_matches = [ ast_refined.match_character(c) for c in p[1]]
		p[0] = ast_refined.concatenation(*list_of_matches)

def match_negative_group(char_set):
	#this method decide whether to create a seq test or a parallel test
	if len(char_set) < MAX_SEQUENTIAL_TEST: 
		return turn_into_a_negative_match_seq(char_set)
	else:
		return turn_into_a_positive_match_seq(complement_char_set(char_set))

def match_positive_group(char_set):
	#this method decide whether to create a seq test or a parallel test
	if (NUM_CHARS- len(char_set)) < MAX_SEQUENTIAL_TEST: 
		return turn_into_a_negative_match_seq(complement_char_set(char_set))
	else:
		return turn_into_a_positive_match_seq(char_set)

def turn_into_a_negative_match_seq(char_set):
	list_of_matches 	= [ ast_refined.match_negative_character(c) for c in char_set]
	return ast_refined.none_of(*list_of_matches)

def turn_into_a_positive_match_seq(char_set):
	list_of_matches 	= [ ast_refined.match_character(c) 			for c in char_set]
	return ast_refined.alternative(*list_of_matches)


def complement_char_set(char_set):
	char_set = list(map( lambda x: x.encode('utf-8')[0] if isinstance(x,str) else x, char_set))
	return [ c  for c in range(NUM_CHARS) if c not in char_set]

def p_group(p):
	''' group 	:  terminal_sequence MINUS terminal_sequence group
				|  terminal_sequence MINUS terminal_sequence 
				|  terminal_sequence group
				|  terminal_sequence
				|  metachar			 group
				|  metachar			 '''
	#group is a special subproduction that does not return an ast 
	#but a list of int representing chars in utf-8 is responsability of
	#other production to produce a valid ast.
	if debug:
		print('try group',p.slice[1], p[1])
	if  len(p) >= 4:
		#the production includes a MINUS
		#in terminal sequence it may be packed multiple chars e.g. in case of a number
		#take the ones facing with MINUS and substitute from the others
		extra = [c for c in p[1][:-1]]+[c for c in p[3][1:]]
		p[1]  = p[1][-1]
		p[3]  = p[3][0]
		
		#produce a list of chars ranging from low to high (included)
		# NOTE: char is described by means of an int
		p[0] 			= set(chars_between(p[1],p[3]))
		p[0].update(extra)
		if len(p) ==5:
			# i.e. if we are in the case terminal_sequence MINUS terminal_sequence group
			# concatenate the list produced by the subgroup 
			p[0].update(p[4])

	else :
		#in the last cases all nonterminals carry a list of symbols
		#just pass them up
		p[0] 			= set(p[1])
		
		if len(p) > 2:
			# if we are in the case (CHAR|NUM) group
			# concatenate the list produced by the subrule group 
			p[0].update(p[2])

def p_terminal_sequence(p):
	''' terminal_sequence : CHAR
						  | NUM
						  | HEXA
						  | COMMA
						  '''

	if p.slice[1].type == 'NUM':
		p[0]   = [c for c in p[1]]
	else:
		# 'CHAR', 'COMMA','MINUS'
		p[0] = [p[1]]

def p_metachar(p):
	''' metachar : WHITESPACE
				 | WHITESPACE_COMPLEMENTED
				 | DIGIT
				 | DIGIT_COMPLEMENTED
				 | ALPHANUMERIC
				 | ALPHANUMERIC_COMPLEMENTED
				 '''

	if p.slice[1].type == 'WHITESPACE': #\s
		#from https://docs.python.org/3.8/library/re.html
		#For Unicode (str) patterns:
		#Matches Unicode whitespace characters (which includes [ \t\n\r\f\v], and also many other characters, 
		# for example the non-breaking spaces mandated by typography rules in many languages). 
		#If the ASCII flag is used, only [ \t\n\r\f\v] is matched.
		#
		#or 8-bit (bytes) patterns:
		#Matches characters considered whitespace in the ASCII character set; this is equivalent to [ \t\n\r\f\v].
		#	 and https://docs.microsoft.com/en-us/cpp/c-language/escape-sequences?view=vs-2019
		space_set = [' ','\t','\n','\r','\f','\v']
		p[0] 	  = space_set
	elif p.slice[1].type == 'WHITESPACE_COMPLEMENTED': #\S
		space_set = [' ','\t','\n','\r','\f','\v']
		p[0] 	  = complement_char_set(space_set)
	elif p.slice[1].type == 'DIGIT': #\d
		digit_set = chars_between('0','9')
		p[0] 	  = digit_set
	elif p.slice[1].type == 'DIGIT_COMPLEMENTED': #\D
		digit_set = chars_between('0','9')
		p[0] 	  = complement_char_set(digit_set)
	elif p.slice[1].type == 'ALPHANUMERIC': #\w
		alphanum_set = chars_between('0','9')+chars_between('a','z')+chars_between('A','Z')+['_']
		p[0] 	  = alphanum_set
	elif p.slice[1].type == 'ALPHANUMERIC_COMPLEMENTED': #\W
		alphanum_set = chars_between('0','9')+chars_between('a','z')+chars_between('A','Z')+['_']
		p[0] 	  = complement_char_set(alphanum_set)
	else:

		raise Exception(f'problem with {p}')

	
def chars_between(a,b):
	a				= a.encode('utf-8')[0] if isinstance(a,str) else a
	b				= b.encode('utf-8')[0] if isinstance(b,str) else b
	low  			= min(a, b)
	high 			= max(a, b)
	#produce a list of chars ranging from low to high (included)
	# NOTE: char is described by means of an int
	return 			[c for c in range(low,high+1)]

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
	raise Exception("Syntax error")

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
	from helper import normalize_regex_input
	tmp = normalize_regex_input(data)
	ast 		= parser.parse(tmp)

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

	try:
		data 		= 'r12ax\\1'
		ast 		= to_ir(data)
		assert False
	except Exception as e:
		pass

	try:
		data 		= 'r(?P=ciao)'
		ast 		= to_ir(data)
		assert False
	except Exception as e:
		pass
	
	regex_string        = '(([RKX]{2}?)(.)([STX]))'
	regex_string = normalize_regex_input(regex_string)
	assert regex_string == '(([RKX]{2})(.)([STX]))'

	regex_string        = '(([RKX]{2,}?)(.)([STX]))'
	regex_string = normalize_regex_input(regex_string)
	assert regex_string == '(([RKX]{2,})(.)([STX]))'

	regex_string        = '(([RKX]{,2}?)(.)([STX]))'
	regex_string = normalize_regex_input(regex_string)
	assert regex_string == '(([RKX]{,2})(.)([STX]))'

	regex_string        = '(([RKX]{,2})/(.)([STX]))'
	regex_string = normalize_regex_input(regex_string)
	assert regex_string == '(([RKX]{,2})/(.)([STX]))'
