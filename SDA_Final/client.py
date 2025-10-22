import pygame
import threading
import socket
import time
import os
from resource_manager import ResourceManager
from structure import Structure, Dome, Mine, Hydroponic, SolarPanel, WaterHarvester
from trading import Trading
from random_event import RandomEvent
from event_manager import EventManager

# Remove the duplicate Structure class definitions that are now in separate files
# Only keep classes that are not in the diagram

class NetworkClient:
    def __init__(self):
        self.socket = None
        self.thread = None
        self.connected = False
        self.messages = []  
        self.lock = threading.Lock()
        self.stop_flag = False

    def connect(self, host, port=5000, username="Player"):
        self.disconnect()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4.0)
            s.connect((host, port))
            s.settimeout(1.0)
            s.sendall((username.strip() + "\n").encode("utf-8"))
            self.socket = s
            self.connected = True
            self.stop_flag = False
            self.thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.thread.start()
            return True, None
        except Exception as e:
            self.disconnect()
            return False, str(e)

    def _recv_loop(self):
        buf = b""
        try:
            while not self.stop_flag and self.socket:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        txt = line.decode("utf-8", errors="replace").strip()
                        if txt:
                            with self.lock:
                                self.messages.insert(0, (txt, time.time()))
                except socket.timeout:
                    continue
                except Exception:
                    break
        finally:
            self.disconnect()

    def send(self, text):
        if not self.socket:
            return False
        try:
            self.socket.sendall((text.strip() + "\n").encode("utf-8"))
            return True
        except Exception:
            self.disconnect()
            return False

    def get_messages(self):
        with self.lock:
            msgs = list(self.messages)
            self.messages.clear()
            return msgs

    def disconnect(self):
        self.stop_flag = True
        self.connected = False
        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass
        self.socket = None

class TextInput:
    def __init__(self, rect, font, initial=""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.text = initial
        self.active = False
        self.cursor_timer = 0.0

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.active = self.rect.collidepoint(ev.pos)
        if self.active and ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif ev.key == pygame.K_RETURN:
                return "enter"
            else:
                if ev.unicode and len(ev.unicode) > 0:
                    self.text += ev.unicode
        return None

    def update(self, dt):
        self.cursor_timer += dt

    def draw(self, surf, color_bg=(30,30,30)):
        pygame.draw.rect(surf, color_bg, self.rect)
        pygame.draw.rect(surf, (200,200,200), self.rect, 2 if self.active else 1)
        txt_s = self.font.render(self.text, True, (230,230,230))
        surf.blit(txt_s, (self.rect.x + 6, self.rect.y + (self.rect.height - txt_s.get_height())//2))
        if self.active and (int(self.cursor_timer*2) % 2 == 0):
            x = self.rect.x + 6 + txt_s.get_width() + 1
            y = self.rect.y + 6
            h = self.rect.height - 12
            pygame.draw.rect(surf, (230,230,230), (x, y, 2, h))

class Button:
    def __init__(self, rect, font, label):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.label = label

    def draw(self, surf, bg=(80,80,120)):
        pygame.draw.rect(surf, bg, self.rect)
        pygame.draw.rect(surf, (220,220,220), self.rect, 2)
        txt = self.font.render(self.label, True, (245,245,245))
        surf.blit(txt, (self.rect.x + (self.rect.width - txt.get_width())//2,
                        self.rect.y + (self.rect.height - txt.get_height())//2))

    def is_clicked(self, ev):
        return ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos)

class GameEngineClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.inputHostIP = ""
        self.topic = []
        self.status = "Idle"
        self.data = None  # Placeholder for game data
        self.screen = None
        self.server_port = 5000
        self.clock = None
        
    def initialize(self):
        pygame.init()
        self.W, self.H = 1600, 767
        self.screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption("Mars Colony Simulator")
        self.clock = pygame.time.Clock()
        
    def cleanup(self):
        pygame.quit()

class PlayerUI:
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.font = pygame.font.SysFont(None, 22)
        self.small = pygame.font.SysFont(None, 18)
        self.setup_ui_elements()
        
    def setup_ui_elements(self):
        # UI elements setup
        self.ip_input = TextInput((12, 12, 260, 36), self.small, initial="localhost")
        self.user_input = TextInput((12, 56, 260, 36), self.small, initial="Player")
        self.connect_btn = Button((284, 12, 100, 36), self.small, "Connect")
        self.disconnect_btn = Button((396, 12, 120, 36), self.small, "Disconnect")
        self.back_to_menu = Button((528, 12, 120, 36), self.small, "Menu")
        self.boo_btn = Button((12, 104, 120, 40), self.small, "Boo")
        self.structure_btn = Button((140, 104, 120, 40), self.small, "Structure")
        
        self.build_btns = {
            'D': Button((12, 140, 40, 28), self.small, 'D'),
            'S': Button((58, 140, 40, 28), self.small, 'S'),
            'H': Button((104, 140, 40, 28), self.small, 'H'),
            'M': Button((150, 140, 40, 28), self.small, 'M'),
            'W': Button((196, 140, 40, 28), self.small, 'W'),
            'R': Button((242, 140, 40, 28), self.small, 'R'),
        }

class SpectatorClient:
    def __init__(self):
        self.spectator_mode = False

class Production:
    def __init__(self):
        self.efficiency = 1.0
        
    def add_resources(self, resource_type, amount):
        # Placeholder for resource addition logic
        pass

class Launchpad:
    def __init__(self):
        self.rocket_present = False
        
    def receive_supply(self):
        pass
        
    def play_launch_animation(self):
        pass
        
    def play_landing_animation(self):
        pass

class GameManager:
    def __init__(self):
        # ... existing code ...
        
        # Event display system
        self.current_event_display = None
        self.event_display_timer = 0
        self.event_display_duration = 3.0  # 3 seconds
        self.event_dark_overlay = None
        
    def trigger_event_display(self, event_name, event_description):
        """Show event notification with dark overlay"""
        self.current_event_display = {
            'name': event_name,
            'description': event_description
        }
        self.event_display_timer = self.event_display_duration
        
        # Create dark overlay surface
        self.event_dark_overlay = pygame.Surface((self.game_engine.W, self.game_engine.H), pygame.SRCALPHA)
        self.event_dark_overlay.fill((0, 0, 0, 150))  # Semi-transparent black
        
    def update_event_display(self, dt):
        """Update event display timer"""
        if self.current_event_display:
            self.event_display_timer -= dt
            if self.event_display_timer <= 0:
                self.current_event_display = None
                self.event_dark_overlay = None
    
    def draw_event_display(self):
        """Draw event notification overlay"""
        if not self.current_event_display:
            return
            
        # Draw dark overlay
        if self.event_dark_overlay:
            self.game_engine.screen.blit(self.event_dark_overlay, (0, 0))
        
        # Draw event text
        event = self.current_event_display
        large_font = pygame.font.SysFont(None, 72)
        medium_font = pygame.font.SysFont(None, 36)
        
        # Event name
        name_text = large_font.render(event['name'], True, (255, 50, 50))
        name_rect = name_text.get_rect(center=(self.game_engine.W//2, self.game_engine.H//2 - 50))
        self.game_engine.screen.blit(name_text, name_rect)
        
        # Event description
        desc_text = medium_font.render(event['description'], True, (255, 255, 255))
        desc_rect = desc_text.get_rect(center=(self.game_engine.W//2, self.game_engine.H//2 + 20))
        self.game_engine.screen.blit(desc_text, desc_rect)
        
        # Timer (optional)
        timer_text = medium_font.render(f"Event active for {int(self.event_display_timer)}s", True, (200, 200, 200))
        timer_rect = timer_text.get_rect(center=(self.game_engine.W//2, self.game_engine.H//2 + 70))
        self.game_engine.screen.blit(timer_text, timer_rect)
        
    def draw_resources(self):
        """Draw the resource display"""
        if self.in_game:
            # Starting position for resources display - shifted more to the right
            x_start = 650  # Increased from 10 to 650
            y_pos = 10
            spacing = 180  # Slightly increased spacing between resources
            icon_size = 24  # Size of resource icons
            
            resources = [
                ('water', self.resource_manager.water),
                ('food', self.resource_manager.food),
                ('energy', self.resource_manager.energy),
                ('mars Ore', self.resource_manager.marsOre),
                ('materials', self.resource_manager.materials),
                ('manpower', self.resource_manager.manpower),
                ('population', f"{self.resource_manager.population}/{self.resource_manager.populationLimit}")
            ]
            
            for i, (resource, amount) in enumerate(resources):
                x_pos = x_start + (i % 4) * spacing
                row = i // 4
                y = y_pos + row * 35  # Slightly increased vertical spacing
                
                # Draw resource icon
                icon = self.resource_icons.get(resource)
                if icon:
                    self.game_engine.screen.blit(icon, (x_pos, y))
                    text_x = x_pos + icon_size + 5  # Add some padding after the icon
                else:
                    text_x = x_pos
                
                # Create the resource text
                text = f"{resource.capitalize()}: {amount}"
                
                # Render the text with a slight shadow for better visibility
                shadow = self.player_ui.font.render(text, True, (0, 0, 0))
                text_surface = self.player_ui.font.render(text, True, (255, 255, 255))
                
                # Draw shadow then text
                self.game_engine.screen.blit(shadow, (text_x + 1, y + 1))
                self.game_engine.screen.blit(text_surface, (text_x, y))
        
    def load_assets(self):
        # Load background image
        img_path = "mars_bg.png"  
        if os.path.exists(img_path):
            try:
                self.bg_image = pygame.image.load(img_path).convert()
                self.bg_image = pygame.transform.smoothscale(self.bg_image, (self.game_engine.W, self.game_engine.H))
                print("[client] loaded background image:", img_path)
            except Exception as e:
                print("[client] failed to load image:", e)
                self.bg_image = None
        
        here = os.path.dirname(os.path.abspath(__file__))
        
        # Load resource icons
        resource_images = {
            'water': 'water.png',
            'food': 'food.png',
            'energy': 'energy.png',
            'marsOre': 'marsore.png',
            'materials': 'materials.png',
            'manpower': 'manpower.png',
            'population': 'population.png'
        }
        
        for resource, filename in resource_images.items():
            p = os.path.join(here, filename)
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert_alpha()
                    # Scale the icon to a reasonable size (24x24 pixels)
                    self.resource_icons[resource] = pygame.transform.smoothscale(img, (24, 24))
                except Exception as e:
                    print(f"[client] failed to load resource icon {filename}: {e}")
                    self.resource_icons[resource] = None
        
        # Load building images
        building_images = {
            'D': 'dome.png',
            'S': 'buildingS.png', 
            'H': 'buildingH.png',
            'M': 'buildingM.png',
            'W': 'buildingW.png',
            'R': 'r.png',
        }
        
        for key, filename in building_images.items():
            p = os.path.join(here, filename)
            if os.path.exists(p):
                try:
                    self.b_images[key] = pygame.image.load(p).convert_alpha()
                except Exception:
                    self.b_images[key] = None

    def run(self):
        running = True
        
        while running:
            dt = self.game_engine.clock.tick(60) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()
            
        self.network_client.disconnect()
        self.game_engine.cleanup()

    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
                
            self.handle_ui_events(ev)
            
        return True

    def handle_ui_events(self, ev):
        ui = self.player_ui
        
        # Handle text input events
        ui.ip_input.handle_event(ev)
        ui.user_input.handle_event(ev)
        
        # Handle button clicks
        if ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos
            btn = ev.button
            
            if ui.connect_btn.is_clicked(ev):
                self.handle_connect()
            elif ui.disconnect_btn.is_clicked(ev):
                self.handle_disconnect()
            elif ui.boo_btn.is_clicked(ev):
                self.handle_boo()
            elif not self.in_game and self.start_btn.rect.collidepoint((mx, my)) and btn == 1:
                self.in_game = True
                self.show_build_menu = False
                self.current_building = None
            elif self.in_game and ui.back_to_menu.rect.collidepoint((mx, my)) and btn == 1:
                self.in_game = False
            elif self.in_game:
                self.handle_in_game_events(ev, mx, my, btn)
                
        return None

    def handle_connect(self):
        host = self.player_ui.ip_input.text.strip()
        username = self.player_ui.user_input.text.strip() or "Player"
        ok, err = self.network_client.connect(host, self.game_engine.server_port, username=username)
        if ok:
            self.game_engine.status = f"Connected to {host}"
        else:
            self.game_engine.status = f"Connect failed: {err}"

    def handle_disconnect(self):
        self.network_client.disconnect()
        self.game_engine.status = "Disconnected"

    def handle_boo(self):
        username = self.player_ui.user_input.text.strip() or "Player"
        self.msgs_to_draw.append((f"You: Boo", 2.5))
        if self.network_client.connected:
            sent = self.network_client.send("Boo")
            if not sent:
                self.game_engine.status = "Send failed"
        else:
            self.game_engine.status = "Not connected - Boo shown locally"

    def handle_in_game_events(self, ev, mx, my, btn):
        ui = self.player_ui
        gx0, gy0 = self.grid_origin
        top_margin = 200
        
        if not self.show_build_menu:
            if ui.structure_btn.rect.collidepoint((mx, my)) and btn == 1:
                self.show_build_menu = True
                return
            if btn == 3 and mx >= gx0 and my >= gy0:
                self.handle_grid_right_click(mx, my)
                return
                
        if self.show_build_menu:
            if ui.structure_btn.rect.collidepoint((mx, my)) and btn == 1:
                self.show_build_menu = not self.show_build_menu
                return
                
            if btn == 1:
                handled = False
                for k, bbtn in ui.build_btns.items():
                    if bbtn.rect.collidepoint((mx, my)):
                        if self.current_building == k:
                            self.current_building = None
                        else:
                            self.current_building = k
                        handled = True
                        break
                if handled:
                    return
                    
        # Grid interactions
        if mx >= gx0 and my >= gy0:
            self.handle_grid_interaction(ev, mx, my, btn)

    def handle_grid_right_click(self, mx, my):
        gx0, gy0 = self.grid_origin
        rx = mx - gx0
        ry = my - gy0
        grid_w = max(1, (self.game_engine.W - gx0 - 8) // self.cell_size)
        grid_h = max(1, (self.game_engine.H - gy0 - 8) // self.cell_size)
        gx = rx // self.cell_size
        gy = ry // self.cell_size
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            if self.network_client.connected:
                self.network_client.send(f"/remove {gx} {gy}")
            else:
                self.placed.pop((gx, gy), None)
                # Also remove from resource manager
                self.resource_manager.remove_structure(gx, gy)

    def handle_grid_interaction(self, ev, mx, my, btn):
        gx0, gy0 = self.grid_origin
        rx = mx - gx0
        ry = my - gy0
        grid_w = max(1, (self.game_engine.W - gx0 - 8) // self.cell_size)
        grid_h = max(1, (self.game_engine.H - gy0 - 8) // self.cell_size)
        gx = rx // self.cell_size
        gy = ry // self.cell_size
        
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            key = (gx, gy)
            if btn == 3:  # Right click remove
                if self.network_client.connected:
                    self.network_client.send(f"/remove {gx} {gy}")
                else:
                    self.placed.pop(key, None)
                    # Also remove from resource manager
                    self.resource_manager.remove_structure(gx, gy)
            elif btn == 1 and self.current_building:  # Left click place/remove
                if self.current_building == 'R':
                    if self.network_client.connected:
                        self.network_client.send(f"/remove {gx} {gy}")
                    else:
                        self.placed.pop(key, None)
                        # Also remove from resource manager
                        self.resource_manager.remove_structure(gx, gy)
                else:
                    # Check if we can build (has materials)
                    if self.resource_manager.can_build_structure():
                        if self.network_client.connected:
                            self.network_client.send(f"/place {self.current_building} {gx} {gy}")
                        else:
                            if key not in self.placed:
                                self.placed[key] = self.current_building
                                # Build in resource manager
                                self.resource_manager.build_structure(self.current_building, gx, gy)
                    else:
                        self.game_engine.status = "Not enough materials to build!"

    def update(self, dt):
    # Update UI elements
        self.player_ui.ip_input.update(dt)
        self.player_ui.user_input.update(dt)
        
        # Update message timers
        for i in range(len(self.msgs_to_draw)-1, -1, -1):
            txt, t = self.msgs_to_draw[i]
            t -= dt
            if t <= 0:
                self.msgs_to_draw.pop(i)
            else:
                self.msgs_to_draw[i] = (txt, t)
                
        # Process network messages
        self.process_network_messages()
        
        # Update event manager and check for new events
        old_active_events = len(self.event_manager.active_events)
        self.event_manager.update()
        new_active_events = len(self.event_manager.active_events)
        
        # If a new event started, trigger the display
        if new_active_events > old_active_events:
            active_events = self.event_manager.get_active_events()
            if active_events:
                latest_event = active_events[-1]  # Get the most recently activated event
                self.trigger_event_display(latest_event['name'], latest_event['description'])
        
        # Update event display
        self.update_event_display(dt)
        
        # Apply event effects to resource production
        self.apply_event_effects()
        
        # Auto-produce resources every interval
        current_time = time.time()
        if current_time - self.last_production_time >= self.production_interval:
            self.resource_manager.stepResources()
            self.last_production_time = current_time
        
        # Update camera for star effect
        self.camera_x += 30 * dt

def apply_event_effects(self):
    """Apply event effects to resource production"""
    active_events = self.event_manager.get_active_events()
    for event in active_events:
        # Apply multipliers to production rates
        for resource, multiplier in event.get('multipliers', {}).items():
            # This would need to be integrated with your resource production system
            pass
            
        # Apply immediate resource changes
        for resource, delta in event.get('deltas', {}).items():
            if delta < 0:
                self.resource_manager.subtractResource(resource, abs(delta))
            else:
                self.resource_manager.addResource(resource, delta)

def draw(self):
    # Draw background (now includes gradient overlay)
    self.draw_background()
    
    # Draw UI panel
    self.draw_ui_panel()
    
    # Draw UI elements
    self.draw_ui_elements()
    
    # Draw game elements if in game
    if self.in_game:
        self.draw_game_elements()
        
    # Draw messages and chat
    self.draw_messages()
    
    # Draw resources
    self.draw_resources()
    
    # Draw event display (on top of everything)
    self.draw_event_display()
    
    # Draw stars (on very top)
    self.draw_stars()
    
    pygame.display.flip()
    def process_network_messages(self):
        incoming = self.network_client.get_messages()
        if incoming:
            for text, ts in incoming:
                text = text.strip()
                if text.startswith("/place "):
                    parts = text.split()
                    if len(parts) == 4:
                        b = parts[1]
                        try:
                            gx = int(parts[2]); gy = int(parts[3])
                            self.placed[(gx, gy)] = b
                            # Also add to resource manager
                            self.resource_manager.add_structure(b, gx, gy)
                        except Exception:
                            pass
                elif text.startswith("/remove "):
                    parts = text.split()
                    if len(parts) == 3:
                        try:
                            gx = int(parts[1]); gy = int(parts[2])
                            self.placed.pop((gx, gy), None)
                            # Also remove from resource manager
                            self.resource_manager.remove_structure(gx, gy)
                        except Exception:
                            pass
                elif not text.startswith("/"):
                    if text.startswith("[server]"):
                        if not any(x[0] == text for x in self.incoming_display):
                            self.incoming_display.insert(0, (text, ts))
                    else:
                        if not any(x[0] == text for x in self.incoming_display):
                            self.incoming_display.insert(0, (text, ts))
            
            self.incoming_display = self.incoming_display[:12]

    def draw(self):
        # Draw background
        self.draw_background()
        
        # Draw UI panel
        self.draw_ui_panel()
        
        # Draw UI elements
        self.draw_ui_elements()
        
        # Draw game elements if in game
        if self.in_game:
            self.draw_game_elements()
            
        # Draw messages and chat
        self.draw_messages()
        
        # Draw resources
        self.draw_resources()
        
        # Draw stars
        self.draw_stars()
        
        pygame.display.flip()

    def draw_background(self):
    # Draw background image first
        if self.bg_image:
            self.game_engine.screen.blit(self.bg_image, (0,0))
        
        # Draw gradient overlay on top of background
        overlay = pygame.Surface((self.game_engine.W, self.game_engine.H), pygame.SRCALPHA)
        for y in range(self.game_engine.H):
            t = y / max(1, self.game_engine.H-1)
            if t < 0.6:
                top = (10, 8, 30, 180)   # Dark blue with transparency
                mid = (120, 30, 25, 120) # Dark red with transparency
                tt = t/0.6
                col = (
                    int(top[0] + (mid[0]-top[0])*tt),
                    int(top[1] + (mid[1]-top[1])*tt),
                    int(top[2] + (mid[2]-top[2])*tt),
                    int(top[3] + (mid[3]-top[3])*tt)  # Alpha interpolation
                )
            else:
                mid = (120, 30, 25, 120)
                horizon = (200, 100, 70, 80)  # Orange with less transparency
                tt = (t-0.6)/0.4
                col = (
                    int(mid[0] + (horizon[0]-mid[0])*tt),
                    int(mid[1] + (horizon[1]-mid[1])*tt),
                    int(mid[2] + (horizon[2]-mid[2])*tt),
                    int(mid[3] + (horizon[3]-mid[3])*tt)  # Alpha interpolation
                )
            pygame.draw.line(overlay, col, (0, y), (self.game_engine.W, y))
        self.game_engine.screen.blit(overlay, (0, 0))

    def draw_ui_panel(self):
        panel_w = min(560, self.game_engine.W-16)
        panel_h = 200
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10,10,12,160))
        self.game_engine.screen.blit(panel, (8, 8))

    def draw_ui_elements(self):
        ui = self.player_ui
        
        ui.ip_input.draw(self.game_engine.screen)
        ui.user_input.draw(self.game_engine.screen)
        ui.connect_btn.draw(self.game_engine.screen)
        ui.disconnect_btn.draw(self.game_engine.screen)
        ui.boo_btn.draw(self.game_engine.screen)

        if self.in_game:
            ui.structure_btn.draw(self.game_engine.screen, bg=(70,90,70))
            if self.show_build_menu:
                for k, btn in ui.build_btns.items():
                    if self.current_building == k:
                        btn.draw(self.game_engine.screen, bg=(120,80,80))
                    else:
                        btn.draw(self.game_engine.screen)
                    img = self.b_images.get(k)
                    if img:
                        iw = btn.rect.width - 8
                        ih = btn.rect.height - 8
                        icon = pygame.transform.smoothscale(img, (iw, ih))
                        self.game_engine.screen.blit(icon, (btn.rect.x + 4, btn.rect.y + 4))

        if not self.in_game:
            overlay = pygame.Surface((self.game_engine.W, self.game_engine.H), pygame.SRCALPHA)
            overlay.fill((0,0,0,160))
            self.game_engine.screen.blit(overlay, (0,0))
            self.start_btn.draw(self.game_engine.screen, bg=(50,120,50))
            s1 = ui.font.render("Welcome — press Start to enter the game.", True, (240,240,240))
            self.game_engine.screen.blit(s1, (self.game_engine.W//2 - s1.get_width()//2, self.game_engine.H//2 - 80))
        else:
            ui.back_to_menu.draw(self.game_engine.screen, bg=(80,60,60))

        # Helper text
        self.game_engine.screen.blit(ui.font.render("Enter server IP, username then Connect. Click Boo to send.", True, (200,200,200)), (12, 180))

    def draw_game_elements(self):
        self.grid_origin = (12, 200)
        self.cell_size = 48
        gx0, gy0 = self.grid_origin
        
        grid_w = max(1, (self.game_engine.W - gx0 - 8) // self.cell_size)
        grid_h = max(1, (self.game_engine.H - gy0 - 8) // self.cell_size)
        
        # Draw grid background
        grid_bg = (15,15,25)
        pygame.draw.rect(self.game_engine.screen, grid_bg, (gx0-4, gy0-4, grid_w*self.cell_size+8, grid_h*self.cell_size+8))
        
        # Draw grid cells
        for gx in range(grid_w):
            for gy in range(grid_h):
                x = gx0 + gx*self.cell_size
                y = gy0 + gy*self.cell_size
                if self.bg_image:
                    sx = min(max(0, x + self.cell_size//2), self.bg_image.get_width()-1)
                    sy = min(max(0, y + self.cell_size//2), self.bg_image.get_height()-1)
                    try:
                        col = self.bg_image.get_at((sx, sy))
                        base = (
                            min(255, int(col.r * 0.6 + 15)),
                            min(255, int(col.g * 0.6 + 15)),
                            min(255, int(col.b * 0.6 + 15))
                        )
                    except Exception:
                        base = (25,25,35)
                    pygame.draw.rect(self.game_engine.screen, base, (x, y, self.cell_size, self.cell_size))
                else:
                    pygame.draw.rect(self.game_engine.screen, (25,25,35), (x, y, self.cell_size, self.cell_size))
        
        # Draw grid lines
        grid_surf = pygame.Surface((grid_w*self.cell_size, grid_h*self.cell_size), pygame.SRCALPHA)
        grid_line = (180,180,190,40)
        for gx in range(grid_w + 1):
            x = gx * self.cell_size
            pygame.draw.line(grid_surf, grid_line, (x, 0), (x, grid_h*self.cell_size))
        for gy in range(grid_h + 1):
            y = gy * self.cell_size
            pygame.draw.line(grid_surf, grid_line, (0, y), (grid_w*self.cell_size, y))
        self.game_engine.screen.blit(grid_surf, (gx0, gy0))
        
        # Draw placed buildings
        for (pgx, pgy), b in self.placed.items():
            x = gx0 + pgx*self.cell_size
            y = gy0 + pgy*self.cell_size
            img = self.b_images.get(b)
            if img:
                img_s = pygame.transform.smoothscale(img, (self.cell_size-4, self.cell_size-4))
                img_x = x + (self.cell_size - img_s.get_width()) // 2
                img_y = y + (self.cell_size - img_s.get_height()) // 2
                self.game_engine.screen.blit(img_s, (img_x, img_y))
            else:
                colors = {'D':(200,100,200),'S':(200,200,100),'H':(100,200,200),'M':(200,150,100),'W':(180,180,180)}
                rect_size = self.cell_size - 12
                rect_x = x + (self.cell_size - rect_size) // 2
                rect_y = y + (self.cell_size - rect_size) // 2
                pygame.draw.rect(self.game_engine.screen, colors.get(b,(200,200,200)), (rect_x, rect_y, rect_size, rect_size))
        
        # Draw building preview
        self.draw_building_preview()

    def draw_building_preview(self):
        if not (self.show_build_menu and self.current_building):
            return
            
        mx, my = pygame.mouse.get_pos()
        gx0, gy0 = self.grid_origin
        grid_w = max(1, (self.game_engine.W - gx0 - 8) // self.cell_size)
        grid_h = max(1, (self.game_engine.H - gy0 - 8) // self.cell_size)
        
        if mx >= gx0 and my >= gy0 and grid_w > 0 and grid_h > 0:
            rx = mx - gx0
            ry = my - gy0
            gx = rx // self.cell_size
            gy = ry // self.cell_size
            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                x = gx0 + gx*self.cell_size
                y = gy0 + gy*self.cell_size
                img = self.b_images.get(self.current_building)
                if self.current_building == 'R':
                    s = pygame.Surface((self.cell_size-18, self.cell_size-18), pygame.SRCALPHA)
                    s.fill((200,40,40,160))
                    self.game_engine.screen.blit(s, (x+6, y+6))
                    pygame.draw.line(self.game_engine.screen, (255,255,255), (x+8, y+8), (x+self.cell_size-10, y+self.cell_size-10), 2)
                    pygame.draw.line(self.game_engine.screen, (255,255,255), (x+8, y+self.cell_size-10), (x+self.cell_size-10, y+8), 2)
                else:
                    if img:
                        img_s = pygame.transform.smoothscale(img, (self.cell_size-6, self.cell_size-6))
                        surf = img_s.copy()
                        surf.set_alpha(160)
                        self.game_engine.screen.blit(surf, (x+3, y+3))
                    else:
                        colors = {'D':(200,100,200),'S':(200,200,100),'H':(100,200,200),'M':(200,150,100),'W':(180,180,180)}
                        col = colors.get(self.current_building,(200,200,200))
                        s = pygame.Surface((self.cell_size-18, self.cell_size-18), pygame.SRCALPHA)
                        s.fill((*col,160))
                        self.game_engine.screen.blit(s, (x+6, y+6))

    def draw_messages(self):
        # Draw transient messages
        y0 = 240
        for i in range(len(self.msgs_to_draw)):
            txt, t = self.msgs_to_draw[i]
            alpha = max(0, min(255, int(255 * (t/2.5))))
            render = self.player_ui.font.render(txt, True, (255,220,180))
            self.game_engine.screen.blit(render, (12, y0 + i*22))
            
        # Draw chat box
        x_msgs = self.game_engine.W - 280
        chat_w = 260
        chat_h = 240
        pygame.draw.rect(self.game_engine.screen, (8,8,10,160), (x_msgs-8, 12, chat_w, chat_h))
        self.game_engine.screen.blit(self.player_ui.font.render(f"Status: {self.game_engine.status}", True, (200,200,200)), (x_msgs, 18))
        self.game_engine.screen.blit(self.player_ui.font.render(f"Connected: {self.network_client.connected}", True, (200,200,200)), (x_msgs, 38))
        self.game_engine.screen.blit(self.player_ui.font.render("Messages:", True, (220,220,220)), (x_msgs, 58))
        
        y = 80
        for i, (text, ts) in enumerate(self.incoming_display[:10]):
            surf = self.player_ui.font.render(text, True, (255,255,255))
            self.game_engine.screen.blit(surf, (x_msgs, y + i*20))

    def draw_stars(self):
        for i in range(40):
            x = (i * 97 + int(self.camera_x) * (i % 3)) % (self.game_engine.W)
            y = (i * 53) % int(self.game_engine.H*0.45)
            pygame.draw.circle(self.game_engine.screen, (255,255,255), (int(x), int(y)), 1)

    # Initialize start button (needed for the menu)
    @property
    def start_btn(self):
        return Button(
            (self.game_engine.W//2 - 70, self.game_engine.H//2 - 30, 140, 40),
            self.player_ui.font,
            "Start Game"
        )

def run_game():
    game_manager = GameManager()
    game_manager.run()

if __name__ == "__main__":
    run_game()