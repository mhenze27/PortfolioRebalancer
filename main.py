import yfinance as yf


PRICES = {}

def get_price(symbol: str) -> float:
    if symbol in PRICES.keys():
        return PRICES[symbol]
    else:
        stock = yf.Ticker(symbol)
        info = stock.get_info()
        # Handle stocks
        if "currentPrice" in info:
            price = info["currentPrice"]
        # Handle ETFs
        elif "regularMarketPrice" in info:
            price = info["regularMarketPrice"]

        PRICES[symbol] = price
        return price

def get_current_portfolio() -> dict:
    portfolio = {}

    complete = False
    while not complete:

        valid_symbol = False
        while not valid_symbol:
            print("\nEnter a stock symbol: ")
            symbol = input(">>> ")
            if not symbol.isalpha():
                print("Not a valid stock symbol.")
            else:
                symbol = symbol.upper()
                if symbol == "STOP":
                    complete = True
                    break
                print(f"Your stock symbol is {symbol}")

                # Confirm it is a valid stock
                try:
                    price = get_price(symbol)
                    #print(f"The current price of {symbol} is ${price}.")
                    valid_symbol = True
                except KeyError:
                    print("Not a valid stock symbol.")
                
        valid_shares = False
        while not valid_shares and not complete:
            print("Enter the number of shares:")
            shares = input(">>> ")

            if not shares.isdigit():
                print("Invalid number of shares.")
            else:
                shares = int(shares)
                if shares > 0:
                    valid_shares = True
                else:
                    print("Invalid number of shares.")
                        
        print(f"You have {shares} shares of {symbol}.")

        # Add the entry to the portfolio dictionary
        if symbol != "STOP":
            portfolio[symbol] = shares
    
    return portfolio

def get_cash_balance() -> float:
    print("\nWhat is the cash balance?")
    valid_cash = False
    while not valid_cash:
        cash = input(">>> ")
        try:
            cash = float(cash)
            valid_cash = True
        except ValueError:
            print("Incorrect cash balance.")
    print(f"The cash balance in your portfolio is ${cash:.2f}")

    return cash

def get_portfolio_value(portfolio: dict) -> float:
    portfolio_value = 0
    for symbol, shares in portfolio.items():
        price = get_price(symbol)
        value = price * shares
        portfolio_value += value
    return portfolio_value

def print_portfolio(portfolio: dict, total_value: float):
    print("| Symbol | Price | Shares | Value | Percentage |")
    for symbol, shares in portfolio.items():
        price = get_price(symbol)
        value = price * shares
        percent = value / total_value
        print(f"| {symbol} | ${price:.2f} | {shares} | ${value:.2f} | {percent * 100:.2f}% |")

def get_desired_portfolio(portfolio: dict) -> dict:
    desired_portfolio = {}
    valid_total = False
    while not valid_total:
        print("\nNow enter the desired allocation for each stock in percent.")

        for key in portfolio.keys():
            valid_percent = False
            while not valid_percent:
                percent = input(f"For {key}: ")
                try:
                    percent = float(percent)
                    if percent < 0 or percent > 100:
                        print("Invalid percentage.")
                    else:
                        valid_percent = True
                except ValueError:
                    print("Invalid percentage.")
            desired_portfolio[key] = percent/100
        
        if sum(desired_portfolio.values()) != 1:
            print("Those do not add up to 100%. Please Try again.")
        else:
            valid_total = True
    
    return desired_portfolio

def rebalance_portfolio(portfolio: dict, desired_portfolio: dict, total_value: float):
    # Now determine difference between the ideal number of shares for each stock and the current number of shares
    # Go through each stock, multiple the total value by the percentage, then divide by the stock price and round down
    portfolio_changes = {}
    for symbol, shares in portfolio.items():
        price = get_price(symbol)
        desired_value = desired_portfolio[symbol] * total_value
        desired_shares = int(desired_value / price)
        difference = desired_shares - shares
        portfolio_changes[symbol] = difference

    # Calculate the new portfolio before the adjustments
    new_portfolio = {}
    for symbol, old_shares in portfolio.items():
        new_shares = old_shares + portfolio_changes[symbol]
        new_portfolio[symbol] = new_shares
    
    # Calulate the new cash balance after the adjustments
    new_cash = total_value - get_portfolio_value(new_portfolio)

    # Check if the cash balance is greater than the price to buy any of the stocks starting with the one most underrepresented
    portfolio_under = {}
    for symbol, shares in new_portfolio.items():
        price = get_price(symbol)
        value = price * shares
        percent = value / total_value
        desired_percent = desired_portfolio[symbol]
        difference = percent - desired_percent

        portfolio_under[symbol] = difference
    
    # Instead sort into a list and go through it one by one
    sorted_portfolio_under = dict(sorted(portfolio_under.items(), key=lambda item: item[1]))
    
    # Check if any of the share prices are less than the amount of cash
    prices = [get_price(x) for x in portfolio.keys()]
    while new_cash > min(prices):
        # If it is then try to buy 1 more share of the most underrepresented stock
        for symbol in sorted_portfolio_under.keys():
            if get_price(symbol) <= new_cash:
                # Add one more share
                portfolio_changes[symbol] += 1
                # print(f"Added 1 more share of {symbol}.")
                # Recalculate the buying and new portfolio
                # Calcuate the new portfolio after the adjustments
                new_portfolio = {}
                for symbol, old_shares in portfolio.items():
                    new_shares = old_shares + portfolio_changes[symbol]
                    new_portfolio[symbol] = new_shares
                
                new_cash = total_value - get_portfolio_value(new_portfolio)
                break
    
    return new_portfolio, portfolio_changes

def main():
    print("Welcome to portfolio rebalancer.")

    print("\nNow enter the stocks in your portfolio. When you are done type STOP.")

    # Get the users current portfolio
    portfolio = get_current_portfolio()
    
    # Check for cash balance
    cash = get_cash_balance()

    # Calculate the total value
    total_value = get_portfolio_value(portfolio) + cash
    
    # Print the complete portfolio
    print("\nYour current portfolio is:")
    print_portfolio(portfolio, total_value)
    print(f"Cash: ${cash:.2f}")
    print(f"Total value: ${total_value:.2f}")
    
    # Now get the desired portfolio
    desired_portfolio = get_desired_portfolio(portfolio)

    print("\nYour desired asset allocation is:")
    for key, value in desired_portfolio.items():
        print(f"{value*100}% - {key}")
    
    # Rebalance the portfolio
    new_portfolio, portfolio_changes = rebalance_portfolio(portfolio, desired_portfolio, total_value)
    new_cash = total_value - get_portfolio_value(new_portfolio)
    
    # Print out the necessary transactions to rebalance your portfolio
    print("\nHere are the transaction you need to make to rebalance your portfolio.")

    print("\nTo sell:")
    for symbol, shares in portfolio_changes.items():
        if shares < 0:
            print(f"{shares} shares of {symbol}")
    
    print("\nTo buy:")
    for symbol, shares in portfolio_changes.items():
        if shares > 0:
            print(f"+{shares} shares of {symbol}")
    
    # Print out the new portfolio
    print("\nYour new portfolio will be:")
    print_portfolio(new_portfolio, total_value)
    print(f"Cash: ${new_cash:.2f}")
    print(f"Total value: ${total_value:.2f}")

if __name__ == "__main__":
    main()
