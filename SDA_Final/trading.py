# trading.py
import time

class Trading:
    def __init__(self):
        self.price_people = 100
        self.price_materials = 50
        self.cool_down_length = 30  # seconds
        self.time_last_trade = 0
        self.available_resources = {}
        self.rocket_present = False
        
    def can_trade(self):
        current_time = time.time()
        return current_time - self.time_last_trade >= self.cool_down_length
        
    def validate_trade(self, resource_type, amount, available_resources):
        """Validate if trade is possible with current resources"""
        if not self.can_trade():
            return False, "Trade on cooldown"
            
        if resource_type not in available_resources:
            return False, f"Resource {resource_type} not available"
            
        if available_resources[resource_type] < amount:
            return False, f"Not enough {resource_type}"
            
        return True, "Valid"
        
    def execute_trade(self, resource_type, amount, resource_manager):
        """Execute a trade and update resources"""
        if not self.can_trade():
            return False, "Trade on cooldown"
            
        valid, message = self.validate_trade(resource_type, amount, resource_manager.__dict__)
        if not valid:
            return False, message
            
        # Apply trade logic here
        self.time_last_trade = time.time()
        return True, "Trade successful"