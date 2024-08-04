import ast

class IfStatementVisitor(ast.NodeVisitor):
    def __init__(self):
        self.simple_ifs = []        
        self.multi_branch_ifs = []  
        self.nested_ifs = []        
        self.terminating_ifs = []   
        self.loop_included_ifs = [] 
        self.current_function_body = []  

    def visit_FunctionDef(self, node):
        # 访问函数定义节点，存储函数体
        self.current_function_body = node.body
        self.generic_visit(node)

    def visit_If(self, node):
        # 访问 if 语句节点
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
        def contains_raise_or_return(stmt_list):
            """
            递归检查 `if` 语句内部所有代码是否包含 `raise` 或 `return` 语句。
            """
            if isinstance(stmt_list, list):
                return any(
                    isinstance(stmt, (ast.Raise, ast.Return)) or
                    (isinstance(stmt, (ast.If, ast.For, ast.While)) and contains_raise_or_return(stmt.body))
                    for stmt in stmt_list
                )
            return False
        
        def contains_raise(stmt_list):
            # 检查语句列表中是否包含 `raise`
            return any(isinstance(stmt, ast.Raise) for stmt in stmt_list)

        def find_remaining_code_after_if(node):
            """
            获取当前 `if` 语句之后的代码块，直到下一个 `raise` 或 `return` 语句的下一行代码开始。
            """
            remaining_code = []
            # 找到当前 `if` 语句在函数体中的索引
            if node not in self.current_function_body:
                return remaining_code
            
            index = self.current_function_body.index(node)

            
            # 遍历函数体，找到 `if` 语句之后的代码
            for i in range(index + 1, len(self.current_function_body)):
                stmt = self.current_function_body[i]
                print(stmt)
                if isinstance(stmt, (ast.Raise, ast.Return)):
                    # 从 `raise` 或 `return` 语句的下一行开始收集代码
                    remaining_code = self.current_function_body[i:]
                    break
            # print(remaining_code)

            return remaining_code

        # 检查 `if` 语句的 body 部分是否包含 `raise` 或 `return`
        contains_outer_raise_or_return = contains_raise_or_return(node.body)

        if contains_outer_raise_or_return:
            # 检查 `if` 语句之后的剩余代码中是否包含 `raise`
            remaining_code = find_remaining_code_after_if(node)
            contains_raise_in_remaining_code = contains_raise(remaining_code)
            
            return contains_raise_in_remaining_code

        return False

    def is_loop_included_if(self, node):
        # 判断 if 语句是否包含循环
        def find_loops_before_raise(stmt_list):
            for stmt in stmt_list:
                if isinstance(stmt, (ast.For, ast.While)):
                    return True
                if isinstance(stmt, ast.If):
                    if find_loops_before_raise(stmt.body):
                        return True
            return False
        
        def contains_raise_and_return_code(stmt_list):
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
