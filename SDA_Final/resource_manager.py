# resource_manager.py
class ResourceManager:
    def __init__(self):
        self.structureList = []
        
        # Resource variables with sensible defaults
        self.food = 100
        self.water = 100
        self.energy = 100
        self.marsOre = 0
        self.materials = 50
        self.manpower = 5
        self.population = 5
        self.populationLimit = 10
        
        # Production rates for each structure type
        self.production_rates = {
            'D': {'manpower': 2},      # Dome produces manpower
            'S': {'energy': 5},        # Solar Panel produces energy
            'H': {'food': 3},          # Hydroponics produces food
            'M': {'marsOre': 4},       # Mine produces marsOre
            'W': {'water': 4}          # Water Purifier produces water
        }

    def addResource(self, resourceType, amount):
        match resourceType:
            case "food":
                self.food += amount
            case "water":
                self.water += amount
            case "energy":
                self.energy += amount
            case "marsOre":
                self.marsOre += amount
            case "materials":
                self.materials += amount
            case "manpower":
                self.manpower += amount
            case "population":
                if self.population + amount <= self.populationLimit:
                    self.population += amount
                else:
                    self.population = self.populationLimit

    def subtractResource(self, resourceType, amount):
        match resourceType:
            case "food":
                self.food = max(0, self.food - amount)
            case "water":
                self.water = max(0, self.water - amount)
            case "energy":
                self.energy = max(0, self.energy - amount)
            case "marsOre":
                self.marsOre = max(0, self.marsOre - amount)
            case "materials":
                self.materials = max(0, self.materials - amount)
            case "manpower":
                self.manpower = max(0, self.manpower - amount)
            case "population":
                self.population = max(0, self.population - amount)

    def setResource(self, resourceType, amount):
        match resourceType:
            case "food":
                self.food = amount
            case "water":
                self.water = amount
            case "energy":
                self.energy = amount
            case "marsOre":
                self.marsOre = amount
            case "materials":
                self.materials = amount
            case "manpower":
                self.manpower = amount
            case "population":
                self.population = amount
            case "populationLimit":
                self.populationLimit = amount

    def add_structure(self, structure_type, x, y):
        """Add a structure to the management system"""
        structure_data = {
            'type': structure_type,
            'x': x,
            'y': y
        }
        self.structureList.append(structure_data)

    def remove_structure(self, x, y):
        """Remove a structure from the management system"""
        self.structureList = [s for s in self.structureList if not (s['x'] == x and s['y'] == y)]

    def stepResources(self):
        """Process resource production from all structures"""
        for structure in self.structureList:
            structure_type = structure['type']
            if structure_type in self.production_rates:
                for resource_type, amount in self.production_rates[structure_type].items():
                    self.addResource(resource_type, amount)

    def get_resource_display(self):
        """Return formatted string of current resources"""
        return (
            f"Food: {self.food} | Water: {self.water} | Energy: {self.energy}\n"
            f"Mars Ore: {self.marsOre} | Materials: {self.materials}\n"
            f"Manpower: {self.manpower} | Population: {self.population}/{self.populationLimit}"
        )

    def can_build_structure(self, cost_materials=10):
        """Check if player has enough resources to build"""
        return self.materials >= cost_materials

    def build_structure(self, structure_type, x, y, cost_materials=10):
        """Attempt to build a structure, deducting costs if possible"""
        if self.can_build_structure(cost_materials):
            self.subtractResource("materials", cost_materials)
            self.add_structure(structure_type, x, y)
            return True
        return False

# Standalone test function
def test_resource_manager():
    """Test the resource manager independently"""
    rm = ResourceManager()
    print("Initial resources:")
    print(rm.get_resource_display())
    
    # Test adding a structure
    rm.build_structure('S', 5, 5)  # Solar panel
    rm.build_structure('H', 6, 5)  # Hydroponics
    
    print("\nAfter building structures:")
    print(rm.get_resource_display())
    
    # Test resource production
    rm.stepResources()
    print("\nAfter one production cycle:")
    print(rm.get_resource_display())

if __name__ == "__main__":
    test_resource_manager()