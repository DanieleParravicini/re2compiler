import ir_re2coprocessor
from helper import reverse

def _subclasses(cls):
	sub_cls 		= cls.__subclasses__()
	sub_sub_cls 	= [s for c in sub_cls for s in _subclasses(c) ]
	return set(cls.__subclasses__()).union(sub_sub_cls)

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
	
	def get_anchestors(self):
		nodes = self.getNodes()
	
		children = {}
		for n in nodes:
			if len(n.children)>0:
				children[n] = n.children

		anchestors = reverse(children)
		return anchestors

	def deep_copy(self):
		
		nodes = self.getNodes()

		nodes_copy = [ copy.copy(n) for n in nodes] 

		for n in nodes:

			for i in range(len(n.children)):
				c = n.children[i]
				index_child = nodes.index(c)
				nodes_copy.children[i] = nodes_copy[index_child]


	def _code_gen(self,**args):
		pass

	def setup(self, codegen_library_name='ir_re2coprocessor_codegen'):
		""" 
		compiler ir frontend and ir backend are decoupled.
		This method is responsible of importing the code_gen process
		from the correct library. This will ultimately generate the appropriate ir.  
		"""
		#dummy code_gen method
		code_gen_dummy_method = lambda self, **args: ''
		import importlib
		#from types import MethodType
		#search for correct <codegen_library> module which contains classes 
		#that can be used in code generation process.
		try : 
			#set global object "codegen_library" equal to module 
			global codegen_library 
			codegen_library = importlib.import_module(codegen_library_name)
		except ImportError :
			#failed to import code_gen method, set a dummy one
			code_gen_dummy_method = lambda self, **args: f'{type(self)} {id(self)}'
			print("WARNING: codegen_library not found ")
		#look for all subclasses of IrInstr
		classes = _subclasses(IrInstr)
		#print('classes found', classes)
		for c in classes:
			try : 
				if issubclass(c, IrInstr) :
					setattr(c, "_code_gen", eval('codegen_library.'+c.__name__))
			except Exception as e : 
				setattr(c, "_code_gen",  code_gen_dummy_method)
				print("WARNING: codegen_library could not be attached to ",c.__name__)
				raise e


class Accept(IrInstr):
	def __init__(self):
		super().__init__()

	def dotty_repr(self):
		return f"{id(self)} [label=\"\\\\00 => ✓\" color=\"black\"  fillcolor=\"#1ac0c6\"	style=\"filled\"]\n"


class Accept_Partial(IrInstr):
	def __init__(self):
		super().__init__()

	def dotty_repr(self):
		return f"{id(self)} [label=\"✓\" color=\"black\"  fillcolor=\"#1ac0c6\"	style=\"filled\"]\n"


class Split(IrInstr):
	def __init__(self, *children):
		super().__init__(*children)

	def dotty_repr(self):
		return f"{id(self)} [label=\"SPLIT\" color=\"black\" fillcolor=\"#dee0e6\" style=\"filled\"]\n"

class Match(IrInstr):
	def __init__(self, achar):
		super().__init__()
		if isinstance(achar, str):
			self.char = bytes(achar, 'utf-8')[0]
		else:
			self.char = achar
		
	def dotty_repr(self):
		return f"{id(self)} [label =\"{chr(self.char)}\" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"


class Match_any(IrInstr):
	def __init__(self, *children):
		super().__init__(*children)
		
		
	def dotty_repr(self):
		return f"{id(self)} [label =\"\\.\" color=\"black\" fillcolor=\"#ffa822\" style=\"filled\"]\n"

	

class Jmp(IrInstr):
	def __init__(self, next):
		super().__init__(next)
	
	def dotty_repr(self):
		return f"{id(self)} [label=\"JMP\" color=\"black\" fillcolor=\"#2792ce\" style=\"filled\"]\n"

	

class End_Without_Accepting(IrInstr):
	def __init__(self):
		super().__init__()

	def dotty_repr(self):
		return f" {id(self)} [label =\"✗\" color=\"black\" fillcolor=\"#ff6150\"	style=\"filled\"]\n"


class PlaceholderNop(IrInstr):
	def __init__(self):
		super().__init__()

	def dotty_repr(self):
		return f" {id(self)} [label =\"Nop\" color=\"black\" fillcolor=\"white\"	style=\"filled\"]\n"

