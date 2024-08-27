# Geographic Information System for Travelers Using Data Spatial Programming

In this example, we are developing a Geographic Information System designed for travelers. The system will be capable of handling tasks such as:

    - Locating tourist attractions within a specific distance of a given location.
    - Estimating travel times between different points of interest.
    - Identifying restaurants situated within a designated area near a tourist attraction.

## Why we prefer data spatial programming over OOP

In an object-oriented programming approach, each feature can be represented with a class, and operations can be performed using custom methods. For example lets look at how we can implement, the above example using OOP;

```python
from math import radians, sin, cos, sqrt, atan2

class City:
    def __init__(self, id, name, location):
        self.id = id
        self.name = name
        self.location = location  # (latitude, longitude)
        self.connections = []

    def add_connection(self, destination, distance):
        self.connections.append(Road(self, destination, distance))

class Landmark:
    def __init__(self, id, name, location):
        self.id = id
        self.name = name
        self.location = location  # (latitude, longitude)
        self.connections = []

    def add_connection(self, destination, distance):
        self.connections.append(Road(self, destination, distance))

class Road:
    def __init__(self, start, end, distance):
        self.start = start
        self.end = end
        self.distance = distance

def calculate_distance(loc1, loc2):
    # Haversine formula to calculate distance between two points on the Earth
    R = 6371.0  # Radius of the Earth in kilometers

    lat1, lon1 = loc1
    lat2, lon2 = loc2

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def find_connections(entity):
    return [(road.end.name, road.distance) for road in entity.connections]

# Example of setting up the GIS network
cities = {
    'A': City(1, "City A", (10.0, 20.0)),
    'B': City(2, "City B", (10.1, 20.1)),
    'C': City(3, "City C", (10.2, 20.2)),
    'D': City(4, "City D", (10.3, 20.3)),
    'E': City(5, "City E", (10.4, 20.4)),
    'F': City(6, "City F", (10.5, 20.5)),
    'G': City(7, "City G", (10.6, 20.6)),
    'H': City(8, "City H", (10.7, 20.7)),
    'I': City(9, "City I", (10.8, 20.8)),
    'J': City(10, "City J", (10.9, 20.9))
}

landmarks = {
    '1': Landmark(1, "Landmark 1", (11.0, 21.0)),
    '2': Landmark(2, "Landmark 2", (11.1, 21.1)),
    '3': Landmark(3, "Landmark 3", (11.2, 21.2)),
    '4': Landmark(4, "Landmark 4", (11.3, 21.3)),
    '5': Landmark(5, "Landmark 5", (11.4, 21.4))
}

# Define connections as per the graph
cities['A'].add_connection(cities['B'], 15)
cities['A'].add_connection(cities['C'], 20)
cities['A'].add_connection(landmarks['1'], 10)

cities['B'].add_connection(cities['D'], 25)
cities['B'].add_connection(landmarks['2'], 30)

cities['C'].add_connection(cities['E'], 35)
cities['C'].add_connection(landmarks['3'], 20)

cities['D'].add_connection(cities['F'], 40)
cities['E'].add_connection(cities['G'], 45)

cities['F'].add_connection(landmarks['4'], 50)
cities['G'].add_connection(cities['H'], 55)
cities['H'].add_connection(landmarks['5'], 60)

cities['I'].add_connection(cities['J'], 10)
cities['I'].add_connection(cities['G'], 70)

cities['J'].add_connection(landmarks['2'], 25)
cities['J'].add_connection(landmarks['3'], 30)

landmarks['1'].add_connection(landmarks['2'], 5)
landmarks['2'].add_connection(landmarks['3'], 15)
landmarks['3'].add_connection(landmarks['4'], 20)
landmarks['4'].add_connection(landmarks['5'], 25)
landmarks['5'].add_connection(cities['A'], 40)

# Example usage: Finding connections for City A
connections = find_connections(cities['A'])
print(f"Connections for {cities['A'].name}: {connections}")

# Example usage: Calculating distance between two cities
distance = calculate_distance(cities['A'].location, cities['B'].location)
print(f"Distance between {cities['A'].name} and {cities['B'].name}: {distance:.2f} km")
```

Consider the above scenario: initially, you might manually perform distance calculations and other spatial operations. However, as the dataset grows, this becomes increasingly complex and inefficient. By utilizing nodes, edges, and walkers, you can enhance the management and querying of geographical data, especially for a travel-oriented system. For instance, let's envision a GIS system intended to aid travelers by providing details about tourist attractions, restaurants, and other points of interest. This system should effectively handle tasks such as locating nearby attractions, estimating travel times, and identifying points within specific areas.

The issue can be represented as a graph with nodes and edges using the spatial programming capabilities of Jaclang. By leveraging these structures, spatial operations can be carried out. The graphical representation is highly expressive and easy to grasp, making it well-suited for conceptualizing and solving computational problems. Some argue that their preferred programming language already includes graph libraries, rendering the concept unnecessary. However, I counter this argument by stating that fundamental design languages are built upon their inherent abstractions. Since graphs are not part of these abstractions, the language is not optimized to take advantage of the rich semantics that graphs offer.

### Graph representation of the problem

To represent the above scenario, we can use a graph to show connections between cities and their attractions. The graph's cities and attractions are nodes, and the edges connecting them show the distances between them. These lines are bidirectional so that you can travel back and forth, see the following picture;

> NOTE:
> + Nodes: Geographic features like cities, tourist attractions, restaurants, and landmarks will be represented as nodes.
> + Edges: Represent spatial relationships or connections between these nodes, such as roads, paths, or distance metrics.

Now let's make some general nodes about cities and landmarks; The `city` node is to represent cities. Each `city` node has two attributes: `name` and `location`.

```jac
node city{
    has name;
    has location;
}

```
The `attraction` represent landmarks or points of interest within or near the cities. Each attraction node has three attributes: `name`, `location` and `description`.

```
node attraction{
    has name;
    has location;
    has description;
}
```

lets create the distance edge; `edge` keyword creates edges, the edge `road` represent the roads connecting the cities and landmarks. Each road has a single attribute: `distance`.

```jac
edge road{
    has distance;
}
```

> NOTE:
> + Walkers: Walkers are agents that traverse the graph to perform specific tasks. In spatial programming in jaclang, walkers can be used to execute spatial queries and operations. 

The structure of the graph can create as follows; The `creator` walker is responsible for creating the graph. Inside the create method of the walker:

- **Cities**: Ten city nodes (`city_a` to `city_j`) are created with unique names and locations.
- **Landmarks**: Five attraction nodes (`landmark_1` to `landmark_5`) are created, each with a unique name, location, and description.
- **Roads**: Roads (edges) are established between various city and landmark nodes to form a network. For example:
`city_a` is connected to `city_b` with a road of distance 15 units. `city_a` is also connected to `city_c` and `landmark_1` with roads of distances 20 and 10 units, respectively. The connections are made using the syntax `city_a +: road(distance=15) :+> city_b;`, which creates a road edge between `city_a` and `city_b` with a specified distance.

```
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
```

