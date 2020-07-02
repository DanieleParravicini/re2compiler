import ir_re2coprocessor
import ir_lower
from collections import namedtuple

class ir_node:
	def __init__(self, *children):
		self.mapping 	= []
		self.children 	= list(children) if children else []

	def getattr(self, name):
		idx = self.mapping.index(name)
		return self.children[idx] if(idx > 0) else None
	
	def setattr(self, name, value):
		idx = self.mapping.index(name)
		if( idx > 0 and idx < len(self.children)):
			self.children[idx] = value
		
	def navigate(self,action, postOrder=False ):

		if not postOrder:
			action(self)
		for c in self.children:
			try :
				c.navigate(action,postOrder)
			except Exception:
				print('exception')
				pass
		if postOrder:
			action(self)
	
	def lower(self):
		'''the lower method returns for each node of the abstract syntax tree two nodes
		The first is the starting node of the sub regular expression
		the second is the last node if the sub regular expression'''
		return [c.lower() for c in self.children]

	
	def dotty_str(self):
		tmp = [ (c.dotty_str() if hasattr(c, 'dotty_str') else str(c))+'\n' for c in self.children]
		
		children_link =[f"{id(self)} -> {id(c)}\n" for c in self.children]

		return "".join(tmp) + "".join(children_link)+ f" {id(self)} [label=\"{str(self)}\"]"

	def __str__(self):
		return type(self).__name__

sub_regex = namedtuple('sub_regex', ['start', 'end'])
class any_char(ir_node):
	def __init__(self, *others):
		super().__init__(*others)
	
	def lower(self):
		raise NotImplementedError()

class alternative(ir_node):
	def __init__(self, *others):
		super().__init__(*others)

	def append(self,other):
		self.children += [other]
	
	def lower(self):
		
		end   = ir_lower.PlaceholderNop()

		lowered_children = super().lower()
		
		for c in lowered_children:
			jmp = ir_lower.Jmp(end)
			c.end.append(jmp)

		#lowered_children[-1].end.append(end)

		while(len(lowered_children) >= 2):
			
			option1 = lowered_children.pop(0).start
			option2 = lowered_children.pop(0).start
			
			split 	= ir_lower.Split(option1,option2)
			lowered_children.append(sub_regex(split,None))
		
		start  = lowered_children[0].start

		return sub_regex(start,end)
		
class concatenation(ir_node):
	def __init__(self, *others):
		super().__init__(*others)
		
	def append(self,other):
		self.children += [other]

	def lower(self):
		lowered_children = super().lower()
		for i in range(len(lowered_children)-1):
			lowered_children[i].end.append(lowered_children[i+1].start)

		return sub_regex(lowered_children[0].start, lowered_children[-1].end)

class any_repetition(ir_node):
	def __init__(self, regex_to_repeat):
		super().__init__(regex_to_repeat)

	def lower(self):
		
		end   = ir_lower.PlaceholderNop()
		
		lowered_children = super().lower()
		assert len(lowered_children)==1
		
		start = ir_lower.Split(lowered_children[0].start, end)
		jmp   = ir_lower.Jmp(start)
		lowered_children[0].end.append(jmp)
		return sub_regex(start,end)

class more_than_one_repetition(ir_node):
	def __init__(self, regex_to_repeat):
		super().__init__(regex_to_repeat)

	def lower(self):
		end = ir_lower.PlaceholderNop()
		lowered_children = super().lower()
		assert len(lowered_children)==1
		start = lowered_children[0].start

		split = ir_lower.Split(end, start)
		
		lowered_children[0].end.append(split)
		return sub_regex(start,end)
		

class optional_repetition(ir_node):
	def __init__(self, regex_to_repeat):
		super().__init__(regex_to_repeat)

	def lower(self):
		end = ir_lower.PlaceholderNop()
		lowered_children = super().lower()
		assert len(lowered_children) == 1

		start = ir_lower.Split(lowered_children[0].start, end)
		lowered_children[0].end.append(ir_lower.Jmp(end))
		return sub_regex(start,end)

class match_character(ir_node):
	def __init__(self, character):
		super().__init__()

		if isinstance(character, str):
			self.character = bytes(character, 'utf-8')[0]
		else:
			self.character = character
	
	def dotty_str(self):
		return f" {id(self)} [label=\"{chr(self.character)}\"]"

	def lower(self):
		x= ir_lower.Match(self.character)
		return sub_regex(x,x)

class any_character(ir_node):
	def __init__(self):
		super().__init__()
	
	def dotty_str(self):
		return f" {id(self)} [label=\".\"]"

	def lower(self):
		x= ir_lower.Match_any()
		return sub_regex(x,x)


class whole_regexp(ir_node):
	def __init__(self, regex):
		super().__init__(regex)

	def dotty_str(self):
		tmp = [ (c.dotty_str() if hasattr(c, 'dotty_str') else str(c))+'\n' for c in self.children]
		
		return 'digraph {'+"".join(tmp)+'}'
	
	def lower(self):
		
			
		end = ir_lower.Accept()
		lowered_children = super().lower()
		assert len(lowered_children) == 1
		child = lowered_children[0]
		child.end.append(end)

		return child.start
	
		 