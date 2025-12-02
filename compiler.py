from llvmlite import ir
import os
from AST import NodeType, Statement, Expression, Program, ExpressionStatement, InfixExpression, IntegerLiteral, FloatLiteral, IdentifierLiteral, WhileStatement, BreakStatement, ContinueStatement, ForStatement
from Environment import Environment
from AST import FunctionStatement, BlockStatement, ReturnStatement, AssignStatement, IfStatement, BooleanLiteral, CallExpression, FunctionParameter, StringLiteral, PrefixExpression, PostfixExpression, ImportStatement
from Lexer import Lexer
from parser import Parser


class Compiler:

    def __init__(self):
        self.type_map={
            'int':ir.IntType(32),
            'float':ir.FloatType(),
            'bool': ir.IntType(1),
            'str':ir.PointerType(ir.IntType(8)),
            'void': ir.VoidType()
        }
        self.module = ir.Module('main')
        self.builder = ir.IRBuilder()
        self.env = Environment()
        #keeping track of errors
        self.errors=[]
        self.counter = 0
        self.__initialize_builtins()

        #for loop block (for, continue, break)
        self.breakpoints = []
        self.continues = []

        self.global_parsed_pallets = {}
    


    def __initialize_builtins(self):

        def __init_print():
            fnty = ir.FunctionType(
                self.type_map['int'],
                [ir.IntType(8).as_pointer()],
                var_arg=True #handle all the parameters
            )
            return ir.Function(self.module, fnty, 'printf')


        def __init_booleans():
            bool_type = self.type_map['bool']
            true_var = ir.GlobalVariable(self.module, bool_type, 'true')
            true_var.initializer = ir.Constant(bool_type, 1) #1 = true
            true_var.global_constant=True

            false_var = ir.GlobalVariable(self.module, bool_type, 'false')
            false_var.initializer = ir.Constant(bool_type, 0) #0 = false
            false_var.global_constant=True #fixed immutable values

            return true_var, false_var
        

        self.env.define('printf', __init_print(), ir.IntType(32))
        
        true_var, false_var = __init_booleans()
        self.env.define('true', true_var, true_var.type)
        self.env.define('false', false_var, false_var.type)


    def compile(self, node):
        match node.type():
            case NodeType.Program:
                self.__visit_program(node)

            case NodeType.ExpressionStatement:
                self.__visit_expression_statement(node)

            case NodeType.LetStatement:
                self.__visit_let_statement(node)

            case NodeType.InfixExpression:
                self.__visit_infixExpression(node)

            case NodeType.FunctionStatement:
                self.__visit_function_statement(node)

            case NodeType.BlockStatement:
                self.__visit_block_statement(node)

            case NodeType.ReturnStatement:
                self.__visit_return_statement(node)

            case NodeType.AssignStatement:
                self.__visit_assign_statement(node)

            case NodeType.IfStatement:
                self.__visit_if_statement(node)
            
            case NodeType.CallExpression:
                self.__visit_call_expression(node)
            
            case NodeType.WhileStatement:
                self.__visit_while_expression(node)

            case NodeType.BreakStatement:
                self.__visit_break_statement(node)
            
            case NodeType.ContinueStatement:
                self.__visit_continue_statement(node)
            
            case NodeType.ForStatement:
                self.__visit_for_statement(node)

            case NodeType.PostfixExpression:
                self.__visit_postfix_expression(node)

            case NodeType.ImportStatement:
                self.__visit_import_expression(node)



    def __visit_program(self, node):
        for stmt in node.statements:
            self.compile(stmt)


    def __visit_expression_statement(self, node):
        self.compile(node.e)


    def __visit_let_statement(self, node):
        name=node.name.value
        value = node.value
        value_type=node.value_type  #TODO

        value, Type = self.__resolve_value(node=value)

        #variable
        if self.env.lookup(name)is None:
            ptr=self.builder.alloca(Type)
            #storeing the value at the pointer (ptr)
            self.builder.store(value, ptr)
            #Add the variable to the environment
            self.env.define(name, ptr, Type)
        else:
            ptr, _=self.env.lookup(name)
            self.builder.store(value, ptr)
        
    
    def __visit_block_statement(self, node):
        for stmt in node.statements:
            self.compile(stmt)

    
    def __visit_return_statement(self, node):
        if node.return_value is None:
            self.builder.ret_void()
        else:
            value, Type = self.__resolve_value(node.return_value)
            if isinstance(Type, ir.ArrayType):
                value = self.builder.gep(value, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
                Type = ir.PointerType(ir.IntType(8))
            self.builder.ret(value)



    def __visit_function_statement(self, node):
        name = node.name.value
        body = node.body
        params=node.parameters
        params_names=[p.name for p in params]
        param_types = [self.type_map[p.value_type]for p in params]
        return_type = self.type_map[node.return_type]

        fnty=ir.FunctionType(return_type, param_types)
        func = ir.Function(self.module, fnty, name=name)
        block = func.append_basic_block(f'{name}_entry')
        previous_builder = self.builder
        self.builder=ir.IRBuilder(block)

        params_ptr=[]
        for i, typ in enumerate(param_types):
            ptr=self.builder.alloca(typ)
            self.builder.store(func.args[i], ptr)
            params_ptr.append(ptr)


        previous_env=self.env
        self.env=Environment(parent=previous_env)

        for i,x in enumerate(zip(param_types, params_names)):
            typ = param_types[i]
            ptr=params_ptr[i]
            self.env.define(x[1], ptr, typ)

        self.env.define(name, func, return_type)
        self.compile(body)

        if self.builder.block.terminator is None:
            if return_type == self.type_map['void']:
                self.builder.ret_void()
            else:
                # For non-void functions without return, add an error
                self.errors.append(f"Function '{name}' must return a value")
                # Add a dummy return to avoid LLVM errors
                if return_type == self.type_map['int']:
                    self.builder.ret(ir.Constant(return_type, 0))
                elif return_type == self.type_map['float']:
                    self.builder.ret(ir.Constant(return_type, 0.0))
                else:
                    self.builder.ret_void()

        self.env=previous_env
        self.env.define(name, func, return_type)
        self.builder = previous_builder


    def __visit_assign_statement(self, node):
        name = node.ident.value
        operator = node.operator
        value = node.right_value
        
        if self.env.lookup(name) is None:
            self.errors.append(f"Compile Error: Identifier {name} has not been declared")
            return

        right_value, right_type = self.__resolve_value(value)

        variable_pointer, _ = self.env.lookup(name)
        original_value = self.builder.load(variable_pointer)
        if isinstance(original_value.type, ir.IntType) and isinstance(right_type, ir.FloatType):
            original_value = self.builder.sitofp(original_value, ir.FloatType())
        
        if isinstance(original_value.type, ir.FloatType) and isinstance(right_type, ir.IntType):
            original_value = self.builder.sitofp(right_value, ir.FloatType())

        value = None
        Type = None

        match operator:
            case '=':
                value = right_value

            case '+=':
                if isinstance(original_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                    value = self.builder.add(original_value, right_value)
                else:
                    value = self.builder.fadd(original_value, right_value)

            case '-=':
                if isinstance(original_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                    value = self.builder.sub(original_value, right_value)
                else:
                    value = self.builder.fsub(original_value, right_value)
        
            case '*=':
                if isinstance(original_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                    value = self.builder.mul(original_value, right_value)
                else:
                    value = self.builder.fmul(original_value, right_value)
        
            case '/=':
                if isinstance(original_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                    value = self.builder.sdiv(original_value, right_value)
                else:
                    value = self.builder.fdiv(original_value, right_value)

            case '-':
                 print("Wrong Assignment Operator")

        pointer, _ = self.env.lookup(name)
        self.builder.store(value, pointer)






    def __visit_if_statement(self, node):
        #if condition = true  ==> if block
        #if condition false ==> else block
        condition = node.condition
        consequence = node.consequence
        alternative = node.alternative

        test, _ = self.__resolve_value(condition)

        if alternative is None:
            with self.builder.if_then(test):
                self.compile(consequence)
        else:
            with self.builder.if_else(test)as(true, otherwise):
                with true:
                    self.compile(consequence)
                with otherwise:
                    if alternative is not None:
                        self.compile(alternative)



    def __visit_infixExpression(self, node):
        operator = node.operator
        left_value, left_type = self.__resolve_value(node.left_node)
        right_value, right_type=self.__resolve_value(node.right_node)
        value = None
        Type=None
        if isinstance(right_type, ir.IntType) and isinstance(left_type, ir.IntType):
            Type = self.type_map['int']
            match operator:
                case '+':
                    value = self.builder.add(left_value, right_value)
                case '-':
                    value = self.builder.sub(left_value, right_value)
                case '*':
                     value = self.builder.mul(left_value, right_value)
                case '/':
                    value = self.builder.sdiv(left_value, right_value)   
                case '%':
                    value= self.builder.srem(left_value, right_value) 
                case '^':
                    # TODO
                    pass
                case '<':
                    value = self.builder.icmp_signed('<',left_value, right_value)
                    Type = ir.IntType(1)
                case '<=':
                    value = self.builder.icmp_signed('<=',left_value, right_value)
                    Type = ir.IntType(1)
                case '>':
                    value = self.builder.icmp_signed('>',left_value, right_value)
                    Type = ir.IntType(1)
                case '>=':
                    value = self.builder.icmp_signed('>=',left_value, right_value) 
                    Type = ir.IntType(1)  
                case '==':
                    value= self.builder.icmp_signed('==',left_value, right_value) 
                    Type = ir.IntType(1) 
                case '!=':
                    value = self.builder.icmp_signed('!=', left_value, right_value)
                    Type = ir.IntType(1)

        elif isinstance(right_type, ir.FloatType) and isinstance(left_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case '+':
                    value = self.builder.fadd(left_value, right_value)
                case '-':
                    value = self.builder.fsub(left_value, right_value)
                case '*':
                    value = self.builder.fmul(left_value, right_value)
                case '/':
                    value = self.builder.fdiv(left_value, right_value)
                case '%':
                    value = self.builder.frem(left_value, right_value)
                case '^':
                    #TODO
                    pass
                case '<':
                    value = self.builder.fcmp_ordered('<',left_value, right_value)
                    Type = ir.IntType(1)
                case '<=':
                    value = self.builder.fcmp_ordered('<=',left_value, right_value)
                    Type = ir.IntType(1)
                case '>':
                    value = self.builder.fcmp_ordered('>',left_value, right_value)
                    Type = ir.IntType(1)
                case '>=':
                    value = self.builder.fcmp_ordered('>=',left_value, right_value) 
                    Type = ir.IntType(1)  
                case '==':
                    value= self.builder.fcmp_ordered('==',left_value, right_value) 
                    Type = ir.IntType(1) 
                case '!=':
                    value = self.builder.fcmp_ordered('!=', left_value, right_value)
                    Type = ir.IntType(1)

        return value, Type

    def __visit_call_expression(self, node):
        name = node.function.value
        params = node.arguments
        args =[]
        types=[]
        if len(params)>0:
            for x in params:
                p_val, p_type = self.__resolve_value(x)
                args.append(p_val)
                types.append(p_type)
        match name:
            case 'printf':
                ret = self.builtin_printf(params=args, return_type=types[0])
                ret_type = self.type_map['int']
            case _:
                func, ret_type = self.env.lookup(name)
                ret = self.builder.call(func, args)
        return ret, ret_type
    


    def __visit_prefix_expression(self, node):
        operator=node.operator
        right_node = node.right_node
        right_value, right_type = self.__resolve_value(right_node)
        Type = None
        value = None
        if isinstance(right_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case '-':
                    value = self.builder.fmul(right_value, ir.Constant(ir.FloatType(), -1.0)) #flip the case and make negative into positive
                case '!':
                    value = ir.Constant(ir.IntType(1), 0)
        elif isinstance(right_type, ir.IntType):
            Type = ir.IntType(32)
            match operator:
                case '-':
                    value = self.builder.mul(right_value, ir.Constant(ir.IntType(32), -1))
                case '!':
                    value = self.builder.not_(right_value)
        return value, Type




    def __visit_postfix_expression(self, node):
        left_node = node.left_node
        operator = node.operator
        if self.env.lookup(left_node.value) is None:
            self.errors.append(f"COMPILE ERROR : Identifier {left_node.value} has not been declared !")
            return
        var_pointer, var_type = self.env.lookup(left_node.value)
        original_value = self.builder.load(var_pointer)
        value = None
        match operator:
            case "++":
                if isinstance(original_value.type, ir.IntType):
                    value = self.builder.add(original_value, ir.Constant(ir.IntType(32), 1))
                elif isinstance(original_value, ir.FloatType):
                    value = self.builder.fadd(original_value, ir.Constant(ir.FloatType(), 1.0))
                else:
                    self.errors.append(f"COMPILE ERROR: Unsupported type for ++ operator")
                    return None, None
    
            case "--":
                if isinstance(original_value.type, ir.IntType):
                    value = self.builder.sub(original_value, ir.Constant(ir.IntType(32), 1))
                elif isinstance(original_value, ir.FloatType):
                    value = self.builder.fsub(original_value, ir.Constant(ir.FloatType(), 1.0))
                else:
                    self.errors.append(f"COMPILE ERROR: Unsupported type for -- operator")
                    return None, None
    
        self.builder.store(value, var_pointer)
        return original_value, var_type
    


    def __visit_while_expression(self, node):
        # node has .condition and .body
        func = self.builder.block.function  # current function object

        # create blocks
        cond_bb = func.append_basic_block(f"while_cond_{self.__increment_counter()}")
        body_bb = func.append_basic_block(f"while_body_{self.__increment_counter()}")
        after_bb = func.append_basic_block(f"while_after_{self.__increment_counter()}")

        # Branch from current block to condition check
        self.builder.branch(cond_bb)

        # CONDITION block: evaluate condition and branch to body or after
        self.builder.position_at_start(cond_bb)
        test, _ = self.__resolve_value(node.condition)
        # ensure test is an i1 (boolean) — if it's i32, compare != 0
        if not isinstance(test.type, ir.IntType) or test.type.width != 1:
            # convert i32 to i1 by comparing to zero
            zero = ir.Constant(test.type, 0)
            test = self.builder.icmp_signed('!=', test, zero)
        self.builder.cbranch(test, body_bb, after_bb)

        # BODY block: compile the loop body, then jump back to condition
        self.builder.position_at_start(body_bb)
        self.compile(node.body)
        # Ensure there's a branch back to condition (avoid falling off)
        # If the body last instruction already returned/branched, don't add an extra branch.
        if self.builder.block.terminator is None:
            self.builder.branch(cond_bb)

        # AFTER block: continue compiling after the loop
        self.builder.position_at_start(after_bb)


    def __visit_break_statement(self, node):
        self.builder.branch(self.breakpoints[-1])

    def __visit_continue_statement(self, node):
        self.builder.branch(self.continues[-1])




    def __visit_for_statement(self, node):
        var_declaration = node.var_declaration
        condition = node.condition
        action = node.action
        body = node.body
        
        self.compile(var_declaration)
        
        func = self.builder.block.function
        cond_bb = func.append_basic_block(f"for_cond_{self.__increment_counter()}")
        body_bb = func.append_basic_block(f"for_body_{self.__increment_counter()}")
        inc_bb = func.append_basic_block(f"for_inc_{self.__increment_counter()}")
        after_bb = func.append_basic_block(f"for_after_{self.__increment_counter()}")
        
        # Setup break/continue targets
        self.breakpoints.append(after_bb)
        self.continues.append(inc_bb)
        
        # Jump to condition block
        self.builder.branch(cond_bb)
        
        # CONDITION BLOCK
        self.builder.position_at_start(cond_bb)
        cond_val, cond_type = self.__resolve_value(condition)
        
        # Convert condition to i1 if needed
        if isinstance(cond_type, ir.IntType) and cond_type.width > 1:
            zero = ir.Constant(cond_type, 0)
            cond_val = self.builder.icmp_signed('!=', cond_val, zero)
        
        self.builder.cbranch(cond_val, body_bb, after_bb)
        
        # BODY BLOCK
        self.builder.position_at_start(body_bb)
        # Create a new environment for the loop body only
        previous_env = self.env
        self.env = Environment(parent=previous_env)
        self.compile(body)
        self.env = previous_env
        
        # If body didn't end with terminator (break/continue/return), go to increment
        if self.builder.block.terminator is None:
            self.builder.branch(inc_bb)
        
        # INCREMENT BLOCK
        self.builder.position_at_start(inc_bb)
        self.compile(action)
        self.builder.branch(cond_bb)  # Go back to condition check
        
        # AFTER BLOCK
        self.builder.position_at_start(after_bb)
        
        # Clean up
        self.breakpoints.pop()
        self.continues.pop()


    
    def __visit_import_expression(self, node):
        file = node.file
        if self.global_parsed_pallets.get(file) is not None:
            print(f"[warning] : `{file}` is already imported globally \n")
            return
        
        # Use os.path.join for cross-platform compatibility
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "Test", file)
        
        if not os.path.exists(file_path):
            # Try relative path
            file_path = os.path.join("Test", file)
            if not os.path.exists(file_path):
                print(f"Error: File '{file}' not found. Looked in: {file_path}")
                return
        
        with open(file_path, 'r') as f:
            pallet_code = f.read()

        l = Lexer(source=pallet_code)
        p = Parser(lexer=l)
        program = p.parse_program()
        
        # Check for parser errors
        if len(p.errors) > 0:
            print(f"Parsing error in file => {file}")
            for err in p.errors:
                print(err)
            exit(1)
        
        # DON'T create a new environment - compile into the current environment
        # This makes imported functions available to the current scope
        previous_breakpoints = self.breakpoints
        previous_continues = self.continues
        
        # Reset loop control stacks for clean compilation
        self.breakpoints = []
        self.continues = []
        
        # Compile the imported program in the CURRENT environment
        self.compile(node=program)
        
        # Restore loop control stacks
        self.breakpoints = previous_breakpoints
        self.continues = previous_continues
        
        # Store the imported program
        self.global_parsed_pallets[file] = program




    def __resolve_value(self, node, value_type=None):
        match node.type():
            case NodeType.IntegerLiteral:
                node=node
                value, Type = node.value, self.type_map['int' if value_type is None else value_type]
                return ir.Constant(Type, value), Type
            
            case NodeType.FloatLiteral:
                node=node
                value, Type = node.value, self.type_map['float' if value_type is None else value_type]
                return ir.Constant(Type, value), Type
            
            case NodeType.InfixExpression:
                return self.__visit_infixExpression(node)
            
            case NodeType.IdentifierLiteral:
                name = node.value
                result = self.env.lookup(name)
                if result is None:
                    raise Exception(f"Compile error: undefined identifier '{name}' (in node {node})")
                ptr, Type = result
                return self.builder.load(ptr), Type
            
            case NodeType.BooleanLiteral:
                node = node
                return ir.Constant(ir.IntType(1), 1 if node.value else 0), ir.IntType(1)
            
            case NodeType.StringLiteral:
                node = node
                string, Type = self.__convert_string(node.value)
                return string, Type
            
            case NodeType.InfixExpression:
                return self.__visit_infixExpression(node)
            case NodeType.CallExpression:
                return self.__visit_call_expression(node)
            case NodeType.PrefixExpression:
                return self.__visit_prefix_expression(node)
            case NodeType.PostfixExpression:
                return self.__visit_postfix_expression(node)



    def __increment_counter(self):
        self.counter += 1
        return self.counter

    def __convert_string(self, string):
        string = string.replace("\\n", "\n")
        fmt = f"{string}\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=f'__str_{self.__increment_counter()}')
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt
        ptr = self.builder.gep(global_fmt, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
        return ptr, ir.PointerType(ir.IntType(8))

    def builtin_printf(self, params, return_type):
        func, _ = self.env.lookup('printf')

        # First argument: string literal (GlobalVariable)
        fmt_val = params[0]
        if isinstance(fmt_val, ir.GlobalVariable):
            fmt_arg = self.builder.bitcast(fmt_val, ir.IntType(8).as_pointer())
        else:
            fmt_arg = fmt_val

        rest_params = []
        for arg in params[1:]:
            if hasattr(arg, "type"):  # likely an LLVM value
                rest_params.append(arg)
            else:
                # AST node, resolve it
                val, typ = self.__resolve_value(arg)
                rest_params.append(val)

        return self.builder.call(func, [fmt_arg, *rest_params])