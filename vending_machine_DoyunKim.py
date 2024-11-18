"""vending_machine_DoyunKim.py - simulate a coin operated vending machine
TPRG 2131 Fall 2022 Project 1
Doyun Kim  (100924397)

This is a demonstration of a simple GUI for a vending machine.
The buttons simply cause their key values to be printed.
Close the window with the X in the top right corner.
"""

import PySimpleGUI as sg
import time
from gpiozero import Servo, Button
from gpiozero.pins.pigpio import PiGPIOFactory

# Hardware interface setup for Raspberry Pi (if hardware is connected)
hardware_present = False  # Flag to indicate if hardware setup is successful
try:
    from gpiozero.pins.pigpio import PiGPIOFactory  # For GPIO control using PiGPIO library
    factory = PiGPIOFactory(host="127.0.0.1", port=8888)  # PiGPIO factory setup
    servo = Servo(17, pin_factory=factory)  # Servo motor connected to GPIO 17
    key1 = Button(26)  # Button connected to GPIO 26 for "Return Coins" function
    hardware_present = True  # Hardware setup successful
except Exception as e:
    # Handle exceptions during hardware setup (e.g., pigpiod service not running)
    print(f"Hardware setup failed: {e}")
    print("Ensure 'pigpiod' is running or use software PWM for testing.")

# Toggle for debug logging
DEBUG_MODE = True  # Enable or disable debug messages

def debug_log(message):
    """Logs debug information to the console if DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(message)

class VendingMachineController:
    # Static configurations for products and coins
    PRODUCTS = {
        "Gum": {"price": 100, "quantity": 5},  # Product name, price (in cents), and stock quantity
        "Beer": {"price": 500, "quantity": 7},
        "Chocolate Bar": {"price": 200, "quantity": 3},
        "Lays' Original Chips": {"price": 90, "quantity": 2},
        "Computer Chips": {"price": 300, "quantity": 4}
    }
    COINS = {'Toonie': 200, 'Loonie': 100, 'Quarter': 25, 'Dime': 10, 'Nickel': 5}  # Coin denominations and their values

    def __init__(self):
        # Initialize machine state and other variables
        self.current_state = None  # Current state of the machine
        self.all_states = {}  # Dictionary to hold all possible states
        self.current_event = ""  # User event (e.g., button press)
        self.total_inserted = 0  # Total amount entered by the user (in cents)
        self.change_to_return = 0  # Change to be returned (in cents)
        self.display_message = ""  # Messages displayed to the user
        self.sorted_coin_values = sorted([v for v in self.COINS.values()], reverse=True)  # Coin values sorted in descending order

    def register_state(self, state):
        """Registers a new state in the machine."""
        self.all_states[state.name] = state

    def switch_state(self, state_name):
        """Transitions the machine to a new state."""
        if self.current_state:
            self.current_state.on_exit(self)  # Call exit handler of the current state
        self.current_state = self.all_states[state_name]  # Update to the new state
        self.current_state.on_entry(self)  # Call entry handler of the new state

    def process_event(self):
        """Updates the machine logic based on the current state."""
        if self.current_state:
            self.current_state.handle_event(self)

    def insert_coin(self, coin):
        """Adds the value of the inserted coin to the total amount."""
        self.total_inserted += self.COINS[coin]

    def return_coins_action(self):
        """Handles the 'Return Coins' button action."""
        self.current_event = 'RETURN'  # Trigger the 'RETURN' event
        self.process_event()  # Update machine logic

    def get_display_message(self):
        """Returns the current message for the user."""
        return self.display_message

    def set_display_message(self, message):
        """Sets a new message for the user."""
        self.display_message = message

class MachineState:
    """Base class for machine states. Subclasses should override methods as needed."""
    _NAME = ""  # Name of the state

    def on_entry(self, machine):
        """Handler for actions when entering this state."""
        pass

    def on_exit(self, machine):
        """Handler for actions when exiting this state."""
        pass

    def handle_event(self, machine):
        """Logic to execute while in this state."""
        pass

    @property
    def name(self):
        """Returns the name of the state."""
        return self._NAME

class IdleState(MachineState):
    """State where the machine waits for user input."""
    _NAME = "idle"

    def handle_event(self, machine):
        if machine.current_event in machine.COINS:
            machine.insert_coin(machine.current_event)  # Add coin value to total
            machine.switch_state('coin_entry')  # Transition to 'coin_entry' state

class CoinEntryState(MachineState):
    """State where the machine handles coin addition."""
    _NAME = "coin_entry"

    def handle_event(self, machine):
        if machine.current_event == "RETURN":
            machine.change_to_return = machine.total_inserted  # Set change due to total amount entered
            machine.total_inserted = 0  # Reset total amount
            machine.switch_state('return_change')  # Transition to 'return_change' state
        elif machine.current_event in machine.COINS:
            machine.insert_coin(machine.current_event)  # Add more coins
        elif machine.current_event in machine.PRODUCTS:
            product = machine.PRODUCTS[machine.current_event]  # Get product details
            if product["quantity"] == 0:
                machine.set_display_message(f"{machine.current_event} is sold out.")  # Notify user if product is out of stock
            elif machine.total_inserted >= product["price"]:
                product["quantity"] -= 1  # Reduce product quantity
                machine.change_to_return = machine.total_inserted - product["price"]  # Calculate change
                machine.total_inserted = 0  # Reset total amount
                machine.switch_state('dispense_product')  # Transition to 'dispense_product' state
            else:
                machine.set_display_message(f"Insufficient funds for {machine.current_event}")  # Notify user of insufficient funds

class DispenseProductState(MachineState):
    """State where the product is dispensed."""
    _NAME = "dispense_product"

    def on_entry(self, machine):
        machine.set_display_message("Dispensing product...")  # Notify user
        if hardware_present:
            servo.min()  # Move servo to dispense position
            time.sleep(1)  # Simulate dispensing delay
            servo.mid()  # Reset servo to neutral position
        if machine.change_to_return > 0:
            machine.switch_state('return_change')  # Transition to 'return_change' state
        else:
            machine.switch_state('idle')  # Transition back to 'idle' state

class ReturnChangeState(MachineState):
    """State where change is returned to the user."""
    _NAME = "return_change"

    def on_entry(self, machine):
        machine.set_display_message(f"Returning change: ${machine.change_to_return / 100:.2f}")  # Notify user of change amount

    def handle_event(self, machine):
        for coin in machine.sorted_coin_values:
            while machine.change_to_return >= coin:
                machine.change_to_return -= coin  # Deduct coin value from change due
        if machine.change_to_return == 0:
            machine.switch_state('idle')  # Transition back to 'idle' state

# GUI setup
def create_gui():
    """Creates the GUI layout for the vending machine."""
    sg.theme('lightgreen')  # Set GUI theme
    coin_col = [[sg.Text("Coins", font=("Arial", 12))]]  # Coin buttons column
    for coin in VendingMachineController.COINS:
        coin_col.append([sg.Button(coin, font=("Arial", 12))])

    select_col = [[sg.Text("Items", font=("Arial", 12))]]  # Product buttons column
    for item, info in VendingMachineController.PRODUCTS.items():
        color = 'black' if info["quantity"] == 0 else 'darkgreen'  # Change color if out of stock
        price_text = f"{item} - ${info['price'] / 100:.2f}"
        select_col.append([sg.Button(price_text, key=item, font=("Arial", 12), button_color=color)])

    layout = [
        [sg.Column(coin_col), sg.VSeparator(), sg.Column(select_col)],
        [sg.Button("return coins", font=("Arial", 12))],
        [sg.Text("Total inserted: $0.00", key="amount", font=("Arial", 12))],
        [sg.Multiline(size=(45, 4), key="message", font=("Arial", 12), disabled=True)]
    ]
    return sg.Window('Vending Machine', layout)

# MAIN PROGRAMif __name__ == "__main__":
if __name__ == "__main__":
    window = create_gui()  # Initialize GUI
    vending = VendingMachineController()  # Create vending machine instance

    # Register all states
    vending.register_state(IdleState())
    vending.register_state(CoinEntryState())
    vending.register_state(DispenseProductState())
    vending.register_state(ReturnChangeState())
    vending.switch_state('idle')  # Start with the 'idle' state

    # Assign button callback for 'Return Coins' if hardware is present
    if hardware_present:
        key1.when_pressed = vending.return_coins_action

    while True:
        event, values = window.read(timeout=10)  # Read GUI events
        if event in (sg.WIN_CLOSED, 'Exit'):  # Handle window close or exit
            break

        # Update the vending machine event based on the user input
        vending.current_event = event
        vending.process_event()  # Process the current event in the state machine

        # **Update the GUI to reflect changes**
        # Update the total amount entered
        window["amount"].update(f"Total inserted: ${vending.total_inserted / 100:.2f}")

        # Update the message displayed to the user
        window["message"].update(vending.get_display_message())

        # Disable buttons for out-of-stock items
        for item, info in vending.PRODUCTS.items():
            if info["quantity"] == 0:
                window[item].update(disabled=True, button_color="lightgreen")

    # Close the GUI window on exit
    window.close()
    print("Normal exit")

