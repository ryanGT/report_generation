test1 = 's*: Teaching'
test2 = 'ss*: Philosophy of Teaching'
test3 = 'ss: Philosophy of Teaching'
test4 = 's: Philosophy of Hair'
tests = [test1, test2, test3, test4]
import re

def run_test(p):
    res = []
    titles = []
    
    for test in tests:
        q = p.search(test)
        res.append(q)
        if q:
            titles.append(q.group(1))
            print(test +':'+q.group(1))
        else:
            titles.append(None)
            print(test +':'+'No Match')
    return res, titles

pat1 = '^s\\**: *(.*)'
p1 = re.compile(pat1)
print('pat1 = '+pat1)
res1, titles1 = run_test(p1)
print('='*10)
pat2 = '^ss\\**: *(.*)'
p2 = re.compile(pat2)
print('pat2 = '+pat2)
res2, titles2 = run_test(p2)
