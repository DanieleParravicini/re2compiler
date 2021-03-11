
debug = False
from frontend_pythonre import to_ir as pythonre_to_ir



def to_ir(data=None, no_postfix=False,no_prefix=False,dotast=None):
	#remove \ and \
	start 	= data.find( "/")
	end 	= data.rfind("/")
	data = data[start+1:end]
	#remove lazy operators
	if "+?" in data:
		print("substituting +? with +")
		data = data.replace("+?", "+")
	if "*?" in data:
		print("substituting *? with *")
		data = data.replace("*?", "*")
	#substitute escape seq.
	if "\/" in data:
		print("substituting \/ with /")
		data = data.replace("\/", "/")

	return  pythonre_to_ir(data)

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