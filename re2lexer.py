import ply.lex as lex

# List of token names.   This is always required
tokens = (
'ANYCHAR',
'CHAR',
'WHITESPACE',
'HEXA',
'PLUS',
'TIMES',
'OPT',
'OR',
'LPAR',
'RPAR',
)

# Regular expression rules for simple tokens
t_PLUS    		= r'\+'
t_TIMES   		= r'\*'
t_LPAR    		= r'\('
t_RPAR	  		= r'\)'
t_OPT     		= r'\?'
t_OR      		= r'\|'
t_WHITESPACE    = r'\\s'
t_ANYCHAR      = r'\.'

# A regular expression rule with some action code
def t_CHAR( t):
	r'[a-zA-Z0-9]'
	t.value = t.value.encode('utf-8')[0]
	return t

def t_HEXA( t):
	r'\\x([0-9A-Fa-f][0-9A-Fa-f])'
	#print(t.value[2:])
	t.value = int(t.value[2:], 16)
	return t

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error( t):
	print("Illegal character '%s'" % t.value[0])
	raise Exception('Regex format error')

## Build the lexe
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
	for tok in lexer:
		print(tok)

	