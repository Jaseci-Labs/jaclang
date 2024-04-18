#example of using semstring for the has variables of an object 
obj Car {
    has make:str,
        model:str,
        year:'represents the year in which the car was produced' int;   
    static has wheels: int = 4;

    can display_car_info {
        print(f"Car Info: {self.year} {self.make} {self.model}");
    }

    static can get_wheels {
        return Car.wheels;
    }
}

with entry {
    car = Car("Toyota", "Camry", 2020);
    car.display_car_info();
    print("Number of wheels:", Car.get_wheels());
}
