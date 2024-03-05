glob : priv a:int=16;
can :priv kukku(){}
obj : priv obj1{
    has :priv jj1 : int=6;
    has :priv llll1 : int=5;

    can:priv func1(){
        print(self.jj1);

    }
}
obj obj90{
    has :priv jj2 : int=4;
    has :priv llll2 : int=3;
}
obj :protect obj902{
    has :priv jj3 : int=10;
    has :priv llll3 : int=11;

    obj :priv obj90232{
    has :priv jj23 : int=12;
    has :priv llll43 : int=13;
}
}
enum :priv ShapeType  {
    CIRCLE="Circle",
    UNKNOWN=a
}
with entry{
    print(a);
    print(obj902());

}