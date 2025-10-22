# event_manager.py
import time
import random

class EventManager:
    def __init__(self):
        self.active_events = []
        self.event_cooldowns = {}
        # We'll create events directly instead of importing
        self.available_events = {
            'dust_storm': self.create_event('Dust Storm', 'Reduces solar panel efficiency', 30),
            'water_leak': self.create_event('Water Leak', 'Loses water reserves', 20),
            'outbreak': self.create_event('Outbreak', 'Reduces manpower', 25)
        }
        self.efficiency_modifiers = {}
    
    def create_event(self, name, description, duration):
        """Create a RandomEvent without importing it"""
        # Create a simple event dictionary instead of RandomEvent instance
        return {
            'name': name,
            'description': description,
            'duration': duration,
            'active': False,
            'start_time': 0,
            'multipliers': {},
            'deltas': {}
        }
        
    def update(self):
        """Update event lifecycle"""
        current_time = time.time()
        
        # Check for expired events
        for event_name in list(self.active_events):
            event = self.available_events[event_name]
            if event['active'] and current_time - event['start_time'] >= event['duration']:
                self.deactivate_event(event_name)
        
        # Random event triggering (simplified)
        if random.random() < 0.01 and len(self.active_events) < 2:
            self.trigger_random_event()
            
    def trigger_random_event(self):
        """Trigger a random event from available events"""
        available_event_names = [name for name in self.available_events.keys() 
                               if name not in self.event_cooldowns or 
                               time.time() - self.event_cooldowns[name] > 60]
        
        if available_event_names:
            event_name = random.choice(available_event_names)
            self.activate_event(event_name)
            
    def activate_event(self, event_name):
        """Activate an event"""
        event = self.available_events[event_name]
        event['active'] = True
        event['start_time'] = time.time()
        self.active_events.append(event_name)
        self.event_cooldowns[event_name] = time.time()
        print(f"Event activated: {event['name']} - {event['description']}")
        
    def deactivate_event(self, event_name):
        """Deactivate an event"""
        event = self.available_events[event_name]
        event['active'] = False
        if event_name in self.active_events:
            self.active_events.remove(event_name)
        print(f"Event deactivated: {event['name']}")
                    
    def get_efficiency_modifier(self, resource_type):
        """Get current efficiency modifier for a resource type"""
        return self.efficiency_modifiers.get(resource_type, 1.0)