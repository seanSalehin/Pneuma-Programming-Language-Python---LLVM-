from Lexer import Lexer
from Token import Token, TokenType
from typing import Callable
from enum import Enum, auto
from AST import Statement, Expression, Program, ExpressionStatement, InfixExpression, IntegerLiteral, FloatLiteral, IdentifierLiteral, LetStatement
from AST import FunctionStatement, ReturnStatement, BlockStatement, AssignStatement, IfStatement, BooleanLiteral, CallExpression, FunctionParameter, StringLiteral

# precedence Type => evels of operator priority from lowest to highest
class PresedanceType(Enum):
    P_LOWEST=0
    P_EQUALS=auto()
    P_LESSGREATER=auto()
    P_SUM=auto()
    P_CALL=auto()
    P_INDEX=auto()
    P_PREFIX=auto()
    P_EXPONENT=auto()
    P_PRODUCT=auto()




# precedence mapping => Maps token types (like PLUS, MINUS) to their corresponding precedence levels.
PRECEDENCES:dict[TokenType, PresedanceType]={
     TokenType.PLUS: PresedanceType.P_SUM,
     TokenType.MINUS:PresedanceType.P_SUM,
     TokenType.SLASH:PresedanceType.P_PRODUCT,
     TokenType.ASTERISK:PresedanceType.P_PRODUCT,
     TokenType.MODULUS:PresedanceType.P_PRODUCT,
     TokenType.POW:PresedanceType.P_EXPONENT,
     TokenType.EQ_EQ:PresedanceType.P_EQUALS,
     TokenType.NOT_EQ:PresedanceType.P_EQUALS,
     TokenType.LT:PresedanceType.P_LESSGREATER,
     TokenType.GT:PresedanceType.P_LESSGREATER,
     TokenType.LT_EQ:PresedanceType.P_LESSGREATER,
     TokenType.GT_EQ:PresedanceType.P_LESSGREATER,
     TokenType.LEFTPARENTHESES:PresedanceType.P_CALL,
}


class Parser:
    def __init__(self, lexer):
        self.lexer=lexer
        self.errors=[]
        self.current_token=None
        self.peek_token=None

        self.prefix_parse={
            TokenType.IDENT: self.__parse_identifier,
            TokenType.INT:self.__parse_int_literal,
            TokenType.FLOAT:self.__parse_float_literal,
            TokenType.LEFTPARENTHESES:self.__parse_grouped_expression,
            TokenType.IF:self.__parse_if_statement,
            TokenType.TRUE:self.__parse_boolean,
            TokenType.FALSE:self.__parse_boolean,
            TokenType.STRING:self.__parse_string_literal,
        }

        self.infix_parse={
            TokenType.MINUS:self.__parse_infix_expression,
            TokenType.MODULUS: self.__parse_infix_expression,
            TokenType.SLASH: self.__parse_infix_expression,
            TokenType.PLUS: self.__parse_infix_expression,
            TokenType.POW: self.__parse_infix_expression,
            TokenType.ASTERISK: self.__parse_infix_expression,
            TokenType.EQ_EQ: self.__parse_infix_expression,
            TokenType.NOT_EQ: self.__parse_infix_expression,
            TokenType.LT: self.__parse_infix_expression,
            TokenType.GT: self.__parse_infix_expression,
            TokenType.LT_EQ: self.__parse_infix_expression,
            TokenType.GT_EQ: self.__parse_infix_expression,
            TokenType.LEFTPARENTHESES:self.__parse_call_expression,
        }


        #load the first two tokens (Calls twice)
        self.__next_token()
        self.__next_token()



    def __next_token(self):
        #Move current token to the peek token and get the next token from lexer
        self.current_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def __current_token(self, tt:TokenType):
        return self.current_token.type == tt
        


    def __peek_token(self, tt):
        #check the type of the next token
        if self.peek_token is None:
            return False
        return self.peek_token.type == tt
    


    def __peek_error(self, tt):
        self.errors.append(f"Expected next token to be {tt}, not {self.peek_token.type}")



    def __expect_peek(self, tt):
        #ensure the next token matches an expected type
        if self.__peek_token(tt):
           self.__next_token()
           return True
        else:
            self.__peek_error(tt)
            return False



    def __no_prefix_parse_error(self, tt):
        #error when no parsing function exists for the current token
        if self.current_token:
            self.errors.append(f"No prefix parse function for {tt} found, current token is {self.current_token.type}")
        else:
            self.errors.append(f"No prefix parse function for {tt} found, current token is None")



    def __current_precedence(self):
        if self.current_token is None:
            return PresedanceType.P_LOWEST
        prec = PRECEDENCES.get(self.current_token.type)
        if prec is None:
            #return the lowest by default if the prec in None
            return PresedanceType.P_LOWEST
        return prec
    


    def __peek_precedence(self):
        if self.peek_token is None:
            return PresedanceType.P_LOWEST
        prec = PRECEDENCES.get(self.peek_token.type)
        if prec is None:
            return PresedanceType.P_LOWEST
        return prec
    

    #Main execution point of the parser
    def parse_program(self):
        program=Program()
        while self.current_token.type != TokenType.EOF:
            stmt=self.__parse_statement()
            if stmt is not None:
                program.statements.append(stmt)
            self.__next_token()
        return program
    

    #statement methods
    def __parse_statement(self):
        if self.current_token.type ==TokenType.IDENT and self.__peek_token(TokenType.EQ):
            return self.__parse_assignment_statement()
        
        match self.current_token.type:
            case TokenType.LET:
                return self.__parse_let_statement()
            case TokenType.ACT:
                return self.__parser_function_statement()
            case TokenType.RETURN:
                return self.__parser_return_statement()
            case _:
                return self.__parse_expression_statement()
    
    
    def __parse_expression_statement(self):
        expr=self.__parse_expression(PresedanceType.P_LOWEST)
        #if we rech : it's mean the expression is done
        if self.__peek_token(TokenType.SEMICOLON):
            self.__next_token()
        # e => based on AST (ExpressionStatement)
        stmt=ExpressionStatement(e=expr)
        return stmt




    def __parse_let_statement(self):
        # mark a:int = 10;
        stmt: LetStatement=LetStatement()
        if not self.__expect_peek(TokenType.IDENT):
            #mark
            return None

        stmt.name=IdentifierLiteral(value=self.current_token.literal)
             #a

        if not self.__expect_peek(TokenType.COLON):
            #:
            return None
        
        if not self.__expect_peek(TokenType.TYPE):
            #int
            return None
        
        stmt.value_type = self.current_token.literal
            # error 
        
        if not self.__expect_peek(TokenType.EQ):
            #=
            return None
        self.__next_token()

        stmt.value=self.__parse_expression(PresedanceType.P_LOWEST)

        while not self.__current_token(TokenType.SEMICOLON) and not self.__current_token(TokenType.EOF):
            self.__next_token()

        return stmt
    


    def __parser_function_statement(self):
        #act test()=>int{return 10;}
        stmt = FunctionStatement()
        if not self.__expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = IdentifierLiteral(value=self.current_token.literal)

        if not self.__expect_peek(TokenType.LEFTPARENTHESES):
            return None
        stmt.parameters= self.__parse_function_parameters()
        
        if not self.__expect_peek(TokenType.ARROW):
            return None
        
        if not self.__expect_peek(TokenType.TYPE):
            return None
        
        stmt.return_type=self.current_token.literal

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        
        stmt.body=self.__parse_block_statement()
        return stmt
        

    def __parse_function_parameters(self):
        params = []
        if self.__peek_token(TokenType.RIGHTPARENTHESES):
            self.__next_token()  # Consume the RIGHTPARENTHESES
            return params
        
        self.__next_token()  # Move to first parameter
        
        # Parse first parameter
        param_name = FunctionParameter(name=self.current_token.literal)
        if not self.__expect_peek(TokenType.COLON):
            return None
        self.__next_token()
        param_name.value_type = self.current_token.literal        
        params.append(param_name)            
        # Parse additional parameters
        while self.__peek_token(TokenType.COMMA):
            self.__next_token()  # Move to COMMA
            self.__next_token()  # Move to next parameter name
            param = FunctionParameter(name= self.current_token.literal)
            if not self.__expect_peek(TokenType.COLON):
                return None
            self.__next_token()
            param.value_type = self.current_token.literal
            params.append(param)        
        # Expect and consume the closing parenthesis
        if not self.__expect_peek(TokenType.RIGHTPARENTHESES):
            return None
        return params



    def __parser_return_statement(self):
        stmt = ReturnStatement()
        self.__next_token()
        stmt.return_value=self.__parse_expression(PresedanceType.P_LOWEST)
        if not self.__expect_peek(TokenType.SEMICOLON):
            return None
        return stmt



    def __parse_block_statement(self):
        block_stmt = BlockStatement()
        self.__next_token()
        while not self.__current_token(TokenType.RBRACE) and not self.__current_token(TokenType.EOF):
            stmt = self.__parse_statement()
            if stmt is not None:
                block_stmt.statements.append(stmt)
            self.__next_token()
        return block_stmt
    

    def __parse_assignment_statement(self):
        stmt = AssignStatement()
        stmt.ident = IdentifierLiteral(value = self.current_token.literal)
        self.__next_token()
        self.__next_token()
        stmt.right_value = self.__parse_expression(PresedanceType.P_LOWEST)
        self.__next_token()
        return stmt

        



    def __current_token_is(self, tt: TokenType):
        return self.current_token.type == tt
        


    def __parse_if_statement(self):
        condition = None
        consequence = None
        alternative = None

        self.__next_token()
        condition=self.__parse_expression(PresedanceType.P_LOWEST)
        if not self.__expect_peek(TokenType.LBRACE):
            return None
        consequence=self.__parse_block_statement()
        if self.__peek_token(TokenType.ELSE):
            self.__next_token()
            if not self.__expect_peek(TokenType.LBRACE):
                return None
            alternative = self.__parse_block_statement()
        return IfStatement(condition, consequence, alternative)
        

    #Expression method
    def __parse_expression(self, precedence):
        prefix_function=self.prefix_parse.get(self.current_token.type)
        if prefix_function is None:
            self.__no_prefix_parse_error(self.current_token.type)
            return None
        left_expr=prefix_function()

        while (self.peek_token is not None and 
            not self.__peek_token(TokenType.SEMICOLON) and 
            precedence.value < self.__peek_precedence().value):
            infix_function=self.infix_parse.get(self.peek_token.type)
            if infix_function is None:
                return left_expr
            self.__next_token()
            left_expr=infix_function(left_expr)
        return left_expr



    def __parse_infix_expression(self, left_node):
        infix_exp = InfixExpression(left_node=left_node, operator=self.current_token.literal)
        precedence = self.__current_precedence()
        self.__next_token()
        infix_exp.right_node=self.__parse_expression(precedence)
        return infix_exp
    

    def __parse_grouped_expression(self):
        self.__next_token()
        expr=self.__parse_expression(PresedanceType.P_LOWEST)
        if not self.__expect_peek(TokenType.RIGHTPARENTHESES):
            #if the last one is not a parentheses => syntax error
            return None
        return expr
    

    def __parse_call_expression(self, function):
        expr = CallExpression(function=function)
        expr.arguments = self.__parse_expression_list(TokenType.RIGHTPARENTHESES)
        return expr
    

    def __parse_expression_list(self, end):
        e_list = []
        if self.__peek_token(end):
            self.__next_token()
            return e_list
        self.__next_token()
        e_list.append(self.__parse_expression(PresedanceType.P_LOWEST))
        while self.__peek_token(TokenType.COMMA):
            self.__next_token()
            self.__next_token()
            e_list.append(self.__parse_expression(PresedanceType.P_LOWEST))
        if not self.__expect_peek(end):
            return None
        return e_list




    

    #prefix methods
    def __parse_int_literal(self):
        try:
            value = int(self.current_token.literal)
        except:
            self.errors.append("could not parse this as an Integer")
            return None
        int_lit = IntegerLiteral(value)
        return int_lit
    

    def __parse_identifier(self):
        return IdentifierLiteral(value=self.current_token.literal)
    

    def __parse_float_literal(self):
        try:
            value=float(self.current_token.literal)
            float_lit=FloatLiteral(value)
        except:
            self.errors.append("could not parse this as an Intiger")
            return None
        return float_lit
    

    def __parse_boolean(self):
        return BooleanLiteral(value=self.__current_token(TokenType.TRUE))
    

    def __parse_string_literal(self):
        return StringLiteral(value = self.current_token.literal)