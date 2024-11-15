def non_reachable(a,b):
    assert a<5
    while b>a:
        a = a + 1
        trace()
        if a > 15:
            target()
            return a
        else:
            continue
            return a


def target():
    print("Wow, target reached!!!")

couter = 0
def trace():
    global couter
    couter += 1
    print("looping... iter: ", couter)


####################################################
# This is an demo showing finding input that leads to a target location in the source code.
# The target location is the function target()
#
# "target" is a reserved function name in this tool
#  - during SE it will be treated as a target location
#  - any other function call will be ignored
#  - in actual execution it will be called as normal, as defined above, which prints a message.
####################################################


import inspect
import ast
from src.SymExec import *

src = inspect.getsource(non_reachable)
func=ast.parse(src)
sym_exec = SymExec(func)

reaching_states = sym_exec.find_path_to_target(steps=80)

print("===============")
print("Reaching states:")
print("===============")

for s in sym_exec.reaching_states:
    print_c(f"====== State [{sym_exec.reaching_states.index(s)}] ======", color="red")
    s.print_state(color="yellow")
    s.print_steps()
    s.print_satisfying_assignment()

print("===============")
print("Calling Func with z3 generated inputs")
print("===============")
# non_reachable(4,16)
non_reachable(4,16)