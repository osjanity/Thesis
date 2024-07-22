#!usr/bin/python
# -*- coding: utf-8 -*-import string

import itertools
import copy

class NodeData:
	'''
	Attributes:
		parents: a list of strings that contains the names of the parent nodes
		conditionals: a list of size 2^p (where p is the number of parents) 
			that contains the conditional probabilities of the RV of this node given all possible values for the parents
	'''
	def __init__(self, name, parents=None, conditionals=None):
		self.name = name
		self.parents = parents

		# initializing the data structures,
		# mostly stuff that ensures that everything also works for nodes without parents
		if parents == None:
			self.num_parents = 0
		else:
			self.num_parents = len(self.parents)

		if conditionals == None:
			self.conditionals = [0 for _ in range(2**self.num_parents)]
		else:
			self.conditionals = conditionals

	def set_conditional(self, p, parent_assignment=None):
		'''
		parent_assignment: a dict that maps values to names of parents, e.g.
		{'x1' : 0, 'x2' : 1, 'x3' : 0, ...}

		this function computes the index of self.conditionals where the required value is stored and sets the conditional probability
		'''

		# handle special case of node without parents:
		if self.parents == None:
			self.conditionals[0] = p
			return

		# general case:
		index = 0
		for p_i in range(len(self.parents)):
			index += parent_assignment[self.parents[p_i]] * 2**p_i

		self.conditionals[index] = p

	def get_conditional(self, parent_assignment):
		'''
		parent_assignment: a dict that maps values to names of parents, e.g.
		{'x1' : 0, 'x2' : 1, 'x3' : 0, ...}

		this function computes the index of self.conditionals where the required value is stored and returns the conditional
		'''

		# handle special case of node without parents:
		if self.parents == None:
			return self.conditionals[0]

		# general case:
		index = 0
		for p_i in range(len(self.parents)):
			index += parent_assignment[self.parents[p_i]] * 2**p_i

		return self.conditionals[index]

	def print_conditionals(self):
		'''
		prints the full conditional distribution
		iterates through all possible assignments and prints the conditional distribution for each assignment in a seperate line
		'''
		all_possible_parent_assignments = [x for x in itertools.product([0,1], repeat=self.num_parents)]

		for a_i in range(2**self.num_parents):
			assignment = {self.parents[i] : all_possible_parent_assignments[a_i][i] for i in range(self.num_parents)}
			# some list-magic that produces a sufficiently nice string:
			assignment_string = "P("+self.name+" = 1 | " + ', '.join([str(x) + " = " + str(assignment[x]) for x in assignment]) + " ) = " + str(self.get_conditional(assignment))
			print (assignment_string)

def switch_edge(x, y):
	'''
	switches the edge (x,y)
	x, y: NodeData
	'''

	# preparation:
	# use itertools.product to get all possible assignments of values for the parent nodes:
	all_possible_parent_assignments = list(itertools.product([0,1], repeat=x.num_parents))
	num_parents_assigments = len(all_possible_parent_assignments)

	# get conditional joint distribution p(x,y | parents):
	# initialization:
	pxe0ye0 = [0 for _ in range(2**x.num_parents)]
	pxe0ye1 = [0 for _ in range(2**x.num_parents)]
	pxe1ye0 = [0 for _ in range(2**x.num_parents)]
	pxe1ye1 = [0 for _ in range(2**x.num_parents)]
	# iterate through all possible assignments for the common parents of x and y:
	for a_i in range(num_parents_assigments):
		assignemnt_dict_x = {x.parents[i] : all_possible_parent_assignments[a_i][i] for i in range(x.num_parents)}
		assignemnt_dict_y = {x.parents[i] : all_possible_parent_assignments[a_i][i] for i in range(x.num_parents)}
		assignemnt_dict_y[x.name] = 0
		# case x=0, y=1:
		pxe0ye1[a_i] = (1-x.get_conditional(assignemnt_dict_x)) * y.get_conditional(assignemnt_dict_y)
		# case x=0, y=0:
		pxe0ye0[a_i] = (1-x.get_conditional(assignemnt_dict_x)) * (1-y.get_conditional(assignemnt_dict_y))
		
		assignemnt_dict_y[x.name] = 1
		# case x=1, y=1:
		pxe1ye1[a_i] = x.get_conditional(assignemnt_dict_x) * y.get_conditional(assignemnt_dict_y)
		# case x=1, y=0:
		pxe1ye0[a_i] = x.get_conditional(assignemnt_dict_x) * (1-y.get_conditional(assignemnt_dict_y))

	# marginalize x from the conditional distribution of y:
	pye0 = [pxe0ye0[i] + pxe1ye0[i] for i in range(num_parents_assigments)]
	pye1 = [pxe0ye1[i] + pxe1ye1[i] for i in range(num_parents_assigments)]
	
	# condition x on the possible values of y:
	pxe0gye0 = [pxe0ye0[i]/pye0[i] for i in range(num_parents_assigments)]
	pxe0gye1 = [pxe0ye1[i]/pye1[i] for i in range(num_parents_assigments)]
	pxe1gye0 = [pxe1ye0[i]/pye0[i] for i in range(num_parents_assigments)]
	pxe1gye1 = [pxe1ye1[i]/pye1[i] for i in range(num_parents_assigments)]

	# construct new nodedata objects:
	x_new_parents = [y.name]
	if not x.parents == None:
		x_new_parents += x.parents
	x_new = NodeData(x.name, parents=x_new_parents)
	for a_i in range(num_parents_assigments):
		# construct the assignment-dictionary:
		assignment_dict = {x.parents[i] : all_possible_parent_assignments[a_i][i] for i in range(x.num_parents)}

		# case y=0:
		# add y to assignment_dict:
		assignment_dict[y.name] = 0
		# set conditional for x_new:
		x_new.set_conditional(p=pxe1gye0[a_i], parent_assignment=assignment_dict)

		# case y=1
		# add y to assignment_dict:
		assignment_dict[y.name] = 1
		# set conditional for x_new:
		x_new.set_conditional(p=pxe1gye1[a_i], parent_assignment=assignment_dict)

	y_new_parents = []
	if not x.parents == None:
		y_new_parents += x.parents
	y_new = NodeData(y.name, parents=y_new_parents)
	for a_i in range(num_parents_assigments):
		# construct the assignment-dictionary:
		assignment_dict = {x.parents[i] : all_possible_parent_assignments[a_i][i] for i in range(x.num_parents)}
		y_new.set_conditional(p=pye1[a_i], parent_assignment=assignment_dict)

	return x_new, y_new

# define graph:
x1 = NodeData('x1')
x1.set_conditional(p=0.8)

x2 = NodeData('x2', parents=['x1'])
x2.set_conditional(p=0.2, parent_assignment={'x1':0})
x2.set_conditional(p=0.4, parent_assignment={'x1':1})

x3 = NodeData('x3', parents=['x1', 'x2'])
x3.set_conditional(p=0.1, parent_assignment={'x1': 0, 'x2': 0})
x3.set_conditional(p=0.2, parent_assignment={'x1': 1, 'x2': 0})
x3.set_conditional(p=0.4, parent_assignment={'x1': 0, 'x2': 1})
x3.set_conditional(p=0.8, parent_assignment={'x1': 1, 'x2': 1})

x1.print_conditionals()
x2.print_conditionals()
x3.print_conditionals()

print ("switch edge (x1, x2)")
x1_new, x2_new = switch_edge(x1, x2)
x1_new.print_conditionals()
x2_new.print_conditionals()

print ("also from original graph, switch edge (x2, x3)")
x2_new, x3_new = switch_edge(x2, x3)
x2_new.print_conditionals()
x3_new.print_conditionals()