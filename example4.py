def non_reachable(a,b):
    c = 0
    assert a > 0
    assert b > 0

    while a != 0:
        inner = b
        while inner != 0:
            c = c + 1
            inner = inner - 1
        a = a - 1

    assert c > 5
    target()
    return c

def target():
    print("Wow, target reached!!!")

####################################################
# This is an demo showing the complexity of SE
# - The function has 6 inputs, each of which controls a if-else statement
####################################################


import inspect
import ast
from src.SymExec import *

src = inspect.getsource(non_reachable)
func=ast.parse(src)
sym_exec = SymExec(func)
reaching_states = sym_exec.find_path_to_target(steps=100)

print(f"Reaching states: {len(sym_exec.reaching_states)}")
print(f"Unreachable: {len(sym_exec.unreachable_states)}")
print(f"Terminated : {len(sym_exec.terminated_states)}")
print(f"In-progress: {len(sym_exec.states)}")

# sym_exec.unreachable_states[-5].print_state()
# sym_exec.unreachable_states[-5].print_steps()
# sym_exec.unreachable_states[-5].print_stack()
# sym_exec.unreachable_states[-5].print_satisfying_assignment()

# for s in sym_exec.terminated_states:
#     s.print_state()
