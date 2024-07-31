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
            # 检查当前节点的 body 是否有嵌套的 if 语句，并且这些 if 语句的 body 中是否包含 raise 语句
            if isinstance(node, ast.If):
                if any(isinstance(inner_stmt, ast.Raise) for inner_stmt in node.body):
                    return True

                # 递归检查 body 中的语句
                for stmt in node.body:
                    if isinstance(stmt, ast.If):
                        if contains_nested_if_with_raise(stmt):
                            return True
                    elif isinstance(stmt, ast.AST):  # 递归检查其他 AST 节点
                        if contains_nested_if_with_raise(stmt):
                            return True

                # 递归检查 orelse 中的语句
                for stmt in node.orelse:
                    if isinstance(stmt, ast.If):
                        if contains_nested_if_with_raise(stmt):
                            return True
                    elif isinstance(stmt, ast.AST):  # 递归检查其他 AST 节点
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
        for stmt in node.body:
            # 如果是 raise 语句，检查上文是否有 for 或 while 循环
            if isinstance(stmt, ast.Raise):
                for prev_stmt in node.body[:node.body.index(stmt)]:
                    if isinstance(prev_stmt, (ast.For, ast.While)):
                        return True
                    if isinstance(prev_stmt, ast.If):
                        if any(isinstance(nstmt, (ast.For, ast.While)) for nstmt in prev_stmt.body):
                            return True
            if isinstance(stmt, ast.If):  # 检查是否是嵌套的 if 语句
                if any(isinstance(nstmt, (ast.For, ast.While)) for nstmt in stmt.body):  # 检查嵌套的 if 语句的主体
                    return True
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