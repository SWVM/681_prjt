def many_branches(a,b,c,d,e,f):
    if a==1:
        z=1
    else:
        z=2

    if b==1:
        z=1
    else:
        z=2

    if c==1:
        z=1
    else:
        z=2

    if d==1:
        z=1
    else:
        z=2

    if e==1:
        z=1
    else:
        z=2

    if f==1:
        z=1
    else:
        z=2

    target()

####################################################
# This is a demo showing the complexity of SE
# - The function has 6 inputs, each of which controls a if-else statement
####################################################


import inspect
import ast
from src.SymExec import *

src = inspect.getsource(many_branches)
func=ast.parse(src)
sym_exec = SymExec(func)

reaching_states = sym_exec.find_path_to_target(steps=40)

print(f"Reaching states: {len(sym_exec.reaching_states)}")
print(f"Unreachable: {len(sym_exec.unreachable_states)}")
print(f"Terminated : {len(sym_exec.terminated_states)}")
print(f"In-progress: {len(sym_exec.states)}")

# for s in sym_exec.terminated_states:
#     s.print_state()
