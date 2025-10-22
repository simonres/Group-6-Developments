# resource_manager.py
"""
How to use ResourceManager in your main game:

1. Initialize Resource Manager:
   from resource_manager import ResourceManager
   from structure import SolarPanel, Hydroponic, WaterHarvester, Mine, Dome
   
   # Create resource manager instance
   resource_manager = ResourceManager()

2. Building Structures:
   # Check if you have enough materials
   if resource_manager.can_build_structure(cost_materials=10):
       # Build a structure at coordinates (x, y)
       solar_panel = resource_manager.build_structure(SolarPanel, (10, 20))
       hydroponic = resource_manager.build_structure(Hydroponic, (15, 25))
   
3. Resource Production Cycle:
   # Call this in your game loop to process all structures
   resource_manager.stepResources()
   # This will:
   # - Calculate manpower requirements
   # - Process resource consumption
   # - Generate resources from structures
   # - Apply efficiency modifiers based on available manpower

4. Resource Management:
   # Add resources
   resource_manager.addResource("food", 10)
   resource_manager.addResource("water", 5)
   
   # Subtract resources
   resource_manager.subtractResource("materials", 10)
   
   # Set specific resource amounts
   resource_manager.setResource("energy", 100)
   
   # Display current resources
   print(resource_manager.get_resource_display())

5. Structure List Management:
   # The structureList contains all built structures
   # Each structure in the list has:
   # - location: (x, y) coordinates
   # - type: Structure type identifier
   # - production_rates: Resources it produces
   # - consumption_rates: Resources it consumes
   # - manpower_required: Workers needed
   # - efficiency_modifiers: Production efficiency

6. Population Management:
   # Add population (limited by populationLimit)
   resource_manager.addResource("population", 5)
   
   # Increase population limit (e.g., when building new Domes)
   resource_manager.setResource("populationLimit", 20)

Example Game Loop Implementation:
```python
def game_loop():
    resource_manager = ResourceManager()
    
    # Build initial structures
    resource_manager.build_structure(Dome, (10, 10))
    resource_manager.build_structure(SolarPanel, (20, 20))
    
    while True:
        # Process resource production/consumption
        resource_manager.stepResources()
        
        # Update display
        print(resource_manager.get_resource_display())
        
        # Handle other game logic...
```

Note: The ResourceManager automatically handles:
- Resource constraints and limits
- Manpower distribution
- Structure efficiency based on available workers
- Resource production and consumption cycles
"""

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

    def add_structure(self, structure):
        """Add a structure to the management system
        Args:
            structure: A Structure object (Hydroponic, Mine, etc.)
        """
        self.structureList.append(structure)

    def remove_structure(self, x, y):
        """Remove a structure from the management system"""
        self.structureList = [s for s in self.structureList if not (s['x'] == x and s['y'] == y)]

    def stepResources(self):
        """Process resource production and consumption from all structures"""
        # Get count of each structure type
        from structure import Structure
        structure_counts = Structure.count_structure_types(self.structureList)
        
        # Calculate available manpower
        total_manpower_needed = 0
        for structure in self.structureList:
            if hasattr(structure, 'manpower_required'):
                total_manpower_needed += structure.manpower_required
        
        # If we don't have enough manpower, structures will run at reduced efficiency
        manpower_efficiency = min(1.0, self.manpower / max(1, total_manpower_needed))
        
        # Process production and consumption for each structure
        for structure in self.structureList:
            if hasattr(structure, 'calculate_production') and hasattr(structure, 'calculate_consumption'):
                # Set efficiency based on available manpower
                structure.efficiency_modifiers = manpower_efficiency
                
                # Process consumption first
                consumption = structure.calculate_consumption()
                can_operate = True
                for resource, amount in consumption.items():
                    if getattr(self, resource.lower(), 0) < amount:
                        can_operate = False
                        break
                
                if can_operate:
                    # Consume resources
                    for resource, amount in consumption.items():
                        self.subtractResource(resource, amount)
                    
                    # Add production
                    production = structure.calculate_production()
                    for resource, amount in production.items():
                        self.addResource(resource, amount)

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

    def build_structure(self, structure_class, location, cost_materials=10):
        """Attempt to build a structure, deducting costs if possible
        Args:
            structure_class: The Structure class to instantiate (Hydroponic, Mine, etc.)
            location: Tuple of (x, y) coordinates
            cost_materials: Cost in materials to build the structure
        Returns:
            Structure object if built successfully, None otherwise
        """
        if self.can_build_structure(cost_materials):
            self.subtractResource("materials", cost_materials)
            new_structure = structure_class(location)
            self.add_structure(new_structure)
            return new_structure
        return None

# Standalone test function
def test_resource_manager():
    """Test the resource manager independently"""
    from structure import SolarPanel, Hydroponic
    
    rm = ResourceManager()
    print("Initial resources:")
    print(rm.get_resource_display())
    
    # Test adding a structure
    rm.build_structure(SolarPanel, (5, 5))  # Solar panel
    rm.build_structure(Hydroponic, (6, 5))  # Hydroponics
    
    print("\nAfter building structures:")
    print(rm.get_resource_display())
    
    # Test resource production
    rm.stepResources()
    print("\nAfter one production cycle:")
    print(rm.get_resource_display())

if __name__ == "__main__":
    test_resource_manager()