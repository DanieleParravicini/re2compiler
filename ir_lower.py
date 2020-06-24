
import ir_re2coprocessor

class IrInstr:
	def __init__(self, *some_children):
		self.children = list([*some_children])

	def replace(self, curr, next_curr):
		i = self.children.index(curr)
		if(i >= 0):
			self.children[i] = next_curr

	def append(self, *other):
		self.children += list([*other])

	def __str__(self):
		return f"{id(self)} TYPE: {type(self)} #CHILDREN {len(self.children)}"
	
	def dotty_repr(self):
		return f"{id(self)} [label=\"unknown\" color=\"black\"  fillcolor=\"gray\"	style=\"filled\" ]\n"

	def dotty_str(self, reset_visited=False):

		children_link = [f"{id(self)} -> {id(c)}\n" for c in self.children]

		return "".join(children_link)+ self.dotty_repr()

	def navigate(self,action):
		visited 	= []
		to_visit 	= [self]

		
		while len(to_visit) > 0:
			
			e = to_visit.pop()
			visited.append(e)
			#print(e,'->', e.children)
			action(e)

			for child in reversed(e.children):
				#print('\t',child)
				if not (child in visited or child in to_visit):
					to_visit.append(child)
	
	def getNodes(self):

		def accumulate(l):
			def action_accumulate(x):
				l.append(x)
			return action_accumulate

		node_list 	= []
		action 		= accumulate(node_list)
		self.navigate(action)

		return node_list
	
	def code_gen(self):
		list_ir_instr = self.getNodes()
		list_instr    = [None for e in list_ir_instr]

		for i in range(len(list_ir_instr)):
			list_ir_instr[i]._code_gen(i,list_ir_instr, list_instr )

		return list_instr

	def _code_gen(self, pc, list_ir_instructions: list, list_instructions: list):
		pass



class Accept(IrInstr):
	def __init__(self):
		super().__init__()

	def dotty_repr(self):
		return f"{id(self)} [label=\"✓\" color=\"black\"  fillcolor=\"#1ac0c6\"	style=\"filled\"]\n"

	def _code_gen(self, pc, list_ir_instructions: list,  list_instructions: list):
		anInstr = ir_re2coprocessor.Accept(pc)
		list_instructions[pc] = anInstr

class Split(IrInstr):
	def __init__(self, next, next_splitted):
		super().__init__(next, next_splitted)

	def dotty_repr(self):
		return f"{id(self)} [label=\"SPLIT\" color=\"black\" fillcolor=\"#dee0e6\" style=\"filled\"]\n"

	def _code_gen(self,  pc, list_ir_instructions: list,  list_instructions: list):
		
		target_split_0_pc = list_ir_instructions.index(self.children[0])
		target_split_1_pc = list_ir_instructions.index(self.children[1])
		if target_split_0_pc == pc+1:
			anInstr = ir_re2coprocessor.Split(pc,target_split_1_pc)
		else:
			assert target_split_1_pc == pc+1
			anInstr = ir_re2coprocessor.Split(pc,target_split_0_pc)
		list_instructions[pc] = anInstr

class Match(IrInstr):
	def __init__(self, achar):
		super().__init__()
		if isinstance(achar, str):
			self.char = bytes(achar, 'utf-8')[0]
		else:
			self.char = achar
		
	def dotty_repr(self):
		return f"{id(self)} [label =\"{chr(self.char)}\" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"

	def _code_gen(self,  pc, list_ir_instructions: list,  list_instructions: list):
		next_pc = list_ir_instructions.index(self.children[0])
		assert pc +1 == next_pc, str(pc+1)+ " !== "+ str(next_pc)

		anInstr = ir_re2coprocessor.Match(pc,self.char)
		list_instructions[pc] = anInstr

class Jmp(IrInstr):
	def __init__(self, next):
		super().__init__(next)
	
	def dotty_repr(self):
		return f"{id(self)} [label=\"JMP\" color=\"black\" fillcolor=\"#2792ce\" style=\"filled\"]\n"

	def _code_gen(self,  pc, list_ir_instructions: list,  list_instructions: list):
		next_pc = list_ir_instructions.index(self.children[0])

		anInstr = ir_re2coprocessor.Jmp(pc,next_pc)
		list_instructions[pc] = anInstr

class End_Without_Accepting(IrInstr):
	def __init__(self):
		super().__init__()

	def dotty_repr(self):
		return f" {id(self)} [label =\"✗\" color=\"black\" fillcolor=\"#ff6150\"	style=\"filled\"]\n"
	
	def _code_gen(self,  pc, list_ir_instructions: list,  list_instructions: list):
		anInstr = ir_re2coprocessor.End(pc)
		list_instructions[pc] = anInstr

class PlaceholderNop(IrInstr):
	def __init__(self):
		super().__init__()

	def dotty_repr(self):
		return f" {id(self)} [label =\"Nop\" color=\"black\" fillcolor=\"white\"	style=\"filled\"]\n"

	def _code_gen(self,  pc, list_ir_instructions: list,  list_instructions: list):
		raise NotImplementedError

