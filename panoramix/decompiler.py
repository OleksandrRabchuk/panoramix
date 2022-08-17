import dataclasses

import logging

from panoramix.loader import Loader
from panoramix.vm import VM
from panoramix.utils.helpers import C, rewrite_trace

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Decompilation:
    text: str = ""
    asm: list = dataclasses.field(default_factory=list)
    json: dict = dataclasses.field(default_factory=dict)


# Derives from BaseException so it bypasses all the "except Exception" that are
# all around Panoramix code.
class TimeoutInterrupt(BaseException):
    """Thrown when a timeout occurs in the `timeout` context manager."""

    def __init__(self, value="Timed Out"):
        self.value = value

    def __str__(self):
        return repr(self.value)


def decompile_bytecode(code: str, only_func_name=None) -> Decompilation:
    loader = Loader()
    loader.load_binary(code)  # Code is actually hex.
    return _decompile_with_loader(loader, only_func_name)


def decompile_address(address: str, only_func_name=None) -> Decompilation:
    loader = Loader()
    loader.load_addr(address)
    return _decompile_with_loader(loader, only_func_name)


def _decompile_with_loader(loader, only_func_name=None) -> Decompilation:
    """

        But the main decompilation process looks like this:

            loader = Loader()
            loader.load(this_addr)

        loader.lines contains disassembled lines now

            loader.run(VM(loader, just_fdests=True))

        After this, loader.func_list contains a list of functions and their locations in the contract.
        Passing VM here is a pretty ugly hack, sorry about it.

            trace = VM(loader).run(target)

        Trace now contains the decompiled code, starting from target location.
        you can do pprint_repr or pprint_logic to see how it looks

            trace = make_whiles(trace)

        This turns gotos into whiles
        then it simplifies the code.
        (should be two functions really)

            functions[hash] = Function(hash, trace)

        Turns trace into a Function class.
        Function class constructor figures out it's kind (e.g. read-only, getter, etc),
        and some other things.

            contract = Contract(addr=this_addr,
                                ver=VER,
                                problems=problems,
                                functions=functions)

        Contract is a class containing all the contract decompiled functions and some other data.

            contract.postprocess()

        Figures out storage structure (you have to do it for the whole contract at once, not function by function)
        And folds the trace (that is, changes series of ifs into simpler forms)

        Finally...

            loader.disasm() -- contains disassembled version
            contract.json() -- contains json version of the contract

        Decompiled, human-readable version of the contract is done within this .py file,
        starting from `with redirect_stdout...`


        To anyone going into this code:
            - yes, it is chaotic
            - yes, there are way too many interdependencies between some modules
            - this is the first decompiler I've written in my life :)

    """

    """
        Fetch code from Web3, and disassemble it.

        Loader holds the disassembled line by line code,
        and the list of functions within the contract.
    """

    logger.info("Running light execution to find functions.")

    loader.run(VM(loader, just_fdests=True))

    if len(loader.lines) == 0:
        # No code.
        return Decompilation(text=C.gray + "# No code found for this contract." + C.end)

    """

        Main decompilation loop

    """


    functionsName = []
    for (hash, fname, target, stack) in loader.func_list:
        """
            hash contains function hash
            fname contains function name
            target contains line# for the given function
        """

        if only_func_name is not None and not fname.startswith(only_func_name):
            # if user provided a function_name in command line,
            # skip all the functions that are not it
            continue

        functionsName.append(fname)

    print(functionsName)
    return functionsName