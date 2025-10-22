# structures.py
import pygame
import os

class Structure:
    def __init__(self, structure_type, location):
        self.type = structure_type
        self.location = location
        self.image = None
        self.enabled = True
        self.scheduling_priority = 1
        
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
        self.manpower_required = 0

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