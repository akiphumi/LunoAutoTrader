import json
from luno_python.client import Client

# Load API keys from the 'keys.json' file
with open('keys.json', 'r') as f:
    api_keys = json.load(f)

# Initialize the Luno client
client = Client(api_key_id=api_keys['api_key_id'], api_key_secret=api_keys['api_key_secret'])

def get_portfolio_balance(client):
    tickers = client.get_tickers()
    balances = client.get_balances()
    total_balance = 0
    
    for balance in balances['balance']:
        asset = balance['asset']
        asset_balance = float(balance['balance'])
        
        if asset != 'MYR':
            for ticker in tickers['tickers']:
                if ticker['pair'] == f"{asset}MYR":
                    asset_price = float(ticker['last_trade'])
                    break
            asset_value = asset_balance * asset_price
        else:
            asset_value = asset_balance
        
        total_balance += asset_value
    
    return total_balance

def calculate_rebalance_amounts(client, target_portfolio, tolerance=0.01):
    current_balance = get_portfolio_balance(client)
    balances = client.get_balances()
    rebalance_amounts = {}
    current_asset_balances = {}

    for balance in balances['balance']:
        asset = balance['asset']
        current_asset_balances[asset] = float(balance['balance'])

    for asset, target_percentage in target_portfolio.items():
        ideal_balance = current_balance * target_percentage
        asset_balance = current_asset_balances.get(asset, 0)

        if asset != 'MYR':
            asset_price = 0
            for ticker in client.get_tickers()['tickers']:
                if ticker['pair'] == f"{asset}MYR":
                    asset_price = float(ticker['last_trade'])
                    break
            asset_value = asset_balance * asset_price
        else:
            asset_value = asset_balance

        rebalance_amount = ideal_balance - asset_value

        if abs(rebalance_amount) / ideal_balance > tolerance:
            rebalance_amounts[asset] = rebalance_amount
        else:
            rebalance_amounts[asset] = 0

    return rebalance_amounts

def post_limit_order(client, order):
    response = client.post_limit_order(pair=order['pair'], price=order['price'], volume=order['volume'], order_type=order['type'])
    return response

def post_market_order(client, order):
    response = client.post_market_order(pair=order['pair'], volume=order['volume'], order_type=order['type'])
    return response

def create_rebalance_orders(client, rebalance_amounts, target_portfolio, min_trade_volumes):
    orders = []

    # Get all the ticker information for supported currency pairs
    tickers = client.get_tickers()

    # Iterate over each asset in the target portfolio
    for asset, target_percentage in target_portfolio.items():
        rebalance_amount = rebalance_amounts[asset]

        # Find the corresponding ticker for the asset
        for ticker in tickers['tickers']:
            if ticker['pair'] == f"{asset}MYR":
                asset_price = float(ticker['last_trade'])
                break

        # Convert the rebalance amount to the asset's currency
        rebalance_amount_asset = rebalance_amount / asset_price

        # Determine the order type (buy or sell)
        order_type = 'BID' if rebalance_amount_asset > 0 else 'ASK'

        # Check if the order volume is within the minimum and maximum trade volumes
        min_trade_volume, max_trade_volume = min_trade_volumes[asset]
        if min_trade_volume <= abs(rebalance_amount_asset) <= max_trade_volume:
            # Create the order
            order = {
                'pair': f"{asset}MYR",
                'price': asset_price,
                'type': order_type,
                'volume': abs(rebalance_amount_asset)
            }

            # Print the order details
            print(f"Created order for {asset}: {order}")

            # Add the order to the list of orders
            orders.append(order)
        else:
            print(f"Order volume for {asset} is out of range: {rebalance_amount_asset}")

    return orders

def get_decimal_precision():
    precision = {
        'ADA': 1,
        'BCH': 3,
        'XBT': 4,
        'ETH': 3,
        'LINK': 2,
        'LTC': 3,
        'SOL': 2,
        'UNI': 1,
        'XRP': 0,
        'MATIC': 0,
        'AVAX': 2  # Added decimal precision for AVAX
    }
    return precision


def execute_rebalance_orders(client, rebalance_amounts, target_portfolio, min_trade_volumes):
    # Create the rebalance orders
    orders = create_rebalance_orders(client, rebalance_amounts, target_portfolio, min_trade_volumes)

    # Get the decimal precision for each asset
    decimal_precision = get_decimal_precision()

    # Execute the orders
    for order in orders:
        try:
            # Round the order volume according to the decimal precision for the asset
            asset = order['pair'].split('MYR')[0]
            rounded_volume = round(order['volume'], decimal_precision[asset])

            # Print the order details
            print(f"Executing {order['type']} order for {order['pair']} at price {order['price']} and volume {rounded_volume}")

            if order['type'] == 'BID':
                response = client.post_limit_order(pair=order['pair'], type='BID', volume=str(rounded_volume), price=str(order['price']))
            else:
                response = client.post_limit_order(pair=order['pair'], type='ASK', volume=str(rounded_volume), price=str(order['price']))

            print(f"Executed {order['type']} order for {order['pair']} at price {order['price']} and volume {rounded_volume}")
        except Exception as e:
            print(f"Error executing {order['type']} order for {order['pair']}: {e}")

def get_pending_orders(client):
    try:
        orders = client.list_orders(state="PENDING")
        if orders is None or 'orders' not in orders:
            return []
        return orders['orders']
    except Exception as e:
        print(f"Error getting pending orders: {e}")
        return []  # 空のリストを返すように変更

def cancel_all_pending_orders(client):
    pending_orders = get_pending_orders(client)
    if pending_orders is not None:  # この行を追加
        for order in pending_orders:
            try:
                client.stop_order(order_id=order['order_id'])
                order_price = order['price'] if 'price' in order else 'unknown'
                order_volume = order['volume'] if 'volume' in order else 'unknown'
                print(f"Canceled pending order {order['order_id']}: {order['type']} {order['pair']} at price {order_price} and volume {order_volume}")
            except Exception as e:
                print(f"Error canceling order {order['order_id']}: {e}")


# Calculate the total portfolio balance
total_balance = get_portfolio_balance(client)
print(f"Total Portfolio Balance (MYR): {total_balance:.2f}")

target_portfolio = {
    "XBT": 0.25,  # BTC
    "ETH": 0.20,
    "XRP": 0.07,
    "LTC": 0.04,
    "ADA": 0.04,
    "SOL": 0.04,
    "LINK": 0.03,
    "UNI": 0.03,
    "BCH": 0.03,
    "MATIC": 0.04,
    "AVAX": 0.03  # Added AVAX with an allocation of 0.04
}

# Calculate the rebalance amounts for the target portfolio
rebalance_amounts = calculate_rebalance_amounts(client, target_portfolio)
print("Rebalance Amounts:", rebalance_amounts)

# Define the minimum and maximum trade volumes for each asset
min_trade_volumes = {
    'ADA': (0.10, 100000),
    'BCH': (0.001, 40),
    'XBT': (0.0002, 1),  # Please double-check this value. It seems quite low compared to others.
    'ETH': (0.001, 100),
    'LINK': (0.1, 1000),
    'LTC': (0.001, 200),
    'SOL': (0.05, 1000),
    'UNI': (0.10, 2000),
    'XRP': (0.10, 80000),
    'MATIC': (0.10, 80000),
    'AVAX': (0.05, 5000),  # Added min and max trade volumes for AVAX
}


# Cancel all pending orders before rebalancing
cancel_all_pending_orders(client)

# Execute the rebalance orders
execute_rebalance_orders(client, rebalance_amounts, target_portfolio, min_trade_volumes)
