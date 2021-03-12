import ir_python
import ir as IR

def simplify_jumps_backend(instr_list):
	#eliminate useless jumps
	#a) 1:jmp(2) -> 2:xxx

	def substitute_i_with_iplus1(i, instr_list):
		for instr in instr_list:
			for c in range(len(instr.children)):
				if instr.children[c] == instr_list[i]: 
				   instr.children[c] = instr_list[i+1]
		
		return instr_list
	
	something_changed = True
	while something_changed:
		something_changed = False
		i = 0
		while i < len(instr_list):
			if (    isinstance(instr_list[i] , ir_python.Jmp) 
					and	instr_list.index(instr_list[i].children[0]) == i+1 ):
					instr_list = substitute_i_with_iplus1(i, instr_list)
					del instr_list[i]
					something_changed = True
			else:
			 	i+=1
				
	
	return instr_list

def add_jmp_if_necessary(list_ir_instr: list):
	#children 0 are the normal prosecution of each instructions so they reaside at pc+1
	#complex transformation may reuse some portion of the code that would be 
	#place fairly distant from current node. 
	#so in case of Splits that have children#0 way before/after in the depth first
	#search add an intermediate Jump.
	i = 0
	while( i < len(list_ir_instr)):
		n 		= list_ir_instr[i]

		if( isinstance(n, IR.Split) and (i+1==len(list_ir_instr) or not(n.children[0] is list_ir_instr[i+1])) ):
			
			inject_jmp		= IR.Jmp(n.children[0])
			n.replace( n.children[0], inject_jmp )
			list_ir_instr.insert(i+1, inject_jmp)
		i+=1
	return list_ir_instr

def code_gen(ir):
	#you know that code_gen does not change the position of nodes 
	list_ir_instr = ir.getNodes()

	add_jmp_if_necessary(list_ir_instr)

	node_generated = [ n._code_gen(i) for i, n in enumerate(list_ir_instr)] 

	for j in range(len(list_ir_instr)):
		for i in range(len(list_ir_instr[j].children)):
			c 								= list_ir_instr[j].children[i]
			index_child 					= list_ir_instr.index(c)
			node_generated[j].children[i] 	= node_generated[index_child]

	return node_generated

def to_code(ir, O1=False, dotcode=None, o=None):
	ir.setup('ir_python_codegen')
	list_instr = code_gen(ir)
	
	if O1:
		list_instr = simplify_jumps_backend(list_instr)
	
	if(dotcode is not None):
		with open(dotcode, 'w', encoding="utf-8") as f:
			dot_content = 'digraph {\n'+"".join([instr.dotty_str() for instr in list_instr ])+'}'
			f.write(dot_content)

	if(o is not None):
		print("WARNING, this backend does not support output code writing.")

	return list_instr[0]