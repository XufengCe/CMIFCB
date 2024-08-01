from mining_past_bug_fixes import extract_functions, extract_condition_raise_statements, construct_pairs, extract_c_m_f
import json
import pdb
import itertools
# pairs = construct_pairs('https://github.com/sola-st/Dynapyt')
pairs = construct_pairs('https://github.com/ActivityWatch/aw-core')

old_func = []
new_func = []
c_m_f_match = {}
c_m_f_no_match = {}
for pair in pairs:
    try:
        old_functions, old_function_names = extract_functions(pair[2])
        
        new_functions, new_function_names = extract_functions(pair[3])
    except Exception as e:
        print(e)
        continue
    old_func.append(old_functions)
    new_func.append(new_functions)

    for i in range(len(old_functions)):
        # Looking for the function in the new code
        for j in range(len(new_functions)):
            if old_function_names[i] == new_function_names[j]:
                c_m_f_old = extract_c_m_f(old_functions[i])
                c_m_f_new = extract_c_m_f(new_functions[j])
                
                unqiue_set = set()
                for c, m, f in c_m_f_old:
                    for c1, m1, f1 in c_m_f_new:
                        if c == c1 and m == m1:
                            # Check if the key already exists
                            if (c, m) not in c_m_f_match:
                                c_m_f_match[(c, m, f, f1)] = (f, f1)
                        
                        if c != c1 and m == m1 and (c, m) not in unqiue_set:
                            if (c, m) not in c_m_f_no_match:
                                unqiue_set.add((c, m))
                                c_m_f_no_match[(c, c1, m, m1)] = (f, f1)
                        if c == c1 and m != m1 and (c, m) not in unqiue_set:
                            # check if the the change of string only unnecessary characters like spaces or tabs or special characters
                            if (c, m) not in c_m_f_no_match:
                                unqiue_set.add((c, m))
                                c_m_f_no_match[(c, c1, m, m1)] = (f, f1)

# Convert the dictionary key and value to a list [c, m, f_old, f_new]
c_m_f_match = [(k[0], k[1], k[2], k[3]) for k, v in c_m_f_match.items()]
# Convert the dictionary key and value to a list [c, c1, m, m1, f_old, f_new]
c_m_f_no_match = [(k[0], k[1], k[2], k[3], v[0], v[1]) for k, v in c_m_f_no_match.items()]


for c, c1, m, m1, f, f1 in c_m_f_no_match:
    for c_, c1_, m_, m1_, f_, f1_ in c_m_f_no_match:
        if c == c_ and m == m_ and f == f_:
            c_m_f_no_match.remove((c, c1, m, m1, f, f1))
            break
with open('c_m_f_match.json', 'w') as f:
    json.dump(c_m_f_match, f, indent=4)

with open('c_m_f_no_match.json', 'w') as f:
    json.dump(c_m_f_no_match, f, indent=4)

    # break

with open('old_func.json', 'w') as f:
    json.dump(old_func, f, indent=4)

with open('new_func.json', 'w') as f:
    json.dump(new_func, f, indent=4)
