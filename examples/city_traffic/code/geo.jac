node city{
    has name:str;
    has location:tupple;

    can welcome with entry{
        print("Welcome to ", name);
    }
}

node attraction{
    has name:str;
    has location:tupple;
    has description:str;
}

edge road{
    has distance:float;
}

walker traveller{
    has name:str;
    has location:tupple;
    has destination:tupple;
    has distance:float;

    can travel with `root entry{
        print("Travelling to destination");

        visit [-->] else{
            visitroot;
        }
    }
}

walker creator {
    can create with `root entry {
        city_a = city(name="City A", location=(10.0, 20.0));
        city_b = city(name="City B", location=(10.1, 20.1));
        city_c = city(name="City C", location=(10.2, 20.2));
        city_d = city(name="City D", location=(10.3, 20.3));
        city_e = city(name="City E", location=(10.4, 20.4));
        city_f = city(name="City F", location=(10.5, 20.5));
        city_g = city(name="City G", location=(10.6, 20.6));
        city_h = city(name="City H", location=(10.7, 20.7));
        city_i = city(name="City I", location=(10.8, 20.8));
        city_j = city(name="City J", location=(10.9, 20.9));

        end=root;
        end++>(end:=[city_a]);
        end++>(end:=[city_b]);
        end++>(end:=[city_c]);
        end++>(end:=[city_d]);
        end++>(end:=[city_e]);
        end++>(end:=[city_f]);
        end++>(end:=[city_g]);
        end++>(end:=[city_h]);
        end++>(end:=[city_i]);
        end++>(end:=[city_j]);

        # Create landmarks
        landmark_1 = attraction(name="Landmark 1", location=(11.0, 21.0), description="Beautiful spot.");
        landmark_2 = attraction(name="Landmark 2", location=(11.1, 21.1), description="Historic place.");
        landmark_3 = attraction(name="Landmark 3", location=(11.2, 21.2), description="Popular tourist spot.");
        landmark_4 = attraction(name="Landmark 4", location=(11.3, 21.3), description="Iconic landmark.");
        landmark_5 = attraction(name="Landmark 5", location=(11.4, 21.4), description="Must-visit place.");

        # Create roads between cities and landmarks
        city_a +: road(distance=15) :+> city_b;
        city_a +: road(distance=20) :+> city_c;
        city_a +: road(distance=10) :+> landmark_1;

        city_b +: road(distance=25) :+> city_d;
        city_b +: road(distance=30) :+> landmark_2;

        city_c +: road(distance=35) :+> city_e;
        city_c +: road(distance=20) :+> landmark_3;

        city_d +: road(distance=40) :+> city_f;
        city_e +: road(distance=45) :+> city_g;

        city_f +: road(distance=50) :+> landmark_4;
        city_g +: road(distance=55) :+> city_h;
        city_h +: road(distance=60) :+> landmark_5;

        city_i +: road(distance=10) :+> city_j;
        city_i +: road(distance=70) :+> city_g;

        city_j +: road(distance=25) :+> landmark_2;
        city_j +: road(distance=30) :+> landmark_3;

        landmark_1 +: road(distance=5) :+> landmark_2;
        landmark_2 +: road(distance=15) :+> landmark_3;
        landmark_3 +: road(distance=20) :+> landmark_4;
        landmark_4 +: road(distance=25) :+> landmark_5;
        landmark_5 +: road(distance=40) :+> city_a;
    }
}

with entry {
    print("Welcome to City Traffic!");
    root spawn creator();

    d1=dotgen();
    l1=d1|>len;
    print(d1);

    }

