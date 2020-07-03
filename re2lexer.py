import ply.lex as lex

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
'CHAR',
)

# Regular expression rules for simple tokens
def t_ESCAPED(t):
	r'\\[\\*+()?.]'
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
	t.value = t.value.encode('utf-8')[0]
	return t


# Error handling rule
def t_error( t):
	print("Illegal character '%s'" % t.value[0], 'pos', t)
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

	