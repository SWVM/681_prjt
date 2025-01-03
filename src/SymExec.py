# CS681 - Project
# Authors: Linhan Li
# Github Copilot was used as a coding assistant for this project
# however, I take full responsibility for the originality and accuracy of the content.

import ast
import z3
from copy import deepcopy
import logging
from termcolor import colored

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_c(text, color="yellow"):
    if not isinstance(text, str):
        text = str(text)
    print(colored(text, color))

# reverse the body, so the execution order is correct when its pushed to the stack
def reverse_body(body):
    body = body.copy()
    body.reverse()
    return body

def check_satisfiability(sym_state):
    solver = z3.Solver()
    solver.add(*sym_state)
    return solver.check() 


# keeps track variable used
# assigns a new postfixed z3 variable for each new assignment
class Z3VarEnv():
    def __init__(self):
        self.env = {}
        self.z3_vars = {}
    
    def assign_var(self, var):
        if var not in self.env:
            self.env[var] = 0
            self.z3_vars[var] = []
        else:
            self.env[var] += 1
        vname = var if self.env[var]==0 else var + "_" + str(self.env[var])
        idx = self.env[var]
        self.z3_vars[var].append(z3.Int(vname))
        return self.z3_vars[var][-1]

    def get_last_assigned(self, var):
        return self.z3_vars[var][-1]

    def copy(self):
        new_env = Z3VarEnv()
        new_env.env = self.env.copy()
        new_env.z3_vars = deepcopy(self.z3_vars)
        return new_env
    
    def reset(self):
        self.env = {}
        self.z3_vars = {}
        
        
# The symbolic state, its defined by the following:
# 1. The stack of AST nodes that are yet to be executed
# 2. The path taken to reach this state
# 3. The symbolic state, a list of z3 constraints
# 4. The variable environment, a mapping of variable names to their z3 variables
class SymState():
    def __init__(self, tree_traversal_stack, path_taken, symbolic_state, z3_var_env):
        self.tree_traversal_stack = tree_traversal_stack
        self.path_taken = path_taken
        self.symbolic_state = symbolic_state
        self.z3_var_env = z3_var_env

    def print_steps(self, color="white"):
        print_c("Path Taken", color)
        for step in self.path_taken:
            print_c(f"\t{step}", color)
    
    def print_stack(self, color="white"):
        print_c("Stack", color)
        print_c("\tstack Bottom", color)
        for node in self.tree_traversal_stack:
            print_c(f"\t{node.lineno} -- {node}", color)
        print_c("\tstack Top", color)

    def print_state(self,color="white"):
        print_c("Symbolic State", color)
        print_c(self.symbolic_state, color)
        
    def print_satisfying_assignment(self, color="white"):
        print_c("Satisfying Assignment", color)
        solver = z3.Solver()
        solver.add(*self.symbolic_state)
        if solver.check() == z3.sat:
            model = solver.model()
            non_underscored_vars = {d.name(): model[d] for d in model.decls() if '_' not in d.name()}
            print_c(non_underscored_vars, "green")
        else:
            print_c("No satisfying assignment", "red")
    def is_satisfiable(self):
        return check_satisfiability(self.symbolic_state) == z3.sat
    def is_terminated(self):
        return len(self.tree_traversal_stack) == 0
    

        


class SymExec():

    def __init__(self, func):
        if not isinstance(func, ast.FunctionDef) and isinstance(func, ast.Module):
            func = func.body[0]
        if not isinstance(func, ast.FunctionDef):
            raise Exception("input is not an ast.FunctionDef OR ast.Module containing a single ast.FunctionDef")
        
        self.func = func
        var_env = Z3VarEnv()

        for arg in func.args.args:
            var_env.assign_var(arg.arg)
        # tree_traversal_stack, path_taken, symbolic_state, z3_var_env
        fn_body = self.func.body
        fn_body.reverse()
        self.states = [SymState(fn_body, [], [], var_env)]
        self.unreachable_states = []
        self.terminated_states = []
        self.reaching_states = []

    # convert a comparison node to z3 constraint
    def ast_cmp_to_z3(self, node, env):
        assert isinstance(node, (ast.Compare, ast.Constant, ast.UnaryOp))
        if isinstance(node, ast.Compare):
            assert len(node.ops) == 1
            assert len(node.comparators) == 1
            left = self.ast_expr_to_z3(node.left, env)
            right = self.ast_expr_to_z3(node.comparators[0], env)
            if isinstance(node.ops[0], ast.Gt):
                return left > right
            elif isinstance(node.ops[0], ast.Lt):
                return left < right
            elif isinstance(node.ops[0], ast.Eq):
                return left == right
            elif isinstance(node.ops[0], ast.NotEq):
                return left != right
            else:
                raise Exception("Unsupported AST node")
        elif isinstance(node, ast.Constant):
            assert isinstance(node.value, bool)
            return node.value
        elif isinstance(node, ast.UnaryOp):
            assert isinstance(node.op, ast.Not)
            return z3.Not(self.ast_cmp_to_z3(node.operand, env))

    # get the z3Int of a variable or numeric constant
    def ast_var_n_const(self, node, env):
        if isinstance(node, ast.Name):
            return env.get_last_assigned(node.id)
        elif isinstance(node, ast.Constant):
            return node.value
        else:
            raise Exception("Unsupported AST node")
    
    # convert an expression to z3
    def ast_expr_to_z3(self, node, env):
        assert isinstance(node, (ast.BinOp, ast.Name, ast.Constant))
        if isinstance(node, ast.BinOp):
            if isinstance(node.left, ast.BinOp):
                left = self.ast_expr_to_z3(node.left, env)
            elif isinstance(node.left, (ast.Name, ast.Constant)):
                left = self.ast_var_n_const(node.left, env)
            else:
                raise Exception("Unsupported AST node")
            if isinstance(node.right, ast.BinOp):
                right = self.ast_expr_to_z3(node.right, env)
            elif isinstance(node.right, (ast.Name, ast.Constant)):
                right = self.ast_var_n_const(node.right, env)
            else:
                raise Exception("Unsupported AST node")
            op = node.op
            if isinstance(op, ast.Add):
                return left + right
            elif isinstance(op, ast.Sub):
                return left - right
            elif isinstance(op, ast.Mult):
                return left * right
            elif isinstance(op, ast.Div):
                return left / right
        elif isinstance(node, (ast.Name, ast.Constant)):
            return self.ast_var_n_const(node, env)
        else:
            raise Exception("Unsupported AST node")

    # find a path to the target within a number of steps from the function entry
    def find_path_to_target(self, steps=10):
        self.reaching_states == []
        for i in range(steps):
            self.step()
            if len(self.reaching_states) > 0:
                logger.info(f"<!>  Target reached after [{i}] steps... number of states explored: {len(self.states) + len(self.unreachable_states) + len(self.terminated_states)}")
                return self.reaching_states
        logger.info(f"<!>  Target not reached after [{steps}] steps... number of states explored: {len(self.states) + len(self.unreachable_states) + len(self.terminated_states)}")
        return self.reaching_states

    # explore within a number of steps from the function entry
    def explore(self, steps=10):
        for i in range(steps):
            self.step()
        return self.states, self.terminated_states, self.unreachable_states, self.reaching_states

    # explore from a given state, within a number of steps
    # stops if the target is reached
    def find_path_to_target_FROM(self, initial_state, steps=10):
        self.states = [initial_state]
        self.reaching_states = []
        self.unreachable_states = []
        self.terminated_states = []
        return self.find_path_to_target(steps)

    # explore from a given state, within a number of steps
    def explore_FROM(self, initial_state, steps=10):
        self.states = [initial_state]
        self.reaching_states = []
        self.unreachable_states = []
        self.terminated_states = []
        return self.explore(steps)

    # explore one step from the current states
    def step(self):
        new_states = []

        # process each state to generate new states
        # action differs based on the type of the ast.node
        for state in self.states:
            logger.debug(f"processing state: {state.symbolic_state}")
            logger.debug(f"\tNodes: {state.tree_traversal_stack}")
            if not state.is_satisfiable():
                logger.warn(f"\tPath unreachable...SKIPPING")
                continue
            if state.is_terminated():
                logger.warn(f"\tPath terminated...SKIPPING")
                continue

            next_node = state.tree_traversal_stack.pop()
            old_env = state.z3_var_env
            if isinstance(next_node, ast.Return):
                logger.debug("Return")
                new_env = old_env.copy()
                z3_ret = new_env.assign_var("fn_ret")
                new_stack = []
                new_path = state.path_taken.copy() + [f"({next_node.lineno})\t"+"Return: "+ast.unparse(next_node)]
                new_sym_state = state.symbolic_state.copy() + [z3_ret == self.ast_expr_to_z3(next_node.value, old_env)]
                new_states.append(SymState(new_stack, new_path, new_sym_state, new_env))
            elif isinstance(next_node, ast.Assert):
                logger.debug("Assert")
                new_env = old_env.copy()
                new_stack = state.tree_traversal_stack.copy()
                new_path = state.path_taken.copy() + [f"({next_node.lineno})\t"+"Assert: "+ast.unparse(next_node.test)]
                new_sym_state = state.symbolic_state.copy() + [self.ast_cmp_to_z3(next_node.test, old_env)]
                new_states.append(SymState(new_stack, new_path, new_sym_state, new_env))
            elif isinstance(next_node, ast.Assign):
                logger.debug("Assign") # assuming basic id = val usage
                new_env = old_env.copy()
                new_var = new_env.assign_var(next_node.targets[0].id)
                new_stack = state.tree_traversal_stack.copy() 
                new_path = state.path_taken.copy() + [f"({next_node.lineno})\t"+"Assign: "+ast.unparse(next_node)]
                new_sym_state = state.symbolic_state.copy() + [new_var == self.ast_expr_to_z3(next_node.value, old_env)]
                new_states.append(SymState(new_stack, new_path, new_sym_state, new_env))
            elif isinstance(next_node, ast.While):
                logger.debug("While")
                # enter loop state (exec body, and return to loop entry)
                new_env_1 = old_env.copy()
                new_stack_1 = state.tree_traversal_stack.copy() + [next_node] + reverse_body(next_node.body)
                new_path_1 = state.path_taken.copy() + [f"({next_node.lineno})\t"+"While(Enter): "+ast.unparse(next_node.test)]
                new_sym_state_1 = state.symbolic_state.copy() + [self.ast_cmp_to_z3(next_node.test, old_env)]
                new_states.append(SymState(new_stack_1, new_path_1, new_sym_state_1, new_env_1))
                # exit loop state (no body exec and continue)
                new_env_2 = old_env.copy()
                new_stack_2 = state.tree_traversal_stack.copy()
                new_path_2 = state.path_taken.copy() + [f"({next_node.lineno})\t"+"While(Exit): "+ast.unparse(next_node.test)]
                new_sym_state_2 = state.symbolic_state.copy() + [z3.Not(self.ast_cmp_to_z3(next_node.test, old_env))]
                new_states.append(SymState(new_stack_2, new_path_2, new_sym_state_2, new_env_2))
            elif isinstance(next_node, ast.Break):
                logger.debug("Break")
                # break state (pop stack until while loop)
                new_env = old_env.copy()
                new_stack = state.tree_traversal_stack.copy()
                logger.debug("poping stack")
                while len(new_stack) > 0:
                    poped = new_stack.pop()
                    logger.debug(f"\t{poped}")
                    if isinstance(poped, ast.While):
                        break
                new_path = state.path_taken.copy() + [f"({next_node.lineno})\t"+"Break: "+ast.unparse(next_node)]
                new_sym_state = state.symbolic_state.copy()
                new_states.append(SymState(new_stack, new_path, new_sym_state, new_env))
            elif isinstance(next_node, ast.Continue):
                logger.debug("Continue")
                # continue state (pop stack until while loop and re-enter)
                new_env = old_env.copy()
                new_stack = state.tree_traversal_stack.copy()
                logger.debug("poping stack")
                while len(new_stack) > 0:
                    poped = new_stack.pop()
                    logger.debug(f"\t{poped}")
                    if isinstance(poped, ast.While):
                        break
                new_stack.append(poped)
                new_path = state.path_taken.copy() + [f"({next_node.lineno})\t"+"Continue: "+ast.unparse(next_node)]
                new_sym_state = state.symbolic_state.copy()
                new_states.append(SymState(new_stack, new_path, new_sym_state, new_env))
            elif isinstance(next_node, ast.Pass):
                logger.debug("Pass")
                # pass state (no exec and continue)
                new_states.append(  SymState(   state.tree_traversal_stack.copy(),
                                                state.path_taken.copy() + [f"({next_node.lineno})\t"+"Pass"],
                                                state.symbolic_state.copy(),
                                                state.z3_var_env.copy()))
            elif isinstance(next_node, ast.If):
                logger.debug("If")
                # enter if state (exec body, and return to if entry)
                new_env_1 = old_env.copy()
                new_stack_1 = state.tree_traversal_stack.copy() + reverse_body(next_node.body)
                new_path_1 = state.path_taken.copy() + [f"({next_node.lineno})\t"+"If(if): "+ast.unparse(next_node.test)]
                new_sym_state_1 = state.symbolic_state.copy() + [self.ast_cmp_to_z3(next_node.test, old_env)]
                new_states.append(SymState(new_stack_1, new_path_1, new_sym_state_1, new_env_1))
                # else state (no body exec and continue)
                new_env_2 = old_env.copy()
                new_stack_2 = state.tree_traversal_stack.copy() + reverse_body(next_node.orelse)
                new_path_2 = state.path_taken.copy() + [f"({next_node.lineno})\t"+"If(else): "+ast.unparse(next_node.test)]
                new_sym_state_2 = state.symbolic_state.copy() + [z3.Not(self.ast_cmp_to_z3(next_node.test, old_env))]
                new_states.append(SymState(new_stack_2, new_path_2, new_sym_state_2, new_env_2))
            elif isinstance(next_node, ast.Expr):
                # some fake func for target location, doesnt exec anything
                assert isinstance(next_node.value, ast.Call)
                logger.debug("Call")
                next_node = next_node.value
                if next_node.func.id == "target":
                    logger.debug("Target Hit")
                    new_states.append(  SymState(   state.tree_traversal_stack.copy(), 
                                                    state.path_taken.copy() + [f"({next_node.lineno})\t"+"Hit Target: target()"], 
                                                    state.symbolic_state.copy(), 
                                                    state.z3_var_env.copy()))
                    self.reaching_states.append(new_states[-1])
                else:
                    logger.debug("Unknown Call <" + next_node.func.id + "> Skipped")
                    new_states.append(  SymState(   state.tree_traversal_stack.copy(), 
                                                    state.path_taken.copy() + [f"({next_node.lineno})\t"+f"Func Call: {next_node.func.id}"], 
                                                    state.symbolic_state.copy(), 
                                                    state.z3_var_env.copy()))
            else:
                raise Exception("Unsupported AST node" + str(next_node.__class__))

        # filter out unreachable and terminated states
        unreachable_states = [state for state in new_states if not state.is_satisfiable()]
        terminated_states = [state for state in new_states if state.is_terminated() and state not in unreachable_states]
        new_states = [state for state in new_states if state not in unreachable_states and state not in terminated_states]

        self.unreachable_states.extend(unreachable_states)
        self.terminated_states.extend(terminated_states)
        self.states = new_states

        logger.debug(f"New States: {len(new_states)}")
        logger.debug(f"Unreachable States removed: {len(unreachable_states)}")
        logger.debug(f"Terminated States removed: {len(terminated_states)}")


if __name__ == "__main__":

    code = """
def non_reachable(a):
    i = 0
    if a < 10:
        while True:
            a = a + 1
    else:
        target()
    if False:
        target()
    return a
"""
#     code = """
# def hit_test(x):
#     x = 0
#     while True:
#         x = x + 1
#         if x > 19:
#             break
#     target()
# """
#    code = """
# def cohendiv_b(x, y):
#     q = 0           #   vassume (non-blocking && within loop body)
#     r = x           #   expecting to see multiple constraints from vassume being added with variable renamed
#     a = 0           #   and finally block the SE (before the loop condition does so)
#     b = 0
#     while True:
#         if not a < 100:
#             break
#         a = 10 + a
#         # vassume(a < 30)        #a greater than -100  with variable renaming
#     return q
# """
#    code = """
# def example(x,y,z):
#     x = 100
#     a = x + y + z
#     while a<10:
#         a = a + 1
#         target()
#     return a
# """
#    code = """
# def example(x,y,z):
#     a = 1
#     while True:
#         if a < 10:
#             x = 1 + 1 + 2 + 3
#             a = a + 1 + 2 + 3
#         else:
#             a = 100 + 1 + 2 + 3
#             break
# """

# Parse the code
    tree = ast.parse(code)
    sym_exec = SymExec(tree.body[0])
    nonterminate, terminated, unreachable, reaching_stetes =  sym_exec.explore(steps=3)

    for i in range(len(nonterminate)):
        print(f"State {i}")
        nonterminate[i].print_steps()
        nonterminate[i].print_state()
        nonterminate[i].print_satisfying_assignment()
        print("--------------------------------------------------")

    sym_exec.find_path_to_target_FROM(nonterminate[0], steps=10)

    for i in range(len(sym_exec.unreachable_states)):
        print(f"State {i}")
        sym_exec.unreachable_states[i].print_steps()
        sym_exec.unreachable_states[i].print_state()
        sym_exec.unreachable_states[i].print_satisfying_assignment()
        print("--------------------------------------------------")


    # for i in range(len(nonterminate)):
    #     print(f"State {i}")
    #     print(nonterminate[i].symbolic_state)
    #     print("Path Taken")
    #     for step in nonterminate[i].path_taken:
    #         print(f"\t{step}")
    #     print(nonterminate[i].tree_traversal_stack)
    #     print(nonterminate[i].z3_var_env.z3_vars)
    #     print("Solving...")
    #     show_sat_inputs(nonterminate[i].symbolic_state)
    #     print("--------------------------------------------------")

    # for i in range(len(terminated)):
    #     print(f"Terminated State {i}")
    #     print(terminated[i].symbolic_state)
    #     print("Path Taken")
    #     for step in terminated[i].path_taken:
    #         print(f"\t{step}")
    #     print(terminated[i].tree_traversal_stack)
    #     print(terminated[i].z3_var_env.z3_vars)
    #     print("Solving...")
    #     show_sat_inputs(terminated[i].symbolic_state)
    #     print("--------------------------------------------------")

    # for i in range(len(unreachable)):
    #     print(f"Unreachable State {i}")
    #     print(unreachable[i].symbolic_state)
    #     print("Path Taken")
    #     for step in unreachable[i].path_taken:
    #         print(f"\t{step}")
    #     print(unreachable[i].tree_traversal_stack)
    #     print(unreachable[i].z3_var_env.z3_vars)
    #     print("Solving...")
    #     show_sat_inputs(unreachable[i].symbolic_state)
    #     print("--------------------------------------------------")

    # for i in range(len(reaching_stetes)):
    #     print(f"Reaching State {i}")
    #     print(reaching_stetes[i].symbolic_state)
    #     print("Path Taken")
    #     for step in reaching_stetes[i].path_taken:
    #         print(f"\t{step}")
    #     print(reaching_stetes[i].tree_traversal_stack)
    #     print(reaching_stetes[i].z3_var_env.z3_vars)
    #     print("Solving...")
    #     show_sat_inputs(reaching_stetes[i].symbolic_state)
    #     print("--------------------------------------------------")


    # print("Summary")
    # print(f"Non-terminated: {len(nonterminate)}")
    # print(f"Terminated: {len(terminated)}")
    # print(f"Unreachable: {len(unreachable)}")
    # print(f"Reaching: {len(reaching_stetes)}")