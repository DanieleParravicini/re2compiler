from enum import Enum

#if you want to estimate code size without actually run this code on CICERO
ESTIMATE_CODE_SIZE 		= False
BITS_DEDICATED_TO_TYPE 	= 3
BITS_DEDICATED_TO_I		= 16
MAX_CODE_SIZE 			= 512

class Re2CoproInstr_type(Enum):
	ACCEPT 			      = 0
	SPLIT  			      = 1
	MATCH  			      = 2
	JMP	   			      = 3
	END_WITHOUT_ACCEPTING = 4
	MATCH_ANY 		      = 5
	ACCEPT_PARTIAL	      = 6
	NOT_MATCH		      = 7

for	symbol in Re2CoproInstr_type:
	if symbol.value >= 2**BITS_DEDICATED_TO_TYPE:
		raise Exception("Not enough bits to represent the instructions") 

class Re2CoproInstr:
	def __init__(self, pc, instr_type, data):
		self.pc   = pc
		self.type = instr_type
		self.data = data

		if ESTIMATE_CODE_SIZE and self.data > MAX_CODE_SIZE or self.pc   > MAX_CODE_SIZE:
			import warnings
			
			warnings.warn("this code can't be executed as it possibly exceed the bits dedicated to pc", Warning)
		elif not ESTIMATE_CODE_SIZE:
			assert self.data < MAX_CODE_SIZE
			assert self.pc   < MAX_CODE_SIZE

	def set_pc(self,aPc):
		self.pc = aPc

	def set_data(self, aData):
		self.data = aData

	def __str__(self):
		return f"@ {self.pc} TYPE: {self.type} DATA: {self.data}"
	
	def dotty_str(self):
		return f"{id(self)} [label=\"unknown\" color=\"black\"  fillcolor=\"gray\"	style=\"filled\" ]\n"

	def code(self):
		payload =(self.type.value*(2**(BITS_DEDICATED_TO_I-BITS_DEDICATED_TO_TYPE))+self.data)

		return f"{hex(payload)}\n"

class Accept(Re2CoproInstr):
	def __init__(self, pc):
		super().__init__(pc, Re2CoproInstr_type.ACCEPT, 0)

	def dotty_str(self):
		return f"{self.pc} [label=\"{self.pc} : \\\\00 => ✓\" color=\"black\"  fillcolor=\"#1ac0c6\"	style=\"filled\"]\n"

class Accept_Partial(Re2CoproInstr):
	def __init__(self, pc):
		super().__init__(pc, Re2CoproInstr_type.ACCEPT_PARTIAL, 0)

	def dotty_str(self):
		return f"{self.pc} [label=\"{self.pc} : ✓\" color=\"black\"  fillcolor=\"#1ac0c6\"	style=\"filled\"]\n"


class Split(Re2CoproInstr):
	def __init__(self, pc, data):
		super().__init__(pc, Re2CoproInstr_type.SPLIT, data)

	def dotty_str(self):
		return 	(f"{self.pc} -> {self.data}\n" +
			   	 f"{self.pc} -> {self.pc+1}\n" +
				 f"{self.pc} [color=\"black\" fillcolor=\"#dee0e6\" style=\"filled\"]\n")

class Match(Re2CoproInstr):
	def __init__(self,pc, char):
		super().__init__(pc, Re2CoproInstr_type.MATCH, char)
	
	def dotty_str(self):
		return (f"{self.pc} -> {self.pc+1}\n"+
				f"{self.pc} [label =\"{self.pc} : {self.data}\" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"             )

class NotMatch(Re2CoproInstr):
	def __init__(self, pc, char):
		super().__init__(pc, Re2CoproInstr_type.NOT_MATCH, char)
		
	def dotty_str(self):
		return (f"{self.pc} -> {self.pc+1}\n"+
				f"{self.pc} [label =\"^{self.pc} : {self.data}\" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"             )
	
class Match_any(Re2CoproInstr):
	def __init__(self,pc):
		super().__init__(pc, Re2CoproInstr_type.MATCH_ANY, 0)
	
	def dotty_str(self):
		return (f"{self.pc} -> {self.pc+1}\n"+
				f"{self.pc} [label =\"{self.pc} : \\. \" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"             )

class Jmp(Re2CoproInstr):
	def __init__(self, pc, data):
		super().__init__(pc, Re2CoproInstr_type.JMP, data)
	
	def dotty_str(self):
		return (f"{self.pc} -> {self.data}\n"+
				f"{self.pc} [color=\"black\" fillcolor=\"#2792ce\" style=\"filled\"]\n")

class End(Re2CoproInstr):
	def __init__(self, pc):
		super().__init__(pc, Re2CoproInstr_type.END_WITHOUT_ACCEPTING, 0 )

	def dotty_str(self):
		return f"{self.pc} [label =\"{self.pc} : ✗\" color=\"black\" fillcolor=\"#ff6150\"	style=\"filled\"]\n"
