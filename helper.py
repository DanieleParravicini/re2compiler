def reverse(dictionary):
	revdict = {}
	for k, v in dictionary.items():
		if isinstance(v, list):
			for e in v:
				revdict.setdefault(e, []).append(k)
		else:
			revdict.setdefault(v, []).append(k)
	return revdict