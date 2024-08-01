from mining_past_bug_fixes import extract_functions, extract_condition_raise_statements, construct_pairs, extract_c_m_f
import json
import pdb
pairs = construct_pairs('https://github.com/sola-st/Dynapyt')

old_func = []
new_func = []
c_m_f_match = {}
c_m_f_no_match = {}
count = 0
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
                            count += 1
                            # Check if the key already exists
                            if (c, m) not in c_m_f_match:
                                c_m_f_match[(c, m, f, f1)] = (f, f1)
                        elif c != c1 and m == m1:
                            if (c, m) not in c_m_f_no_match:
                                c_m_f_no_match[(c, c1, m, m1)] = (f, f1)
                        elif c == c1 and m != m1:
                            # check if the the change of string only unnecessary characters like spaces or tabs or special characters
                            if (c, m) not in c_m_f_no_match:
                                c_m_f_no_match[(c, c1, m, m1)] = (f, f1)

# Convert the dictionary key and value to a list [c, m, f_old, f_new]
c_m_f_match = [(k[0], k[1], k[2], k[3]) for k, v in c_m_f_match.items()]
# Convert the dictionary key and value to a list [c, c1, m, m1, f_old, f_new]
c_m_f_no_match = [(k[0], k[1], k[2], k[3], v[0], v[1]) for k, v in c_m_f_no_match.items()]
with open('c_m_f_match.json', 'w') as f:
    json.dump(c_m_f_match, f, indent=4)

with open('c_m_f_no_match.json', 'w') as f:
    json.dump(c_m_f_no_match, f, indent=4)

    # break

with open('old_func.json', 'w') as f:
    json.dump(old_func, f, indent=4)

with open('new_func.json', 'w') as f:
    json.dump(new_func, f, indent=4)
print("Number of functions that match: ", count)