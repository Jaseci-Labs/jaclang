glob : priv a:int=9999;
can :priv kukku(){}
obj : priv obj1{
    has :priv jj1 : int=9;
    has :priv llll1 : int=9;
    
    can:priv func1(){
        print(self.jj1);
    
    }
}
obj obj90{
    has :priv jj2 : int=9;
    has :priv llll2 : int=9;
}
obj :protect obj902{
    has :priv jj3 : int=9;
    has :priv llll3 : int=9;

    obj :protect obj90232{
    has :priv jj23 : int=jj;
    has :priv llll43 : int=9;
}
}
enum :priv ShapeType  {
    CIRCLE="Circle",
    UNKNOWN=a
}
with entry{
    print(a);
}