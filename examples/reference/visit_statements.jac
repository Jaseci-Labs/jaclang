walker walker_1{
     can func2 with `<root> entry;
}
node node_1{ 
    has val :int;
     can func_1 with walker_1 entry;
}
walker w3{
    can func_3 with `<root> entry;
}
:node:node_1:can:func_1{
        print(<s>);
        # if  <s>.val==3{
        if  <s>.val==30{
                print("visiting stops at node 3");
                disengage; 
             }
        else{
               visit-->else{
                           print("finished visitng all nodes  ..\n");
                        };
            }
 }
:walker:walker_1:can:func2{
    end = <here>;
    for i=0 to i<5 by i+=1 {
        end ++>  end := node_1(val=i+1);  
    }
    visit -->;
}
:walker:w3:can:func_3{
        print("visiting root by w3\n");  
        visit(node_1(val=2));
}
node node2{
    has val2:int;

}
walker w4:w3:{
    can cc with `<r> entry{
        print("Method inside a inherited walker");
    }
}
with entry{
         <root> spawn walker_1();
         <r> spawn w3();
         w4.cc(<r>,<r>);
        #  <r>._jac_.gen_dot();
}




