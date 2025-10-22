# structures.py
"""
How to use Structure classes in your main game:

1. Importing the necessary classes:
   from structure import Hydroponic, WaterHarvester, Mine, SolarPanel, Dome

2. Creating structures:
   # Structures need a location tuple (x, y) when created
   solar_panel = SolarPanel((10, 20))
   hydroponic = Hydroponic((15, 25))
   water_harvester = WaterHarvester((30, 30))
   mine = Mine((40, 40))
   dome = Dome((50, 50))

3. Managing structures with ResourceManager:
   # Assuming you have a resource_manager instance
   resource_manager.build_structure(SolarPanel, (10, 20))
   
4. Getting structure counts:
   # If you have a list of all structures
   all_structures = [solar_panel, hydroponic, water_harvester]
   counts = Structure.count_structure_types(all_structures)
   # counts will return: {'H': 1, 'W': 1, 'M': 0, 'S': 1, 'D': 0}

5. Structure Properties:
   - Each structure has a type identifier (H, W, M, S, D)
   - Production rates are predefined for each type
   - Structures require manpower to operate
   - Structures can be enabled/disabled (self.enabled)
   - Efficiency can be modified (self.efficiency_modifiers)
   - Domes have population capacity management

6. Example of full implementation:
   # In your main game loop:
   structures = []
   
   # Creating structures
   new_solar = SolarPanel((10, 20))
   structures.append(new_solar)
   
   # Loading images (if using pygame)
   new_solar.load_image("path/to/solar_image.png")
   
   # Getting production counts
   structure_counts = Structure.count_structure_types(structures)
   
   # Managing population in domes
   dome = Dome((30, 30))
   if dome.can_accommodate(5):
       dome.add_population(5)

Note: The Structure system is designed to work with ResourceManager
for handling resource production and consumption cycles.
"""

import pygame
import os

class Structure:
    def __init__(self, structure_type, location):
        self.type = structure_type
        self.location = location
        self.image = None
        self.enabled = True
        self.scheduling_priority = 1
    
    @staticmethod
    def count_structure_types(structures):
        """
        Returns a dictionary with the count of each structure type
        Args:
            structures (list): List of Structure objects
        Returns:
            dict: Dictionary with structure types as keys and counts as values
        """
        structure_counts = {
            'H': 0,  # Hydroponic
            'W': 0,  # WaterHarvester
            'M': 0,  # Mine
            'S': 0,  # SolarPanel
            'D': 0   # Dome
        }
        
        for structure in structures:
            if structure.type in structure_counts:
                structure_counts[structure.type] += 1
                
        return structure_counts
        
    def load_image(self, image_path):
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                return True
            except Exception:
                return False
        return False
    
    def place(self): pass
    def remove(self): pass
    def tick(self): pass

class Harvester(Structure):
    def __init__(self, structure_type, location):
        super().__init__(structure_type, location)
        self.production_rates = {}
        self.consumption_rates = {}
        self.manpower_required = 0
        self.run_fraction = 1.0
        self.efficiency_modifiers = 1.0
        
    def calculate_production(self):
        if not self.enabled: return {}
        actual_production = {}
        for resource, amount in self.production_rates.items():
            actual_production[resource] = amount * self.run_fraction * self.efficiency_modifiers
        return actual_production
        
    def calculate_consumption(self):
        if not self.enabled: return {}
        actual_consumption = {}
        for resource, amount in self.consumption_rates.items():
            actual_consumption[resource] = amount * self.run_fraction
        return actual_consumption

class Hydroponic(Harvester):
    def __init__(self, location):
        super().__init__('H', location)
        self.production_rates = {'food': 3}
        self.consumption_rates = {'water': 1, 'energy': 1}
        self.manpower_required = 2

class WaterHarvester(Harvester):
    def __init__(self, location):
        super().__init__('W', location)
        self.production_rates = {'water': 4}
        self.consumption_rates = {'energy': 1}
        self.manpower_required = 1

class Mine(Harvester):
    def __init__(self, location):
        super().__init__('M', location)
        self.production_rates = {'marsOre': 4}
        self.consumption_rates = {'energy': 2}
        self.manpower_required = 3

class SolarPanel(Harvester):
    def __init__(self, location):
        super().__init__('S', location)
        self.production_rates = {'energy': 5}
        self.consumption_rates = {}
        self.manpower_required = 1

class Dome(Structure):
    def __init__(self, location):
        super().__init__('D', location)
        self.capacity = 10
        self.population = 0
        self.consumption_rates = {'food': 2, 'water': 2, 'energy': 1}
        self.production_rates = {'manpower': 2}
        
    def can_accommodate(self, additional_people=1):
        return self.population + additional_people <= self.capacity
        
    def add_population(self, count=1):
        if self.can_accommodate(count):
            self.population += count
            return True
        return False