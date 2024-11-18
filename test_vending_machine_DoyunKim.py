"""test_vending_machine_DoyunKim.py - simulate a coin operated vending machine
TPRG 2131 Fall 2022 Project 1
Doyun Kim  (100924397)"""



import pytest
from vending_machine_DoyunKim import VendingMachineController, IdleState, CoinEntryState, DispenseProductState, ReturnChangeState

@pytest.fixture
def vending_machine():
    """Fixture to create a new vending machine for each test."""
    print("\nCreating a new vending machine instance...")
    vm = VendingMachineController()
    vm.register_state(IdleState())
    vm.register_state(CoinEntryState())
    vm.register_state(DispenseProductState())
    vm.register_state(ReturnChangeState())
    vm.switch_state('idle')  # Start with the 'idle' state
    return vm

def test_initial_state(vending_machine):
    """Test the initial state of the vending machine."""
    print("Running test: test_initial_state")
    assert vending_machine.current_state.name == "idle"
    assert vending_machine.total_inserted == 0
    assert vending_machine.get_display_message() == ""

def test_coin_insertion(vending_machine):
    """Test inserting coins into the vending machine."""
    print("Running test: test_coin_insertion")
    vending_machine.current_event = 'Toonie'
    vending_machine.process_event()
    assert vending_machine.total_inserted == 200
    assert vending_machine.current_state.name == "coin_entry"

    vending_machine.current_event = 'Quarter'
    vending_machine.process_event()
    assert vending_machine.total_inserted == 225  # 200 + 25

def test_product_selection_with_sufficient_funds(vending_machine):
    """Test buying a product with sufficient funds."""
    print("Running test: test_product_selection_with_sufficient_funds")
    # Insert coins
    vending_machine.current_event = 'Toonie'
    vending_machine.process_event()

    # Buy product
    vending_machine.current_event = 'Gum'  # Price: 100
    vending_machine.process_event()

    assert vending_machine.total_inserted == 0  # Change returned automatically
    assert vending_machine.current_state.name == "dispense_product"
    assert vending_machine.get_display_message() == "Dispensing product..."
    assert vending_machine.PRODUCTS["Gum"]["quantity"] == 4  # Quantity reduced

def test_product_selection_with_insufficient_funds(vending_machine):
    """Test trying to buy a product with insufficient funds."""
    print("Running test: test_product_selection_with_insufficient_funds")
    # Insert coins
    vending_machine.current_event = 'Quarter'
    vending_machine.process_event()

    # Attempt to buy product
    vending_machine.current_event = 'Gum'  # Price: 100
    vending_machine.process_event()

    assert vending_machine.total_inserted == 25  # No coins deducted
    assert vending_machine.current_state.name == "coin_entry"
    assert vending_machine.get_display_message() == "Insufficient funds for Gum"

def test_return_coins(vending_machine):
    """Test returning coins."""
    print("Running test: test_return_coins")
    # Insert coins
    vending_machine.current_event = 'Loonie'
    vending_machine.process_event()

    # Return coins
    vending_machine.current_event = 'RETURN'
    vending_machine.process_event()

    assert vending_machine.total_inserted == 0
    assert vending_machine.current_state.name == "return_change"
    assert vending_machine.get_display_message() == "Returning change: $1.00"

def test_out_of_stock_product(vending_machine):
    """Test trying to buy a product that is out of stock."""
    print("Running test: test_out_of_stock_product")
    # Set product quantity to 0
    vending_machine.PRODUCTS["Gum"]["quantity"] = 0

    # Insert coins
    vending_machine.current_event = 'Toonie'
    vending_machine.process_event()

    # Attempt to buy the out-of-stock product
    vending_machine.current_event = 'Gum'
    vending_machine.process_event()

    assert vending_machine.total_inserted == 200  # Coins not deducted
    assert vending_machine.current_state.name == "coin_entry"
    assert vending_machine.get_display_message() == "Gum is sold out."

def test_multiple_coin_insertion(vending_machine):
    """Test inserting multiple coins and making a purchase."""
    print("Running test: test_multiple_coin_insertion")
    # Insert multiple coins
    vending_machine.current_event = 'Loonie'
    vending_machine.process_event()
    vending_machine.current_event = 'Quarter'
    vending_machine.process_event()
    vending_machine.current_event = 'Quarter'
    vending_machine.process_event()

    assert vending_machine.total_inserted == 150  # 100 + 25 + 25

    # Purchase product
    vending_machine.current_event = 'Chocolate Bar'  # Price: 200
    vending_machine.process_event()

    assert vending_machine.get_display_message() == "Insufficient funds for Chocolate Bar"

def test_exact_change_purchase(vending_machine):
    """Test purchasing a product with exact change."""
    print("Running test: test_exact_change_purchase")
    # Insert exact change
    vending_machine.current_event = 'Loonie'
    vending_machine.process_event()
    vending_machine.current_event = 'Quarter'
    vending_machine.process_event()
    vending_machine.current_event = 'Quarter'
    vending_machine.process_event()

    # Buy product
    vending_machine.current_event = 'Lays\' Original Chips'  # Price: 90
    vending_machine.process_event()

    assert vending_machine.total_inserted == 60  # 150 - 90
    assert vending_machine.current_state.name == "dispense_product"
    assert vending_machine.get_display_message() == "Dispensing product..."
    assert vending_machine.PRODUCTS["Lays' Original Chips"]["quantity"] == 1

def test_return_coins_after_insert(vending_machine):
    """Test returning coins after inserting multiple coins."""
    print("Running test: test_return_coins_after_insert")
    vending_machine.current_event = 'Toonie'
    vending_machine.process_event()
    vending_machine.current_event = 'Quarter'
    vending_machine.process_event()

    # Return coins
    vending_machine.current_event = 'RETURN'
    vending_machine.process_event()

    assert vending_machine.total_inserted == 0  # All coins returned
    assert vending_machine.current_state.name == "return_change"
    assert vending_machine.get_display_message() == "Returning change: $2.25"
