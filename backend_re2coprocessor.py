import ir_re2coprocessor
import ir as IR

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
		list_ir_instr = ir.getNodes()
		
		add_jmp_if_necessary(list_ir_instr)

		list_instr    = [None for _ in list_ir_instr]

		for i in range(len(list_ir_instr)):
			list_ir_instr[i]._code_gen(pc=i, list_ir_instructions=list_ir_instr, list_instructions=list_instr )

		return list_instr

def to_code(ir, O1=False, dotcode=None, o=None):
	ir.setup('ir_re2coprocessor_codegen')
	list_instr = code_gen(ir)
	
	if O1:
		list_instr = simplify_jumps_backend(list_instr)
	
	if(dotcode is not None):
		with open(dotcode, 'w', encoding="utf-8") as f:
			dot_content = 'digraph {\n'+"".join([instr.dotty_str() for instr in list_instr ])+'}'
			f.write(dot_content)

	o_content = "".join([instr.code() for instr in list_instr ])
	if(o is not None):
		with open(o, 'w', encoding="utf-8") as f:
			f.write(o_content)
	return o_content