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

# Third-party Imports
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from web3 import Web3
import schedule

from api_utils import DataSource, get_stake_data, get_validators, get_deposits, get_grt_validators, get_lpt_validators, get_max_rebate, calculate_price_by_blockchain, calculate_rate_by_blockchain, generate_summary, update_leaderboard, fetch_prices, read_env_var_as_float, get_db_connection, close_db_connection
# Initialize Flask App and Configuration
app = Flask(__name__, static_folder="../build", template_folder="../build")
CORS(app)

e = 'generic error'

# Create a lock object
lock = threading.Lock()

# Set up logging
log_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
log_handler = RotatingFileHandler(
    "/home/ubuntu/leaderboard/server/flask_app.log", maxBytes=100000000, backupCount=1
)
# Set up a logger for the main process
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(log_formatter)
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.DEBUG)

# Set up a custom logger for the repeating task process
task_logger = logging.getLogger("repeating_task_logger")
task_logger.setLevel(logging.DEBUG)
task_log_handler = logging.FileHandler(
    "/home/ubuntu/leaderboard/server/task.log")
task_log_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
task_log_handler.setFormatter(task_log_formatter)
task_logger.addHandler(task_log_handler)

# Flag to track whether the job is scheduled
job_scheduled = False

GRT_DENOM = read_env_var_as_float("GRT_DENOM_EXP", 18)
LPT_DENOM = read_env_var_as_float("LPT_DENOM_EXP", 1)
TLPT_DENOM = read_env_var_as_float("TLPT_DENOM_EXP", 18)
OSMO_DENOM = read_env_var_as_float("OSMO_DENOM_EXP", 6)
AKASH_DENOM = read_env_var_as_float("AKASH_DENOM_EXP", 6)
STRIDE_DENOM = read_env_var_as_float("STRIDE_DENOM_EXP", 6)
KAVA_DENOM = read_env_var_as_float("KAVA_DENOM_EXP", 6)
MARS_DENOM = read_env_var_as_float("MARS_DENOM_EXP", 6)
FETCH_DENOM = read_env_var_as_float("FETCH_DENOM_EXP", 18)
CUDOS_DENOM = read_env_var_as_float("CUDOS_DENOM_EXP", 18)
CHEQD_DENOM = read_env_var_as_float("CHEQD_DENOM_EXP", 9)

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
        try:
            with lock:
                app.logger.debug("Acquired lock.")
                with app.app_context():
                    app.logger.debug("Entered app context.")
                    prices = fetch_prices()
                    deposits = get_deposits()
                    app.logger.debug(f"Deposits Y: {deposits}")

                    app.logger.debug("Fetched prices: {}".format(prices))
                    if prices:
                        app.logger.debug(
                            "Prices exist, proceeding to get stake data.")

                        # Example debug statement before calling get_stake_data for GRT
                        app.logger.debug("Getting GRT stake data...")
                        validators = get_validators()
                        app.logger.debug(f"Validators X: {validators}")

                        grt_validators = get_grt_validators()
                        for val in grt_validators:
                            # Check if the validator address needs to be switched
                            if val == "0xd365FdC4535626464A69cADA251853654546816f":
                                val = "0x07ca020fdde5c57c1c3a783befdb08929cf77fec"
                            app.logger.debug("GRT Validator:" + str(val))
                            root_query = environ.get("ROOT_GRT_QUERY") % val
                            get_stake_data(
                                delegator_stakes, prices,
                                environ.get("GRT_SYMBOL"), environ.get("GRT_ID"),
                                environ.get("GRT_URL"), root_query,
                                denom=GRT_DENOM, source=DataSource.GRT
                            )
                        app.logger.debug("Fetched GRT stake data.")
                        
                        app.logger.debug("Getting LPT stake data...")
                        lpt_validators = get_lpt_validators()
                        for val in lpt_validators:
                            if val == "0x61977B07824512e6AA91d47105B57a5F04C5f4d2":
                                val = "0x4a1c83b689816e40b695e2f2ce8fc21229076e74"
                            root_query = environ.get("ROOT_LPT_QUERY") % val
                            get_stake_data(
                                delegator_stakes, prices,
                                environ.get("LPT_SYMBOL"), environ.get("LPT_ID"),
                                environ.get("LPT_URL"), root_query,
                                denom=LPT_DENOM, source=DataSource.LPT,
                                special_address=environ.get("TENDERIZE_ADDRESS")
                            )
                        app.logger.debug("Fetched LPT stake data.")
                        
                        # Debug statement for TLPT
                        app.logger.debug("Getting TLPT stake data...")
                        get_stake_data(
                            delegator_stakes, prices,
                            environ.get("LPT_SYMBOL"), environ.get("TLPT_ID"),
                            environ.get("TLPT_URL"), environ.get("TLPT_QUERY"),
                            denom=TLPT_DENOM, source=DataSource.TLPT
                        )
                        app.logger.debug("Fetched TLPT stake data.")
                        app.logger.debug(
                            "tlpt delegator data: " + str(delegator_stakes))

                        # Debug statement for Akash
                        app.logger.debug("Getting Akash stake data...")
                        get_stake_data(
                            delegator_stakes, prices,
                            environ.get("AKASH_SYMBOL"), environ.get(
                                "AKASH_ID"),
                            environ.get("AKASH_URL"), None,
                            denom=AKASH_DENOM, source=DataSource.COSMOS, method='GET'
                        )
                        app.logger.debug("Fetched Akash stake data.")

                        # Cosmos data (Stride as another example)
                        app.logger.debug("Fetching Stride stake data...")
                        get_stake_data(
                            delegator_stakes, prices,
                            environ.get("STRIDE_SYMBOL"), environ.get(
                                "STRIDE_ID"),
                            environ.get("STRIDE_URL"), None,
                            denom=STRIDE_DENOM, source=DataSource.COSMOS, method='GET'
                        )
                        app.logger.debug("Fetched Stride stake data.")

                        # Cosmos data (Kava as another example)
                        app.logger.debug("Fetching Kava stake data...")
                        get_stake_data(
                            delegator_stakes, prices,
                            environ.get("KAVA_SYMBOL"), environ.get("KAVA_ID"),
                            environ.get("KAVA_URL"), None,
                            denom=KAVA_DENOM, source=DataSource.COSMOS, method='GET'
                        )
                        app.logger.debug("Fetched Kava stake data.")

                        # Cosmos data (Mars as another example)
                        app.logger.debug("Fetching Mars stake data...")
                        get_stake_data(
                            delegator_stakes, prices,
                            environ.get("MARS_SYMBOL"), environ.get("MARS_ID"),
                            environ.get("MARS_URL"), None,
                            denom=MARS_DENOM, source=DataSource.COSMOS, method='GET'
                        )
                        app.logger.debug("Fetched Mars stake data.")

                        # Cosmos data (Fetch as another example)
                        app.logger.debug("Fetching Fetch stake data...")
                        get_stake_data(
                            delegator_stakes, prices,
                            environ.get("FETCH_SYMBOL"), environ.get(
                                "FETCH_ID"),
                            environ.get("FETCH_URL"), None,
                            denom=FETCH_DENOM, source=DataSource.COSMOS, method='GET'
                        )
                        app.logger.debug("Fetched Fetch stake data.")

                        # Cosmos data (Cudos as another example)
                        app.logger.debug("Fetching Cudos stake data...")
                        get_stake_data(
                            delegator_stakes, prices,
                            environ.get("CUDOS_SYMBOL"), environ.get(
                                "CUDOS_ID"),
                            environ.get("CUDOS_URL"), None,
                            denom=CUDOS_DENOM, source=DataSource.COSMOS, method='GET'
                        )
                        app.logger.debug("Fetched Cudos stake data.")

                        # Cosmos data (Cheqd as another example)
                        app.logger.debug("Fetching Cheqd stake data...")
                        get_stake_data(
                            delegator_stakes, prices,
                            environ.get("CHEQD_SYMBOL"), environ.get(
                                "CHEQD_ID"),
                            environ.get("CHEQD_URL"), None,
                            denom=CHEQD_DENOM, source=DataSource.COSMOS, method='GET'
                        )
                        app.logger.debug("Fetched Cheqd stake data.")
                        
                        update_leaderboard(delegator_stakes, prices)

                        generate_summary()
                        # Calculate the time taken for the data calculation and leaderboard update
                        elapsed_time = time.time() - start_time

                        # Calculate the time remaining until the next update (60 seconds - elapsed time)
                        time_remaining = max(60 - elapsed_time, 0)

                        # Sleep for the time remaining before updating again
                        time.sleep(time_remaining)
        except Exception as e:
            app.logger.exception("Error in repeating task")
            time.sleep(60)


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

@app.route('/placeholder-data')
def placeholder_data():
    app.logger.debug("Entering /leaderboard route")
    try:
        app.logger.debug("Connecting to SQLite database...")
        conn = sqlite3.connect('leaderboard.db')
        c = conn.cursor()
        app.logger.debug("Executing SQL query to fetch leaderboard data...")
        c.execute(
            "SELECT * FROM leaderboard ORDER BY total_points DESC LIMIT 500")

        rows = c.fetchall()
        app.logger.debug(f"Fetched {len(rows)} rows.")
        leaderboard_data = [{'address': address, 'protocol': blockchain, 'treasury_contribution': treasury_contribution, 'delegated_stake': delegated_stake, 'daily_hour_change': daily_hour_change, 'total_points': total_points}
                            for address, blockchain,treasury_contribution, delegated_stake, daily_hour_change, total_points in rows]
        app.logger.debug("Closing SQLite database connection.")
        conn.close()
        app.logger.debug("Returning leaderboard data.")
        return jsonify(leaderboard_data)
    except sqlite3.Error as e:
        app.logger.debug(f"SQLite error in /leaderboard route: {e}")
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
        distribution_address = environ.get("DISTRIBUTION_ADDRESS")

        app.logger.debug("Setting token address...")
        token_address = environ.get("TOKEN_ADDRESS")

        app.logger.debug("Setting validator subscription addess...")
        val_registry_address = environ.get("VALIDATOR_REGISTRY")

        app.logger.debug("Setting treasury address...")
        treasury_address = environ.get("TREASURY_ADDRESS")

        app.logger.debug("Initializing contract...")

        with open("/home/ubuntu/leaderboard/server/token_abi.json", "r") as f:
            TOKEN_ABI = json.load(f)

        with open("/home/ubuntu/leaderboard/server/distribution_abi.json", "r") as f:
            DISTRIBUTION_ABI = json.load(f)

        with open("/home/ubuntu/leaderboard/server/validator_registry_abi.json", "r") as f:
            VAL_REGISTRY_ABI = json.load(f)

        with open("/home/ubuntu/leaderboard/server/treasury_abi.json", "r") as f:
            TREASURY_ABI = json.load(f)

        distribution_contract = w3.eth.contract(
            address=distribution_address, abi=DISTRIBUTION_ABI)
        token_contract = w3.eth.contract(address=token_address, abi=TOKEN_ABI)
        val_registry_contract = w3.eth.contract(address=val_registry_address, abi=VAL_REGISTRY_ABI)
        treasury_contract = w3.eth.contract(address=treasury_address, abi=TREASURY_ABI)

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
                    app.logger.debug(f"Reward: {reward}")  # Corrected f-string
                    app.logger.debug(f"Delegator weight: {delegator_weight}")  # Corrected f-string
                    app.logger.debug(f"Total: {total}")  # Corrected f-strin
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
                # Build the transaction to call setClaimableAmozZZzz-untzz
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
        conn = get_db_connection()
        app.logger.debug("Fetching max rebate from database...")
        treasury_contribution_value = get_max_rebate(
            blockchain, blockchain, conn)
        app.logger.debug(f"Max rebate fetched: {treasury_contribution_value}")
        app.logger.debug("Closing database .")
        close_db_connection(conn)

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
        prices = fetch_prices()

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
            price = calculate_price_by_blockchain(
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
