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
    has location:str;
    has destination:str;

    can travel with entry{
        print("Distance travelled: ", distance);
    }

    can find_path with entry{
        print("Finding path to ", destination);
    }

    can visit with entry{
        print("Visiting ", location);
    }

    can leave with exit{
        print("Leaving ", location);
    }

    can find_nearest_landmark with entry{
        print("Finding nearest landmark");
    }

    can visit_landmark with entry{
        print("Visiting landmark");

    }
}

:walker:traveller:can:travel {
    print(self.name, " is travelling from ", self.location, " to ", self.destination);
    visit [-->](?location == self.destination) else{

    #####
    }
}


walker creator {

}

can create{


}

with entry {

    print("Welcome to City Traffic!");

    cities = [];
    for i in range(10){
        city_name = f"City {chr(65 + i)}";
        location = (10.0 + i * 0.1, 20.0 + i * 0.1);
        cities.append(city(name=city_name, location=location));
    }

    end=root;
    end++>(end:=[cities[0]]);

    # Create landmarks
    landmark_1 = attraction(name="Landmark 1", location=(11.0, 21.0), description="Beautiful spot.");
    landmark_2 = attraction(name="Landmark 2", location=(11.1, 21.1), description="Historic place.");
    landmark_3 = attraction(name="Landmark 3", location=(11.2, 21.2), description="Popular tourist spot.");
    landmark_4 = attraction(name="Landmark 4", location=(11.3, 21.3), description="Iconic landmark.");
    landmark_5 = attraction(name="Landmark 5", location=(11.4, 21.4), description="Must-visit place.");

    landmarks = [landmark_1, landmark_2, landmark_3, landmark_4, landmark_5];

    # Create roads between cities and landmarks
    cities[0] <+: road(distance=15) :+> cities[1];
    cities[0] <+: road(distance=20) :+> cities[2];
    cities[0] <+: road(distance=10) :+> landmark_1;

    cities[1] <+: road(distance=25) :+> cities[3];
    cities[1] <+: road(distance=30) :+> landmark_2;

    cities[2] <+: road(distance=35) :+> cities[4];
    cities[2] <+: road(distance=20) :+> landmark_3;

    cities[3] <+: road(distance=40) :+> cities[5];
    cities[4] <+: road(distance=45) :+> cities[6];

    cities[5] <+: road(distance=50) :+> landmark_4;
    cities[6] <+: road(distance=55) :+> cities[7];
    cities[7] <+: road(distance=60) :+> landmark_5;

    cities[8] <+: road(distance=10) :+> cities[9];
    cities[8] <+: road(distance=70) :+> cities[6];

    cities[9] <+: road(distance=25) :+> landmark_2;
    cities[9] <+: road(distance=30) :+> landmark_3;

    landmark_1 <+: road(distance=5) :+> landmark_2;
    landmark_2 <+: road(distance=15) :+> landmark_3;
    landmark_3 <+: road(distance=20) :+> landmark_4;
    landmark_4 <+: road(distance=25) :+> landmark_5;
    landmark_5 <+: road(distance=40) :+> cities[0];

    # Create a traveller
    traveller_1 = traveller(name="Traveller 1", location=cities[0], destination=landmark_3);
    #root spawn traveller_1();

    #d1=dotgen();
    #l1=d1|>len;
    #print(d1);

    d1=dotgen(cities[0]);

    #print([cities-->landmarks-->cities]);

    visitable = [cities[0]-->];
    print(visitable);
    print([x.name for x in visitable]);

    #print([i.distance for i in (:e:[cities[0] -->])]);

    print([i.distance for i in (:e:[cities[9] --> landmarks])]);

    l1=d1|>len;
    #print(d1);

    print([i.distance for i in (:e:[cities[1] --> landmark_2])]);

    }

