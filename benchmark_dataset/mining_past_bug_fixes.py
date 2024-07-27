import re
from pydriller import Repository
# from .utils import run_merge_responses
import ast
import astor
from typing import List, Tuple

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

# Remove the lines after the else statement
# Ignore this function for now
def remove_lines_after_else(code):
    # Parse the code into an AST
    tree = ast.parse(code)
    
    # Define a helper function to unparse nodes back to source code
    def unparse_node(node):
        try:
            return ast.unparse(node)
        except AttributeError:
            import astor
            return astor.to_source(node).strip()

    # Traverse the AST
    for node in ast.walk(tree):
        # Check if the node is an if statement
        if isinstance(node, ast.If):
            # Check if the orelse part contains elif with raise statement and if with raise statement
            has_raise_in_body = any(isinstance(child, ast.Raise) for child in node.body)
            if has_raise_in_body:
                # Remove the lines after the else statement
                node.orelse = []
                return unparse_node(node)
    return code


class IfRaiseTransformer(ast.NodeTransformer):
    def visit_If(self, node):
        # Visit the body of the if statement
        self.generic_visit(node)
        
        def remove_lines_until_raise(body):
            for i, stmt in enumerate(body):
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
    
    return new_code


"""
Extracts the condition raise statements from the given function code.
Return the list of condistion raise statements

Parameters:
    code (str): The function code.

Returns:
    List[str]: A list of strings containing the extracted condition raise statements.

"""
def extract_condition_raise_statements(code) -> List[str]:
    code.strip()
    condition_raise_list = []
    # Parse the code into an AST
    tree = ast.parse(code)
    
    
    # Define a helper function to unparse nodes back to source code
    def unparse_node(node):
        try:
            return ast.unparse(node)
        except AttributeError:
            import astor
            return astor.to_source(node).strip()

    # Traverse the AST
    for node in ast.walk(tree):
        # Check if the node is an if statement
        if isinstance(node, ast.If):
            
            # Check if the orelse part contains elif with raise statement and if with raise statement
            has_raise_in_body = any(isinstance(child, ast.Raise) for child in node.body)
            if has_raise_in_body:

                temp = remove_lines_between(unparse_node(node))
                # temp = remove_lines_after_else(temp)
                # print(temp)
                # if b % 2 == 0 and b % 3 == 0:\n    raise OSError('error')\n
                # will be if b % 2 == 0 and b % 3 == 0 : raise OSError('error')\n
                temp = temp.split(':\n')
                temp = temp[0].strip() + ' : ' + temp[1].strip()

                
                condition_raise_list.append(temp)
    return condition_raise_list