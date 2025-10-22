# random_event.py
import time

class RandomEvent:
    def __init__(self, name, description, duration):
        self.name = name
        self.description = description
        self.duration = duration
        self.start_time = 0
        self.active = False
        self.multipliers = {}  # Dictionary of resource multipliers
        self.deltas = {}  # Dictionary of resource deltas
        
    def activate(self):
        self.start_time = time.time()
        self.active = True
        print(f"Event activated: {self.name} - {self.description}")
        
    def deactivate(self):
        self.active = False
        print(f"Event deactivated: {self.name}")
        
    def is_expired(self):
        if not self.active:
            return False
        return time.time() - self.start_time >= self.duration
        
    def change_energy_production(self, amount):
        self.deltas['energy'] = amount
        
    def change_manpower(self, amount):
        self.deltas['manpower'] = amount
        
    def get_effects(self):
        """Return current effects of this event"""
        return {
            'multipliers': self.multipliers.copy(),
            'deltas': self.deltas.copy()
        }