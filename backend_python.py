import ir_python

def simplify_jumps_backend(instr_list):
	#eliminate useless jumps
	#a) 1:jmp(2) -> 2:xxx

	def decrement_target_pc(i, instr_list):
		for j in range( len(instr_list)):
			if (isinstance(instr_list[j], ir_python.Jmp) 
				and	instr_list[j].children[0] == instr_list[i]): 
					instr_list[j].children[0] = instr_list[i+1]
			elif (isinstance(instr_list[j], ir_python.Split)): 
				if( instr_list[j].children[0] == instr_list[i]): 
					instr_list[j].children[0] = instr_list[i+1]
				if( instr_list[j].children[1] == instr_list[i]): 
					instr_list[j].children[1] = instr_list[i+1]

		return instr_list
	
	something_changed = True
	while something_changed:
		something_changed = False
		i = 0
		while i < len(instr_list):
			if (    isinstance(instr_list[i] , ir_python.Jmp) 
					and	instr_list.index(instr_list[i].children[0]) == i+1 ):
					instr_list = decrement_target_pc(i, instr_list)
					del instr_list[i]
					something_changed = True
			else:
			 	i+=1
				
	
	return instr_list
def code_gen(ir):
	#you know that code_gen does not change the position of nodes 
	nodes = ir.getNodes()
	node_generated = [ n._code_gen(i) for i, n in enumerate(nodes)] 

	for j in range(len(nodes)):
		for i in range(len(nodes[j].children)):
			c 								= nodes[j].children[i]
			index_child 					= nodes.index(c)
			node_generated[j].children[i] 	= node_generated[index_child]

	return node_generated

def to_code(ir, O1=False, dotcode=None, o=None):
	ir.setup('ir_python_codegen')
	list_istr = code_gen(ir)
	
	if O1:
		list_istr = simplify_jumps_backend(list_istr)
	
	if(dotcode is not None):
		with open(dotcode, 'w', encoding="utf-8") as f:
			dot_content = 'digraph {\n'+"".join([instr.dotty_str() for instr in list_istr ])+'}'
			f.write(dot_content)

	if(o is not None):
		print("WARNING, this backend does not support output code writing.")

	return list_istr[0]