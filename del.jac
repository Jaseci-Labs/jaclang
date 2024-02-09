node c{
    has cc : int=9;
}
edge aaa{
        has vvv:int=45;
}


node a{
    has aa:int =1;
}
node b{
    has bb:int =4;
}
with entry{
    x=[a(aa=x) for x in range(0,3)];
    y=[b(bb=x) for x in range(0,3)];
    x++>y;



    z=[c(cc=x) for x in range(0,3)];

    xx=a(aa=9);
    yy=b(bb=9);
    # xx++>yy;
    print('x : ',x);
    print('y : ',y);
    print('z : ',z);
    # x+:aaa:vvv=9:+>y;   #list -list
    y+:aaa:vvv=9:+>z;
    y[1]++>a(aa=9000);
    a(aa=900)++>y[1];
    # y++>z;
    # print(<r>._jac_.gen_dot());
    print(x[1],'x[1]'); 
    print((x[1]-->)-->,'uffff');
    print(x[2]-->,' it should be [bb=0 bb=1 bb=2] ');
    print(y -:aaa:->,'this is what u r looking for');
    # print(y[1] !-:aaa:->,'this is what u r looking for');
    print(<r>._jac_.gen_dot()); 
    # print(x[1]-->,'it should be [bb=0 bb=1 bb=2]');
    # print((x[1]-->)-->,'theriya');
    # print();


    # xx++>x;    #single- list
    # print(<r>._jac_.gen_dot());
    # y++>yy;     #list - single
    # print(<r>._jac_.gen_dot()); 
    # +:MyEdge:val=i:+>;

}


# n = [0..2] done
# j = [0..2] done

# n[1] -:blah:-> j[1]

# with entry {
# x = n -:blah:-> j;  # x==[j[1]]
# x = n !-:blah:-> j; 
# }