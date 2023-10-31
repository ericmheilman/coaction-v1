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
from dotenv import load_dotenv

load_dotenv()

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


def parse_data(response_text, validator):
    blockchain = validator[0]
    # app.logger.debug(f"Parsing data for {blockchain.name}")
    parsed_json = response_text
    if blockchain == 'GRT':
        return parsed_json['data']['indexer']['delegators']
    elif blockchain == 'LPT':
        return parsed_json['data']['transcoder']['delegators']
    else:
        return 'No JSON to parse'
    

def calculate_delegator_rewards(delegators, token_allocation):
    result = []
    for delegator in delegators:
        tokens_mined = float(token_allocation) * delegator['weight']
        # Store the address and weight in a dictionary
        result.append({
            'address': delegator['address'],
            'amount':tokens_mined 
        })
    return result

def assign_tokens(delegators, token_allocation):
    result = []
    for delegator in delegators:
        tokens_mined = float(token_allocation) * delegator['weight']
        # Store the address and weight in a dictionary
        result.append({
            'address': delegator['address'],
            'amount':tokens_mined 
        })
    return result

def distribute_tokens(addresses):
    w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))
    my_private_key = environ.get("MY_PRIVATE_KEY")
    app.logger.debug("Setting sender address...")
    sender_address = environ.get("SENDING_ADDRESS")
    contract = token_contract()
    formatted_addresses = []
    distributed_tokens = []

    for address in addresses:
        formatted_addresses.append(Web3.to_checksum_address(address['address']))
        distributed_tokens.append(int(address['amount']))
    
        # Get the current nonce
    current_nonce = w3.eth.get_transaction_count(sender_address)

    # Increment the nonce
    next_nonce = current_nonce + 1
        
    # Build the transaction to call setClaimableAmounts
    transaction = contract.functions.setClaimableAmounts(formatted_addresses,distributed_tokens).build_transaction({
        'chainId': 11155111,
        'gas': 2000000, 
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': next_nonce,
    })

    app.logger.debug("Signing transaction...")
    signed_txn = w3.eth.account.sign_transaction(
        transaction, my_private_key)

    app.logger.debug("Sending transaction...")
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    app.logger.debug(f'Transaction hash: {txn_hash.hex()}')
    return str(txn_hash.hex())
'''
def set_claimable(addresses, token_allocation):
    w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))
    app.logger.debug("Setting sender address...")
    sender_address = environ.get("SENDING_ADDRESS")
    my_private_key = environ.get("MY_PRIVATE_KEY")
    contract = token_contract()
    for address in addresses:

        # Build the transaction to call setClaimableAmounts
        checksum_address = Web3.to_checksum_address(address['address'])
        payout =  int(address['amount'])
        transaction = contract.functions.setClaimableAmount(checksum_address,payout).build_transaction({
            'chainId': 11155111,
            'gas': 50000, 
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(sender_address),
        })

    app.logger.debug("Signing transaction...")
    signed_txn = w3.eth.account.sign_transaction(
        transaction, my_private_key)

    app.logger.debug("Sending transaction...")
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    app.logger.debug(f'Transaction hash: {txn_hash.hex()}')
    return txn_hash.hex()
'''
def get_total_validator_stake(delegators, validator):
    # Extract the blockchain type from the validator argument
    blockchain = validator[0]
    app.logger.warning(f"Delegate11111: {delegators}")
   # Determine the token_id based on the blockchain type
    if blockchain == 'LPT':
        token_id = 'bondedAmount'
    elif blockchain == 'GRT':
        token_id = 'stakedTokens'
    else:
        raise ValueError(f'Unsupported blockchain type: {blockchain}')

    # Initialize the total stake variable
    total = 0
    app.logger.warning(f"Type of delegators: {type(delegators)}")

    # Check the type of delegators
    if not isinstance(delegators, list):
        app.logger.error(f"Expected delegators to be a list, got {type(delegators)}")
        return 0
    
    
    # Iterate through the delegators list and accumulate the total stake
    for delegator in delegators:
        if not isinstance(delegator, dict):
            app.logger.error(f"Expected each delegator to be a dict, got {type(delegator)}: {delegator}")
            continue
        app.logger.warning(f"Type of delegator: {type(delegator)}")

        app.logger.warning(f"Delegator-------: {delegator}")
        app.logger.warning(f"Delegators: {delegators}")
        # Ensure the token_id key exists in the delegator dictionary
        # Convert the stake amount to float and add it to the total stake
        total += float(delegator[token_id])

    # Return the total stake
    return total
def calculate_delegator_weights(delegators, validator):
    # Ensure total is a float for accurate division
    total_validator_stake = get_total_validator_stake(delegators, validator)
    blockchain = validator[0]
    if blockchain == 'LPT':
        token_id = 'bondedAmount'
    elif blockchain == 'GRT':
        token_id = 'stakedTokens'
    
    # Initialize an empty list to hold the result
    result = []
    if total_validator_stake == 0:
        return result
    # Iterate through the delegators list
    for delegator in delegators:
        # Convert bondedAmount to float for accurate division
        bonded_amount = float(delegator[token_id])
        
        # Calculate the weight
        weight = (bonded_amount / total_validator_stake) * 100
        
        # Store the address and weight in a dictionary
        result.append({
            'address': delegator['id'],
            'weight': weight
        })
    
    return result



def assign_weights(delegators, total):
    # Ensure total is a float for accurate division
    total = float(total)
    
    # Initialize an empty list to hold the result
    result = []
    
    # Iterate through the delegators list
    for delegator in delegators:
        # Convert bondedAmount to float for accurate division
        bonded_amount = float(delegator['bondedAmount'])
        
        # Calculate the weight
        weight = (bonded_amount / total) * 100
        
        # Store the address and weight in a dictionary
        result.append({
            'address': delegator['id'],
            'weight': weight
        })
    
    return result

    
def grt_deposit_value(grt):
   return grt * grt_price()

def grt_deposit_value(lpt):
   return lpt * lpt_price()
        
def total_communal_deposits():
    try:
        app.logger.debug("Fetching test...")
        contract = treasury_contract()
        app.logger.debug("Web3 is connected. Fetching validators...")
        app.logger.debug("Fetching LPT deposits...")
        deposited_lpt = contract.functions.totalLPTDeposited().call()
        app.logger.debug(f"Deposited LPT: {deposited_lpt}")
        app.logger.debug("Fetching GRT deposits...")
        deposited_grt = contract.functions.totalGRTDeposited().call()
        app.logger.debug(f"Deposited GRT: {deposited_grt}")
        grt_value = deposited_grt * grt_price()
        app.logger.debug(f"GRT Value: {grt_value}")
        lpt_value = deposited_lpt * lpt_price()
        app.logger.debug(f"LPT Value: {lpt_value}")
        total_communal_deposits = grt_value + lpt_value
        return total_communal_deposits

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed to distribute rewards"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500
def get_validator_deposit(validator, deposits):
    blockchain = validator[0]
    total_validator_deposits = 0
    for deposit in deposits:
        if deposit[1] == blockchain:
            total_validator_deposits += deposit[2]
    return total_validator_deposits
  
def get_lpt_val_deposit(validator):
    try:
        validators = get_validator_addresses()
        contract = treasury_contract()
        app.logger.debug("Web3 is connected. Fetching deposits...")
        lpt_deposits = contract.functions.getAllLPTDeposits(validators).call()
        deposits = [deposit[1] for deposit in lpt_deposits if deposit[0] == validator[1]]
        app.logger.debug(f"Registered lptvalidator deposits: {deposits}")
        return deposits

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed deposits"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_lpt_val_deposits():
    try:
        validators = get_validator_addresses()
        contract = treasury_contract()
        app.logger.debug("Web3 is connected. Fetching deposits...")
        lpt_deposits = contract.functions.getAllLPTDeposits(validators).call()
        deposits = [deposit[1] for deposit in lpt_deposits if deposit[1] != 0]
        app.logger.debug(f"Registered lptvalidator deposits: {deposits}")
        return deposits

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed deposits"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_grt_val_deposits():
    try:
        validators = get_validator_addresses()
        contract = treasury_contract()
        app.logger.debug("Web3 is connected. Fetching deposits...")
        grt_deposits = contract.functions.getAllGRTDeposits(validators).call()
        deposits = [deposit[1] for deposit in grt_deposits if deposit[1] != 0]
        app.logger.debug(f"Registered grtvalidator deposits: {deposits}")
        return deposits

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed deposits"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
def get_grt_val_deposit(validator):
    try:
        validators = get_validator_addresses()
        contract = treasury_contract()
        app.logger.debug("Web3 is connected. Fetching deposits...")
        grt_deposits = contract.functions.getAllGRTDeposits(validators).call()
        deposits = [deposit[1] for deposit in grt_deposits if deposit[0] == validator[1]]
        app.logger.debug(f"Registered grtvalidator deposits: {deposits}")
        return deposits

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed deposits"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_blockchain(validator):
    return validator[0]

def get_deposits():
    try:
        validators = get_validator_addresses()
        app.logger.debug("Fetching all deposits..")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))

        app.logger.debug("Setting treasury addess...")
        treasury_address = environ.get("TREASURY_ADDRESS")

        app.logger.debug("Initializing contract...")
        with open(environ.get("TREASURY_ABI_JSON"), "r") as f:
            TREASURY_ABI = json.load(f)
        treasury_contract = w3.eth.contract(address=treasury_address, abi=TREASURY_ABI)

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching lpt deposits...")
            registered_grt_deposits = treasury_contract.functions.getAllGRTDeposits(validators).call()
            app.logger.debug(f"Registered grt deposits: {registered_grt_deposits}")
            registered_lpt_deposits = treasury_contract.functions.getAllLPTDeposits(validators).call()
           # registered_deposits = treasury_contract.functions.getAllDeposits(validators).call()
         # Initialize an empty list to store consolidated deposits
            consolidated_deposits = []

            # Process GRT deposits
            for deposit in registered_grt_deposits:
                address, amount = deposit  # Unpack deposit tuple
                consolidated_deposits.append((address, 'GRT', amount))

            # Process LPT deposits
            for deposit in registered_lpt_deposits:
                address, amount = deposit  # Unpack deposit tuple
                consolidated_deposits.append((address, 'LPT', amount))

            # Now consolidated_deposits contains the desired formatted data
            app.logger.debug(f"Consolidated deposits: {consolidated_deposits}")
            return consolidated_deposits

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

def calculate_token_allocation(deposit, validator, minted_tokens):
    deposit_value = get_deposit_value(deposit, validator)
    app.logger.debug(f"Deposit value: {deposit_value}")
    total_deposit_value = get_total_deposit_value()
    app.logger.debug(f"Total deposit value: {total_deposit_value}")
    deposit_weight = float(deposit_value) / float(total_deposit_value)
    token_allocation = deposit_weight * float(minted_tokens)
    return token_allocation

def get_validators():
    try:
        app.logger.debug("Fetching all validators..")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))

        app.logger.debug("Setting validator subscription addess...")
        val_registry_address = environ.get("VALIDATOR_REGISTRY")

        app.logger.debug("Initializing contract...")
        with open(environ.get("VALIDATOR_ABI_JSON"), "r") as f:
            VAL_REGISTRY_ABI = json.load(f)
        val_registry_contract = w3.eth.contract(address=val_registry_address, abi=VAL_REGISTRY_ABI)

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching validators...")
            registered_validators = val_registry_contract.functions.getValidators().call()
            app.logger.debug(f"Registered Validators: {registered_validators}")
         
            return registered_validators

        else:
            app.logger.debug("Web3 is not connected.")

        return jsonify({"error": str(e)}), 500

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
        with open(environ.get("VALIDATOR_ABI_JSON"), "r") as f:
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

        return jsonify({"error": str(e)}), 500

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
        with open(environ.get("VALIDATOR_ABI_JSON"), "r") as f:
            VAL_REGISTRY_ABI = json.load(f)
        val_registry_contract = w3.eth.contract(address=val_registry_address, abi=VAL_REGISTRY_ABI)

        if w3.is_connected():
            app.logger.debug("Web3 is connected. Fetching validators...")
            registered_validators = val_registry_contract.functions.getValidators().call()
            app.logger.debug(f"Registered Validators: {registered_validators}")
            # Filter the list to include only lpt validators
            lpt_validators = [validator for validator in registered_validators if validator[0] == 'LPT']

            # Extract the addresses of lpt validators
            lpt_addresses = [validator[1] for validator in lpt_validators]
            return lpt_addresses

        else:
            app.logger.debug("Web3 is not connected.")

        return jsonify({"error": str(e)}), 500

    except ValueError as e:
        error_message = str(e)
        if "execution reverted" in error_message:
            app.logger.debug(f"Transaction failed: {error_message}")
        return jsonify({"error": "Failed to fetch lpt validators"}), 500

    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_delegator_data(validator):
    blockchain = validator[0]
    if blockchain == 'LPT':
        return get_lpt_delegators(validator)
    elif blockchain == 'GRT':
        return get_grt_delegators(validator)

def get_lpt_delegators(validator,headers=None,method='POST'):
    address = validator[1]
    if address == "0x61977B07824512e6AA91d47105B57a5F04C5f4d2":
        address = "0x4a1c83b689816e40b695e2f2ce8fc21229076e74"
    query = environ.get("ROOT_LPT_QUERY") % address
    app.logger.debug(f"Query: {query}")
    url = environ.get("LPT_URL")
    total_tokens = 0
    try:
        response = fetch_data(url, query, headers, method)
        app.logger.debug(response)
        delegators = parse_lpt_data(response.text)    
      #  delegators = [response.json() for response in delegators_response]
    
        for delegator in delegators:
            app.logger.debug(f"Delegator: {delegator['id']}")
            app.logger.debug(f"Delegator: {delegator['bondedAmount']}")
            total_tokens += float(delegator['bondedAmount'])
        return delegators
    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_grt_delegators(validator, headers=None, method='POST'):
    address = validator[1].split("-")[0]
    if address == "0xd365FdC4535626464A69cADA251853654546816f":
        address = "0x07ca020fdde5c57c1c3a783befdb08929cf77fec"
    query = environ.get("ROOT_GRT_QUERY") % address
    url = environ.get("GRT_URL")
    grt_denom = environ.get('GRT_DENOM_EXP')
    result = []

    try:
        response = fetch_data(url, query, headers, method)
        app.logger.debug(response)

        delegators = parse_grt_data(response.text)
        app.logger.debug(f"Delegators: {delegators}")
        if not isinstance(delegators, list):
            app.logger.warning(f"parse_grt_data did not return a list: {delegators}")
            return []

        for delegator in delegators:
            # app.logger.debug(f"Delegator: {delegator['id']}")
            # app.logger.debug(f"Delegator: {delegator['stakedTokens']}")
            bonded_amount = delegator['stakedTokens'] / 10**int(grt_denom)
            result.append({
                'id': delegator['id'],
                'bondedAmount': bonded_amount
            })

        return result
    except Exception as e:
        app.logger.debug(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def parse_grt_data(response_text):
  #  app.logger.debug(f"Parsing data for {response_text}")
    parsed_json = json.loads(response_text)
   # app.logger.debug(f"Parsed json: {parsed_json}")
    return parsed_json['data']['indexer']['delegators']

def parse_lpt_data(response_text):
    #app.logger.debug(f"Parsing data for {response_text}")
    parsed_json = json.loads(response_text)
  #  app.logger.debug(f"Parsed json: {parsed_json}")
    return parsed_json['data']['transcoder']['delegators']

def get_stake_data(delegator_stakes, prices, currency_id, blockchain, url, query, denom=1, source=DataSource, headers=None, special_address=None, method='POST'):
    #app.logger.debug("Retrieving stake data for " + blockchain)
    #app.logger.debug(f"delegator_stakes: {delegator_stakes}")
    #app.logger.debug(f"prices: {prices}")
    #app.logger.debug(f"currency_id: {currency_id}")
 #   #app.logger.debug(f"blockchain: {blockchain}")
    #app.logger.debug(f"url: {url}")
    #app.logger.debug(f"query: {query}")
    #app.logger.debug(f"denom: {denom}")
    #app.logger.debug(f"source: {source}")
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
    
def token_contract():
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))
        token_address = environ.get("TOKEN_ADDRESS")
        with open(environ.get("TOKEN_ABI_JSON"), "r") as f:
                    TOKEN_ABI = json.load(f)
        return w3.eth.contract(address=token_address, abi=TOKEN_ABI)

def decay_amount():
    contract = token_contract()
    return contract.functions.getDecayedAmount().call()

    
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

def treasury_contract():

        app.logger.debug("Fetching test...")

        app.logger.debug("Initializing Web3...")
        w3 = Web3(Web3.HTTPProvider(environ.get("INFURA_API")))
        app.logger.debug("Setting treasury address...")
        treasury_address = environ.get("TREASURY_ADDRESS")

        app.logger.debug("Initializing contract...")

        with open(environ.get("TREASURY_ABI_JSON"), "r") as f:
            TREASURY_ABI = json.load(f)

        return w3.eth.contract(address=treasury_address, abi=TREASURY_ABI)

def get_deposit_value(deposit, validator):
    blockchain = validator[0]
    if blockchain == 'LPT':
        return deposit * lpt_price()
    if blockchain == 'GRT':
        return deposit * grt_price()

def get_total_deposits():
    # Assume the validators and depositors are known and are in these lists
    contract = treasury_contract()
    total_grt_deposited = contract.functions.totalGRTDeposited().call()
    total_lpt_deposited = contract.functions.totalLPTDeposited().call()

    app.logger.debug(f'Total GRT Deposited: {total_grt_deposited}')
    app.logger.debug(f'Total LPT Deposited: {total_lpt_deposited}')

    return total_grt_deposited, total_lpt_deposited

def get_total_deposit_value():
    # Assume the validators and depositors are known and are in these lists
    grt_deposits, lpt_deposits = get_total_deposits()

    return grt_deposits * grt_price() + lpt_deposits * lpt_price()

def lpt_price():
    prices = fetch_prices()
    return prices['data']['LPT']['quote']['USD']['price']

def grt_price():
    prices = fetch_prices()
    return prices['data']['GRT']['quote']['USD']['price']

def fetch_prices():
    url = environ.get("COINMARKETCAP_BASE_URL")
    symbols = environ.get("COINMARKETCAP_SYMBOLS")
    api_key = environ.get("COINMARKETCAP_API_KEY")

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
     #   app.logger.debug("Received HTTP %s: %s",
        #          response.status_code, response.json())ßs
        if response.status_code == 200:
            return response.json()
        else:
            app.logger.debug("Error: Could not fetch prices.")
            time.sleep(15)
            return {}
    except requests.exceptions.RequestException as e:
        app.logger.debug("Error: Could not fetch prices.")
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
        c.execute("SELECT * FROM leaderboard")
        rows = c.fetchall()

        # Close the connection
        conn.close()

        #  app.logger.debug the header
        app.logger.debug(f"{'Address': <50}{'blockchain': <20}{'Tokens Deposited': <20}")
        app.logger.debug("=" * 160)

        # app.logger.debug each row in a nicely formatted manner with 2 decimal
        for row in rows:
            address, blockchain, treasury_contribution = row
            app.logger.debug(f"{address: <50}{blockchain: <20}{treasury_contribution: <20.5f}")

    except sqlite3.Error as e:
        app.logger.debug(f"Error in generate_summary: {e}")

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
        app.logger.debug(f"Error in get_max_rebate: {e}")
        return 0.0  # Return 0 in case of an error
