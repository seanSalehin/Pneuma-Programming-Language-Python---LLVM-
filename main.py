from Lexer import Lexer
from parser import Parser
from AST import Program
import time
import json
from compiler import Compiler
from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float
import os


Lexer_Bug=False
Parse_Bug=False
Compiler_Bug = False
RUN_CODE = True


if __name__=='__main__':

    for filename in os.listdir('.'):
        if filename.endswith('.Pneuma'):
            new_filename = filename.replace('.Pneuma', '.pn')
            os.rename(filename, new_filename)

    with open("Test/code.pn", 'r') as f:
        code=f.read()


    #lexer debug
    if Lexer_Bug:
        debug=Lexer(source=code)
        while debug.current_character is not None:
            print(debug.next_token())

    l=Lexer(source=code)
    p = Parser(lexer=l)

    program = p.parse_program()
    if len(p.errors)>0:
         for err in p.errors:
             print(err)
         exit(1)

    #parser debug
    if Parse_Bug:
        print("parser debug")
        #program = p.parse_program()
        with open("debug/ast.json", "w") as f:
            json.dump(program.json(), f, indent=4)
        print("wrote AST to debug/ast.json sucessfully")


    #compiler debug
    c=Compiler()
    c.compile(node=program)
    module=c.module
    module.triple = llvm.get_default_triple()
    if Compiler_Bug:
        with open("debug/ir.ll", "w") as f:
            f.write(str(module))
    if RUN_CODE:
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        try:
            llvm_ir_parsed = llvm.parse_assembly(str(module))
            llvm_ir_parsed.verify()
        except Exception as e:
            print(e)
            raise

        target_machine = llvm.Target.from_default_triple().create_target_machine()

        engine = llvm.create_mcjit_compiler(llvm_ir_parsed, target_machine)
        engine.finalize_object()

        entry = engine.get_function_address('main')
        cfunc = CFUNCTYPE(c_int)(entry)
        st=time.time()
        result = cfunc()
        et = time.time()
        print(f'\n\nResult: {result}\n===Executed in {round((et-st)*1000, 6)}  ms\n')