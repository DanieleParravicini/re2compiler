def reverse(dictionary):
	revdict = {}
	for k, v in dictionary.items():
		if isinstance(v, list):
			for e in v:
				revdict.setdefault(e, []).append(k)
		else:
			revdict.setdefault(v, []).append(k)
	return revdict

def pcre_to_python(regex):
	
	#remove \ and \
	start_pcre = regex.find( "/")
	end_pcre   = regex.rfind("/")
	flags = regex[end_pcre+1:]
	
	if start_pcre >= 0 and end_pcre >= 0:
		regex = regex[start_pcre+1:end_pcre]
	
	if end_pcre != -1 and flags.strip() != '':
		raise Exception('Flags not supported')
	regex = regex.replace("\\/", "/")
	
	#substitute escape seq.
	return regex 

def normalize_regex_input(regex):
	#remove lazy operators -> (+|*|?|{\d+(,(\d+)?)?})?
	# infos @: https://www.regular-expressions.info/refrepeat.html
	regex = regex.replace("+?", "+")
	regex = regex.replace("*?", "*")
	regex = regex.replace("??", "?")
	regex = regex.replace("??", "?")
	
	import re
	regex = re.sub(r"\{(\d+),(\d+)\}\?", r"{\1,\2}", regex)
	regex = re.sub(r"\{(\d+)(|,)\}\?", r"{\1\2}"   , regex)
	regex = re.sub(r"\{(|,)(\d+)\}\?", r"{\1\2}"   , regex)
	#what about possessive operators? -> (+|*|?)+

	regex = regex.replace('(?:','(') #A non-capturing version of regular parentheses. 
	if re.search('\(\?[aiLmsux](-[imsx])?:', regex):
		raise Exception('subflags are not supported')
	if re.search('\(\?P=?', regex):
		raise Exception('Named group or backreference are not supported')
	if re.search('\(\?#', regex):
		raise Exception('Comments are not supported')
	if re.search('\(\?[=!<]', regex):
		raise Exception('Positive/Negative look ahead/behind are not supported')
	if re.search(r'\\\d+', regex):
		raise Exception('Group identification not supported')
	if re.search(r'\(\?\(', regex):
		raise Exception('Conditional not supported')
	
	return regex