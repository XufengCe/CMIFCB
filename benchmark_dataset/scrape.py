from mining_past_bug_fixes import extract_functions, extract_condition_raise_statements, construct_pairs, extract_c_m_f
import json
import time
from multiprocessing import Pool, cpu_count
import inspect
import difflib
import ast


def check_if_there_is_raise(line, func):
    tree = ast.parse(func)
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            x = 0
            for n in ast.walk(node):
                if line == ast.unparse(n).strip():
                    # return True
                    x = 1
                if x == 1 and isinstance(n, ast.Raise):
                    return True
    return False
def check_c_m_change(old_func, new_func):
    diff = difflib.ndiff(old_func.splitlines(), new_func.splitlines())

    for line in diff:
        # print("line", line)
        if line.startswith('-'):
            
            line = line.replace('-', '')
            line = line.replace(':', '')
            if 'if' in line:
                line = line.replace('if', '')
            elif 'elif' in line:
                line = line.replace('elif', '')

            elif 'raise' in line:
                return True
            else:
                continue
            if check_if_there_is_raise(line.strip(), old_func):
                return True
        if line.startswith('+'):
            line = line.replace('+', '')
            line = line.replace(':', '')
            if 'if' in line:
                line = line.replace('if', '')
            elif 'elif' in line:
                line = line.replace('elif', '')
            elif 'raise' in line:
                return True
            else:
                continue
            if check_if_there_is_raise(line.strip(), new_func):
                return True
    return False


def process_link(link):
    print("Processing link: ", link)

    # pairs = construct_pairs('https://github.com/sola-st/Dynapyt')
    # pairs = construct_pairs('https://github.com/ActivityWatch/aw-core')
    try:

        pairs = construct_pairs(link)
    except Exception as e:
        print(e)
        return [], [], [], []

    old_func = []
    new_func = []
    c_m_f_match_all = []
    c_m_f_no_match_all = []
    # Each pair is a tuple of 4 elements: (commit_link, file_name, old_code, new_code)
    for pair in pairs:
        try:
            old_functions, old_function_names = extract_functions(pair[2])
            
            new_functions, new_function_names = extract_functions(pair[3])
        except Exception as e:
            # print(e)
            continue
        old_func.append(old_functions)
        new_func.append(new_functions)

        # Loop through all the functions in the old code and new code
        for i in range(len(old_functions)):
            # Looking for the function in the new code
            for j in range(len(new_functions)):

                if old_function_names[i] == new_function_names[j] and old_functions[i] != new_functions[j] and check_c_m_change(old_functions[i], new_functions[j]):
                    c_m_f_old = extract_c_m_f(old_functions[i])
                    c_m_f_new = extract_c_m_f(new_functions[j])
                    
                    # Loop through all the condition raise statements in the old code and new code in one function
                    c_m_f_match = {}
                    c_m_f_no_match = {}
                    for c, m, f in c_m_f_old:
                        for c1, m1, f1 in c_m_f_new:
                            if c != c1 and m != m1:
                                continue
                            if c == c1 and m == m1:
                                # Check if the key already exists
                                if (c, c1, m, m1) not in c_m_f_match:
                                    c_m_f_match[(c, c1, m, m1)] = (f, f1, pair[0])
                            
                            if c != c1 and m == m1 and (c, m):
                                if (c, c1, m, m1) not in c_m_f_no_match:
                                    c_m_f_no_match[(c, c1, m, m1)] = (f, f1, pair[0])
                            if c == c1 and m != m1:
                                # check if the the change of string only unnecessary characters like spaces or tabs or special characters
                                if (c, c1, m, m1) not in c_m_f_no_match:
                                    c_m_f_no_match[(c, c1, m, m1)] = (f, f1, pair[0])
                    if c_m_f_match != []:
                        for k, v in c_m_f_match.items():
                            c_m_f_match_all.append((k[0], k[1], k[2], k[3], v[0], v[1], v[2]))
                    if c_m_f_no_match != []:
                        for k, v in c_m_f_no_match.items():
                            c_m_f_no_match_all.append((k[0], k[1], k[2], k[3], v[0], v[1], v[2]))
    return c_m_f_match_all, c_m_f_no_match_all, old_func, new_func

def scrape_links(links, cpu_count=cpu_count()):
    print("cpu_count: ", cpu_count)
    with Pool(cpu_count) as pool:
        results = pool.map(process_link, links)

    
    # Combine results from all processes
    all_old_func = []
    all_new_func = []
    all_c_m_f_match_all = []
    all_c_m_f_no_match_all = []
    
    for result in results:
        c_m_f_match_all, c_m_f_no_match_all, old_func, new_func = result
        all_old_func.extend(old_func)
        all_new_func.extend(new_func)
        all_c_m_f_match_all.extend(c_m_f_match_all)
        all_c_m_f_no_match_all.extend(c_m_f_no_match_all)
    
    with open('testdatafiles/c_m_f_match.json', 'w') as f:
        json.dump(all_c_m_f_match_all, f, indent=4)

    with open('testdatafiles/c_m_f_no_match.json', 'w') as f:
        json.dump(all_c_m_f_no_match_all, f, indent=4)

        # break

    with open('testdatafiles/old_func.json', 'w') as f:
        json.dump(all_old_func, f, indent=4)

    with open('testdatafiles/new_func.json', 'w') as f:
        json.dump(all_new_func, f, indent=4)


if __name__ == '__main__':
    start_time = time.time()
    print("Scraping links")
    # Read the links from the testdata/repo_links.json file
    with open('testdata/repo_links.json', 'r') as f:
        links = json.load(f)
    print("Links: ", len(links))
    # links = links[:25]
    links = ["https://github.com/c3nav/c3nav"]
    scrape_links(links)
    print("Time taken: ", time.time() - start_time)