
debug = False
from frontend_pythonre import to_ir as pythonre_to_ir
from helper import pcre_to_python


def to_ir(data=None, no_postfix=False,no_prefix=False,dotast=None):
	return  pythonre_to_ir(pcre_to_python(data))

if __name__ == "__main__":
	
	

	def save_dotty(fout):
		def save_dotty_action(x):
			fout.write( x.dotty_str() )

		return save_dotty_action

	regex 		= '/[^a-zA-Z]\\-/'
	ir 			= to_ir(regex)
	
	with open('test.dot', 'w', encoding="utf-8") as f:
			f.write('digraph{\n')
			ir.navigate(save_dotty(f))
			f.write('\n}')
	input("Enter any key to continue")

	regex 	= '/r12ax\\-/'
	ir 		= to_ir(regex)

	with open('test.dot', 'w', encoding="utf-8") as f:
			f.write('digraph{\n')
			ir.navigate(save_dotty(f))
			f.write('\n}')
	input("Enter any key to continue")


	regex_string        = '/(([RKX]{2}?)(.)([STX]))/'
	regex_string = pcre_to_python(regex_string)
	assert regex_string == '(([RKX]{2}?)(.)([STX]))'

	regex_string        = '/(([RKX]{2,}?)(.)([STX]))/'
	regex_string = pcre_to_python(regex_string)
	assert regex_string == '(([RKX]{2,}?)(.)([STX]))'

	regex_string        = '/(([RKX]{,2}?)(.)([STX]))/'
	regex_string = pcre_to_python(regex_string)
	assert regex_string == '(([RKX]{,2}?)(.)([STX]))'

	regex_string        = '/(([RKX]{,2}?)\\/(.)([STX]))/'
	regex_string = pcre_to_python(regex_string)
	assert regex_string == '(([RKX]{,2}?)/(.)([STX]))'

	regex_string        = '(([RKX]{,2}?)(.)([STX]))'
	regex_string = pcre_to_python(regex_string)
	assert regex_string == '(([RKX]{,2}?)(.)([STX]))'