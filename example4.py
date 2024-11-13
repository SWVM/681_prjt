def non_reachable(a,b):
    c_ = 0
    assert a > 3
    assert b > 0

    while a != 0:
        inner_ = b
        while inner_ != 0:
            c_ = c_ + 1
            inner_ = inner_ - 1
        a = a - 1

    assert c_ > 12
    target()
    return c_

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

sym_exec.reaching_states[0].print_state()
sym_exec.reaching_states[0].print_steps()
sym_exec.reaching_states[0].print_stack()
sym_exec.reaching_states[0].print_satisfying_assignment()


print(non_reachable(4,4))