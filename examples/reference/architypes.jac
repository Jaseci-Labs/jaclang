can print_base_classes(cls: type) -> type {
    print(f"Base classes of {cls.__name__}: {[c.__name__  for c in cls.__bases__]}");
    return cls;
}
#example of using semstring
obj 'This refers to the Obj Animal'
Animal {}

obj Domesticated {}

@print_base_classes
node Mammal :Animal, Domesticated: {}

walker Dog :Mammal: {}

#example of using semstring for walker also can be used for node edge class like this
walker 'represents one type of dog'
Labrador :Dog: {}

@print_base_classes
walker DecoratedLabrador :Labrador: {}

class School {}

@print_base_classes
edge student :School: {}
