import ir_re2coprocessor

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
	
def code_gen(ir):
		list_ir_instr = ir.getNodes()
		list_instr    = [None for e in list_ir_instr]

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