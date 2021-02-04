import ply.lex as lex
# For more information on ply look at https://www.dabeaz.com/ply/ply.html
# List of token names.   This is always required
tokens = (
'ANYCHAR',
'WHITESPACE',
'ESCAPED',
'HEXA',
'PLUS',
'TIMES',
'OPT',
'OR',
'LPAR',
'RPAR',
'LSPAR',
'RSPAR',
'MINUS',
'HAT',
'CHAR',
)

# Regular expression rules for simple tokens
# From docs: " When building the master regular expression, rules are added in the following order:
# 	1) All tokens defined by functions are added in the same order as they appear in the lexer file.
#	2) Tokens defined by strings are added next by sorting them in order of decreasing 
# 	   regular expression length (longer expressions are added first).
# Without this ordering, it can be difficult to correctly match certain types of
#  tokens. For example, if you wanted to have separate tokens for "=" and "==", 
#  you need to make sure that "==" is checked first. By sorting regular expressions 
# in order of decreasing length, this problem is solved for rules defined as strings. 
# ***For functions, the order can be explicitly controlled since rules appearing first are checked first*** "
# THIS AVOIDS AMBIGUITY!!
def t_ESCAPED(t):
	r'\\[\\*+()?.\[\]\-\^]'
	#Adds the possibility to escape special characters.
	# Note that \ has to be escaped as well inside python re so \\ stands for \ 
	# consequently the re matches a \ followed by one of the following: '\','*','+','(',')','?','.','[',']','-', or ^ .
	# Moreover note that type has been changed to 'CHAR' 
	t.type 	= 'CHAR'
	t.value = t.value[1:]
	return t

def t_WHITESPACE(t):
	r'\\s'
	return t

def t_LPAR(t):
	r'\('
	return t

def t_RPAR(t):
	r'\)'
	return t

def t_LSPAR(t):
	r'\['
	return t

def t_RSPAR(t):
	r'\]'
	return t

def t_MINUS(t):
	r'-'
	return t

def t_HAT(t):
	r'\^'
	return t

def t_OPT (t):
	r'\?'
	return t

def t_OR  (t):
	r'\|'
	return t

def t_ANYCHAR(t):
	r'\.'
	return t

def t_PLUS(t):
	r'\+'
	return t

def t_TIMES(t):
	r'\*'
	return t

def t_HEXA( t):
	r'\\x([0-9A-Fa-f][0-9A-Fa-f])'
	#print(t.value[2:])
	t.value = int(t.value[2:], 16)
	return t

def t_CHAR( t):
	r'[\x20-\x7F]'
	#Because Ascii printable character range is \u0020 - \u007f
	t.value = t.value.encode('utf-8')[0]
	return t


# Error handling rule
def t_error( t):
	print("Illegal character '%s'" % t.value[0], 'pos', t)
	raise Exception('Regex format error')

## Build the lexer
#def build( **kwargs):
#	self.lexer = lex.lex(module=self, **kwargs)
#
## Test it output
#def test(self, data):
#	self.lexer.input(data)
#	for tok in self.lexer:
#		print(tok)
#
lexer = lex.lex()

if __name__ == "__main__":
	data = "((a|b)*c?e)+"
	# Give the lexer some input
	lexer.input(data)
	#the lexer will tokenize the inputs
	for tok in lexer:
		print(tok)

	