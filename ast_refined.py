import ir
from copy import deepcopy
from collections import namedtuple


class ast_refined_node:
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
	
	def to_ir(self):
		'''the to_ir method returns for each node of the abstract syntax tree two nodes
		The first is the starting node of the sub regular expression
		the second is the last node if the sub regular expression'''
		return [c.to_ir() for c in self.children]

	
	def dotty_str(self):
		tmp = [ (c.dotty_str() if hasattr(c, 'dotty_str') else str(c))+'\n' for c in self.children]
		
		children_link =[f"{id(self)} -> {id(c)}\n" for c in self.children]

		return "".join(tmp) + "".join(children_link)+ f" {id(self)} [label=\"{str(self)}\"]"

	def __str__(self):
		return type(self).__name__

sub_regex = namedtuple('sub_regex', ['start', 'end'])

class alternative(ast_refined_node):
	def __init__(self, *others):
		super().__init__(*others)

	def append(self,other):
		self.children += [other]
	
	def to_ir(self):
		
		end   = ir.PlaceholderNop()

		lowered_children = super().to_ir()
		
		for c in lowered_children:
			jmp = ir.Jmp(end)
			c.end.append(jmp)

		#lowered_children[-1].end.append(end)

		while(len(lowered_children) >= 2):
			
			option1 = lowered_children.pop(0).start
			option2 = lowered_children.pop(0).start
			
			split 	= ir.Split(option1,option2)
			lowered_children.append(sub_regex(split,None))
		
		start  = lowered_children[0].start

		return sub_regex(start,end)

class none_of(ast_refined_node):
	def __init__(self, *others):
		super().__init__(*others)

	def append(self,other):
		self.children += [other]
	
	def to_ir(self):
		
		lowered_children = super().to_ir()
		
		start  = lowered_children[0].start
		end    = lowered_children[0].end
		for c in lowered_children[1:]:
			end.append(c.start)
			end = c.end

		conclude_matching_any = ir.Match_any()
		end.append(conclude_matching_any)
		end = conclude_matching_any

		return sub_regex(start,end)
	
class concatenation(ast_refined_node):
	def __init__(self, *others):
		super().__init__(*others)
		
	def append(self,other):
		self.children += [other]

	def to_ir(self):
		lowered_children = super().to_ir()
		for i in range(len(lowered_children)-1):
			lowered_children[i].end.append(lowered_children[i+1].start)

		return sub_regex(lowered_children[0].start, lowered_children[-1].end)

class any_repetition(ast_refined_node):
	def __init__(self, regex_to_repeat):
		super().__init__(regex_to_repeat)

	def to_ir(self):
		
		end   = ir.PlaceholderNop()
		
		lowered_children = super().to_ir()
		assert len(lowered_children)==1
		
		start = ir.Split(lowered_children[0].start, end)
		jmp   = ir.Jmp(start)
		lowered_children[0].end.append(jmp)
		return sub_regex(start,end)

class more_than_one_repetition(ast_refined_node):
	def __init__(self, regex_to_repeat):
		super().__init__(regex_to_repeat)

	def to_ir(self):
		end = ir.PlaceholderNop()
		lowered_children = super().to_ir()
		assert len(lowered_children)==1
		start = lowered_children[0].start

		split = ir.Split(end, start)
		lowered_children[0].end.append(split)
		return sub_regex(start,end)
		
class bounded_num_repetition(ast_refined_node):
	def __init__(self, regex_to_repeat, min_num=1, max_num=1):
		super().__init__(regex_to_repeat)
		self.min_num = min(min_num,max_num)
		self.max_num = max(min_num,max_num)

	def to_ir(self):
		end = ir.PlaceholderNop()
		lowered_children = super().to_ir()
		assert len(lowered_children)==1
		child = lowered_children[0]
		start = child.start
		
		child_copies = [child]
		for _ in range(self.max_num-1):
			child_copies.append(deepcopy(child))

		for i in range(self.max_num):
			
			if i+1 < self.min_num:
				child_copies[i].end.append(child_copies[i+1].start)
			elif i+1 != self.max_num:
				if i == 0 and self.min_num==0:
					start = ir.Split(child_copies[0].start,end)
				split = ir.Split(child_copies[i+1].start,end)
				child_copies[i].end.append(split)
			else:
				child_copies[i].end.append(end)

		return sub_regex(start,end)

	def __str__(self):
		if self.min_num == self.max_num:
			if self.min_num ==1:
				return type(self).__name__
			else:
				return type(self).__name__+f'{ {self.min_num} }'
		else:
			return type(self).__name__+f'{ {self.min_num,self.max_num} }'

class min_bounded_num_repetition(ast_refined_node):
	def __init__(self, regex_to_repeat, min_num=1):
		super().__init__(regex_to_repeat)
		self.min_num = min_num
		assert(min_num > 0)

	def to_ir(self):
		end = ir.PlaceholderNop()
		lowered_children = super().to_ir()
		assert len(lowered_children)==1
		child = lowered_children[0]
		start = child.start
		
		child_copies = [child]
		for _ in range(self.min_num):
			child_copies.append(deepcopy(child))

		for count in range(self.min_num-1):
			child_copies[count].end.append(child_copies[count+1].start)
		
			
		split = ir.Split(child_copies[self.min_num].start,end)
		child_copies[self.min_num].end.append(ir.Jmp(split))
		
		child_copies[self.min_num-1].end.append(split)

		return sub_regex(start,end)

	def __str__(self):
		
		if self.min_num ==1:
			return type(self).__name__
		else:
			return type(self).__name__+f'{ {self.min_num} }'
		

class optional_repetition(ast_refined_node):
	def __init__(self, regex_to_repeat):
		super().__init__(regex_to_repeat)

	def to_ir(self):
		end = ir.PlaceholderNop()
		lowered_children = super().to_ir()
		assert len(lowered_children) == 1

		start = ir.Split(lowered_children[0].start, end)
		lowered_children[0].end.append(ir.Jmp(end))
		return sub_regex(start,end)

class match_character(ast_refined_node):
	def __init__(self, character):
		super().__init__()

		if isinstance(character, str):
			self.character = bytes(character, 'utf-8')[0]
		else:
			self.character = character
	
	def dotty_str(self):
		# printable Ascii \x20-\x7F
		char = chr(self.character)
		if self.character == 32:
			char = "SPACE"
		elif self.character < 32 or self.character > 127 or char in "\"\\":
			char = hex(self.character)
		return f" {id(self)} [label=\"{char}\"]"

	def to_ir(self):
		x= ir.Match(self.character)
		return sub_regex(x,x)

class match_negative_character(ast_refined_node):
	def __init__(self, character):
		super().__init__()

		if isinstance(character, str):
			self.character = bytes(character, 'utf-8')[0]
		else:
			self.character = character
	
	def dotty_str(self):
		# printable Ascii \x20-\x7F
		char = chr(self.character)
		if self.character == 32:
			char = "SPACE"
		elif self.character < 32 or self.character > 127 or char in "\"\\":
			char = hex(self.character)
		return f" {id(self)} [label=\"^{char}\"]"

	def to_ir(self):
		x= ir.NotMatch(self.character)
		return sub_regex(x,x)

class any_character(ast_refined_node):
	def __init__(self):
		super().__init__()
	
	def dotty_str(self):
		return f" {id(self)} [label=\"\\.\"]"

	def to_ir(self):
		x= ir.Match_any()
		return sub_regex(x,x)
	
class end_of_string(ast_refined_node):
	def __init__(self):
		super().__init__()
	
	def dotty_str(self):
		return f" {id(self)} [label=\"end of string\"]"

	def to_ir(self):
		x= ir.Accept()
		return sub_regex(x,x)


class whole_regexp(ast_refined_node):
	def __init__(self, regex, accept_partial=True, ignore_prefix=False):
		self.accept_partial = accept_partial
		self.ignore_prefix  = ignore_prefix
		super().__init__(regex)

	def set_accept_partial(self, accept_partial=True):
		self.accept_partial = accept_partial
	
	def set_ignore_prefix(self, ignore_prefix=True):
		self.ignore_prefix  = ignore_prefix

	def dotty_str(self):
		tmp = [ (c.dotty_str() if hasattr(c, 'dotty_str') else str(c))+'\n' for c in self.children]
		
		return 'digraph {'+"".join(tmp)+'}'
	
	def to_ir(self):
		
		
		lowered_children = super().to_ir()
		assert len(lowered_children) == 1
		end = ir.Accept_Partial() if self.accept_partial else ir.Accept()
		child = lowered_children[0]
		if self.ignore_prefix :
			start     = ir.Split()
			jmp       = ir.Jmp(start)
			match_any = ir.Match_any(jmp)
			start.append(match_any)
			start.append(child.start)
		else:
			start     = child.start
		child.end.append(end)

		return start
	
class epsilon_move(ast_refined_node):
	def __init__(self):
		super().__init__()
	
	def dotty_str(self):
		return f" {id(self)} [label=\"ε\"]"

	def to_ir(self):
		x= ir.PlaceholderNop()
		return sub_regex(x,x)