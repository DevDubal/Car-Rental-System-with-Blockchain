# This code can give error in a different machine if localhost and ethereum are not defined properly and there's not sufficient balance present.

# Import necessary libraries
import mysql.connector
from web3 import Web3
from tkinter import Tk, Label, Button, Entry, Listbox, messagebox
from eth_account import Account
import time

# Set up Web3 connection
web3 = Web3(Web3.HTTPProvider('http://localhost:8545'))  # Connect to your Ethereum node

# Initializing MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="car_rental"
)

# Define a function to convert Ether to Wei
def ether_to_wei(ether_amount):
    return int(ether_amount * (10 ** 18))

# Defining MySQL tables if not already created
def create_tables():
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS cars(id INT AUTO_INCREMENT PRIMARY KEY, make VARCHAR(255), model VARCHAR(255), year INT, price DECIMAL(10, 2))")
    cursor.execute("CREATE TABLE IF NOT EXISTS available_cars(id INT AUTO_INCREMENT PRIMARY KEY, make VARCHAR(255), model VARCHAR(255), year INT, price DECIMAL(10, 2), status VARCHAR(50))")
    cursor.execute("CREATE TABLE IF NOT EXISTS rent_car(id INT AUTO_INCREMENT PRIMARY KEY, make VARCHAR(255), model VARCHAR(255), year INT, price DECIMAL(10, 2), status VARCHAR(50))")
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions(id INT AUTO_INCREMENT PRIMARY KEY, sender_address VARCHAR(255), receiver_address VARCHAR(255), amount DECIMAL(10, 2), status VARCHAR(50))")
    db.commit()


# Function to generate a unique transaction ID using a combination of timestamp and nonce
def generate_transaction_id(sender_address):
    # Get current timestamp (in seconds)
    timestamp = int(time.time())

    # Use a nonce (e.g., a random number) to ensure uniqueness
    nonce = 123  # You should use a better nonce generation method

    # Concatenate sender address, timestamp, and nonce to create a unique transaction ID
    transaction_id = f"{sender_address}-{timestamp}-{nonce}"

    return transaction_id

# Define functions for Ethereum transactions
def send_ethereum_transaction(sender_address, receiver_address, amount, private_key):
    amount_in_wei = ether_to_wei(amount)
    
    # Generate a unique transaction ID using timestamp and nonce
    transaction_id = generate_transaction_id(sender_address)
    print(transaction_id)

    # Get the chain ID
    chain_id = web3.eth.chain_id

    # Set the gas limit for the transaction
    gas_limit = 21000  # Gas limit is according to localhost it can change depending upon the user

    # Build transaction dictionary
    transaction = {
        'nonce': web3.eth.get_transaction_count(sender_address),
        'to': receiver_address,
        'value': amount_in_wei,
        'gas': gas_limit,  # Gas limit
        'gasPrice': web3.eth.gas_price,  # Use the default gas price from the node
        'chainId': chain_id,  # Specify the chain ID for replay protection
    }

    # Estimate gas needed for the transaction
    gas_estimate = web3.eth.estimate_gas(transaction)

    # Adjust the gas limit to be slightly higher than the estimated gas
    transaction['gas'] = gas_estimate + 10000  # Add some buffer to the estimated gas

    # Sign and send the transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("This is transaction hash: ", transaction_hash)

# Define functions for user interface
def rent_car_ui():
    # Initialize Tkinter
    root = Tk()
    root.title("Car Rental System")

    # Function to handle renting a car
    def rent_car():
        # Retrieve input values from the UI
        make = make_entry.get()
        model = model_entry.get()
        year = year_entry.get()
        price = price_entry.get()

        # Check if the requested car is available
        cursor = db.cursor()
        cursor.execute("SELECT * FROM available_cars WHERE make = %s AND model = %s AND year = %s AND price = %s", (make, model, year, price))
        car = cursor.fetchone()

        if car:
            # Update the database to mark the car as rented
            cursor.execute("DELETE FROM available_cars WHERE id = %s", (car[0],))
            cursor.execute("INSERT INTO rent_car (make, model, year, price, status) VALUES (%s, %s, %s, %s, %s)", (car[1], car[2], car[3], car[4], 'rented'))
            db.commit()

            # Record the transaction in the transactions table
            sender_address = "0x7324b423E80F1856abf1C0CbA1F323056fC9CF25"  # Placeholder for user's Ethereum address
            receiver_address = "0x29F0752a40978763FE4E717a56eEF7Dba9216474"  # Placeholder for rental service's Ethereum address
            amount = float(price)
            cursor.execute("INSERT INTO transactions (sender_address, receiver_address, amount, status) VALUES (%s, %s, %s, %s)", (sender_address, receiver_address, amount, 'completed'))
            db.commit()

            # Execute Ethereum transaction
            send_ethereum_transaction(sender_address, receiver_address, amount, private_key='2ced69751e35eb9ecfaf58075eaefd195eed7e7f639e4c87b7031b84cb7d9de7')

            messagebox.showinfo("Success", "Car rented successfully!")
        else:
            messagebox.showerror("Error", "Car not available!")

        # Close database cursor
        cursor.close()

    # Function to handle viewing rented cars
    def view_rented_cars():
        cursor = db.cursor()
        cursor.execute("SELECT * FROM rent_car")
        rented_cars = cursor.fetchall()
        messagebox.showinfo("Rented Cars", "\n".join([str(car) for car in rented_cars]))
        cursor.close()

    # Function to handle viewing available cars
    def view_available_cars():
        cursor = db.cursor()
        cursor.execute("SELECT * FROM available_cars")
        available_cars = cursor.fetchall()
        messagebox.showinfo("Available Cars", "\n".join([str(car) for car in available_cars]))
        cursor.close()

    # Function to handle viewing all cars
    def view_all_cars():
        cursor = db.cursor()
        cursor.execute("SELECT * FROM cars")
        all_cars = cursor.fetchall()
        messagebox.showinfo("All Cars", "\n".join([str(car) for car in all_cars]))
        cursor.close()

    # Function to handle viewing transactions
    def view_transactions():
        cursor = db.cursor()
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()
        messagebox.showinfo("Transactions", "\n".join([str(transaction) for transaction in transactions]))
        cursor.close()

    # Function to handle adding a new car
    def add_new_car():
        make = make_entry.get()
        model = model_entry.get()
        year = year_entry.get()
        price = price_entry.get()

        cursor = db.cursor()
        cursor.execute("INSERT INTO cars (make, model, year, price) VALUES (%s, %s, %s, %s)", (make, model, year, price))
        cursor.execute("INSERT INTO available_cars (make, model, year, price, status) VALUES (%s, %s, %s, %s, %s)", (make, model, year, price, 'available'))
        db.commit()
        messagebox.showinfo("Success", "Car added successfully!")
        cursor.close()

    # Function to handle unrenting a car
    def unrent_car():
        # Retrieve the selected rented car
        selected_car_index = rented_listbox.curselection()
        if selected_car_index:
            selected_car_id = rented_listbox.get(selected_car_index)
            cursor = db.cursor()
            # Retrieve the details of the selected rented car
            cursor.execute("SELECT * FROM rent_car WHERE id = %s", (selected_car_id,))
            unrented_car = cursor.fetchone()
            if unrented_car:
                # Delete the car from the rent_car table
                cursor.execute("DELETE FROM rent_car WHERE id = %s", (selected_car_id,))
                db.commit()
                # Insert the unrented car back into available_cars table
                cursor.execute("INSERT INTO available_cars (make, model, year, price, status) VALUES (%s, %s, %s, %s, %s)",
                               (unrented_car[1], unrented_car[2], unrented_car[3], unrented_car[4], 'available'))
                db.commit()
                messagebox.showinfo("Success", "Car unrented successfully!")
                cursor.close()
                refresh_rented_list()
            else:
                messagebox.showerror("Error", "Car details not found!")
        else:
            messagebox.showerror("Error", "Please select a car to unrent.")

    # Function to refresh the rented cars list
    def refresh_rented_list():
        cursor = db.cursor()
        cursor.execute("SELECT * FROM rent_car")
        rented_cars = cursor.fetchall()
        rented_listbox.delete(0, 'end')
        for car in rented_cars:
            rented_listbox.insert('end', car[0])
        cursor.close()

    # Create UI elements
    label = Label(root, text="Welcome to Car Rental System", font=("Arial", 18))
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    make_label = Label(root, text="Make:")
    make_label.grid(row=1, column=0, padx=10, pady=5)
    make_entry = Entry(root)
    make_entry.grid(row=1, column=1, padx=10, pady=5)

    model_label = Label(root, text="Model:")
    model_label.grid(row=2, column=0, padx=10, pady=5)
    model_entry = Entry(root)
    model_entry.grid(row=2, column=1, padx=10, pady=5)

    year_label = Label(root, text="Year:")
    year_label.grid(row=3, column=0, padx=10, pady=5)
    year_entry = Entry(root)
    year_entry.grid(row=3, column=1, padx=10, pady=5)

    price_label = Label(root, text="Price:")
    price_label.grid(row=4, column=0, padx=10, pady=5)
    price_entry = Entry(root)
    price_entry.grid(row=4, column=1, padx=10, pady=5)

    rent_button = Button(root, text="Rent", command=rent_car)
    rent_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    view_rented_button = Button(root, text="View Rented Cars", command=view_rented_cars)
    view_rented_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    view_available_button = Button(root, text="View Available Cars", command=view_available_cars)
    view_available_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

    view_all_button = Button(root, text="View All Cars", command=view_all_cars)
    view_all_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

    view_transactions_button = Button(root, text="View Transactions", command=view_transactions)
    view_transactions_button.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

    add_car_button = Button(root, text="Add New Car", command=add_new_car)
    add_car_button.grid(row=10, column=0, columnspan=2, padx=10, pady=10)

    # Create a listbox to display rented cars
    rented_label = Label(root, text="Rented Cars:")
    rented_label.grid(row=11, column=0, padx=10, pady=5)
    rented_listbox = Listbox(root, width=30, height=5)
    rented_listbox.grid(row=11, column=1, padx=10, pady=5)
    refresh_rented_list()

    # Button to unrent a car
    unrent_button = Button(root, text="Unrent Car", command=unrent_car)
    unrent_button.grid(row=12, column=0, columnspan=2, padx=10, pady=10)

    root.mainloop()

def main():
    create_tables()
    rent_car_ui()

if __name__ == '__main__':
    main()
