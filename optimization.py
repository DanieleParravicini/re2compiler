import ir
import ir_re2coprocessor
import itertools
import pprint
from helper import reverse

def pretty_printer(dictionary):
	pprint.PrettyPrinter(indent=4).pprint(dictionary)

def eliminate_nops(start_node):
	#eliminate nop used during construction
	still_a_nop = True
	while(still_a_nop):
		still_a_nop = False
		nodes = start_node.getNodes()
		for node in nodes:
			for i in range(len(node.children)):
				if isinstance(node.children[i] , ir.PlaceholderNop):
					node.replace(node.children[i], node.children[i].children[0])
					still_a_nop = True
					
	if isinstance(start_node, ir.PlaceholderNop):
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
				if ( isinstance(node.children[i] , ir.Jmp) and 
					 isinstance(node.children[i].children[0] , ir.Jmp) ):
					node.replace(node.children[i], ir.Jmp(node.children[i].children[0].children[0]))
					something_changed = True
		if (isinstance(start_node , ir.Jmp) and 
			isinstance(start_node.children[0] , ir.Jmp)):
		   start_node = start_node.children[0]
		   something_changed = True
	
	return start_node

def enhance_splits(start_node, debug=False):
	# enhance splits
	
	#collect split
	nodes = start_node.getNodes()
	father = start_node.get_anchestors()

	split_nodes = list(filter(lambda x: isinstance(x, ir.Split), nodes))
	
	double_fathers = []
	for child in father:
		if len(father[child]) >= 2:
			double_fathers.append(child)
	if not( start_node in double_fathers):
		double_fathers.append(start_node)
	if debug:
		print('childrens')
		pretty_printer(children)
		print('fathers')
		pretty_printer(father)
		print('double fathers')
		pretty_printer(double_fathers)
	#collect each split and its directly connected split for further processing.
	#This is a first step of an iterative substitution of children with their fathers 
	# NOTE: only split with two or one incoming arrows stop the recursive substition.
	# D   E
	#  \ /
	#	A
	#  / \	
	# B   C 
	# expected result.
	# A -> A
	# B -> A
	# C -> A
	# D -> D
	# E -> E
	split_anchestor = {}
	for node in split_nodes:
		#if that node has not already been considered add itself as its topmost split
		if not( node in split_anchestor ):
			split_anchestor[node] = node
		#then consider all its child and set <node> as their split_anchestor
		directly_connected_splits = filter(lambda x: isinstance(x,ir.Split) and not(x in double_fathers) , node.children)
		for connected_split in directly_connected_splits :
			split_anchestor[connected_split] = split_anchestor[node]
	
	#iterative substitution till fixed point.
	something_changed = True
	while something_changed :
		something_changed = False
		for node in split_nodes:
			directly_connected_splits = filter(lambda x: isinstance(x,ir.Split) and not(x in double_fathers), node.children)
			for connected_split in directly_connected_splits :
				if not( split_anchestor[connected_split] == split_anchestor[node]):
					something_changed = True
					split_anchestor[connected_split] = split_anchestor[node]
	# In the end we have a map from each split to its 'group'
	# invert mapping split->split_group to split_group -> split
	split_group_to_splits = reverse(split_anchestor)
	if debug:
		print('split->group') 
		pretty_printer(split_anchestor)
		print('group->split')
		pretty_printer(split_group_to_splits)
	#now we can manipulate the code so that splits are all parallel
	i = 0
	for split_anchestor in split_group_to_splits:
		#ignore unoptimizable splits
		if len(split_group_to_splits[split_anchestor]) == 1:
			continue
		#take all splits related to that group
		splits = split_group_to_splits[split_anchestor]
		#take all their children ignoring splits which belong to the group
		all_children = list(itertools.chain(*[ s.children for s in splits]))
		all_children = list(filter(lambda x: x not in splits, all_children))
		#eliminate splits from father
		for s in splits:
			for c in s.children:
				father[c].remove(s)
		
		#organize all children in a well shaped tree
		while len(all_children)>=2:
			#print(len(all_children))
			option0 = all_children.pop(0)
			option1 = all_children.pop(0)
			split   = ir.Split(option0, option1)
			#update father relationship
			#pretty_printer(father)
			if not( option0 in father.keys()):
				father[option0] = []
			
			father[option0].append(split)
			if not( option1 in father.keys()):
				father[option1] = []
			father[option1].append(split)
			all_children.append(split)
		#tree root is new_split_anchestor
		new_split_anchestor = all_children[0]

		if(split_anchestor == start_node):
			start_node = new_split_anchestor

		if split_anchestor in father:
			for f in father[split_anchestor]:
				f.replace(split_anchestor,new_split_anchestor )
			#update father relationship
			for f in father:
				if split_anchestor in father[f]:
				   father[f].remove(split_anchestor)
				   father[f].append(new_split_anchestor)
		if debug:
			with open('debug'+str(i)+'.dot', 'w', encoding="utf-8") as f:
				f.write('digraph{\n')
				start_node.navigate(save_dotty(f))
				f.write('\n}')
		i+=1
	return start_node

def save_dotty(fout):
	def save_dotty_action(x):
		fout.write( x.dotty_str() )

	return save_dotty_action



def check_infinite_loops(start_node :ir.IrInstr):
	def collect_reachable_without_match(reachable_from_without_match):
		
		def action_collect_reachable_without_match(x):
			
			if not( x in reachable_from_without_match.keys()):
				reachable_from_without_match[x] = []
				if not ( isinstance(x, ir.Match) or 
				         isinstance(x, ir.Match_any) ) :
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
	a = ir.Match('a')
	b = ir.Match('b')
	nop   = ir.PlaceholderNop()
	start = ir.Split(a,nop)
	split = ir.Split(start, b)
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
	
	nop   = ir.PlaceholderNop()
	start = ir.Jmp(nop)
	jmp   = ir.Jmp(start)
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


	
	