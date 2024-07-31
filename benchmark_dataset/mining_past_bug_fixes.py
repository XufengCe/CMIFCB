import re
from pydriller import Repository
# from .utils import run_merge_responses
import ast
import astor
from typing import List, Tuple


raise_line = {}

"""
Constructs a list of tuple containing information about commits that fix bugs in python files from a given range of repositories.

Parameters:
    repo_url (str): 

Returns:
    List[Tuple[str, str, str, str]]: A list of tuples containing the repository url, filename, old code and new code for commits that fix bugs in python files.
"""
def construct_pairs(repo_url):
    if_files_list = []
    for commit in Repository(repo_url).traverse_commits():
        if 'fix' in commit.msg.lower() or 'bug' in commit.msg.lower():
            for m in commit.modified_files:
                if m.filename.endswith('.py'):
                    old = m.source_code_before
                    new = m.source_code
                    if old is not None and new is not None:
                        if_files_list.append((repo_url+'/commit/'+commit.hash, m.filename, old, new))
    return if_files_list


"""
Extracts the function as a string from the given code.

Parameters:
    file_content (str): The python file content.

Returns:
    List[str]: A list of strings containing the extracted functions.
"""
def extract_functions(file_content):
    tree = ast.parse(file_content)
    functions = []

    class FunctionExtractor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            function_code = ast.get_source_segment(file_content, node)
            functions.append(function_code)
            self.generic_visit(node)

    extractor = FunctionExtractor()
    extractor.visit(tree)
    return functions
# # Remove the lines after the else statement
# # Ignore this function for now
# def remove_lines_after_else(code):
#     # Parse the code into an AST
#     tree = ast.parse(code)
    
#     # Define a helper function to unparse nodes back to source code
#     def unparse_node(node):
#         try:
#             return ast.unparse(node)
#         except AttributeError:
#             import astor
#             return astor.to_source(node).strip()

#     # Traverse the AST
#     for node in ast.walk(tree):
#         # Check if the node is an if statement
#         if isinstance(node, ast.If):
#             # Check if the orelse part contains elif with raise statement and if with raise statement
#             has_raise_in_body = any(isinstance(child, ast.Raise) for child in node.body)
#             if has_raise_in_body:
#                 # Remove the lines after the else statement
#                 node.orelse = []
#                 return unparse_node(node)
#     return code

# Define a helper function to unparse nodes back to source code
def unparse_node(node):
    try:
        return ast.unparse(node)
    except AttributeError:
        return astor.to_source(node).strip()


class IfRaiseTransformer(ast.NodeTransformer):
    def visit_If(self, node):
        # Visit the body of the if statement
        self.generic_visit(node)
        
        def remove_lines_until_raise(body):
            for i, stmt in enumerate(body):
                # if isinstance(body[i], ast.If) and len(body[i].orelse) == 0:
                #     return
                if isinstance(stmt, ast.Raise):
                    return [stmt]
            return body

        # Modify the body of the if statement
        node.body = remove_lines_until_raise(node.body)

        # Modify elif and else blocks recursively
        for i, stmt in enumerate(node.orelse):
            if isinstance(stmt, ast.If):
                node.orelse[i] = self.visit_If(stmt)
            elif isinstance(stmt, list):
                node.orelse[i] = remove_lines_until_raise(stmt)
            else:
                node.orelse[i] = stmt

        return node

def remove_lines_between(code: str) -> str:
    # Parse the code into an AST
    tree = ast.parse(code)
    
    # Transform the AST
    transformer = IfRaiseTransformer()
    transformed_tree = transformer.visit(tree)
    
    # Unparse the AST back into code
    new_code = astor.to_source(transformed_tree)
    print('raise statement found', new_code)
    return new_code

# Remove the lines until the raise statement

def if_elif_else_block(node, result):
    if isinstance(node, ast.If):
        result.append("if " + unparse_node(node.test) + " : " + unparse_node(node.body[0]))
        if_elif_else_block(node.orelse[0], result)
    else:
        result.append("else : " + unparse_node(node))
        

# Extract raise statements from an AST If node
def extract_raise_statements(node) -> List[str]:
    # Check if the node is an if_elif_else block or if_else block
    result = []
    if node.orelse:
        # print("This is an if_elif_else block\n")
        # Extract raise statements from the all the if and elif, and else blocks
        if_elif_else_block(node, result)
    else:
        # print("This is an if block\n")
        if isinstance(node.body[0], ast.If):
            # Check if the there are other if statements in the block
            if len(node.body) > 1:
                raise_node = None
                # If there are other if statements, make sure the if statement have orlese block
                for i in range(len(node.body) - 1, -1, -1):
                    if isinstance(node.body[i], ast.Raise):
                        raise_node = node.body[i]
                    if isinstance(node.body[i], ast.If) and not node.body[i].orelse and raise_node:
                        # Negate the condition use ast.UnaryOp to get the negation of the condition
                        negated_condition = ast.UnaryOp(op=ast.Not(), operand=node.body[i].test)
                        result.append("if " + unparse_node(negated_condition) + " : " + unparse_node(raise_node))
                        break

            else:
                negated_condition = ast.UnaryOp(op=ast.Not(), operand=node.body[0].test)
                result.append("if " + unparse_node(negated_condition) + " : " + unparse_node(node.body[0]))
        else:
            # Ignore the line that is not if or raise statement
            if_str = unparse_node(node.test)
            for i in range(0, len(node.body)):
                if isinstance(node.body[i], ast.Raise):
                    result.append("if " + if_str + " : " + unparse_node(node.body[i]))
                    break

    return result
                
                        
"""
Extracts the condition raise statements from the given function code.
Return the list of condistion raise statements

Parameters:
    code (str): The function code.

Returns:
    List[str]: A list of strings containing the extracted condition raise statements.

"""
def extract_condition_raise_statements(code) -> List[str]:
    code = code.strip()
    result = []
    # Parse the code into an AST
    tree = ast.parse(code)
    # Traverse the AST
    if_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            if_node = node
            # print("Node:")
            # print(unparse_node(node))
            # print("isinstance of node is:" + type(node).__name__)
            # print()
            result.extend(extract_raise_statements(node))

            # result.extend(extract_raise_statements(node))
        elif isinstance(node, ast.Raise) and if_node and (node.col_offset == 4 or node.col_offset == 2):
            if len(if_node.body) > 1:
                for n in if_node.body:
                    # If there are if statements and is not closed with an else block
                    if isinstance(n, ast.If) and not n.orelse:
                        negated_condition = ast.UnaryOp(op=ast.Not(), operand=n.test)
                        result.append("if " + unparse_node(negated_condition) + " : " + unparse_node(node))
                        break
            else:
                negated_condition = ast.UnaryOp(op=ast.Not(), operand=if_node.test)
                result.append("if " + unparse_node(negated_condition) + " : " + unparse_node(node))
            

            
    return list(set(result))


