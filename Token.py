from enum import Enum
from typing import Any

class TokenType(Enum):
    #End of file token
    EOF = "EOF"

    #Lexor Error
    ILLEGAL = "ILLEGAL"
    
    #Data Types
    IDENT = "IDENT"
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING" 

    #Arithmatic Symbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    POW = "POW"
    MODULUS = "MODULUS"

    #Assignment Symbols
    EQ = "EQ"
    PLUS_EQ = "PLUS_EQ"
    MINUS_EQ = "MINUS_EQ"
    MUL_EQ = "MUL_EQ"
    DIV_EQ = "DIV_EQ"
    PLUS_PLUS = "PLUS_PLUS"
    MINUS_MINUS = "MINUS_MINUS"

    #Comparison SYmbols
    LT = '<'
    GT = '>'
    EQ_EQ = '=='
    NOT_EQ = '!='
    LT_EQ = '<='
    GT_EQ = '>='

    #Symbols
    COLON = "COLON"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    LEFTPARENTHESES = "LEFTPARENTHESES"
    RIGHTPARENTHESES="RIGHTPARENTHESES"
    ARROW = "ARROW"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    BANG = "BANG"


    #Syntax - Keywords
    LET = "LET"
    ACT = "ACT"
    RETURN = "RETURN"
    IF = "IF"
    ELSE = "ELSE"
    TRUE = "TRUE"
    FALSE = "FALSE"
    WHILE = "WHILE"
    CONTINUE = "CONTINUE"
    BREAK = "BREAK"
    FOR = "FOR"

    #Syntax - Typing
    TYPE = "TYPE"


class Token:
    def __init__(self, type, literal, line_number, position):
        self.type=type
        self.literal=literal
        self.line_number=line_number
        self.position=position
        
    #error
    def __str__(self):
        return f"Token[{self.type}:{self.literal}:Line{self.line_number}:Position{self.position}]"
        
    #representing
    def __repr__(self):
        return str(self)
            

KEYWORDS: dict[str, TokenType] = {
    "let":TokenType.LET,
    "act":TokenType.ACT,
    "return":TokenType.RETURN,
    "if":TokenType.IF,
    "else":TokenType.ELSE,
    "true":TokenType.TRUE,
    "false":TokenType.FALSE,
    "while": TokenType.WHILE,
    "continue":TokenType.CONTINUE,
    "break":TokenType.BREAK,
    "for":TokenType.FOR,

}

ALT_KEYWORDS: dict[str, TokenType]={
    "mark": TokenType.LET,
    "=": TokenType.EQ,
    ";" : TokenType.SEMICOLON,
    "act":TokenType.ACT,
    "return":TokenType.RETURN,
    "=>": TokenType.ARROW,
    "if":TokenType.IF,
    "else":TokenType.ELSE,
    "while":TokenType.WHILE,
    "break":TokenType.BREAK,
    "continue":TokenType.CONTINUE,
    "scan": TokenType.FOR,
}

TYPE_KEYWORDS: list[str] = ["int", "float", "str", "void"]

def lookup_ident(ident:str) -> TokenType:
    tt: TokenType | None = KEYWORDS.get(ident)
    if tt is not None:
        return tt
    tt: TokenType|None = ALT_KEYWORDS.get(ident)
    if tt is not None:
        return tt

    if ident in TYPE_KEYWORDS:
        return TokenType.TYPE
    
    return TokenType.IDENT