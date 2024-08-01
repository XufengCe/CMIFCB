import ast

class IfStatementVisitor(ast.NodeVisitor):
    def __init__(self):
        self.simple_ifs = []
        self.multi_branch_ifs = []
        self.nested_ifs = []
        self.terminating_ifs = []
        self.loop_included_ifs = []

    def visit_If(self, node):
        if self.is_simple_if(node):
            self.simple_ifs.append(node)
        
        if self.is_multi_branch_if(node):
            self.multi_branch_ifs.append(node)
        
        if self.is_nested_if(node):
            self.nested_ifs.append(node)
        
        if self.is_terminating_if(node):
            self.terminating_ifs.append(node)
        
        if self.is_loop_included_if(node):
            self.loop_included_ifs.append(node)
        
        self.generic_visit(node)
    
    def is_simple_if(self, node):
        # 如果 `if` 语句存在 `else` 或 `elif` 分支
        if node.orelse:
            # 检查 `if` 语句内部是否存在 `raise` 语句
            contains_raise_in_if = any(isinstance(stmt, ast.Raise) for stmt in node.body)

            # 检查 `else` 或 `elif` 分支中是否存在 `raise` 语句
            contains_raise_in_orelse = any(isinstance(stmt, ast.Raise) for stmt in node.orelse)

            # 如果 `if` 语句存在 `raise` 语句，并且 `else` 或 `elif` 分支不存在 `raise` 语句，返回 True
            return contains_raise_in_if and not contains_raise_in_orelse
        else:
            contains_raise = False

            for stmt in node.body:
                if isinstance(stmt, ast.Raise):
                    contains_raise = True
                if isinstance(stmt, ast.If):
                    # 如果内层 `if` 语句的 body 中包含 `raise` 语句，则返回 False
                    if any(isinstance(inner_stmt, ast.Raise) for inner_stmt in stmt.body):
                        return False
                for i, stmt in enumerate(node.body): # 根据索引来访问下一行代码
                    if i + 1 < len(node.body):
                        stmt = node.body[i + 1]
                    else:
                        return contains_raise        

            return contains_raise

    def is_multi_branch_if(self, node):
        # 检查是否有多分支结构（即存在 else 或 elif 分支）
        has_multiple_branches = isinstance(node.orelse, list) and len(node.orelse) > 0

        # 检查 else 或 elif 分支中是否包含 raise 语句
        contains_raise_in_orelse = any(
            isinstance(stmt, ast.Raise) for stmt in node.orelse
        )

        return has_multiple_branches and contains_raise_in_orelse

    def is_nested_if(self, node):
        def contains_nested_if_with_raise(node):
            for stmt in node.body:
                if isinstance(stmt, ast.If):
                    # 检查内层 if 语句的 body 中是否包含 raise 语句
                    if any(isinstance(inner_stmt, ast.Raise) for inner_stmt in stmt.body):
                        return True
                    # 递归检查内层 if 语句的 body 和 orelse 部分
                    if self.is_nested_if(stmt):
                        return True
                elif isinstance(stmt, ast.If):
                    # 如果在 body 中找到内层的 if 语句，递归检查这个内层 if 语句
                    if contains_nested_if_with_raise(stmt):
                        return True
            
            return False

        return contains_nested_if_with_raise(node)


    def is_terminating_if(self, node):
        contains_outer_raise = False
        
        for stmt in node.body:
            # 检查外层的 if 语句中是否存在 `raise` 语句
            if isinstance(stmt, ast.Raise):
                contains_outer_raise = True
                break

        if contains_outer_raise and not self.is_simple_if(node):
            for stmt in node.body:
                if isinstance(stmt, ast.If):
                    # 检查内层的 if 语句中是否包含 `return` 或 `raise` 语句
                    if any(isinstance(inner_stmt, (ast.Return, ast.Raise)) for inner_stmt in stmt.body):
                        return True
                    # 递归检查嵌套的 if 语句
                    if self.is_terminating_if(stmt):
                        return True

        return False

    def is_loop_included_if(self, node):
        def find_loops_before_raise(stmt_list):
            for stmt in stmt_list:
                if isinstance(stmt, (ast.For, ast.While)):
                    return True
                if isinstance(stmt, ast.If):
                    if find_loops_before_raise(stmt.body):
                        return True
            return False
        
        def contains_raise_and_return_code(stmt_list):
            """
            检查语句列表是否包含 `raise` 语句，如果包含，则返回从最外层 `if` 语句到 `raise` 语句之间的所有代码段。
            """
            code_block = []
            for stmt in stmt_list:
                code_block.append(stmt)
                if isinstance(stmt, ast.Raise):
                    return code_block
                elif isinstance(stmt, (ast.If, ast.For, ast.While)):
                    nested_code_block = contains_raise_and_return_code(stmt.body)
                    if nested_code_block:
                        return code_block + nested_code_block
            return False

        raise_code_block = contains_raise_and_return_code(node.body)
        if raise_code_block:
            return find_loops_before_raise(raise_code_block)
        else:
            return False



def classify_if_statements(code):
    tree = ast.parse(code)
    visitor = IfStatementVisitor()
    visitor.visit(tree)
    
    return {
        "simple_ifs": visitor.simple_ifs,
        "multi_branch_ifs": visitor.multi_branch_ifs,
        "nested_ifs": visitor.nested_ifs,
        "terminating_ifs": visitor.terminating_ifs,
        "loop_included_ifs": visitor.loop_included_ifs,
    }