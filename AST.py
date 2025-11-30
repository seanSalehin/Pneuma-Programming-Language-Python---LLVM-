#Abstract Syntax Tree =>showing only meaningful parts like expressions and statements without extra syntax details.
from abc import ABC, abstractmethod
from enum import Enum

class NodeType(Enum):
    Program="Program"
    ExpressionStatement = "ExpressionStatement"
    LetStatement = "LetStatement"
    InfixExpression = "InfixExpression"
    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"
    IdentifierLiteral = "IdentifierLiteral"
    FunctionStatement = "FunctionStatement"
    BlockStatement = "BlockStatement"
    ReturnStatement = "ReturnStatement"
    AssignStatement = "AssignStatement"
    IfStatement = "IfStatement"
    BooleanLiteral = "BooleanLiteral"
    CallExpression = "CallExpression"
    FunctionParameter = "FunctionParameter"
    StringLiteral = "StringLiteral"


class Node(ABC):
    #each node represents a piece of the program's syntax.
    #each node has type and can be converted to JSON.
    @abstractmethod
    def type(self):
        pass


    @abstractmethod
    #for debuging
    def json(self):
        pass


    
class Statement(Node):
    pass

class Expression(Node):
    pass

class Program(Node):
    def __init__(self):
        self.statements=[]
    
    def type(self):
        return NodeType.Program
    
    def json(self):
        return {
            "type":self.type().value,
            "statements":[{stmt.type().value:stmt.json()}for stmt in self.statements]
        }
    

class LetStatement(Statement):
    def __init__(self, name:Expression = None, value:Expression=None, value_type:str=None) -> None:
        self.name=name
        self.value=value
        self.value_type=value_type

    def type(self) -> NodeType:
        return NodeType.LetStatement

    def json(self) -> dict:
        return{
            "type":self.type().value,
            "name":self.name.json(),
            "value":self.value.json(),
            "value_type":self.value_type
        }
    

class BlockStatement(Statement):
    def __init__(self, statements=None):
        self.statements = statements if statements is not None else []
    def type(self):
        return NodeType.BlockStatement
    def json(self):
        return{
            "type": self.type().value,
            "statement": [stmt.json() for stmt in self.statements]
        }
    

class ReturnStatement(Statement):
    def __init__(self, return_value=Expression):
        self.return_value = return_value
    def type(self):
        return NodeType.ReturnStatement
    def json(self):
        return{
            "type": self.type().value,
            "return_value": self.return_value.json()
        }
    


class FunctionStatement(Statement):
    def __init__(self, parameters=[], body:BlockStatement = None, name=None, return_type=None ):
        self.parameters=parameters
        self.body=body
        self.name=name
        self.return_type=return_type
    def type(self):
        return NodeType.FunctionStatement
    def json(self):
        return{
            "type": self.type().value,
            "name": self.name.json(),
            "return_type": self.return_type,
            "parameters":[p.json() for p in self.parameters],
            "body":self.body.json() if self.body is not None else None
        }
    


class AssignStatement(Statement):
    def __init__(self, ident:Expression=None, right_value = None ):
        self.ident = ident
        self.right_value=right_value
    def type(self):
        return NodeType.AssignStatement
    def json(self):
        return{
            "type": self.type().value,
            "ident": self.ident.json(),
            "right_value":self.right_value.json()
        }
    

class IfStatement(Statement):
    def __init__(self, condition=None, consequence=None, alternative=None):
        self.condition = condition
        self.consequence=consequence
        self.alternative = alternative
    def type(self):
        return NodeType.IfStatement
    def json(self):
        return{
            "type": self.type().value,
            "condition":self.condition.json(),
            "consequence": self.consequence.json(),
            "alternative": self.alternative.json() if self.alternative is not None else None
        }



class FunctionParameter(Expression):
    def __init__(self, name, value_type=None):
        self.name=name
        self.value_type=value_type
    def type(self):
        return NodeType.FunctionParameter
    def json(self):
        return {
            "type":self.type().value,
            "name":self.name,
            "value_type":self.value_type
        }


#statement
class ExpressionStatement(Statement):
    def __init__(self, e):
        self.e=e

    def type(self):
        return NodeType.ExpressionStatement

    def json(self):
        return{
            "type":self.type().value,
            "e":self.e.json()
        }
    

#expressions
class InfixExpression(Expression):
    def __init__(self, left_node, operator, right_node=None):
        self.left_node=left_node
        self.operator=operator
        self.right_node=right_node

    def type(self):
        return NodeType.InfixExpression
    
    def json(self):
        return {
            "type":self.type().value,
            "left_node":self.left_node.json(),
            "operator":self.operator,
            "right_node":self.right_node.json()
        }
    


class CallExpression(Expression):
    def __init__(self, function = None, arguments=None):
        self.function=function
        self.arguments = arguments

    def type(self):
        return NodeType.CallExpression
    
    def json(self):
        return {
            "type":self.type().value,
            "function":self.function.json(),
            "arguments":[arg.json() for arg in self.arguments]
        }
    

#Literals
class IntegerLiteral(Expression):
    def __init__(self, value):
        self.value=value
    
    def type(self):
        return NodeType.IntegerLiteral
    
    def json(self):
        return {
            "type":self.type().value,
            "value":self.value
        }
    


class FloatLiteral(Expression):
    def __init__(self, value):
        self.value=value
    
    def type(self):
        return NodeType.FloatLiteral
    
    def json(self):
        return {
            "type":self.type().value,
            "value":self.value
        }
    


#IdentifierLiteral
class IdentifierLiteral(Expression):
    def __init__(self, value=None):
        self.value = value

    def type(self):
        return NodeType.IdentifierLiteral

    def json(self):
        return {
            "type": self.type().value,
            "value": self.value
        }
    
class BooleanLiteral(Expression):
    def __init__(self, value=None):
        self.value = value

    def type(self):
        return NodeType.BooleanLiteral

    def json(self):
        return {
            "type": self.type().value,
            "value": self.value
        }
    


class StringLiteral(Expression):
    def __init__(self, value=None):
        self.value = value

    def type(self):
        return NodeType.StringLiteral

    def json(self):
        return {
            "type": self.type().value,
            "value": self.value
        }
