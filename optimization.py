import ir_lower
import ir_re2coprocessor
import itertools

def eliminate_nops(start_node):
	#eliminate nop used during construction
	still_a_nop = True
	while(still_a_nop):
		still_a_nop = False
		nodes = start_node.getNodes()
		for node in nodes:
			for i in range(len(node.children)):
				if isinstance(node.children[i] , ir_lower.PlaceholderNop):
					node.replace(node.children[i], node.children[i].children[0])
					still_a_nop = True
					
	if isinstance(start_node, ir_lower.PlaceholderNop):
		return start_node.children[0]
	else:
		return start_node

def simplify_jumps(start_node):
	#eliminate useless jumps
	#a) 1:match(a) -> 2:jmp(3)-> 3:jmp(7)
	

	something_changed = True
	while something_changed:
		something_changed = False
		nodes = start_node.getNodes()
		for node in nodes:
			for i in range(len(node.children)):
				if ( isinstance(node.children[i] , ir_lower.Jmp) and 
				     isinstance(node.children[i].children[0] , ir_lower.Jmp) ):
					node.replace(node.children[i], ir_lower.Jmp(node.children[i].children[0].children[0]))
					something_changed = True
		if (isinstance(start_node , ir_lower.Jmp) and 
		    isinstance(start_node.children[0] , ir_lower.Jmp)):
		   start_node = start_node.children[0]
		   something_changed = True
	
	return start_node

def reverse(dictionary):
	revdict = {}
	for k, v in dictionary.items():
		if isinstance(v, list):
			for e in v:
				revdict.setdefault(e, []).append(k)
		else:
			revdict.setdefault(v, []).append(k)
	return revdict

def enhance_splits(start_node):
	# enhance splits
	split_to_connected_split = {}
	
	#collect split
	nodes = start_node.getNodes()
	split_nodes = filter(lambda x: isinstance(x, ir_lower.Split), nodes)
	
	children = {}
	for n in nodes:
		if len(n.children)>0:
			children[n] = n.children

	father = reverse(children)
	double_fathers = []
	for child in father:
		if len(father[child]) > 2:
			double_fathers.append(child)

	#collect splits and directly connected fixed point.
	for node in split_nodes:
		if not( node in split_to_connected_split ):
			split_to_connected_split[node] = node
	
		directly_connected_splits = filter(lambda x: isinstance(x,ir_lower.Split) and not(x in double_fathers) , node.children)
		for connected_split in directly_connected_splits :
			split_to_connected_split[connected_split] = split_to_connected_split[node]
	#iterative substitution till fixed point.
	something_changed = True
	while something_changed :
		something_changed = False
		for node in split_nodes:
			directly_connected_splits = filter(lambda x: isinstance(x,ir_lower.Split) and not(x in double_fathers), node.children)
			for connected_split in directly_connected_splits :
				if not( split_to_connected_split[connected_split] == split_to_connected_split[node]):
					something_changed = True
					split_to_connected_split[connected_split] = split_to_connected_split[node]
	#invert mapping split->split_group to split_group -> split
	split_group_to_splits = reverse(split_to_connected_split)
	#print(split_group_to_splits)

	for split_group in split_group_to_splits:
		if len(split_group_to_splits[split_group]) == 1:
			continue

		splits = split_group_to_splits[split_group]
		all_children = list(itertools.chain(*[ s.children for s in splits]))
		all_children = list(filter(lambda x: not isinstance(x,ir_lower.Split) ,all_children))
		#print(all_children)

		while len(all_children)>=2:
			#print(len(all_children))
			option0 = all_children.pop(0)
			option1 = all_children.pop(0)
			split   = ir_lower.Split(option0, option1)

			all_children.append(split)

		new_split_group = all_children[0]

		if(split_group == start_node):
			start_node = new_split_group
		
		for f in father[split_group]:
			f.replace(split_group,new_split_group )

	return start_node

def simplify_jumps_backend(instr_list):
	#eliminate useless jumps
	#a) 1:jmp(2) -> 2:xxx

	def decrement_target_pc(i, instr_list):
		for j in range( len(instr_list)):
			if (isinstance(instr_list[j], ir_re2coprocessor.Jmp) 
				and	instr_list[j].data > i): 
					instr_list[j].data-=1
			elif (isinstance(instr_list[j], ir_re2coprocessor.Split) 
				and	instr_list[j].data > i): 
					instr_list[j].data-=1

		return instr_list
	
	def decrement_pc(i, instr_list):
		for j in range(i+1, len(instr_list)):
			instr_list[j].pc = instr_list[j].pc - 1
		return instr_list

	
	something_changed = True
	while something_changed:
		something_changed = False
		i = 0
		while i < len(instr_list):
			if (    isinstance(instr_list[i] , ir_re2coprocessor.Jmp) 
					and	instr_list[i].data == i+1 ):
					instr_list = decrement_target_pc(i, instr_list)
					instr_list = decrement_pc(i,instr_list)
					del instr_list[i]
					something_changed = True
			else:
			 	i+=1
				
	
	return instr_list

def check_infinite_loops(start_node :ir_lower.IrInstr):
	def collect_reachable_without_match(reachable_from_without_match):
		
		def action_collect_reachable_without_match(x):
			
			if not( x in reachable_from_without_match.keys()):
				reachable_from_without_match[x] = []
				if not isinstance(x, ir_lower.Match):
					reachable_from_without_match[x] = x.children
							

		return action_collect_reachable_without_match

			
	reachable_from_without_match = {}
	fixed_point_not_reached      = True
	action = collect_reachable_without_match(reachable_from_without_match)
	start_node.navigate(action)

	
	while fixed_point_not_reached:
		fixed_point_not_reached = False

		for x in reachable_from_without_match:
			to_add = []
			for reachable in reachable_from_without_match[x]:
				if reachable in reachable_from_without_match:
					for reachable_plus_1 in reachable_from_without_match[reachable]:
						if not (reachable_plus_1 in to_add or reachable_plus_1 in reachable_from_without_match[x] ):
							fixed_point_not_reached = True
							to_add.append(reachable_plus_1) 
			
			reachable_from_without_match[x] = [ *reachable_from_without_match[x] , *to_add]
		
		#print('fixed?',fixed_point_not_reached)
	
	#print('info:', reachable_from_without_match)
	for node in reachable_from_without_match:
		if node in reachable_from_without_match[node]:
			raise Exception("Error: there's a looping path without a character to be matched")

	return True





if __name__ == "__main__":
	a = ir_lower.Match('a')
	b = ir_lower.Match('b')
	nop   = ir_lower.PlaceholderNop()
	start = ir_lower.Split(a,nop)
	split = ir_lower.Split(start, b)
	nop.append(split)

	#nodes = start.getNodes()
	#print('digraph{')
	#for n in nodes:
	#	print(n.dotty_str())
	#print('}')
	
	try:
		check_infinite_loops(start)
		assert False, 'Test check infinite loops failed'
	except AssertionError:
		print('KO')
	except Exception :
		print('OK')
	
	nop   = ir_lower.PlaceholderNop()
	start = ir_lower.Jmp(nop)
	jmp   = ir_lower.Jmp(start)
	nop.append(jmp)

	#nodes = start.getNodes()
	#print('digraph{')
	#for n in nodes:
	#	print(n.dotty_str())
	#print('}')
	
	try:
		check_infinite_loops(start)
		assert False, 'Test check infinite loops failed'
	except AssertionError:
		print('KO')
	except Exception :
		print('OK')


	
	