import ir_python

def Accept(self, pc):
	
	return ir_python.Accept(pc)

def Accept_Partial(self, pc):

	return ir_python.Accept_Partial(pc)

def Split(self, pc):
	
	child0 = self.children[0]
	child1 = self.children[1]

	return ir_python.Split(pc, child0, child1)
		
def Match(self, pc):
	child = self.children[0]
	return ir_python.Match(pc, self.char, child)
		
def Match_any(self, pc):
	child = self.children[0]
	return ir_python.Match_any(pc, child)
		
def Jmp(self, pc):
	child = self.children[0]
	return ir_python.Jmp(pc, child)

def NotMatch(self, pc):
	child = self.children[0]
	return ir_python.NotMatch(pc, self.char, child)
		
def End_Without_Accepting(self, pc):
	return ir_python.End_Without_Accepting(pc)
		
def PlaceholderNop(self, pc):
	child = self.children[0]
	return ir_python.PlaceholderNop(pc, child)
		