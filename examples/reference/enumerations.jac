#example of using semstring with enum
enum 'represents the values for the colors'
Color;

:enum:Color{
    Red,
    Green,
    Blue,
    Black
}

with entry {
    print(Color.Black.value);
    
    ::py::
    print(Color.Green.value)
    ::py::
}