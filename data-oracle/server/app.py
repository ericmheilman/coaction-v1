# Standard Library Imports
import json
import logging
import requests
import sqlite3
import threading
import time
from decimal import Decimal
from logging.handlers import RotatingFileHandler
from os import environ
from dotenv import load_dotenv

# Third-party Imports
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from web3 import Web3
import schedule
import api_utils

from api_utils import treasury_contract, grt_price, lpt_price
app = Flask(__name__, static_folder="../build", template_folder="../build")
CORS(app)
load_dotenv()


LOG_LEVEL = logging.WARNING
# Create a lock object
lock = threading.Lock()

# Set up logging
log_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
log_handler = RotatingFileHandler(environ.get("FLASK_LOG"), maxBytes=100000000, backupCount=1)
# Set up a logger for the main process
log_handler.setLevel(LOG_LEVEL)
log_handler.setFormatter(log_formatter)
app.logger.addHandler(log_handler)
app.logger.setLevel(LOG_LEVEL)

# Set up a custom logger for the repeating task process
task_logger = logging.getLogger("repeating_task_logger")
task_logger.setLevel(LOG_LEVEL)
task_log_handler = logging.FileHandler(environ.get("TASK_LOG"))
task_log_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
task_log_handler.setFormatter(task_log_formatter)
task_logger.addHandler(task_log_handler)

# Flag to track whether the job is scheduled
job_scheduled = False

GRT_DENOM = api_utils.read_env_var_as_float("GRT_DENOM_EXP", 18)
LPT_DENOM = api_utils.read_env_var_as_float("LPT_DENOM_EXP", 1)
TLPT_DENOM = api_utils.read_env_var_as_float("TLPT_DENOM_EXP", 18)
OSMO_DENOM = api_utils.read_env_var_as_float("OSMO_DENOM_EXP", 6)
AKASH_DENOM = api_utils.read_env_var_as_float("AKASH_DENOM_EXP", 6)
STRIDE_DENOM = api_utils.read_env_var_as_float("STRIDE_DENOM_EXP", 6)
KAVA_DENOM = api_utils.read_env_var_as_float("KAVA_DENOM_EXP", 6)
MARS_DENOM = api_utils.read_env_var_as_float("MARS_DENOM_EXP", 6)
FETCH_DENOM = api_utils.read_env_var_as_float("FETCH_DENOM_EXP", 18)
CUDOS_DENOM = api_utils.read_env_var_as_float("CUDOS_DENOM_EXP", 18)
CHEQD_DENOM = api_utils.read_env_var_as_float("CHEQD_DENOM_EXP", 9)

# Function to schedule the job if it's not already scheduled
def schedule_job():
    global job_scheduled
    if not job_scheduled:
        schedule.every(12).hours.do(job)
        job_scheduled = True
        print("Job scheduled")

# Home page
@app.route("/")
def index():
    return render_template("index.html")

def repeating_task():
    app.logger.debug("Starting repeating_task function.")
    schedule_job()
    while True:
        app.logger.debug("Entered while loop.")
        start_time = time.time()
        delegator_stakes = {}
        prices = {}
        active_networks = ['LPT','GRT']
        try:
            with lock:
                with app.app_context():
                    prices = api_utils.fetch_prices()
                    deposits = api_utils.get_deposits()
                    app.logger.debug(f'Deposits retrieved: {deposits}')
                    if prices and deposits:
                        app.logger.debug('Checking if prices and deposits are present.')
                    
                        validators = api_utils.get_validators()
                        app.logger.debug(f'Validators retrieved: {validators}')
                        app.logger.warning(f'Validators retrieved: {validators}')

                        minted_tokens = api_utils.decay_amount() / (10 ** 18)
                        app.logger.debug(f'Minted tokens calculated: {minted_tokens}')
                        app.logger.warning(f'Minted tokens calculated: {minted_tokens}')

                        deposits = api_utils.get_deposits()
                        app.logger.debug(f'Deposits retrieved: {deposits}')
                        app.logger.warning(f'Deposits retrieved: {deposits}')

                        for validator in validators:
                            app.logger.debug(f'Processing validator: {validator}')
                            app.logger.warning(f'Processing validator: {validator}')

                            deposit = api_utils.get_validator_deposit(validator, deposits)
                            app.logger.debug(f'Deposit retrieved : {deposit}')
                            app.logger.warning(f'Deposit retrieved : {deposit}')

                            delegators = api_utils.get_delegator_data(validator)
                            
                            app.logger.debug(f'Delegator response retrieved : {delegators}')
                            app.logger.warning(f'Delegator response retrieved : {delegators}')

                            weighted_delegators = api_utils.calculate_delegator_weights(delegators, validator)
                            app.logger.debug(f'Weighted delegators calculated : {weighted_delegators}')
                            app.logger.warning(f'Weighted delegators calculated : {weighted_delegators}')

                            token_allocation = api_utils.calculate_token_allocation(deposit, validator, minted_tokens)
                            app.logger.debug(f'Token allocation calculated : {token_allocation}')
                            app.logger.warning(f'Token allocation calculated : {token_allocation}')

                            delegator_rewards = api_utils.calculate_delegator_rewards(weighted_delegators, token_allocation)
                            app.logger.debug(f'Delegator rewards calculated : {delegator_rewards}')
                            app.logger.warning(f'Delegator rewards calculated : {delegator_rewards}')

                            txn_hash = api_utils.distribute_tokens(delegator_rewards)
                            app.logger.debug(f'Delegator rewards {delegator_rewards}')
                            app.logger.debug(f'Transaction hash: {txn_hash}')
                            app.logger.debug(f'Validator {validator} processed.')
                        # Calculate the time taken for the data calculation and leaderboard update
                        elapsed_time = time.time() - start_time

                        # Calculate the time remaining until the next update (60 seconds - elapsed time)
                        time_remaining = max(3600 - elapsed_time, 0)

                        # Sleep for the time remaining before updating again
                        time.sleep(time_remaining)
        except Exception as e:
            app.logger.exception("Error in repeating task")
            time.sleep(3600)


@app.route('/leaderboard')
def leaderboard():
    app.logger.debug("Entering /leaderboard route")
    try:
        app.logger.debug("Connecting to SQLite database...")
        conn = sqlite3.connect('leaderboard.db')
        c = conn.cursor()
        app.logger.debug("Executing SQL query to fetch leaderboard data...")
        c.execute(
            "SELECT address, blockchain, treasury_contribution FROM leaderboard WHERE CAST(treasury_contribution AS INTEGER) != 0 ORDER BY treasury_contribution DESC LIMIT 500")
        rows = c.fetchall()
        app.logger.debug(f"Fetched {len(rows)} rows.")
        leaderboard_data = [{'address': address, 'treasury_contribution': treasury_contribution}
                            for address, treasury_contribution in rows]
        app.logger.debug("Closing SQLite database connection.")
        conn.close()
        app.logger.debug("Returning leaderboard data.")
        return jsonify(leaderboard_data)
    except sqlite3.Error as e:
        app.logger.debug(f"SQLite error in /leaderboard route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/reward-deposits')
def reward_deposits():
    try:
        app.logger.debug("Fetching test...")

        app.logger.debug("Initializing Web3...")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))
        with open(environ.get("VALIDATOR_ABI_JSON"), "r") as f:
            VAL_REGISTRY_ABI = json.load(f)
        with open(environ.get("TREASURY_ABI_JSON"), "r") as f:
            TREASURY_ABI = json.load(f)
        contract = treasury_contract()
        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching validators...")
            validator_addresses = api_utils.get_validator_addresses()  # Call to get_validators function
            if validator_addresses is not None:
                all = []
                all = contract.functions.getAllDeposits(validator_addresses).call()
                app.logger.debug(f"Deposited all: {all}")
                for deposit in all:
                    validator = deposit[0]
                    grt_deposit = deposit[1]
                    lpt_deposit = deposit[2]
                return jsonify("testing")
            else:
                app.logger.error("Failed to fetch validator addresses")

        return jsonify("test")

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed to distribute rewards"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/distribute')
def distribute():
    # Schedule the job to run every moth
    schedule.every(720).hours.do(job)
    try:
        app.logger.debug("Fetching treasury data...")

        all_percentages_data = percentage_treasury_contribution()

        app.logger.debug("Parsing total treasury and data...")
        data = all_percentages_data['data']

        app.logger.debug("Validating that data is not empty...")
        if not data:
            return jsonify({"error": "No data found"}), 404

        app.logger.debug("Setting sender address...")
        sender_address = environ.get("SENDING_ADDRESS")

        app.logger.debug("Initializing Web3...")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))

        app.logger.debug("Setting distribution address...")
        distribution_address = env
        iron.get("DISTRIBUTION_ADDRESS")

        app.logger.debug("Setting token address...")
        token_address = environ.get("TOKEN_ADDRESS")

        app.logger.debug("Setting validator subscription addess...")
        val_registry_address = environ.get("VALIDATOR_REGISTRY")

        app.logger.debug("Setting treasury address...")
        treasury_address = environ.get("TREASURY_ADDRESS")

        app.logger.debug("Initializing contract1...")

        with open(environ.get("TOKEN_ABI_JSON"), "r") as f:
            TOKEN_ABI = json.load(f)

        with open(environ.get("DISTRIBUTION_ABI_JSON"), "r") as f:
            DISTRIBUTION_ABI = json.load(f)

        with open(environ.get("VALIDATOR_ABI_JSON"), "r") as f:
            VAL_REGISTRY_ABI = json.load(f)

        with open(environ.get("TREASURY_ABI_JSON"), "r") as f:
            TREASURY_ABI = json.load(f)


        distribution_contract = w3.eth.contract(
            address=distribution_address, abi=DISTRIBUTION_ABI)
        token_contract = w3.eth.contract(address=token_address, abi=TOKEN_ABI)
        val_registry_contract = w3.eth.contract(address=val_registry_address, abi=VAL_REGISTRY_ABI)
        treasury_contract = treasury_contract()

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching decayed amount...")
            decayed_amount = token_contract.functions.getDecayedAmount().call()
            app.logger.debug("Web3 is connected. Fetching validators...")

            registered_validators = val_registry_contract.functions.getValidators().call()

            app.logger.debug("Web3 is connected. Fetching lpt deposits...")
            lpt = []
            deposited_lpt = treasury_contract.functions.getAllLPTDeposits(lpt).call()
            app.logger.debug("Web3 is connected. Fetching grt deposits...")

            deposited_grt = treasury_contract.functions.getAllGRTDeposits(lpt).call()

            # Print debugging information
            app.logger.debug("Debug Information:")
            app.logger.debug(f"Registered Validators: {registered_validators}")
            app.logger.debug(f"Deposited LPT: {deposited_lpt}")
            app.logger.debug(f"Deposited GRT: {deposited_grt}")

            app.logger.debug("Initializing variables...")
            size = 0
            addresses = {}

            app.logger.debug("Processing rows in data...")
            total = 0
            for row in all_percentages_data['data']:
                address_address = row['address']

                if address_address.startswith("0x"):
                    app.logger.debug("Converting to checksum address...")
                    checksum_address = Web3.to_checksum_address(
                        address_address)
                    app.logger.debug("Calculating rewards...")
                    delegator_weight = Decimal(row['treasury_contribution']) / 100
                    reward = (
                        Decimal(row['treasury_contribution']) / 100) * (Decimal(decayed_amount))
                    total += reward
                    app.logger.debug(f"Reward: {reward}")  
                    app.logger.debug(f"Delegator weight: {delegator_weight}") 
                    app.logger.debug(f"Total: {total}") 
                    app.logger.debug("Storing rewards...")
                    addresses[checksum_address] = int(reward)

            app.logger.debug("Converting addresses and amounts to lists...")
            addresses = {k: v for k, v in addresses.items() if v != 0}
            wallets = list(addresses.keys())
            amounts = list(addresses.values())
            app.logger.debug("Wallets: " + str(wallets))
            app.logger.debug("Amounts: " + str(amounts))
            app.logger.debug(f"Amounts sum:  {str(sum(amounts))}")
            app.logger.debug("Decayed amount: " + str(decayed_amount))
            app.logger.debug("Building transaction...")
            app.logger.debug(f"distribution_address: {distribution_address}")
            app.logger.debug(f"wallets: {wallets}")
            app.logger.debug(f"amounts: {amounts}")
            my_private_key = environ.get("MY_PRIVATE_KEY")

            for address, amount in addresses.items():
                # Build the transaction to call setClaimableAmounts
                transaction = token_contract.functions.setClaimableAmount(address, amount).build_transaction({
                    'chainId': 11155111,
                    'gas': 2000000,  # Adjust asssneeded
                    'gasPrice': w3.to_wei('50', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(sender_address),
                })

            app.logger.debug("Signing transaction...")
            signed_txn = w3.eth.account.sign_transaction(
                transaction, my_private_key)

            app.logger.debug("Sending transaction...")
            txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            app.logger.debug(f'Transaction hash: {txn_hash.hex()}')

        else:
            app.logger.debug("Web3 is not connected.")

        return jsonify({txn_hash.hex(): addresses})

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed to distribute rewards"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route to get treasury contribution by blockchain
@app.route('/max-rebate', methods=['GET'])
def max_rebate():
    app.logger.debug("Entering /max-rebate route")
    try:
        blockchain = request.args.get('blockchain')
        blockchain = request.args.get('blockchain')
        app.logger.debug(
            f"Received blockchain: {blockchain}, blockchain: {blockchain}")

        if not blockchain or not blockchain:
            app.logger.debug("Missing 'blockchain' or 'blockchain' parameter.")
            return jsonify({"error": "Missing 'blockchain' or 'blockchain' parameter"}), 400

        app.logger.debug("Connecting to database for max rebate...")
        conn = api_utils.get_db_connection()
        app.logger.debug("Fetching max rebate from database...")
        treasury_contribution_value = api_utils.get_max_rebate(
            blockchain, blockchain, conn)
        app.logger.debug(f"Max rebate fetched: {treasury_contribution_value}")
        app.logger.debug("Closing database .")
        api_utils.close_db_connection(conn)

        response_data = {
            "max-rebate": treasury_contribution_value / 2
        }

        app.logger.debug("Returning max rebate data.")
        return jsonify(response_data), 200

    except Exception as e:
        app.logger.debug(f"Exception in /max-rebate route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/data')
def fetch_data():
    app.logger.debug("Entering /data route")
    try:
        app.logger.debug("Connecting to SQLite database...")
        conn = sqlite3.connect('leaderboard.db')
        c = conn.cursor()
        app.logger.debug("Executing SQL query to fetch data...")

        c.execute(
            "SELECT address, blockchain, treasury_contribution  FROM leaderboard ORDER BY treasury_contribution DESC LIMIT 500")
        rows = c.fetchall()
        app.logger.debug(f"Fetched {len(rows)} rows.")
        app.logger.debug("Closing SQLite database connection.")
        conn.close()
        app.logger.debug("Returning fetched data.")
        return jsonify(rows)
    except sqlite3.Error as e:
        app.logger.debug(f"SQLite error in /data route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/all-data')
def all_data():
    app.logger.debug("Entered all_data route.")
    try:
        conn = sqlite3.connect('leaderboard.db')
        c = conn.cursor()

        app.logger.debug("Executing SQL query to fetch data.")
        c.execute(
            "SELECT * FROM leaderboard WHERE CAST(treasury_contribution AS INTEGER) != 0 ORDER BY treasury_contribution DESC LIMIT 500")
        rows = c.fetchall()
        app.logger.debug(f"Fetched {len(rows)} rows.")

        # Fetch column names
        column_names = [desc[0] for desc in c.description]
        app.logger.debug(f"Column names: {column_names}")

        # Create a list of dictionaries, each representing a row
        result = []
        for row in rows:
            row_dict = {}
            for i in range(len(column_names)):
                row_dict[column_names[i]] = row[i]
            result.append(row_dict)

        conn.close()
        app.logger.debug("Database connection closed.")

        # Convert the list of dictionaries to a JSON response
        app.logger.debug("Returning JSON response.")
        return jsonify(result)

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return {"error": "An error occurred"}, 500


@app.route('/percentage-treasury-contribution')
def percentage_treasury_contribution():
    app.logger.debug("Entered percentage_treasury_contribution route")
    try:

        conn = sqlite3.connect('leaderboard.db')
        prices = api_utils.fetch_prices()

        c = conn.cursor()

        # Fetch individual records
        c.execute(
            "SELECT address, blockchain, treasury_contribution FROM leaderboard WHERE treasury_contribution != 0 ORDER BY treasury_contribution DESC LIMIT 500")
        rows = c.fetchall()
        app.logger.debug("Fetched individual records")

        # Fetch column names
        column_names = [desc[0] for desc in c.description]
        app.logger.debug(f"Column Names: {column_names}")

        # Create a list of dictionaries, each representing a row
        result = []
        percentages = []

        # Initialize total_treasury in dollars
        total_treasury_dollars = 0.0

        for row in rows:
            row_dict = {}
            for i in range(len(column_names)):
                row_dict[column_names[i]] = row[i]

            # Calculate rate and convert treasury contribution to dollars
            price = api_utils.calculate_price_by_blockchain(
                prices, row_dict['blockchain'])

            treasury_dollars = row_dict['treasury_contribution'] * price
            total_treasury_dollars += treasury_dollars

            row_dict['treasury_contribution_dollars'] = treasury_dollars

            result.append(row_dict)

        # Calculate and print the treasury contribution percentage in dollars for each address
        for row_dict in result:
            if total_treasury_dollars != 0:
                percentage = (
                    row_dict['treasury_contribution_dollars'] / total_treasury_dollars) * 100
                app.logger.debug(
                    f"Address: {row_dict['address']}, Treasury Contribution: {percentage:.10f}%")
                percentages.append(f"{percentage:.10f}%")
                row_dict['treasury_contribution_percentage'] = percentage

        # Sort the result by treasury_contribution_percentage in descending order
        result.sort(
            key=lambda x: x['treasury_contribution_dollars'], reverse=True)

        # Print all percentages in a row
        app.logger.debug("All percentages in a row: " + ", ".join(percentages))

        conn.close()
        return {
            'total_treasury_dollars': total_treasury_dollars,
            'data': result
        }
    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return {"error": "An error occurred"}, 500


@app.route('/fetch_treasury_data')
def fetch_treasury_data():
    conn = sqlite3.connect('leaderboard.db')
    c = conn.cursor()

    c.execute("SELECT SUM(treasury_contribution) FROM leaderboard")
    total_treasury = c.fetchone()[0]

    c.execute(
        "SELECT address, blockchain, treasury_contribution FROM leaderboard WHERE treasury_contribution != 0 ORDER BY treasury_contribution DESC LIMIT 500")
    rows = c.fetchall()
    column_names = [desc[0] for desc in c.description]

    result = []
    percentages = []
    for row in rows:
        row_dict = {}
        for i in range(len(column_names)):
            row_dict[column_names[i]] = row[i]
        if total_treasury != 0:
            percentage = (
                row_dict['treasury_contribution'] / total_treasury) * 100
            row_dict['treasury_contribution'] = round(percentage, 2)
            percentages.append(round(percentage, 2))
        result.append(row_dict)
    conn.close()
    return {
        "percentages_in_row": percentages,
        "data": result,
        "total_treasury": total_treasury
    }


@app.route('/all-percentages')
def all_percentages():
    all_percentages_data = fetch_treasury_data()
    return jsonify(all_percentages_data)


@app.route('/addresses')
def addresses():
    rows = fetch_data()
    addresses = [row[0].split(" ", 1)[0] for row in rows]
    return jsonify({"addresses": ",".join(addresses)})


@app.route('/blockchain')
def blockchain():
    rows = fetch_data()
    blockchain = [row[0].split(" ", 1)[1] if len(
        row[0].split(" ", 1)) == 2 else "" for row in rows]
    return jsonify({"blockchain": ",".join(blockchain)})


@app.route('/treasury_contribution')
def treasury_contribution():
    rows = fetch_data()
    total_treasury_contribution = sum([row[1] for row in rows])
    treasury_contributions = [
        round((row[1] / total_treasury_contribution) * 100, 4) for row in rows]
    return jsonify({"treasury_contribution": ",".join(map(str, treasury_contributions))})


@app.route('/size')
def size():
    rows = fetch_data()
    return jsonify({"size": len(rows)})

# Define a job function to call the distribute function


def job():
    app.logger.debug("Entering job function")
    try:
        app.logger.debug("Running distribute function...")
        distribute()
    except Exception as e:
        app.logger.debug(f"Exception in job function: {e}")


if __name__ == '__main__':
    # Create a thread for the repeating task
    task_thread = threading.Thread(target=repeating_task)
    try:
        app.logger.debug("Initializing repeating task thread...")
        task_thread.start()
        app.logger.debug("Running Flask app...")
        app.run(host='0.0.0.0', port='5000', debug=True, use_reloader=False)
    except Exception as e:
        app.logger.debug(f"Exception in main function: {e}")

