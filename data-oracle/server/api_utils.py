import json
import requests
import sqlite3
import random
from enum import Enum
import time
from os import environ
from flask import current_app as app, Flask, jsonify, request, render_template
from flask_cors import CORS
from web3 import Web3
from decimal import Decimal
from logging.handlers import RotatingFileHandler

e = 'generic error'

class DataSource(Enum):
    GRT = 1
    LPT = 2
    TLPT = 3
    COSMOS = 4


def read_env_var_as_float(env_name, default_value):
    try:
        return 10 ** int(environ.get(env_name, default_value))
    except ValueError:
        app.logger.debug(f"Error: {env_name} is not set or is not an integer.")
        return None


# Constants for denominators
GRT_DENOM, LPT_DENOM, TLPT_DENOM = map(read_env_var_as_float, [
                                       "GRT_DENOM_EXP", "LPT_DENOM_EXP", "TLPT_DENOM_EXP"], [18, 1, 18])
OSMO_DENOM, AKASH_DENOM, STRIDE_DENOM = map(read_env_var_as_float, [
                                            "OSMO_DENOM_EXP", "AKASH_DENOM_EXP", "STRIDE_DENOM_EXP"], [6, 6, 6])
KAVA_DENOM, MARS_DENOM, FETCH_DENOM = map(read_env_var_as_float, [
                                          "KAVA_DENOM_EXP", "MARS_DENOM_EXP", "FETCH_DENOM_EXP"], [6, 6, 18])


def fetch_price(prices, currency_id, source):
    app.logger.debug(f"Fetching price for {currency_id} from {source.name}")
   # app.logger.debug(f"Prices in fetch price XX: {prices}")

    price = prices['data'][currency_id]['quote']['USD']['price']
    app.logger.debug(f"Price for {currency_id} is {price}")
    return price


def fetch_data(url, query, headers=None, method='POST'):
  #  app.logger.debug(f"Fetching data from URL {url} with query {query}")
    if method == 'POST':
        return requests.post(url, json={'query': query}, headers=headers)
    elif method == 'GET':
        return requests.get(url, headers=headers)


def parse_data(response_text, source):
    # app.logger.debug(f"Parsing data for {source.name}")
    parsed_json = json.loads(response_text)
    if source == DataSource.GRT:
        return parsed_json['data']['indexer']['delegators']
    elif source == DataSource.LPT:
        return parsed_json['data']['transcoder']['delegators']
    elif source == DataSource.TLPT:
        # Flatten the nested 'users' list to match the format of the other data sources
        deployments = parsed_json['data']['deployments']
        return [user for deployment in deployments for user in deployment['users']]
    elif source == DataSource.COSMOS:
        return parsed_json.get('delegation_responses')

def get_validators():
    try:
        app.logger.debug("Fetching all validators..")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))

        app.logger.debug("Setting validator subscription addess...")
        val_registry_address = environ.get("VALIDATOR_REGISTRY")

        app.logger.debug("Initializing contract...")
        with open("/home/ubuntu/leaderboard/server/validator_registry_abi.json", "r") as f:
            VAL_REGISTRY_ABI = json.load(f)
        val_registry_contract = w3.eth.contract(address=val_registry_address, abi=VAL_REGISTRY_ABI)

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching validators...")
            registered_validators = val_registry_contract.functions.getValidators().call()
            app.logger.debug(f"Registered Validators: {registered_validators}")
         
            return registered_validators

        else:
            app.logger.debug("Web3 is not connected.")

        return jsonify({"error": str('error 3')}), 500

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed to fetch grt validators"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_deposits():
    try:
        validators = get_validator_addresses()
        app.logger.debug("Fetching all deposits..")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))

        app.logger.debug("Setting treasury addess...")
        treasury_address = environ.get("TREASURY_ADDRESS")

        app.logger.debug("Initializing contract...")
        with open("/home/ubuntu/leaderboard/server/treasury_abi.json", "r") as f:
            TREASURY_ABI = json.load(f)
        treasury_contract = w3.eth.contract(address=treasury_address, abi=TREASURY_ABI)

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching deposits...")
            registered_deposits = treasury_contract.functions.getAllDeposits(validators).call()
            app.logger.debug(f"Registered deposits: {registered_deposits}")
         
            return registered_deposits

        else:
            app.logger.debug("Web3 is not connected.")

        return jsonify({"error": "depositerror"}), 500

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed deposits"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500


def get_validators():
    try:
        app.logger.debug("Fetching all validators..")
        #w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))
        w3 = Web3(Web3.HTTPProvider("https://eth-sepolia.g.alchemy.com/v2/ruITE4LBU-DGE-bY03e1FKUw-1NWhb2p"))
        app.logger.debug("Setting validator subscription addess...")
        val_registry_address = environ.get("VALIDATOR_REGISTRY")

        app.logger.debug("Initializing contract...")
        with open("/home/ubuntu/leaderboard/server/validator_registry_abi.json", "r") as f:
            VAL_REGISTRY_ABI = json.load(f)
        val_registry_contract = w3.eth.contract(address=val_registry_address, abi=VAL_REGISTRY_ABI)

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching validators...")
            registered_validators = val_registry_contract.functions.getValidators().call()
            app.logger.debug(f"Registered Validators: {registered_validators}")
         
            return registered_validators

        else:
            app.logger.debug("Web3 is not connected.")

        return jsonify({"error": str('error 2')}), 500

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed to fetch grt validators"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_validator_addresses():
    registered_validators = get_validators()
    addresses = [validator[1] for validator in registered_validators]
    return addresses


def get_grt_validators():
    try:
        app.logger.debug("Fetching grt validators..")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))

        app.logger.debug("Setting validator subscription addess...")
        val_registry_address = environ.get("VALIDATOR_REGISTRY")

        app.logger.debug("Initializing contract...")
        with open("/home/ubuntu/leaderboard/server/validator_registry_abi.json", "r") as f:
            VAL_REGISTRY_ABI = json.load(f)
        val_registry_contract = w3.eth.contract(address=val_registry_address, abi=VAL_REGISTRY_ABI)

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching validators...")
            registered_validators = val_registry_contract.functions.getValidators().call()
            app.logger.debug(f"Registered Validators: {registered_validators}")
            # Filter the list to include only GRT validators
            grt_validators = [validator for validator in registered_validators if validator[0] == 'GRT']

            # Extract the addresses of GRT validators
            grt_addresses = [validator[1] for validator in grt_validators]
            return grt_addresses

        else:
            app.logger.debug("Web3 is not connected.")

        return jsonify({"error": str('e4')}), 500

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed to fetch grt validators"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_lpt_validators():
    try:
        app.logger.debug("Fetching lpt validators..")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))

        app.logger.debug("Setting validator subscription addess...")
        val_registry_address = environ.get("VALIDATOR_REGISTRY")

        app.logger.debug("Initializing contract...")
        with open("/home/ubuntu/leaderboard/server/validator_registry_abi.json", "r") as f:
            VAL_REGISTRY_ABI = json.load(f)
        val_registry_contract = w3.eth.contract(address=val_registry_address, abi=VAL_REGISTRY_ABI)

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching validators...")
            registered_validators = val_registry_contract.functions.getValidators().call()
            app.logger.debug(f"Registered Validators: {registered_validators}")
            # Filter the list to include only lpt validators
            lpt_validators = [validator for validator in registered_validators if validator[0] == 'lpt']

            # Extract the addresses of lpt validators
            lpt_addresses = [validator[1] for validator in lpt_validators]
            return lpt_addresses

        else:
            app.logger.debug("Web3 is not connected.")

        return jsonify({"error": str('error1')}), 500

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {erroressage}")
        return jsonify({"error": "Failed to fetch lpt validators"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_stake_data(delegator_stakes, prices, currency_id, blockchain, url, query, denom=1, source=DataSource, headers=None, special_address=None, method='POST'):
    app.logger.debug("Retrieving stake data for " + blockchain)
    app.logger.debug(f"delegator_stakes: {delegator_stakes}")
    app.logger.debug(f"prices: {prices}")
    app.logger.debug(f"currency_id: {currency_id}")
    app.logger.debug(f"blockchain: {blockchain}")
    app.logger.debug(f"url: {url}")
    app.logger.debug(f"query: {query}")
    app.logger.debug(f"denom: {denom}")
    app.logger.debug(f"source: {source}")
    usd_price = fetch_price(prices, currency_id, source)

    total, tokens, count = 0, 0, 0

    try:
        response = fetch_data(url, query, headers, method)
        delegators = parse_data(response.text, source)

        for delegator in delegators:
            count += 1
            id, staked_tokens = None, 0

            if source == DataSource.GRT:
                id = delegator['id'].split("-")[0]
                staked_tokens = float(delegator['stakedTokens']) / float(denom)

            elif source == DataSource.LPT:
                id = delegator['id']
                staked_tokens = float(delegator['bondedAmount'])

            elif source == DataSource.TLPT:
                app.logger.debug(f"Tenderize user: {delegator}")
                id = delegator['id'].replace("_Livepeer", "")
                staked_tokens = float(
                    delegator['tenderizerStake']) / float(denom)

            elif source == DataSource.COSMOS:
                delegator_info = delegator['delegation']
                id = delegator_info['delegator_address']
                staked_tokens = float(delegator_info['shares']) / float(denom)

            stake = staked_tokens * usd_price
            total += stake
            tokens += staked_tokens

            if id in delegator_stakes:
                delegator_stakes[id]['stake'] += stake
                delegator_stakes[id]['staked_tokens'] = staked_tokens
                # Add more fields as needed
                # delegator_stakes[id]['some_other_field'] = some_value
            else:
                delegator_stakes[id] = {'stake': stake}
                delegator_stakes[id]['blockchain'] = blockchain
                delegator_stakes[id]['staked_tokens'] = staked_tokens

                # Initialize other fields as needed
                # delegator_stakes[id]['some_other_field'] = some_initial_value

    except (requests.exceptions.RequestException, KeyError, json.JSONDecodeError) as e:
        app.logger.debug(f"Error: Could not retrieve {source.name} data: {e}")
        return

    app.logger.debug(
        f"{tokens:.0f} {blockchain} staked by {count} delegators with value of ${total:.0f}")


def calculate_price_by_blockchain(prices, blockchain):

    blockchain_symbol = swap_symbol_id(blockchain)
    if blockchain_symbol == "TLPT":
        blockchain_symbol = "LPT"
    return prices['data'][blockchain_symbol]['quote']['USD']['price']


def swap_symbol_id(value):
    # Define the mapping between symbols and IDs
    symbol_to_id = {
        'GRT': 'the-graph',
        'LPT': 'livepeer',
        'TLPT': 'tenderize',
        'AKT': 'akash-network',
        'STRD': 'stride',
        'KAVA': 'kava',
        'MARS': 'marscoin',
        'FET': 'fetch-ai',
        'CUDOS': 'cudos',
        'CHEQ': 'cheqd-network'
    }

    # Reverse the mapping for id_to_symbol
    id_to_symbol = {v: k for k, v in symbol_to_id.items()}

    # Check if the given value exists in either dictionary and return the corresponding value
    return symbol_to_id.get(value) or id_to_symbol.get(value) or "Value not found"


def calculate_rate_by_blockchain(blockchain):
    rate_values_str = environ.get("RATE_VALUES")
    if rate_values_str:
        # Parse the JSON string to a Python dictionary
        rate_values = json.loads(rate_values_str)
        # Look up the rate value based on the blockchain (ignoring white spaces)
        rate = rate_values.get(blockchain.strip(), 0.0)
        return rate
    else:
        # Return 0.0 if RATE_VALUES is not set
        return 0.0


def fetch_cheqd_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=cheqd&vs_currencies=usd"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if 'cheqd' in data:
            return data['cheqd']['usd']
        else:
            return "CHEQD not found in CoinGecko API."
    else:
        return f"Failed to get data from CoinGecko API. Status code: {response.status_code}"


def fetch_prices():
    url = environ.get("COINMARKETCAP_BASE_URL")
    symbols = environ.get("COINMARKETCAP_SYMBOLS")
    api_key = environ.get("COINMARKETCAP_API_KEY")

    app.logger.debug(f"URL IS: {url}")
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key
    }

    params = {
        'symbol': symbols,
        'convert': 'USD'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        app.logger.debug("Received HTTP %s: %s",
                  response.status_code, response.json())
        if response.status_code == 200:
            return response.json()
        else:
            app.logger.debug("Error: Could not fetch prices.")
            time.sleep(15)
            return {}
    except requests.exceptions.RequestException as e:
        app.logger.debug("Error: Could not fetch prices.")
        app.logger.debug(str(e))
        return {}

# Use total staked value for each delegator to update the leaderboard


def update_leaderboard(delegator_stakes, prices):
    try:
        app.logger.debug("=== Starting Leaderboard Update ===")
      #  app.logger.debug(f"delegator_stakes: {delegator_stakes}")
      #  app.logger.debug(f"prices: {prices}")
        app.logger.debug("Connecting to SQLite database...")
        conn = sqlite3.connect('leaderboard.db')
        c = conn.cursor()
        app.logger.debug("Creating leaderboard table if not exists...")
        c.execute('''CREATE TABLE IF NOT EXISTS leaderboard
                    (address text UNIQUE, blockchain text, treasury_contribution real,
                delegated_stake real,
                daily_hour_change real,
                total_points real)''')

        for delegator, stake_data in delegator_stakes.items():
            address = delegator
            staked_value = stake_data['stake']
            blockchain = stake_data['blockchain']
            staked_tokens = stake_data['staked_tokens']
            delegated_stake, daily_hour_change, total_points = generate_placeholder_data()

            deposit = staked_tokens * \
                calculate_rate_by_blockchain(blockchain)

            app.logger.debug(
                f"Processing delegator: {delegator}, staked_value: {staked_value}, blockchain: {blockchain}")

            # Check if it already exists
            c.execute(
                "SELECT treasury_contribution FROM leaderboard WHERE address = ?", (address,))
            result = c.fetchone()
            app.logger.debug(f"SQL Fetch result: {result}")

            if result:
                app.logger.debug("Updating existing delegator...")

                total_contribution = result[0] + deposit

                app.logger.debug(
                    "Updating leaderboard database for existing delegator...")
                c.execute(
                    "UPDATE leaderboard SET treasury_contribution = ? WHERE address = ?", (total_contribution, address))
            else:
                app.logger.debug("Adding new delegator...")

                app.logger.debug(
                    "Inserting into leaderboard database for new delegator...")
                c.execute(
                    "INSERT INTO leaderboard (address, blockchain, treasury_contribution, delegated_stake, daily_hour_change, total_points) VALUES (?, ?, ?, ?, ?, ?)", (address, blockchain, deposit, delegated_stake, daily_hour_change, total_points))

        conn.commit()
        conn.close()

    except (sqlite3.Error, requests.exceptions.RequestException, KeyError, json.JSONDecodeError) as e:
        app.logger.debug(f"Error in update leaderboard: {e}")

    app.logger.debug("Leaderboard Updated")
    return delegator_stakes

def generate_placeholder_data():

    delegated_stake = random.randint(5000, 50000)
    daily_hour_change = random.randint(1000, 10000)
    total_points = random.randint(100000, 10000000)
       
    return delegated_stake, daily_hour_change, total_points


def generate_summary():
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('leaderboard.db')
        c = conn.cursor()

        # Execute SQL query to fetch all rows from the leaderboard table
        c.execute("SELECT * FROM leaderboard where tokens_staked != 0")
        rows = c.fetchall()

        # Close the connection
        conn.close()

        # Print the header
        print(f"{'Address': <50}{'blockchain': <20}{'Tokens Deposited': <20}")
        print("=" * 160)

        # Print each row in a nicely formatted manner with 2 decimal
        for row in rows:
            address, blockchain, treasury_contribution = row
            print(f"{address: <50}{blockchain: <20}{treasury_contribution: <20.5f}")

    except sqlite3.Error as e:
        print(f"Error in generate_summary: {e}")

# Function to get a database connection


def get_db_connection():
    return sqlite3.connect('leaderboard.db')

# Function to close a database connection


def close_db_connection(conn):
    if conn:
        conn.close()

# Function to get treasury contribution by blockchain


def get_max_rebate(address, blockchain, conn):
    try:
        c = conn.cursor()
        c.execute("SELECT SUM(treasury_contribution) FROM leaderboard WHERE address = ? and blockchain = ?", (address, blockchain))
        result = c.fetchone()

        if result and result[0]:
            return result[0]
        else:
            return 0.0

    except sqlite3.Error as e:
        print(f"Error in get_max_rebate: {e}")
        return 0.0  # Return 0 in case of an error
