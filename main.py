import yfinance as yf


PRICES = {}

def get_price(symbol: str, currency) -> float:
    if currency == "CAD":
        symbol = symbol + ".TO"

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
        else:
            return -1

        PRICES[symbol] = price
        return price

def get_current_portfolio(currency: str) -> dict:
    portfolio = {}

    complete = False
    while not complete:

        valid_symbol = False
        while not valid_symbol:
            print("\nEnter a stock symbol: ")
            symbol = input(">>> ")
            if not symbol.replace(".", "").isalpha():
                print(f">{symbol.replace(".", "")}<")
                print("Not a valid stock symbol. #1")
            else:
                symbol = symbol.upper()
                if symbol == "STOP":
                    complete = True
                    break
                print(f"Your stock symbol is {symbol}")

                # Confirm it is a valid stock
                try:
                    price = get_price(symbol, currency)
                    #print(f"The current price of {symbol} is ${price}.")
                    if price != -1:
                        valid_symbol = True
                    else:
                        print("Not a valid stock symbol. #2")
                except KeyError:
                    print("Not a valid stock symbol. #3")
                
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

def get_portfolio_value(portfolio: dict, currency: str) -> float:
    portfolio_value = 0
    for symbol, shares in portfolio.items():
        price = get_price(symbol, currency)
        value = price * shares
        portfolio_value += value
    return portfolio_value

def print_portfolio(portfolio: dict, total_value: float, currency: str):
    print("| Symbol | Price | Shares | Value | Percentage |")
    for symbol, shares in portfolio.items():
        price = get_price(symbol, currency)
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

def rebalance_portfolio(portfolio: dict, desired_portfolio: dict, total_value: float, currency: str):
    # Now determine difference between the ideal number of shares for each stock and the current number of shares
    # Go through each stock, multiple the total value by the percentage, then divide by the stock price and round down
    portfolio_changes = {}
    for symbol, shares in portfolio.items():
        price = get_price(symbol, currency)
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
    new_cash = total_value - get_portfolio_value(new_portfolio, currency)

    # Check if the cash balance is greater than the price to buy any of the stocks starting with the one most underrepresented
    portfolio_under = {}
    for symbol, shares in new_portfolio.items():
        price = get_price(symbol, currency)
        value = price * shares
        percent = value / total_value
        desired_percent = desired_portfolio[symbol]
        difference = percent - desired_percent

        portfolio_under[symbol] = difference
    
    # Instead sort into a list and go through it one by one
    sorted_portfolio_under = dict(sorted(portfolio_under.items(), key=lambda item: item[1]))
    
    # Check if any of the share prices are less than the amount of cash
    prices = [get_price(x, currency) for x in portfolio.keys()]
    while new_cash > min(prices):
        # If it is then try to buy 1 more share of the most underrepresented stock
        for symbol in sorted_portfolio_under.keys():
            if get_price(symbol, currency) <= new_cash:
                # Add one more share
                portfolio_changes[symbol] += 1
                # print(f"Added 1 more share of {symbol}.")
                # Recalculate the buying and new portfolio
                # Calcuate the new portfolio after the adjustments
                new_portfolio = {}
                for symbol, old_shares in portfolio.items():
                    new_shares = old_shares + portfolio_changes[symbol]
                    new_portfolio[symbol] = new_shares
                
                new_cash = total_value - get_portfolio_value(new_portfolio, currency)
                break
    
    return new_portfolio, portfolio_changes

def account_type_selection() -> int:
    print("\nIs your portfolio: \n1) $CAD Only\n2) $USD Only\n3) Both $CAD and $USD")
    valid_type = False
    while not valid_type:
        type = input(">>> ")
        if type.isdigit():
            type = int(type)
            if type in (1, 2, 3):
                valid_type = True
            else:
                print("Invalid selection. Please try again.")
        else:
            print("Invalid selection. Please try again.")
    
    return type

def exchange_rate_selection() -> float:
    print("\nPlease enter the $CAD/$USD exchange rate you would like to use.")
    valid_rate = False
    while not valid_rate:
        rate = input(">>> ")
        try:
            rate = float(rate)
            if rate > 0.5 and rate < 1.5:
                valid_rate = True
            else:
                print("Invalid exchange rate. Please try again.")
        except ValueError:
            print("Invalid exchange rate. Please try again.")
    print(f"\nWe will use an exchange rate of {rate:.4f} $CAD/$USD.")

    return rate

def balance_currencies():
        rate = exchange_rate_selection()

        # Determine the total value of each account
        print("\nWhat is the total value of your $CAD account, in $CAD.")
        valid_cad_amount = False
        while not valid_cad_amount:
            cad_value = input(">>> ")
            try:
                cad_value = float(cad_value)
                if cad_value >= 0:
                    valid_cad_amount = True
                else:
                    print("Invalid amount.")
            except ValueError:
                print("Invalid amount.")
        
        print("What is the total value of your $USD account, in $USD?")
        valid_usd_value = False
        while not valid_usd_value:
            usd_value = input(">>> ")
            try:
                usd_value = float(usd_value)
                if usd_value >= 0:
                    valid_usd_value = True
                else:
                    print("Invalid amount.")
            except ValueError:
                print("Invalid amount.")
        
        print(f"\nThe total value of your $CAD account is ${cad_value:.2f}")
        print(f"The total value of your $USD account is ${usd_value:.2f}")

        # Calculate the current currency split
        combined_value_cad = cad_value + usd_value/rate
        combined_value_usd = cad_value*rate + usd_value
        print(f"The combined total value of your accounts is ${combined_value_cad:.2f} CAD or ${combined_value_usd:.2f} USD.")

        current_cad_split = cad_value / combined_value_cad
        current_usd_split = usd_value / combined_value_usd

        print(f"\nThe current currency split of your account is {current_cad_split*100:.2f}% $CAD : {current_usd_split*100:.2f}% $USD.")

        # Determine the ideal currency split
        print("\nWhat is the desired currency split in your portfolio. Enter a percent for $CAD and $USD (0-100)%.")
        valid_split = False
        while not valid_split:
            cad_split = input("For $CAD: ")
            usd_split = input("For $USD: ")

            try:
                cad_split = float(cad_split)/100
                usd_split = float(usd_split)/100

                if cad_split > 0 and cad_split < 1 and usd_split > 0 and usd_split < 1:
                    if cad_split + usd_split == 1:
                        valid_split = True
                    else:
                        print("Invalid currency split. Please try again.")
                else:
                    print("Invalid currency split. Please try again.")
            except ValueError:
                print("Invalid currency split. Please try again.")
        
        print(f"\nYour target currency split is {cad_split*100:.2f}% $CAD : {usd_split*100:.2f}% $USD.")

        # Calculate the conversion necessary to achieve the ideal currency split
        ideal_usd_amount = combined_value_usd * usd_split
        if current_usd_split < usd_split and (ideal_usd_amount - usd_value) > 5:
            to_usd_adjustment = ideal_usd_amount - usd_value
            print(f"\nYou need to transfer enough $CAD to buy ${to_usd_adjustment:.2f} USD.")
        elif current_usd_split > usd_split and (usd_value - ideal_usd_amount) > 5:
            to_cad_adjustment = usd_value - ideal_usd_amount
            print(f"\nYou need to transfer ${to_cad_adjustment:.2f} USD to $CAD.")
        else:
            print("\nYour accounts are perfectly balanced in terms of currency.")

def main_calculation_loop(currency: str):
    print("\nNow enter the stocks in your portfolio. When you are done type STOP.")

    # Get the users current portfolio
    portfolio = get_current_portfolio(currency)
    
    # Check for cash balance
    cash = get_cash_balance()

    # Calculate the total value
    total_value = get_portfolio_value(portfolio, currency) + cash
    
    # Print the complete portfolio
    print("\nYour current portfolio is:")
    print_portfolio(portfolio, total_value, currency)
    print(f"Cash: ${cash:.2f}")
    print(f"Total value: ${total_value:.2f}")
    
    # Now get the desired portfolio
    desired_portfolio = get_desired_portfolio(portfolio)

    print("\nYour desired asset allocation is:")
    for key, value in desired_portfolio.items():
        print(f"{value*100}% - {key}")
    
    # Rebalance the portfolio
    new_portfolio, portfolio_changes = rebalance_portfolio(portfolio, desired_portfolio, total_value, currency)
    new_cash = total_value - get_portfolio_value(new_portfolio, currency)
    
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
    print_portfolio(new_portfolio, total_value, currency)
    print(f"Cash: ${new_cash:.2f}")
    print(f"Total value: ${total_value:.2f}")

def main():
    print("Welcome to portfolio rebalancer.")

    # Select account type
    type = account_type_selection()
    
    # If the account is across currencies balance currencies
    if type == 3:
        # First balance currencies
        balance_currencies()

        # Then rebalance the two portfolios
        print("\nWhich portfolio would you like to rebalance first? (CAD or USD):")
        valid_selection = False
        while not valid_selection:
            selection = input(">>> ")
            if selection.isalpha():
                selection = selection.upper()
                if selection == "CAD" or selection == "USD":
                    valid_selection = True
                else:
                    print("Invalid selection.")
            else:
                print("Invalid selection.")
        
        if selection == "CAD":
            print("\nWe will rebalance your $CAD portfolio first.")
            main_calculation_loop(currency="CAD")
            input("\nPress Enter to continue...")
            print("\nWe will rebalance your $USD portfolio next.")
            main_calculation_loop(currency="USD")
        else:
            print("\nWe will rebalance your $USD portfolio first.")
            main_calculation_loop(currency="USD")
            input("\nPress Enter to continue...")
            print("\nWe will rebalance your $CAD portfolio next.")
            main_calculation_loop(currency="CAD")
    elif type == 1:
        # Run through the program for one $CAD portfolio
        main_calculation_loop(currency="CAD")
    else:
        # Run through the program for one $USD portfolio
        main_calculation_loop(currency="USD")

if __name__ == "__main__":
    main()
