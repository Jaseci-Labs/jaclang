import sys

before = list(sys.modules.keys())

from deep.mycode_py import code as py_c

print([x for x in sys.modules.keys() if x not in before])
print(sys.modules["deep"])
print(sys.modules["deep"].__path__)
print(sys.modules["deep.mycode_py"])

from deep.othercode_py import foo

print([x for x in sys.modules.keys() if x not in before])
