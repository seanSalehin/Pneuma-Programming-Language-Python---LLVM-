from llvmlite import ir

from AST import NodeType, Statement, Expression, Program, ExpressionStatement, InfixExpression, IntegerLiteral, FloatLiteral, IdentifierLiteral
from Environment import Environment
from AST import FunctionStatement, BlockStatement, ReturnStatement, AssignStatement, IfStatement, BooleanLiteral, CallExpression, FunctionParameter, StringLiteral

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
        value = node.return_value
        value, Type = self.__resolve_value(value)
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
        self.env=previous_env
        self.env.define(name, func, return_type)
        self.builder = previous_builder


    def __visit_assign_statement(self, node):
        name = node.ident.value
        value = node.right_value
        value, Type = self.__resolve_value(value)
        if self.env.lookup(name) is None:
            self.errors.append(f"Compile Error: Identifier {name} has not been declared")
        else:
            ptr, _ = self.env.lookup(name)
            self.builder.store(value, ptr)


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
                    else:
                        self.builder.ret_void() 



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
        return global_fmt, global_fmt.type

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