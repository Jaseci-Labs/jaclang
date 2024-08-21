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

Now let's make some general nodes about cities and landmarks;

```jac
node city{
    has name;
    has location;
}

node attraction{
    has name;
    has location;
    has description;
}
```

lets create the distance edge;

```jac
edge road{
    has distance;
}
```

> NOTE:
> + Walkers: Walkers are agents that traverse the graph to perform specific tasks. In spatial programming in jaclang, walkers can be used to execute spatial queries and operations. 