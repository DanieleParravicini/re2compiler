import ir
import itertools
import pprint
import traceback
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

def get_split_groups(start_node, debug=False):
	'''collect each split and its directly connected split for further processing.
	This is a first step of an iterative substitution of children with their fathers 
	 NOTE: only split with two or one incoming arrows stop the recursive substition.
	 D   E
	  \ /
		A
	  / \	
	 B   C 
	 expected result.
	 A -> A
	 B -> A
	 C -> A
	 D -> D
	 E -> E'''
	nodes 			= start_node.getNodes()
	father 			= start_node.get_ancestors()
	split_nodes 	= list(filter(lambda x: isinstance(x, ir.Split), nodes))
	
	#the start node is always a multifather as this avoid cycles during fixed point
	#operation that follows
	multi_fathers 	= [start_node]
	for child in father:
		if len(father[child]) >= 2:
			multi_fathers.append(child)
	
	if debug:
		print('fathers')
		pretty_printer(father)
		print('double fathers')
		pretty_printer(multi_fathers)
	
	#create split ancestor relationship
	split_ancestor = {}
	#iterative substitution till fixed point.
	something_changed = True
	while something_changed :
		something_changed = False

		for node in split_nodes:
			#if that node has not already been considered add itself as its topmost split
			if not( node in split_ancestor ):
				split_ancestor[node] = node
			#then consider all its child and set <node> as their split_ancestor
			directly_connected_splits = filter(lambda x: isinstance(x,ir.Split) and not(x in multi_fathers), node.children)
			for connected_split in directly_connected_splits :
				if connected_split not in split_ancestor or  split_ancestor[connected_split] != split_ancestor[node]:
					something_changed = True
					split_ancestor[connected_split] = split_ancestor[node]

	# In the end we have a map from each split to its 'group'
	# invert mapping split->split_group to split_group -> split
	split_groups = reverse(split_ancestor)
	if debug:
		print('split->group') 
		pretty_printer(split_ancestor)
		print('group->split')
		pretty_printer(split_groups)
	return split_groups, father

def remove_from_tree(father, *l):
	for e in l:
		#0. it may be the root node so it has no father :(
		if e in father:
			#1. take advantage of father relationship
			#   to eliminate incoming connection
			for f in father[e]:
				if e in f.children:
					f.children.remove(e)
			del father[e]	
		#2. consider e's children 
		#   remove father child-relationship
		for c in e.children:
			# child may be already deleted from father relationship
			# if a sibling has already been eliminated
			if c in father and e in father[c]: 
				father[c].remove(e)
		#3. other missing connections due to improper tree 
		# manipulations
		for k in father:
			if e in father[k]: 
				father[k].remove(e)

def is_a_split_tree(group_of_connected_splits):
	'''it is a tree of split if non-split children are leaves'''
	for s in group_of_connected_splits:
		has_a_non_split_child = (not isinstance(s.children[0], ir.Split) or
								 not isinstance(s.children[1], ir.Split)	)
		if has_a_non_split_child:
			for sub_split in filter(lambda x: isinstance(x, ir.Split) , s.children):
				has_a_non_split_child = (not isinstance(sub_split.children[0], ir.Split) or
								 		 not isinstance(sub_split.children[1], ir.Split)	)
				if has_a_non_split_child:
					return False
	return True

def remove_from_father(father,e):
	for c in father[e].children:
		if e in father[c]:
			father.remove(e)

def get_equivalence_classes(nodes):
	tmp = list(nodes)
	i=0
	while (i < len(tmp)):

		equiv 	  	= [tmp[i]]
		j = i+1
		while (j < len(tmp)):
			if( tmp[i].equiv(tmp[j])):
				equiv.append(tmp[j])
				del tmp[j]
			else:
				j+=1

		del tmp[i]
		yield equiv
		i+=1

def enhance_splits(start_node, debug=True):
	split_groups, father= get_split_groups(start_node)
	#collect split
	#now we can manipulate the code so that splits are arranged in a balanced tree
	count = 0
	if debug:
		with open('debug'+str(count)+'.dot', 'w', encoding="utf-8") as f:
			f.write('digraph{\n')
			start_node.navigate(save_dotty(f))
			f.write('\n}')
	count += 1
			
	for split_root, group in split_groups.items():
		#ignore non-optimizable splits i.e. splits groups that contain only a split
		if len(group) == 1:
			continue
		
		#take all their children ignoring splits which belong to the group
		all_children = list(itertools.chain(*[ s.children for s in group]))
		all_children = list(filter(lambda x: x not in group, all_children))

		if(len(all_children)-1 == len(group) and is_a_split_tree(group) ):
			#no need for optimization
			#	print(split_root)
			#	pretty_printer(group)
			continue
		#organize all children in a well shaped tree
		new_split_root = create_a_balanced_tree_of_splits(all_children,father)
		
		if(split_root == start_node):
			start_node = new_split_root

		#update father relationship
		replace_in_tree(split_root, new_split_root, father)

		#eliminate old splits from tree and father
		for s in group:
			remove_from_tree(father,s)

		if debug:
			with open('debug'+str(count)+'.dot', 'w', encoding="utf-8") as f:
				f.write('digraph{\n')
				start_node.navigate(save_dotty(f))
				f.write('\n}')
		count+=1
		
		split_groups, father = get_split_groups(start_node)
	return start_node

def merge_redundant_parallel(start_node, debug=False):
	# 		|			|
	#     SPLIT  =>     a
	#	   / \		   / \
	#     a   a      ... ***
	#     |   |
	#	 ... ***

	something_changed 	= True 
	count				= 0
	#repeat till fixed point
	while(something_changed):
		something_changed 	 = False
		split_groups, father = get_split_groups(start_node)
		#collect split
		#	now we can manipulate the code so that splits+equivalent instructions are merged 
		for split_root, g in split_groups.items():
			
			#take all children (ignoring splits) that belong to the group
			all_children 	= list(itertools.chain(*[ s.children for s in g]))
			#all_children 	= list(filter(lambda x:  not isinstance(x,ir.Split) , all_children)) the following should be equal
			all_children 	= list(filter(lambda x:  not x in g , all_children))
			all_non_reentrant_children =  list(filter(lambda x: len(father[x]) == 1, all_children))
			#for the moment we do not target multifather
			others					   =  list(filter(lambda x: len(father[x]) > 1 , all_children))
			#avoid naive cases where not posible to perform optimizations
			if len(all_non_reentrant_children)<=1:
				continue
			#iteratively select equivalent ones
			for equiv in get_equivalence_classes(all_non_reentrant_children):
				
				new_equiv = merge(equiv, father)
				if not new_equiv:
					continue
				# if all went smoothly remove equivalent instances from
				#  all_non_reentrant_children and update father
				 
				for e in equiv:
					
					if e != new_equiv:
						remove_from_tree(father, e)
						all_non_reentrant_children.remove(e)
				
				something_changed = True

				if debug:
					print('found equivalent', equiv )
					print('father')
					pretty_printer(father) 
					print('equivalence class:', equiv ,'->', new_equiv)
					with open('debug'+str(count)+'.dot', 'w', encoding="utf-8") as f:
						f.write('digraph{\n')
						start_node.navigate(save_dotty(f))
						f.write('\n}')
					count +=1

			# After all equivalence classes have been considered and possibly merged, 
			# reshape children in a balanced tree of splits
			new_split_root = create_a_balanced_tree_of_splits(all_non_reentrant_children+others, father)
			if debug:
				with open('debug'+str(count)+'.dot', 'w', encoding="utf-8") as f:
					f.write('digraph{\n')
					start_node.navigate(save_dotty(f))
					f.write('\n}')
				count +=1
			# if necessary exchange root node
			if(split_root == start_node):
				start_node = new_split_root

			#update father relationship
			replace_in_tree(split_root, new_split_root, father)

			#eliminate intermediate splits.
			for s in g:
				remove_from_tree(father,s)

			if debug:
				with open('debug'+str(count)+'.dot', 'w', encoding="utf-8") as f:
					f.write('digraph{\n')
					start_node.navigate(save_dotty(f))
					f.write('\n}')
				count +=1

			split_groups, father = get_split_groups(start_node)

	return start_node

def merge(equiv,father, debug=False):
	an_equiv = equiv[0]

	#Is there any equivalent instruction?
	#instructions with more than a child (Splits) are ignored
		
	if len(equiv) != 1 :
		if 	 len(an_equiv.children) == 0 :
			#In case equivalent nodes have no (0) children (Accept/Reject/ecc..), we can simply collapse them in a single instruction
			#In that case in particular we have nothing to do since in equiv[0] holds already the correct value.
			return an_equiv
		elif len(an_equiv.children) == 1 :
			#now we substitute other instructions with a an_equiv followed
			# by parallel paths that continue from children

			# in this case we assume that those instructions continue with 
			# just one other instruction (already checked. recheck to be sure)
			assert len(list(filter(lambda x: len(x.children)>1, equiv))) ==0
			continuations = list(map(lambda x: x.children[0],   equiv))
			#disconnect from split the leaves of the tree (i.e. their children)
			# remember: for the moment we do not target multifather
			for f, c in zip(equiv, continuations):
				f.children.remove(c)
				father[c].remove(f)

			#create a tree of instructions
			tree 		  = create_a_balanced_tree_of_splits(continuations,father)
			an_equiv.append(tree)
			father[tree]  = [an_equiv]
			#append the tree of continuation below the equiv instruction
			#father[equiv_inst].remove(equiv_inst)
			return an_equiv
	
	#signal not possible to merge
	return None

def replace_in_tree(old, new, father):
	if old in father:
		for f in father[old]:
				f.replace(old,new )

		#update father relationship
		for f in father:
			if old in father[f]:
				father[f].remove(old)
				father[f].append(new)

def save_dotty(fout):
	def save_dotty_action(x):
		fout.write( x.dotty_str() )

	return save_dotty_action

def create_a_balanced_tree_of_splits(children, father= None):
	while len(children)>=2:
		#print(len(all_children))
		option0 = children.pop(0)
		option1 = children.pop(0)
		split   = ir.Split(option0, option1)
		#update father relationship
		#pretty_printer(father)
		if father :
			if not( option0 in father.keys()):
				father[option0] = []
			
			father[option0].append(split)

			if not( option1 in father.keys()):
				father[option1] = []
			father[option1].append(split)

		children.append(split)
	return children[0]
		

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
	for node, nodes_that_can_be_reached_without_match in reachable_from_without_match.items():
		if node in nodes_that_can_be_reached_without_match:
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
		exit()
	except AssertionError:
		print('KO')
		exit()
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
		exit()
	except AssertionError:
		print('KO')
		exit()
	except Exception :
		print('OK')

	
	for i in range(1,3):
		equiv 	= []
		for _ in range(i):
			
			ci 		= ir.Match('a') if i %2 ==0 else ir.Match_any()
			endi   	= ir.Accept()
			ci.append(endi)
			equiv.append(ci)

		start 	= create_a_balanced_tree_of_splits(equiv)
		with open('debug.dot', 'w', encoding="utf-8") as f:
					f.write('digraph{\n')
					start.navigate(save_dotty(f))
					f.write('\n}')

		try:
			res = merge_redundant_parallel(start 	)
			with open('debug1.dot', 'w', encoding="utf-8") as f:
					f.write('digraph{\n')
					start.navigate(save_dotty(f))
					f.write('\n}')
			assert res.equiv(ir.Match('a') if i %2 ==0 else ir.Match_any()) and len(res.children) == 1 and res.children[0].equiv(ir.Accept()) , 'Test merge_redundant_parallel failed'

			res = merge_redundant_parallel(res 		)
			
			assert res.equiv(ir.Match('a') if i %2 ==0 else ir.Match_any()) and len(res.children) == 1 and res.children[0].equiv(ir.Accept()) , 'Test merge_redundant_parallel failed'
			print('OK')
		except AssertionError :
			print('KO')
			traceback.print_exc()
			exit()
		except Exception :
			print('KO')
			traceback.print_exc()
			exit()

	for i in range(1,10):
		equiv 	= []
		for _ in range(i):
			
			ci 		= ir.Match('a') if i %2 ==0 else ir.Match_any()
			endi   	= ir.Accept()
			cj		= ir.Match('a')  if i %2 ==0 else ir.Match_any()
			endj	= ir.Accept()
			splitj  = ir.Split(endj,cj)
			cj.append(splitj)
			ci.append(endi)
			equiv.append(ci)
			equiv.append(cj)

		start 	= create_a_balanced_tree_of_splits(equiv)
		with open('debug.dot', 'w', encoding="utf-8") as f:
			f.write('digraph{\n')
			start.navigate(save_dotty(f))
			f.write('\n}')
		try:
			res = merge_redundant_parallel(start)
			assert not(res.equiv(ir.Match('a') if i %2 ==0 else ir.Match_any()) and len(res.children) == 1 and res.children[0].equiv(ir.Accept())), 'Test merge_redundant_parallel failed'

			res = merge_redundant_parallel(res 		)
			
			assert not(res.equiv(ir.Match('a') if i %2 ==0 else ir.Match_any()) and len(res.children) == 1 and res.children[0].equiv(ir.Accept())) , 'Test merge_redundant_parallel failed'

			print('OK')
		except AssertionError :
			print('KO')
			traceback.print_exc()
			exit()
		except Exception :
			print('KO')
			traceback.print_exc()
			exit()
	#complex test: use real re and try to match using optimized and unoptimized version of the code.
	#detect any mismatch.
	REs = [
		"(((R|K|X)(R|K|X))?.(S|T|X))",
		"(S|T|X)(..)?(D|B|E|Z|X)",
		"(C|X).(D|B|N|B|X)(....)?(F|Y|X).(C|X).(C|X)",
		"(C|X)(.....?)?(C|X)(C|X)(S|X)(..)?(G|X).(C|X)(G|X)(....?)?(F|Y|W|X)(C|X)",
		"(C|X)(..(..)?)?(C|X)(...)?(L|I|V|M|F|Y|W|C|X)(........)?(H|X)(...(..)?)?(H|X)",
		"((L|I|V|M|F|E|Z|X)(F|Y|X)(P|X)(W|X)(M|X)(K|R|Q|Z|T|A|X))",
		"((L|X)(M|X)(A|X)(E|Z|Q|Z|X)(G|X)(L|X)(Y|X)(N|B|X))",
		"((R|X)(P|X)(C|X)(..........)?(C|X)(V|X)(S|X))",
		"(R|K|X)(...?)?(D|B|E|Z|X)(...?)?(Y|X)",
		".(G|X)(R|K|X)(R|K|X)",
		"(S|T|X).(R|K|X)",
		"(.(G|X)(R|K|X)(R|K|X))|((S|T|X).(R|K|X))",
		"((L|X)(M|X)(A|X)(E|Z|Q|Z|X)(G|X)(L|X)(Y|X)(N|B|X))|((R|X)(P|X)(C|X)(..........)?(C|X)(V|X)(S|X))",
		"((R|X)(P|X)(C|X)(..........)?(C|X)(V|X)(S|X))|((R|K|X)(...?)?(D|B|E|Z|X)(...?)?(Y|X))",
		"((L|X)(M|X)(A|X)(E|Z|Q|Z|X)(G|X)(L|X)(Y|X)(N|B|X))|((R|K|X)(...?)?(D|B|E|Z|X)(...?)?(Y|X))",
		"((L|X)(M|X)(A|X)(E|Z|Q|Z|X)(G|X)(L|X)(Y|X)(N|B|X))|((R|X)(P|X)(C|X)(..........)?(C|X)(V|X)(S|X))|((R|K|X)(...?)?(D|B|E|Z|X)(...?)?(Y|X))",
		"((R|X)(P|X)(C|X)(..........)?(C|X)(V|X)(S|X))|((R|K|X)(...?)?(D|B|E|Z|X)(...?)?(Y|X))|((S|T|X).(R|K|X))",
		"((R|K|X)(...?)?(D|B|E|Z|X)(...?)?(Y|X))|(.(G|X)(R|K|X)(R|K|X))|((S|T|X).(R|K|X))",
		"((C|X)(.....?)?(C|X)(C|X)(S|X)(..)?(G|X).(C|X)(G|X)(....?)?(F|Y|W|X)(C|X))|((C|X)(..(..)?)?(C|X)(...)?(L|I|V|M|F|Y|W|C|X)(........)?(H|X)(...(..)?)?(H|X))|((R|X)(P|X)(C|X)(..........)?(C|X)(V|X)(S|X))",
		"((C|X)(.....?)?(C|X)(C|X)(S|X)(..)?(G|X).(C|X)(G|X)(....?)?(F|Y|W|X)(C|X))|((C|X)(..(..)?)?(C|X)(...)?(L|I|V|M|F|Y|W|C|X)(........)?(H|X)(...(..)?)?(H|X))|((R|X)(P|X)(C|X)(..........)?(C|X)(V|X)(S|X))|(.(G|X)(R|K|X)(R|K|X))",
		"((C|X)(..(..)?)?(C|X)(...)?(L|I|V|M|F|Y|W|C|X)(........)?(H|X)(...(..)?)?(H|X))|((R|K|X)(...?)?(D|B|E|Z|X)(...?)?(Y|X))|(((R|X)(P|X)(C|X)(..........)?(C|X)(V|X)(S|X)))|(((L|X)(M|X)(A|X)(E|Z|Q|Z|X)(G|X)(L|X)(Y|X)(N|B|X)))",
		"((C|X).(D|B|N|B|X)(....)?(F|Y|X).(C|X).(C|X))|((C|X)(.....?)?(C|X)(C|X)(S|X)(..)?(G|X).(C|X)(G|X)(....?)?(F|Y|W|X)(C|X))|((C|X)(..(..)?)?(C|X)(...)?(L|I|V|M|F|Y|W|C|X)(........)?(H|X)(...(..)?)?(H|X))|(((L|X)(M|X)(A|X)(E|Z|Q|Z|X)(G|X)(L|X)(Y|X)(N|B|X)))"
	]

	inputs = [
		"MAFSAEDVLKEYDRRRRMEALLLSLYYPNDRKLLDYKEWSPPRVQVECPKAPVEWNNPPSEKGLIVGHFSGIKYKGEKAQASEVDVNKMCCWVSKFKDAMRRYQGIQTCKIPGKVLSDLDAKIKAYNLTVEGVEGFVRYSRVTKQHVAAFLKELRHSKQYENVNLIHYILTDKRVDIQHLEKDLVKDFKALVESAHRMRQGHMINVKYILYQLLKKHGHGPDGPDILTVKTGSKGVLYDDSFRKIYTDLGWKFTPL",
		"MSIIGATRLQNDKSDTYSAGPCYAGGCSAFTPRGTCGKDWDLGEQTCASGFCTSQPLCARIKKTQVCGLRYSSKGKDPLVSAEWDSRGAPYVRCTYDADLIDTQAQVDQFVSMFGESPSLAERYCMRGVKNTAGELVSRVSSDADPAGGWCRKWYSAHRGPDQDAALGSFCIKNPGAADCKCINRASDPVYQKVKTLHAYPDQCWYVPCAADVGELKMGTQRDTPTNCPTQVCQIVFNMLDDGSVTMDDVKNTINCDFSKYVPPPPPPKPTPPTPPTPPTPPTPPTPPTPPTPRPVHNRKVMFFVAGAVLVAILISTVRW",
		"MASNTVSAQGGSNRPVRDFSNIQDVAQFLLFDPIWNEQPGSIVPWKMNREQALAERYPELQTSEPSEDYSGPVESLELLPLEIKLDIMQYLSWEQISWCKHPWLWTRWYKDNVVRVSAITFEDFQREYAFPEKIQEIHFTDTRAEEIKAILETTPNVTRLVIRRIDDMNYNTHGDLGLDDLEFLTHLMVEDACGFTDFWAPSLTHLTIKNLDMHPRWFGPVMDGIKSMQSTLKYLYIFETYGVNKPFVQWCTDNIETFYCTNSYRYENVPRPIYVWVLFQEDEWHGYRVEDNKFHRRYMYSTILHKRDTDWVENNPLKTPAQVEMYKFLLRISQLNRDGTGYESDSDPENEHFDDESFSSGEEDSSDEDDPTWAPDSDDSDWETETEEEPSVAARILEKGKLTITNLMKSLGFKPKPKKIQSIDRYFCSLDSNYNSEDEDFEYDSDSEDDDSDSEDDC",
		"MYQAINPCPQSWYGSPQLEREIVCKMSGAPHYPNYYPVHPNALGGAWFDTSLNARSLTTTPSLTTCTPPSLAACTPPTSLGMVDSPPHINPPRRIGTLCFDFGSAKSPQRCECVASDRPSTTSNTAPDTYRLLITNSKTRKNNYGTCRLEPLTYGI",
		"MARPLLGKTSSVRRRLESLSACSIFFFLRKFCQKMASLVFLNSPVYQMSNILLTERRQVDRAMGGSDDDGVMVVALSPSDFKTVLGSALLAVERDMVHVVPKYLQTPGILHDMLVLLTPIFGEALSVDMSGATDVMVQQIATAGFVDVDPLHSSVSWKDNVSCPVALLAVSNAVRTMMGQPCQVTLIIDVGTQNILRDLVNLPVEMSGDLQVMAYTKDPLGKVPAVGVSVFDSGSVQKGDAHSVGAPDGLVSFHTHPVSSAVELNYHAGWPSNVDMSSLLTMKNLMHVVVAEEGLWTMARTLSMQRLTKVLTDAEKDVMRAAAFNLFLPLNELRVMGTKDSNNKSLKTYFEVFETFTIGALMKHSGVTPTAFVDRRWLDNTIYHMGFIPWGRDMRFVVEYDLDGTNPFLNTVPTLMSVKRKAKIQEMFDNMVSRMVTS",
		"MNAKYDTDQGVGRMLFLGTIGLAVVVGGLMAYGYYYDGKTPSSGTSFHTASPSFSSRYRY",
		"MRYTVLIALQGALLLLLLIDDGQGQSPYPYPGMPCNSSRQCGLGTCVHSRCAHCSSDGTLCSPEDPTMVWPCCPESSCQLVVGLPSLVNHYNCLPNQCTDSSQCPGGFGCMTRRSKCELCKADGEACNSPYLDWRKDKECCSGYCHTEARGLEGVCIDPKKIFCTPKNPWQLAPYPPSYHQPTTLRPPTSLYDSWLMSGFLVKSTTAPSTQEEEDDY",
		"MQNPLPEVMSPEHDKRTTTPMSKEANKFIRELDKKPGDLAVVSDFVKRNTGKRLPIGKRSNLYVRICDLSGTIYMGETFILESWEELYLPEPTKMEVLGTLESCCGIPPFPEWIVMVGEDQCVYAYGDEEILLFAYSVKQLVEEGIQETGISYKYPDDISDVDEEVLQQDEEIQKIRKKTREFVDKDAQEFQDFLNSLDASLLS",
		"MDSLNEVCYEQIKGTFYKGLFGDFPLIVDKKTGCFNATKLCVLGGKRFVDWNKTLRSKKLIQYYETRCDIKTESLLYEIKGDNNDEITKQITGTYLPKEFILDIASWISVEFYDKCNNIIINYFVNEYKTMDKKTLQSKINEVEEKMQKLLNEKEEELQEKNDKIDELILFSKRMEEDRKKDREMMIKQEKMLRELGIHLEDVSSQNNELIEKVDEQVEQNAVLNFKIDNIQNKLEIAVEDRAPQPKQNLKRERFILLKRNDDYYPYYTIRAQDINARSALKRQKNLYNEVSVLLDLTCHPNSKTLYVRVKDELKQKGVVFNLCKVSISNSKINEEELIKAMETINDEKRDV",
		"MYKMYFLKDQKFSLSGTIRINDKTQSEYGSVWCPGLSITGLHHDAIDHNMFEEMETEIIEYLGPWVQAEYRRIKG"
	]

	import emulate_execution as emu
	for r in REs:
		for i in inputs:
			try:
				emu.compile_and_run(r,i,O1=True, allow_prefix=True, double_check=True)
			except Exception :
				print(f'KO @{r,i}')
				traceback.print_exc()
				exit()
	