import ir_re2coprocessor

def Accept(self, pc, list_ir_instructions: list,  list_instructions: list):
		anInstr = ir_re2coprocessor.Accept(pc)
		list_instructions[pc] = anInstr

def Accept_Partial(self, pc, list_ir_instructions: list,  list_instructions: list):
		anInstr = ir_re2coprocessor.Accept_Partial(pc)
		list_instructions[pc] = anInstr

def Split(self,  pc, list_ir_instructions: list,  list_instructions: list):
		target_split_0_pc = list_ir_instructions.index(self.children[0])
		target_split_1_pc = list_ir_instructions.index(self.children[1])
		if target_split_0_pc == pc+1:
			anInstr = ir_re2coprocessor.Split(pc,target_split_1_pc)
		else:
			assert target_split_1_pc == pc+1
			anInstr = ir_re2coprocessor.Split(pc,target_split_0_pc)
		list_instructions[pc] = anInstr

def Match(self,  pc, list_ir_instructions: list,  list_instructions: list):
		next_pc = list_ir_instructions.index(self.children[0])
		assert pc +1 == next_pc, str(pc+1)+ " !== "+ str(next_pc)

		anInstr = ir_re2coprocessor.Match(pc,self.char)
		list_instructions[pc] = anInstr

def NotMatch(self,  pc, list_ir_instructions: list,  list_instructions: list):
		next_pc = list_ir_instructions.index(self.children[0])
		assert pc +1 == next_pc, str(pc+1)+ " !== "+ str(next_pc)

		anInstr = ir_re2coprocessor.NotMatch(pc,self.char)
		list_instructions[pc] = anInstr
		
def Match_any(self,  pc, list_ir_instructions: list,  list_instructions: list):
		next_pc = list_ir_instructions.index(self.children[0])
		assert pc +1 == next_pc, str(pc+1)+ " !== "+ str(next_pc)

		anInstr = ir_re2coprocessor.Match_any(pc)
		list_instructions[pc] = anInstr

def Jmp(self,  pc, list_ir_instructions: list,  list_instructions: list):
		next_pc = list_ir_instructions.index(self.children[0])

		anInstr = ir_re2coprocessor.Jmp(pc,next_pc)
		list_instructions[pc] = anInstr

def End_Without_Accepting(self,  pc, list_ir_instructions: list,  list_instructions: list):
		anInstr = ir_re2coprocessor.End(pc)
		list_instructions[pc] = anInstr

def PlaceholderNop(self,  pc, list_ir_instructions: list,  list_instructions: list):
		raise NotImplementedError