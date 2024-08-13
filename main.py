import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json
import random
from random import randint

# Class for characters
class Character:
    def __init__(self, name, character_type, player_id):
        self.name = name
        self.character_type = character_type
        self.items = []
        self.spells = []
        self.stamina = 100
        self.currency = 100
        self.health = 100
        self.player_id = player_id
        self.shield = 0
        self.items_list = []

    def __str__(self):
        return f"{self.name} the {self.character_type} - Health: {self.health}, Shield: {self.shield}, Stamina: {self.stamina}, Currency: {self.currency}"


# Class for items
class Item:
    def __init__(self, name, damage, stamina_cost, stamina_gain, cost, currency_gain, health_gain, shield):
        self.name = name
        self.damage = damage
        self.stamina_cost = stamina_cost
        self.stamina_gain = stamina_gain
        self.cost = cost
        self.currency_gain = currency_gain
        self.health_gain = health_gain
        self.shield = shield

# Class for spells
class Spell:
    def __init__(self, name, cost):
        self.name = name
        self.cost = cost

# Class for the shop
class Shop:
    def __init__(self):
        self.items = [Item("None", 0, 0, 0, 0, 0, 0, 0), Item("Small Health Potion", 0, 5, 0, 20, 0, 10, 0), Item("Small Stamina Potion", 0, 0, 10, 25, 0, 0, 0), Item("Mystic Amulet", 0, 0, 5, 20, 0, 5, 10)]

    def get_items(self):
        return self.items

# Main game class
class FantasyGame:
    def __init__(self, root):
        self.root = root
        self.character = None
        self.enemy = Character("Enemy", "Unknown", "1")  # Placeholder for enemy
        self.peers = []
        self.server_thread = None
        self.server_ip = '0.0.0.0'
        # self.server_port = randint(8000, 8999)
        self.server_port = 5000
        self.client_socket = None
        self.shop = Shop()
        self.ready = False  # Track if the player is ready
        self.peer_ready = False  # Track if the peer is ready
        self.game_started = False

        # Initialize threading event for peer readiness
        self.both_ready_event = threading.Event()
        

        # Define stats
        self.stats = {
            "combat_actions": {
                "Magic Wand": {"damage": 25, "stamina_cost": 6},
                "Sword": {"damage": 40, "stamina_cost": 10},
                "Poisoned Dagger": {"damage": 15, "stamina_cost": 5},
                "Staff": {"damage": 20, "stamina_cost": 7}
            },
            "defense_actions": {
                "Wall of Fire": {"defense_bonus": 15, "stamina_cost": 3},
                "Shield": {"defense_bonus": 10, "stamina_cost": 1},
                "Cloak of Shadows": {"defense_bonus": 20, "stamina_cost": 3},
                "Prayer": {"defense_bonus": 12, "stamina_cost": 3}
            },
            "explore_actions": {
                "None": {"stamina_cost": 0},
                "Explore": {"stamina_cost": 20}
            }
        }

        self.treasures = [Item("5 coins", 0, 0, 0, 0, 5, 0, 0),
                        Item("10 coins", 0, 0, 0, 0, 10, 0, 0),
                        Item("20 coins", 0, 0, 0, 0, 20, 0, 0),
                        Item("30 coins", 0, 0, 0, 0, 30, 0, 0),
                        Item("Large Health Potion (+30)", 0, 0, 0, 0, 0, 30, 0),
                        Item("Large Stamina Potion", 0, 0, 30, 0, 0, 0, 0),
                        Item("Fire Ball Spell", 30, 30, 0, 0, 0, 0, 0),
                        Item("Ice Wall Spell", 0, 20, 0, 0, 0, 0, 20)]

        self.create_widgets()

    def create_widgets(self):
        # Title
        self.title_label = tk.Label(self.root, text="Fantasy Game", font=("Arial", 24))
        self.title_label.pack(pady=10)

        # Initialize action variables with default value
        self.fight_type = tk.StringVar(value="None")
        self.defend_type = tk.StringVar(value="None")
        self.explore_type = tk.StringVar(value="None")
        self.item_type = tk.StringVar(value="None")
        self.shop_type = tk.StringVar(value="None")

        # Name entry field
        self.name_label = tk.Label(self.root, text="Enter your character's name:")
        self.name_label.pack()
        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack()

        # Enemy label
        self.enemy_label = tk.Label(self.root, text="")
        self.enemy_label.pack()

        # Peer IP and Port labels
        self.peer_ip_label = tk.Label(self.root, text="Peer IP: Not started")
        self.peer_ip_label.pack()

        self.peer_port_label = tk.Label(self.root, text=f"Peer Port: {self.server_port}")
        self.peer_port_label.pack()

        # Character type dropdown menu
        self.type_label = tk.Label(self.root, text="Choose your character type:")
        self.type_label.pack()
        
        self.character_types = ["Wizard", "Warrior", "Goblin", "Monk"]
        self.selected_type = tk.StringVar()
        self.selected_type.set(self.character_types[0])  # Default value

        self.type_menu = tk.OptionMenu(self.root, self.selected_type, *self.character_types)
        self.type_menu.pack()

        self.start_button = tk.Button(self.root, text="Start Game", command=self.start_game)
        self.start_button.pack(pady=10)

        # Frame for OptionMenus
        self.option_frame = tk.Frame(self.root)
        self.option_frame.pack(pady=10)

        # OptionMenu labels and widgets
        self.fight_label = tk.Label(self.option_frame, text="Fight:")
        self.fight_label.grid(row=0, column=0, padx=10)
        self.fight_optionmenu = tk.OptionMenu(self.option_frame, self.fight_type, "None")
        self.fight_optionmenu.grid(row=1, column=0, padx=10)

        self.defend_label = tk.Label(self.option_frame, text="Defend:")
        self.defend_label.grid(row=0, column=1, padx=10)
        self.defend_optionmenu = tk.OptionMenu(self.option_frame, self.defend_type, "None")
        self.defend_optionmenu.grid(row=1, column=1, padx=10)

        self.explore_label = tk.Label(self.option_frame, text="Explore:")
        self.explore_label.grid(row=0, column=2, padx=10)
        self.explore_optionmenu = tk.OptionMenu(self.option_frame, self.explore_type, "None", "Explore")
        self.explore_optionmenu.grid(row=1, column=2, padx=10)

        self.item_label = tk.Label(self.option_frame, text="Items:")
        self.item_label.grid(row=0, column=3, padx=10)
        self.item_optionmenu = tk.OptionMenu(self.option_frame, self.item_type, "None")
        self.item_optionmenu.grid(row=1, column=3, padx=10)

        self.shop_label = tk.Label(self.option_frame, text="Shop:")
        self.shop_label.grid(row=0, column=4, padx=10)
        self.shop_optionmenu = tk.OptionMenu(self.option_frame, self.shop_type, "None")
        self.shop_optionmenu.grid(row=1, column=4, padx=10)

        self.ready_button = tk.Button(self.root, text="Ready", command=self.perform_action)
        self.ready_button.pack(pady=10)

        # Status label
        self.status_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Network settings
        self.peer_ip_label = tk.Label(self.root, text="Peer IP:")
        self.peer_ip_label.pack()
        self.peer_ip_entry = tk.Entry(self.root)
        self.peer_ip_entry.pack()

        self.peer_port_label = tk.Label(self.root, text="Peer Port:")
        self.peer_port_label.pack()
        self.peer_port_entry = tk.Entry(self.root)
        self.peer_port_entry.pack()

        self.connect_button = tk.Button(self.root, text="Connect to Peer", command=self.connect_to_peer)
        self.connect_button.pack(pady=10)

    def start_game(self):
        name = self.name_entry.get()
        character_type = self.selected_type.get()
        if name:
            player_id = 1  # Assign a unique ID, replace with proper logic
            self.character = Character(name, character_type, player_id)
            self.enemy = Character("Enemy", "Unknown", player_id-1)
            self.update_player_health_label()  # Update player's health label
            self.update_enemy_health_label()  # Update enemy's health label
            self.enable_buttons()
            self.name_label.config(text=f"Character Name: {name}")
            self.name_entry.pack_forget()
            self.type_label.pack_forget()
            self.type_menu.pack_forget()
            self.start_button.pack_forget()
            self.update_option_menus()
            self.start_server()
        else:
            messagebox.showwarning("Input Error", "Please enter a name.")


    def enable_buttons(self):
        # Enable the OptionMenus and Ready button
        if self.character:
            self.fight_optionmenu.config(state=tk.NORMAL)
            self.defend_optionmenu.config(state=tk.NORMAL)
            self.explore_optionmenu.config(state=tk.NORMAL)
            self.shop_optionmenu.config(state=tk.NORMAL)
            self.ready_button.config(state=tk.NORMAL)

    def update_option_menus(self):
        # Update fight, defend, and shop OptionMenus based on character type
        actions = {
            'Wizard': ["None", "Magic Wand"],
            'Warrior': ["None", "Sword"],
            'Goblin': ["None", "Poisoned Dagger"],
            'Monk': ["None", "Staff"]
        }
        self.fight_optionmenu['menu'].delete(0, 'end')
        for action in actions[self.character.character_type]:
            self.fight_optionmenu['menu'].add_command(label=action, command=tk._setit(self.fight_type, action))

        defenses = {
            'Wizard': ["None", "Wall of Fire"],
            'Warrior': ["None", "Shield"],
            'Goblin': ["None", "Cloak of Shadows"],
            'Monk': ["None", "Prayer"]
        }
        self.defend_optionmenu['menu'].delete(0, 'end')
        for defense in defenses[self.character.character_type]:
            self.defend_optionmenu['menu'].add_command(label=defense, command=tk._setit(self.defend_type, defense))

        self.explore_optionmenu['menu'].delete(0, 'end')
        self.explore_optionmenu['menu'].add_command(label="Explore", command=tk._setit(self.explore_type, "Explore"))

        shop_items = [item.name for item in Shop().get_items()]
        self.shop_optionmenu['menu'].delete(0, 'end')
        for item in shop_items:
            self.shop_optionmenu['menu'].add_command(label=item, command=tk._setit(self.shop_type, item))

    def update_status(self):
        if self.character:
            self.status_label.config(text=str(self.character))
            self.update_enemy_health_label()

    def start_server(self):
        if self.server_thread is None:
            self.server_thread = threading.Thread(target=self.run_server)
            self.server_thread.daemon = True
            self.server_thread.start()

    def run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_ip, self.server_port))
            server_socket.listen()

            while True:
                client_socket, addr = server_socket.accept()
                self.peers.append(client_socket)
                self.peer_ip_label.config(text=f"Connected to peer: {addr[0]}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()

    def start_new_round(self):
        self.peer_ready = False  # Reset peer_ready at the beginning of a new round
        print("Starting new round. Peer ready status reset.")
        # Lisää muu uuden kierroksen aloitukseen liittyvä logiikka tähän

        # Reset shield
        self.character.shield = 0
    

        
    def handle_client(self, client_socket):
        try:
            while True:

                # Receive data from the socket
                message = client_socket.recv(1024).decode()
                if message:
                    print(f"Received from peer: {message}")
                    data = json.loads(message)

                    # Get the data type from the parsed JSON data
                    data_type = data.get('type')
                    if data_type == 'ready':
                        self.set_peer_ready()
                        print("Peer is ready, proceeding with the game.")
                    else:
                        # Process other actions if any
                        self.process_received_action(data)
                else:
                    print("No message received, breaking loop.")
                    break
        except Exception as e:
            print(f"Error handling client: {e}")



    def connect_to_peer(self):
        try:
            peer_ip = self.peer_ip_entry.get()
            peer_port = int(self.peer_port_entry.get())

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((peer_ip, peer_port))

            messagebox.showinfo("Connection Successful", f"Connected to peer at {peer_ip}:{peer_port}")

            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

        except Exception as e:
            print(f"Connection error: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect to peer: {e}")

    def set_peer_ready(self):
        # This method will be called when the peer is ready
        self.peer_ready = True
        self.perform_action()

    def disable_buttons(self):
        self.fight_optionmenu.config(state='disabled')
        self.defend_optionmenu.config(state='disabled')
        self.explore_optionmenu.config(state='disabled')
        self.item_optionmenu.config(state='disabled')
        self.shop_optionmenu.config(state='disabled')
        self.ready_button.config(state='disabled')

    def enable_buttons(self):
        self.fight_optionmenu.config(state='normal')
        self.defend_optionmenu.config(state='normal')
        self.explore_optionmenu.config(state='normal')
        self.item_optionmenu.config(state='normal')
        self.shop_optionmenu.config(state='normal')
        self.ready_button.config(state='normal')


    def perform_action(self):

        # Mark the player as ready
        self.ready = True

        self.send_to_server({"type": "ready", "player_id": self.character.player_id})

        print(f'Action performed, peer ready is {self.peer_ready}')

        self.disable_buttons()

        if self.peer_ready is not True:
            self.disable_buttons()
            return

        self.enable_buttons()

        self.game_started = True

        selected_fight = self.fight_type.get()
        if selected_fight != "None":
            self.fight_type.set("None")
            action_data = {
                "type": "attack",
                "action": selected_fight,
                "damage": self.stats["combat_actions"].get(selected_fight, {}).get("damage", 0),
                "player_id": self.character.player_id,
            }
            # Hyökkääjä päivittää vihollisen healthin paikallisesti
            self.enemy.health -= action_data["damage"]
            self.update_enemy_health_label()
            # Lähetetään hyökkäystieto vastustajalle
            self.send_to_server(action_data)
            stamina_cost = self.stats["combat_actions"].get(selected_fight, {}).get("stamina_cost", 0)
            self.character.stamina -= stamina_cost
            self.update_player_health_label()  # Päivitetään hyökkääjän health myös
    
        selected_shop = self.shop_type.get()

        if selected_shop != "None":
            self.add_option(selected_shop)
            item = next((item for item in Shop().get_items() if item.name == selected_shop), None)
            self.shop_type.set("None")
            if item:
                if self.character.currency >= item.cost:
                    # Vähennä rahaa
                    self.character.currency -= item.cost
                    
                    # Lisää item pelaajan listalle
                    self.character.items_list.append(item.name)

                    # Päivitä status labeli näyttämään uusi rahamäärä
                    self.update_status()

                else:
                    print("Not enough currency to buy this item.")

        selected_explore = self.explore_type.get()

        if selected_explore != "None":
            self.explore_type.set("None")
            x = randint(0,100)
            if x > 50:
                random_index = randint(0, len(self.treasures) - 1)
                random_value = self.treasures[random_index]

                print(random_index)
                print(random_value.name)

                self.add_option(random_value.name)

        selected_item = self.item_type.get()

        if selected_item != "None":
            # Get selected item
            item = next((item for item in self.treasures if item.name == selected_item), None)
            if item:
                print(f"Applying effects of item: {item.name}")
                self.character.stamina -= item.stamina_cost
                self.character.stamina += item.stamina_gain
                self.character.currency += item.currency_gain
                self.character.health += item.health_gain
                self.character.shield += item.shield

                # Update status label
                self.update_status()
            else:
                print(f"Item not found in treasures, checking inventory: {selected_item}")
                item = next((item for item in self.shop.items if item.name == selected_item), None)
                if item:
                    print(f"Applying effects of item from inventory: {item.name}")
                    self.character.stamina -= item.stamina_cost
                    self.character.stamina += item.stamina_gain
                    self.character.currency += item.currency_gain
                    self.character.health += item.health_gain
                    self.character.shield += item.shield
        
                    # Update status label
                    self.update_status()
                else:
                    print(f"Item {selected_item} not found in inventory either.")
            
            # Remove used items
            self.character.items_list.remove(selected_item)
            print(f"items_list: {self.character.items_list}")
            self.update_item_option_menu()
            # Apply shield
            self.character.shield += item.shield
        
        # Puolustuksen käsittely
        selected_defense = self.defend_type.get()

        if selected_defense != "None":
            self.defend_type.set("None")
            defense_data = {
                "type": "defense",
                "action": selected_defense,
                "defense_value": self.stats["defense_actions"].get(selected_defense, {}).get("defense_value", 0),
                "player_id": self.character.player_id
            }
            # Lisää puolustuksen vaikutus pelaajan terveydelle
            self.character.shield += defense_data["defense_value"]
            self.update_player_health_label()  # Päivitä pelaajan status

            # Lähetetään puolustustieto palvelimelle
            self.send_to_server(defense_data)
    
        # Reset peer_ready at the beginning of each loop iteration if needed
        self.start_new_round()
        

    def add_option(self, option_text):
        # Lisää uusi vaihtoehto
        self.item_optionmenu['menu'].add_command(label=option_text, command=tk._setit(self.item_type, option_text))


    def update_item_option_menu(self):
        # Poista kaikki nykyiset vaihtoehdot
        self.item_optionmenu['menu'].delete(0, 'end')

        # Lisää "None" vaihtoehto
        self.item_optionmenu['menu'].add_command(label="None", command=tk._setit(self.item_type, "None"))

        # Lisää kaikki saatavilla olevat esineet
        for item in self.character.items_list:
            self.item_optionmenu['menu'].add_command(label=item, command=tk._setit(self.item_type, item))


        # Select "None"
        self.item_type.set("None")

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    print(f"Received from peer: {message}")
                    data = json.loads(message)
                    self.process_received_action(data)
                    self.update_status()
                    self.enable_buttons()
                else:
                    break
            except Exception as e:
                print(f"Receiving error: {e}")
                break
    

    def process_received_action(self, data):
        print(f"Received data: {data}")  # Debug: Tulosta koko data
        action_type = data.get("type")
        attacker_id = data.get("player_id")

        print(f"Action Type: {action_type}, Attacker ID: {attacker_id}")  # Debug: Tulosta avainten arvot

        if action_type == "attack":
            # Puolustava osapuoli, päivitetään oma health
            damage = data.get("damage", 0)
            print(f"Damage: {damage}")  # Debug: Tulosta damage-arvo

            # Shield
            if self.character.shield > 0:
                damage = max(0, damage - self.character.shield)

            self.character.health -= damage
            self.update_player_health_label()

            if self.character.health <= 0:
                self.status_label.config(text="You have been defeated!")



    def update_player_health_label(self):
        if self.character:
            self.status_label.config(text=str(self.character))
            print(self.character.health)

    def update_enemy_health_label(self):
        self.enemy_label.config(text=f"Enemy Health: {self.enemy.health}")



    def send_to_server(self, data):
        try:
            if self.client_socket:
                message = json.dumps(data)
                self.client_socket.sendall(message.encode())
            else:
                print("No connection to server.")
                messagebox.showwarning("Connection Error", "No connection to server. Please connect to a peer first.")
        except BrokenPipeError:
            print("Broken pipe error: Unable to send message, connection lost.")
            messagebox.showerror("Connection Error", "Lost connection to server. Please try reconnecting.")
            self.client_socket.close()
            self.client_socket = None
        except Exception as e:
            print(f"Sending error: {e}")
            messagebox.showerror("Connection Error", f"An error occurred while sending data: {e}")



# Main application
if __name__ == "__main__":
    root = tk.Tk()
    root.config(cursor="arrow")
    app = FantasyGame(root)
    root.mainloop()
