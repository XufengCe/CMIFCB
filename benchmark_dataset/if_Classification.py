import ast

class IfStatementVisitor(ast.NodeVisitor):
    def __init__(self):
        self.simple_ifs = []
        self.multi_branch_ifs = []
        self.nested_ifs = []
        self.terminating_ifs = []
        self.loop_included_ifs = []
        self.terminating_if_candidates = []

    def visit_If(self, node):
        if self.is_simple_if(node):
            self.simple_ifs.append(node)
        
        if self.is_multi_branch_if(node):
            self.multi_branch_ifs.append(node)
        
        if self.is_nested_if(node):
            self.nested_ifs.append(node)
        
        if self.contains_terminating_stmt(node):
            self.terminating_if_candidates.append(node)
        
        if self.is_loop_included_if(node):
            self.loop_included_ifs.append(node)
        
        self.generic_visit(node)
    
    def is_simple_if(self, node):
        # 检查 `if` 语句是否没有 `else` 或 `elif` 分支
        if node.orelse:
            return False
        
        # 检查 `if` 语句的 body 中是否只有一个 `raise` 语句
        raise_count = sum(isinstance(stmt, ast.Raise) for stmt in node.body)
        if raise_count != 1:
            return False
        
        # 检查 body 中是否仅包含一个 `raise` 语句，没有其他的 `if`、`elif`、`else` 语句
        for stmt in node.body:
            if isinstance(stmt, ast.If) or isinstance(stmt, ast.Raise):
                continue
            else:
                return False

        return True

    def is_multi_branch_if(self, node):
        # 检查是否有多分支结构
        if isinstance(node.orelse, list) and len(node.orelse) > 0:
            return True
        return False

    def is_nested_if(self, node):
        for stmt in node.body:
            if isinstance(stmt, ast.If):
                return True
        return False

    def contains_terminating_stmt(self, node):
        # 检查 `if` 语句的 `body` 是否包含内层 `if` 语句，并且这些内层 `if` 语句中包含 `return` 或 `raise` 语句
        for stmt in node.body:
            if isinstance(stmt, ast.If):
                if self.has_terminating_stmt(stmt):
                    return True
        return False

    def has_terminating_stmt(self, node):
        # 检查内层 `if` 语句中是否包含 `return` 或 `raise` 语句
        if any(isinstance(stmt, (ast.Return, ast.Raise)) for stmt in node.body):
            return True
        for stmt in node.body:
            if isinstance(stmt, ast.If) and self.has_terminating_stmt(stmt):
                return True
        return False

    def is_loop_included_if(self, node):
        for stmt in node.body:
            if isinstance(stmt, (ast.For, ast.While)):
                return True
            if isinstance(stmt, ast.If):
                if any(isinstance(nstmt, (ast.For, ast.While)) for nstmt in stmt.body):
                    return True
        return False

def classify_if_statements(code):
    tree = ast.parse(code)
    visitor = IfStatementVisitor()
    visitor.visit(tree)
    
    terminating_ifs = []
    for candidate in visitor.terminating_if_candidates:
        # 检查候选的 terminating if 是否符合条件
        if any(isinstance(stmt, ast.Raise) for stmt in candidate.body):
            terminating_ifs.append(candidate)
    
    return {
        "simple_ifs": visitor.simple_ifs,
        "multi_branch_ifs": visitor.multi_branch_ifs,
        "nested_ifs": visitor.nested_ifs,
        "terminating_ifs": terminating_ifs,
        "loop_included_ifs": visitor.loop_included_ifs,
    }

