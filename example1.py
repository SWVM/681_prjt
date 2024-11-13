def non_reachable(a):
    if a < 5:
        while True:
            a = a + 1
            if a > 10:
                target()
                return a
    else:
        return a

####################################################
# This is an demo showing how we manipulate the ast traversal to perform symbolic execution.
####################################################



import inspect
import ast
from src.SymExec import *

src = inspect.getsource(non_reachable)
func=ast.parse(src)
sym_exec = SymExec(func)


def step_n_log_first_state(steps = 10):
    for i in range(steps):
        print_c(f"==========================", color="blue")
        print_c(f"Step [{i}]", color="blue")
        for s in sym_exec.states:
            print_c(f"====== State [{sym_exec.states.index(s)}] ======", color="red")
            s.print_state(color="yellow")
            s.print_stack()
            print_c(f"================================================", color="red")

        sym_exec.step()

        if sym_exec.states[0].is_terminated():
            break

step_n_log_first_state(steps=10)