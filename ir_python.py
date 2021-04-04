

class PythonInstr:
	def __init__(self, pc, *some_children):
		self.pc		  = pc
		self.children = list([*some_children])

	def replace(self, curr, next_curr):
		i = self.children.index(curr)
		if(i >= 0):
			self.children[i] = next_curr

	def append(self, *other):
		self.children += list([*other])

	def __str__(self):
		return f"PC {self.pc} TYPE: {type(self)} "
	
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
			#append children in reversed order because elements to visit 
			#are popped from to_visit list. Hence in order to have
			# as first elem to visiti the first children, just push
			# children in to_visit list in reversed order.
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
	
	def execute(self, string, cur_char_index ):
		raise NotImplementedError 


#sub_regex = namedtuple('sub_regex', ['start', 'end'])
class Accept(PythonInstr):
	def __init__(self,pc):
		super().__init__(pc)

	def dotty_repr(self):
		return f"{id(self)} [label=\"{self.pc} : \\\\00 => ✓\" color=\"black\"  fillcolor=\"#1ac0c6\"	style=\"filled\"]\n"

	def execute(self, string, cur_char_index ):
		if(len(string)-1 == cur_char_index):
			return [Accepted]
		else:
			return []
	
	def __str__(self):
		return f"PC {self.pc} ACCEPT \\0 ✓ "

class Accept_Partial(PythonInstr):
	def __init__(self,pc):
		super().__init__(pc)

	def dotty_repr(self):
		return f"{id(self)} [label=\"{self.pc} : ✓\" color=\"black\"  fillcolor=\"#1ac0c6\"	style=\"filled\"]\n"

	def execute(self, string, cur_char_index ):
		return [Accepted]
	
	def __str__(self):
		return f"PC {self.pc} ACCEPT ✓ "

class Split(PythonInstr):
	def __init__(self,pc, *children):
		super().__init__(pc,*children)

	def dotty_repr(self):
		return f"{id(self)} [label=\"{self.pc} : SPLIT\" color=\"black\" fillcolor=\"#dee0e6\" style=\"filled\"]\n"
	
	def execute(self, string, cur_char_index ):
		return [Continuation(self.children[0], string, cur_char_index), 
				Continuation(self.children[1], string, cur_char_index)]

	def __str__(self):
		return f"PC {self.pc} SPLIT {self.children[0].pc, self.children[1].pc} "

class Match(PythonInstr):
	def __init__(self, pc, achar, child):
		super().__init__(pc, child)
		if isinstance( achar, str):
			self.char = bytes(achar, 'utf-8', 'ignore')[0]
		else:
			self.char = achar
		
	def dotty_repr(self):
		return f"{id(self)} [label =\"{self.pc} : {chr(self.char)}\" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"

	def execute(self, string, cur_char_index ):
		if cur_char_index < len(string) and string[cur_char_index] == self.char :
			return [Continuation(self.children[0], string, cur_char_index+1)]  
		else : 
			return []
	
	def __str__(self):
		c = chr(self.char)
		return f"PC {self.pc} MATCH {c} "

class NotMatch(PythonInstr):
	def __init__(self, pc, achar, child):
		super().__init__(pc, child)
		if isinstance( achar, str):
			self.char = bytes(achar, 'utf-8', 'ignore')[0]
		else:
			self.char = achar
		
	def dotty_repr(self):
		return f"{id(self)} [label =\"{self.pc} : ^{chr(self.char)}\" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"

	def execute(self, string, cur_char_index ):
		if cur_char_index < len(string) and string[cur_char_index] != self.char :
			return [Continuation(self.children[0], string, cur_char_index)]  
		else : 
			return []
	
	def __str__(self):
		c = chr(self.char)
		return f"PC {self.pc} NOT MATCH {c} "
	
class Match_any(PythonInstr):
	def __init__(self, pc, *children):
		super().__init__(pc, *children)
			
	def dotty_repr(self):
		return f"{id(self)} [label =\"{self.pc} : \\.\" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"

	def execute(self, string, cur_char_index ):
		if cur_char_index < len(string):
			return [Continuation(self.children[0], string, cur_char_index+1)]
		else:
			return []
	
	def __str__(self):
		return f"PC {self.pc} MATCH ANY "
	
class Jmp(PythonInstr):
	def __init__(self, pc, next):
		super().__init__(pc, next)
	
	def dotty_repr(self):
		return f"{id(self)} [label=\"{self.pc} : JMP\" color=\"black\" fillcolor=\"#2792ce\" style=\"filled\"]\n"

	def execute(self, string, cur_char_index ):
		return [Continuation(self.children[0],string,cur_char_index)]
	
	def __str__(self):
		return f"PC {self.pc} JMP to {self.children[0].pc} "

class End_Without_Accepting(PythonInstr):
	def __init__(self, pc):
		super().__init__(pc)

	def dotty_repr(self):
		return f" {id(self)} [label =\"{self.pc} : ✗\" color=\"black\" fillcolor=\"#ff6150\"	style=\"filled\"]\n"

	def execute(self, string, cur_char_index ):
		return []
	
	def __str__(self):
		return f"PC {self.pc} ✗ "

class PlaceholderNop(PythonInstr):
	def __init__(self, pc, child):
		super().__init__(pc, child)

	def dotty_repr(self):
		return f" {id(self)} [label =\"{self.pc} : Nop\" color=\"black\" fillcolor=\"white\"	style=\"filled\"]\n"

	def execute(self, string, cur_char_index ):
		return [Continuation(self.children[0], string, cur_char_index)]
	
	def __str__(self):
		return f"PC {self.pc} NOP "

class Continuation:
	def __init__(self, instr, string, cur_char_index):
		self.instr 			= instr
		self.string 		= string
		self.cur_char_index = cur_char_index

	def execute(self):
		return self.instr.execute(self.string, self.cur_char_index)

	def __str__(self):
		old_chars   = self.string[:self.cur_char_index]
		cur_char    = bytes([self.string[self.cur_char_index]])
		next_chars  = self.string[self.cur_char_index+1:] if self.cur_char_index+1 < len(self.string) else ""
		return f'@ {old_chars}[{cur_char}]{next_chars} : {self.instr}'

	def __repr__(self):
		return self.__str__()
#object to signal completion
Accepted = {}


