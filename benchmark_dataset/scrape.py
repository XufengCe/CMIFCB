from mining_past_bug_fixes import extract_functions, extract_condition_raise_statements, construct_pairs, extract_c_m_f
import json
import pdb
pairs = construct_pairs('https://github.com/sola-st/Dynapyt')

old_func = []
new_func = []
c_m_f_match = []
c_m_f_no_match = []
for pair in pairs:
    old_functions, old_function_names = extract_functions(pair[2])
    
    new_functions, new_function_names = extract_functions(pair[3])
    old_func.append(old_functions)
    new_func.append(new_functions)
    
    for i in range(len(old_functions)):
        # Looking for the function in the new code
        for j in range(len(new_functions)):
            if old_function_names[i] == new_function_names[j]:
                c_m_f_old = extract_c_m_f(old_functions[i])
                c_m_f_new = extract_c_m_f(new_functions[j])
                
                
                for c, m ,f in c_m_f_old:
                    for c1, m1, f1 in c_m_f_new:
                        if c == c1 and m == m1:
                            c_m_f_match.append((c, m, f1))
                        elif c != c1 and m == m1:
                            c_m_f_no_match.append((c, c1, m, m1, f, f1))
                        elif c == c1 and m != m1:
                            # check if the the change of string only unnecessary characters like spaces or tabs or special characters
                            c_m_f_no_match.append((c, c1, m, m1, f, f1))


with open('c_m_f_match.json', 'w') as f:
    json.dump(c_m_f_match, f, indent=4)

with open('c_m_f_no_match.json', 'w') as f:
    json.dump(c_m_f_no_match, f, indent=4)

    # break

with open('old_func.json', 'w') as f:
    json.dump(old_func, f, indent=4)

with open('new_func.json', 'w') as f:
    json.dump(new_func, f, indent=4)
    