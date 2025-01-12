# expression parser/evaluator

token_t = int|str

def tokenize_int(expr: str) -> list[token_t]:
    '''
    tokenize an integer expression
    '''
    ret: list[token_t] = []
    raise NotImplementedError()

def evalexpr_int(expr: str, vars: dict[str,int]) -> int:
    '''
    evaluate an integer expression
    '''
    raise NotImplementedError()

if __name__ == '__main__':
    pass
