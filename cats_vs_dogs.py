import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GROUND_LEVEL = SCREEN_HEIGHT - 50
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
FPS = 60
ATTACK_COOLDOWN = 500  # milliseconds
ATTACK_DAMAGE = 10

# Clock initialization
clock = pygame.time.Clock()

# Attack class to handle different types of attacks
class Attack:
    def __init__(self, damage, cooldown, range, hitbox_width, hitbox_height, hitbox_shape="rectangle"):
        self.damage = damage
        self.cooldown = cooldown
        self.range = range  # Range of the attack
        self.hitbox_width = hitbox_width  # Width of the hitbox
        self.hitbox_height = hitbox_height  # Height of the hitbox
        self.hitbox_shape = hitbox_shape  # Shape of the hitbox (e.g., "rectangle", "circle")
        self.last_attack_time = 0

    def can_attack(self):
        current_time = pygame.time.get_ticks()
        return current_time - self.last_attack_time > self.cooldown

    def execute_attack(self, attacker, target):
        # Determine the position and size of the hitbox based on the shape
        if self.hitbox_shape == "rectangle":
            if attacker.facing_right:
                hitbox = pygame.Rect(attacker.x + attacker.width, attacker.y, self.hitbox_width, self.hitbox_height)
            else:
                hitbox = pygame.Rect(attacker.x - self.hitbox_width, attacker.y, self.hitbox_width, self.hitbox_height)
        elif self.hitbox_shape == "circle":
            if attacker.facing_right:
                hitbox_center = (attacker.x + attacker.width + self.range, attacker.y + attacker.height // 2)
            else:
                hitbox_center = (attacker.x - self.range, attacker.y + attacker.height // 2)

        # Check for collision between the hitbox and the target
        target_rect = pygame.Rect(target.x, target.y, target.width, target.height)

        if self.hitbox_shape == "rectangle":
            if hitbox.colliderect(target_rect):
                target.take_damage(self.damage)
        elif self.hitbox_shape == "circle":
            distance = pygame.math.Vector2(hitbox_center).distance_to(target_rect.center)
            if distance < self.hitbox_width:  # Use hitbox width as the radius for circular hitboxes
                target.take_damage(self.damage)

    def perform_attack(self, screen, attacker, target):
        if self.can_attack():
            self.execute_attack(attacker, target)
            self.last_attack_time = pygame.time.get_ticks()

            # Visualize the hitbox depending on the shape (for debugging purposes)
            if self.hitbox_shape == "rectangle":
                if attacker.facing_right:
                    pygame.draw.rect(screen, (255, 255, 0), (attacker.x + attacker.width, attacker.y, self.hitbox_width, self.hitbox_height))
                else:
                    pygame.draw.rect(screen, (255, 255, 0), (attacker.x - self.hitbox_width, attacker.y, self.hitbox_width, self.hitbox_height))
            elif self.hitbox_shape == "circle":
                if attacker.facing_right:
                    pygame.draw.circle(screen, (255, 255, 0), (attacker.x + attacker.width + self.range, attacker.y + attacker.height // 2), self.hitbox_width)
                else:
                    pygame.draw.circle(screen, (255, 255, 0), (attacker.x - self.range, attacker.y + attacker.height // 2), self.hitbox_width)



# Base Entity class
class Entity:
    def __init__(self, x, y, width, height, health, sprite):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.health = health
        self.vel_y = 0
        self.on_ground = True
        self.sprite = sprite
        self.facing_right = True  # Default facing direction

    def apply_gravity(self, gravity=1):
        if not self.on_ground:
            self.vel_y += gravity

    def update_position(self):
        self.y += self.vel_y
        if self.y >= GROUND_LEVEL - self.height:
            self.y = GROUND_LEVEL - self.height
            self.on_ground = True
            self.vel_y = 0

    def draw(self, screen):
        # Draw sprite based on the direction it's facing
        if self.facing_right:
            screen.blit(self.sprite, (self.x, self.y))
        else:
            flipped_sprite = pygame.transform.flip(self.sprite, True, False)  # Flip horizontally
            screen.blit(flipped_sprite, (self.x, self.y))

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def flip(self):
        """Flips the sprite and all relative actions (like attack) when the player changes direction."""
        self.facing_right = not self.facing_right

# Base State class for player actions
class PlayerState:
    def __init__(self, player, all_players=None):  # Add all_players as an optional argument
        self.player = player
        self.all_players = all_players  # Store all_players if provided


    def handle_input(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

class IdleState(PlayerState):
    def handle_input(self):
        action = self.player.input_manager.get_action()

        # Update player's rect position for collision checking
        self.player.rect.topleft = (self.player.x, self.player.y)

        # Assume players can move freely initially
        can_move_left = True
        can_move_right = True

        for other_player in self.player.all_players:
            if other_player is not self.player:
                # Detect collision
                if self.player.rect.colliderect(other_player.rect):
                    # Handle collisions from left or right
                    if self.player.x > other_player.x:  # Player is on the right side of the opponent
                        can_move_left = False
                    elif self.player.x < other_player.x:  # Player is on the left side of the opponent
                        can_move_right = False

        # Handle movement with collision detection
        if action == "move_left" and can_move_left:
            self.player.x -= 5
        elif action == "move_right" and can_move_right:
            self.player.x += 5
        elif action == "jump":
            self.player.vel_y = -15
            self.player.on_ground = False
            self.player.set_state(JumpState(self.player, self.player.all_players))
        elif action == "attack":
            self.player.set_state(AttackState(self.player, self.player.current_attack))

        # Ensure the player always faces the opponent
        self.player.check_and_flip(self.player.opponent)

    def update(self):
        pass



class AttackState(PlayerState):
    def __init__(self, player, current_attack):
        super().__init__(player)
        self.current_attack = current_attack
        self.attack_started = pygame.time.get_ticks()

    def handle_input(self):
        pass  # Ignore input while attacking

    def update(self):
        # Check if the attack has finished (based on cooldown)
        if pygame.time.get_ticks() - self.attack_started > self.current_attack.cooldown:
            # Pass both player and all_players when transitioning back to IdleState
            self.player.set_state(IdleState(self.player, self.all_players))  # Pass all_players



# Jump state for the player (when jumping)
class JumpState(PlayerState):
    def handle_input(self):
        # Continue to apply gravity until player lands
        if self.player.y >= GROUND_LEVEL - self.player.height:
            self.player.y = GROUND_LEVEL - self.player.height
            self.player.on_ground = True
            # Pass both player and all_players when transitioning back to IdleState
            self.player.set_state(IdleState(self.player, self.all_players))  # Pass all_players

    def update(self):
        # Apply gravity and update position
        self.player.apply_gravity()
        self.player.update_position()






# Player class inheriting from Entity
class Player(Entity):
    def __init__(self, x, y, sprite, input_manager, attacks, all_players):
        super().__init__(x, y, 50, 80, 100, sprite)
        self.input_manager = input_manager
        self.attacks = attacks  # List of Attack objects
        self.current_attack = attacks[0]  # Default to the first attack
        self.state = IdleState(self, all_players)  # Pass self and all_players to IdleState
        self.all_players = all_players  # Add all_players to access other players
        self.opponent = None
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)  # Create a rect for collision

    def set_opponent(self, opponent):
        """Assign the opponent."""
        self.opponent = opponent    

    def update_position(self):
        self.y += self.vel_y
        # Update the player's rect position to match its current coordinates
        self.rect.topleft = (self.x, self.y)
        if self.y >= GROUND_LEVEL - self.height:
            self.y = GROUND_LEVEL - self.height
            self.on_ground = True
            self.vel_y = 0
        self.rect.topleft = (self.x, self.y)  # Sync rect with the player’s position



    def handle_input(self):
        self.state.handle_input()  # Delegate input handling to the current state

    def update(self):
        self.state.update()  # Delegate updates to the current state

    def set_state(self, new_state):
        """Change the player's state."""
        self.state = new_state

    def attack(self, screen, target, attack_name=None):
        """Perform the attack. If attack_name is provided, use that attack."""
        if attack_name:
            # Switch to the appropriate attack based on attack_name
            for attack in self.attacks:
                if attack_name == attack.name:
                    self.current_attack = attack
        
        # Perform the current attack
        self.current_attack.perform_attack(screen, self, target)

    def check_and_flip(self, opponent):
        """Flip the sprite to face the opponent if necessary."""
        if self.x < opponent.x and not self.facing_right:
            self.flip()
        elif self.x > opponent.x and self.facing_right:
            self.flip()


# Cat and Dog classes
class Dog(Player):
    def __init__(self, x, y, sprite, input_manager, attacks, all_players):
        super().__init__(x, y, sprite, input_manager, attacks, all_players)

class Cat(Player):
    def __init__(self, x, y, sprite, input_manager, attacks, all_players):
        super().__init__(x, y, sprite, input_manager, attacks, all_players)


# InputManager Class
class InputManager:
    def __init__(self, control_map):
        self.control_map = control_map  # control_map is a dictionary mapping actions to keys

    def get_action(self):
        """Check which action is triggered by the player's input."""
        keys = pygame.key.get_pressed()
        for action, key in self.control_map.items():
            if keys[key]:
                return action
        return None

import json

class AttackLoader:
    def __init__(self, filepath):
        self.filepath = filepath

    def load_attacks(self, character_name):
        with open(self.filepath, 'r') as file:
            data = json.load(file)
        
        attacks = []
        if character_name in data:
            for attack_data in data[character_name]:
                attack = Attack(
                    attack_data["damage"],
                    attack_data["cooldown"],
                    attack_data["range"],  # New parameter
                    attack_data["hitbox_width"],  # New parameter
                    attack_data["hitbox_height"],  # New parameter
                    attack_data.get("hitbox_shape", "rectangle")  # Default to rectangle if not specified
                )
                attacks.append(attack)
        return attacks



# Game Manager class
class GameManager:
    def __init__(self):
        # Load sprites
        dog_sprite = pygame.image.load('sprites/dog02_idle.png').convert_alpha()
        self.dog_sprite = pygame.transform.scale(dog_sprite, (int(dog_sprite.get_width() * 0.3), int(dog_sprite.get_height() * 0.25)))
        
        cat_sprite = pygame.image.load('sprites/cat_idle.png').convert_alpha()
        self.cat_sprite = pygame.transform.scale(cat_sprite, (int(cat_sprite.get_width() * 0.5), int(cat_sprite.get_height() * 0.4)))

        # Load attacks from the JSON file
        attack_loader = AttackLoader('json/attacks.json')
        self.dog_attacks = attack_loader.load_attacks("Dog")
        self.cat_attacks = attack_loader.load_attacks("Cat")

        # Initialize players as None for now, will be set in character_selection
        self.player1 = None
        self.player2 = None


    def character_selection(self):
        player1_controls = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "jump": pygame.K_SPACE,
            "attack": pygame.K_v
        }
        player2_controls = {
            "move_left": pygame.K_LEFT,
            "move_right": pygame.K_RIGHT,
            "jump": pygame.K_RCTRL,
            "attack": pygame.K_RETURN
        }

        player1_input_manager = InputManager(player1_controls)
        player2_input_manager = InputManager(player2_controls)

        # Initialize both players first
        self.player1 = Dog(100, GROUND_LEVEL - self.dog_sprite.get_height(), self.dog_sprite, player1_input_manager, self.dog_attacks, [])
        self.player2 = Cat(SCREEN_WIDTH - 150, GROUND_LEVEL - self.cat_sprite.get_height(), self.cat_sprite, player2_input_manager, self.cat_attacks, [])

        # Assign opponents
        self.player1.set_opponent(self.player2)
        self.player2.set_opponent(self.player1)

        # Now that both players are initialized, add them to the all_players list
        self.all_players = [self.player1, self.player2]

        # Set IdleState for each player, and pass all players for collision detection
        self.player1.state = IdleState(self.player1, self.all_players)
        self.player2.state = IdleState(self.player2, self.all_players)

        # Manually adjust Y-position to ensure players start on the ground level
        self.player1.y = GROUND_LEVEL - self.player1.height
        self.player2.y = GROUND_LEVEL - self.player2.height







        
    def draw_health_bars(self):
        pygame.draw.rect(screen, RED, (50, 50, 200, 25))  # Player 1 health background
        pygame.draw.rect(screen, GREEN, (50, 50, 2 * self.player1.health, 25))  # Player 1 health
        pygame.draw.rect(screen, RED, (SCREEN_WIDTH - 250, 50, 200, 25))  # Player 2 health background
        pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH - 250, 50, 2 * self.player2.health, 25))  # Player 2 health

    def game_loop(self):
        running = True
        while running:
            screen.fill(WHITE)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Player 1
            self.player1.apply_gravity()
            self.player1.handle_input()  # Use the state machine to handle input
            self.player1.update_position()
            self.player1.update()  # Update based on current state

            # Player 2
            self.player2.apply_gravity()
            self.player2.handle_input()  # Use the state machine to handle input
            self.player2.update_position()
            self.player2.update()  # Update based on current state


            # Ensure players are facing each other
            self.player1.check_and_flip(self.player2)
            self.player2.check_and_flip(self.player1)

            # Handle inputs for Player 1 (Dog)
            action_p1 = self.player1.input_manager.get_action()
            if action_p1 == "attack":
                self.player1.attack(screen, self.player2)  # Dog attack on Cat

            # Handle inputs for Player 2 (Cat)
            action_p2 = self.player2.input_manager.get_action()
            if action_p2 == "attack":
                self.player2.attack(screen, self.player1)  # Cat attack on Dog


            # Draw players
            self.player1.draw(screen)
            self.player2.draw(screen)

            # Draw health bars
            self.draw_health_bars()

            pygame.display.flip()
            clock.tick(FPS)

# Main function
def main():
    global screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game_manager = GameManager()
    game_manager.character_selection()
    game_manager.game_loop()

main()
pygame.quit()
