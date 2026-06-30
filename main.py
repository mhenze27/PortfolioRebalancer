import yfinance as yf


PRICES = {}


def get_price(symbol: str, currency, ne=False) -> float:
    #print(f"PRICES: {PRICES}")

    if currency == "CAD" and not ne:
        symbol = symbol + ".TO"
    if currency == "CAD" and ne:
        symbol = symbol + ".NE"

    if symbol in PRICES.keys():
        return PRICES[symbol]
    elif currency=="CAD" and symbol[:-3] in PRICES.keys():
        return PRICES[symbol[:-3]]
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

        if currency == "CAD":
            PRICES[symbol[:-3]] = price
        else:
            PRICES[symbol] = price
        return price

def get_current_portfolio(currency: str) -> dict:
    portfolio = {}

    if currency == "CAD":
        print("Note: A HTTP error message may display if some Canadian ETFs are found with the suffix .NE instead of .TO on Yahoo Finance. However everything is still working correctly.")

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
                    elif price == -1 and currency=="CAD":
                        price = get_price(symbol, currency, ne=True)
                        if price != -1:
                            valid_symbol = True
                        else:
                            print("Not a valid stock symbol. #2")
                    else:
                        print("Not a valid stock symbol. #3")
                except KeyError:
                    print("Not a valid stock symbol. #4")
                
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

def balance_currencies(cad_value, usd_value):
        rate = exchange_rate_selection()

        # Determine the total value of each account

        # print("\nWhat is the total value of your $CAD account, in $CAD.")
        # valid_cad_amount = False
        # while not valid_cad_amount:
        #     cad_value = input(">>> ")
        #     try:
        #         cad_value = float(cad_value)
        #         if cad_value >= 0:
        #             valid_cad_amount = True
        #         else:
        #             print("Invalid amount.")
        #     except ValueError:
        #         print("Invalid amount.")
        
        # print("What is the total value of your $USD account, in $USD?")
        # valid_usd_value = False
        # while not valid_usd_value:
        #     usd_value = input(">>> ")
        #     try:
        #         usd_value = float(usd_value)
        #         if usd_value >= 0:
        #             valid_usd_value = True
        #         else:
        #             print("Invalid amount.")
        #     except ValueError:
        #         print("Invalid amount.")
        
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
            overweight_currency = "CAD"
            return overweight_currency, to_usd_adjustment, rate
        elif current_usd_split > usd_split and (usd_value - ideal_usd_amount) > 5:
            to_cad_adjustment = usd_value - ideal_usd_amount
            print(f"\nYou need to transfer ${to_cad_adjustment:.2f} USD to $CAD.")
            overweight_currency = "USD"
            return overweight_currency, to_cad_adjustment, rate
        else:
            print("\nYour accounts are perfectly balanced in terms of currency.")
            return None, None, rate

def ignore_stocks(portfolio: dict) -> dict:
        print("\nWhat stocks do you want to ignore. Enter the stocks then enter STOP when you are done.")
        to_ignore = []

        symbol = ""
        while symbol != "STOP":
            symbol = input("Enter a symbol: ")
            if symbol.isalpha():
                symbol = symbol.upper()
                if symbol not in portfolio.keys() and symbol != "STOP":
                    print("Invalid symbol. #1")
                elif symbol in to_ignore:
                    print("Invalid symbol. #2")
                elif symbol in portfolio.keys():
                    to_ignore.append(symbol)
            else:
                print("Invalid symbol. #3")
        
        print(f"We will ignore the following symbols in the rebalancing: {to_ignore}.")

        # Remove the symbols from the portfolio
        for symbol in to_ignore:
            portfolio.pop(symbol)
    
        return portfolio

def main_calculation_loop_part_1(currency: str):
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

    # Check if the user wants to ignore any stocks from the rebalance
    # Determine if the use wants to ignore any stocks in the rebalance
    print("\nDo you want to ignore any stocks?")
    ignore_any = False
    valid_answer = False
    while not valid_answer:
        answer = input(">>> ")
        if answer.isalpha():
            answer = answer.upper()
            if answer == "YES" or answer == "Y":
                ignore_any = True
                valid_answer = True
            elif answer == "NO" or answer == "N":
                ignore_any = False
                valid_answer = True
            else:
                print("Invalid answer.")
        else:
            print("Invalid answer.")
    
    if ignore_any:
        portfolio = ignore_stocks(portfolio)
    
        # Get the adjusted portfolio value
        total_value = get_portfolio_value(portfolio, currency) + cash

        # Print the adjusted portfolio
        print("\nYour adjusted current portfolio is:")
        print_portfolio(portfolio, total_value, currency)
        print(f"Cash: ${cash:.2f}")
        print(f"Total adjusted value: ${total_value:.2f}")

    return portfolio, cash

def main_calculation_loop_part_2(currency: str, portfolio: dict, cash: float):
    # Calculate the total value
    total_value = get_portfolio_value(portfolio, currency) + cash
    
    # Now get the desired portfolio
    desired_portfolio = get_desired_portfolio(portfolio)

    print("\nYour desired asset allocation is:")
    for key, value in desired_portfolio.items():
        print(f"{value*100:.2f}% - {key}")
    
    # Check if the user wants to add a cash buffer
    print("\nWould you like to include a cash buffer in your rebalance? (yes/no)")
    add_buffer = False
    valid_answer = False
    while not valid_answer:
        answer = input(">>> ")
        if answer.isalpha():
            answer = answer.upper()
            if answer == "YES" or answer == "Y":
                add_buffer = True
                valid_answer = True
                print("\nEnter a percent for the cash buffer. (0-100)")
                valid_percent = False
                if not valid_percent:
                    buffer_percent = input(">>> ")
                    try:
                        buffer_percent = float(buffer_percent)
                        if buffer_percent < 0 or buffer_percent > 100:
                            print("Invalid percent")
                        else:
                            valid_percent = True
                            print(f"We will add a cash buffer of {buffer_percent:.2f}%")
                            buffer_percent /= 100
                    except ValueError:
                        print("Invalid percent.")
            elif answer == "NO" or answer == "N":
                valid_answer = True
            else:
                print("Invalid answer.")
        else:
            print("Invalid answer.")
    
    # Add a cash buffer if requested
    if add_buffer:
        buffer = total_value * buffer_percent
        total_value = total_value - buffer

    # Rebalance the portfolio
    new_portfolio, portfolio_changes = rebalance_portfolio(portfolio, desired_portfolio, total_value, currency)
    new_cash = total_value - get_portfolio_value(new_portfolio, currency)

    # If we added a buffer correct the cash value
    if add_buffer:
        new_cash = new_cash + buffer
        total_value = get_portfolio_value(new_portfolio, currency) + new_cash

    # Check if a rebalance is necessary
    changes_necessary = False
    for symbol, shares in portfolio_changes.items():
        if shares != 0:
            changes_necessary = True
    
    # Print out the necessary transactions to rebalance your portfolio
    if changes_necessary:
        print("\nHere are the transaction you need to make to rebalance your portfolio.")

        print("\nTo sell:")
        for symbol, shares in portfolio_changes.items():
            if shares < 0:
                print(f"{shares} shares of {symbol}")
        
        print("\nTo buy:")
        for symbol, shares in portfolio_changes.items():
            if shares > 0:
                print(f"+{shares} shares of {symbol}")
    else:
        # There is no need to rebalance anything
        print("\nYour portfolio is already perfectly balanced. There is no need to make any changes.")
    
    # Print out the new portfolio
    print("\nYour new portfolio will be:")
    print_portfolio(new_portfolio, total_value, currency)
    print(f"Cash: ${new_cash:.2f}")
    print(f"Total value: ${total_value:.2f}")

def main():
    print("Welcome to portfolio rebalancer.")

    # Select account type
    type = account_type_selection()
    
    if type == 1:
        # Run through the program for one $CAD portfolio
        portfolio, cash = main_calculation_loop_part_1(currency="CAD")
        main_calculation_loop_part_2(currency="CAD", portfolio=portfolio, cash=cash)
        input("\nPress Enter to exit...")

    elif type == 2:
        # Run through the program for one $USD portfolio
        portfolio, cash = main_calculation_loop_part_1(currency="USD")
        main_calculation_loop_part_2(currency="USD", portfolio=portfolio, cash=cash)
        input("\nPress Enter to exit...")

    # If the account is across currencies balance currencies
    else:
        # Get the current $CAD portfolio first
        print("\nEnter your current $CAD portfolio first.")
        cad_portfolio, cad_cash = main_calculation_loop_part_1(currency="CAD")
        cad_total_value = get_portfolio_value(cad_portfolio, currency="CAD") + cad_cash

        # Get the current $USD portfolio next
        print("\nNow enter your current $USD portfolio.")
        usd_portfolio, usd_cash = main_calculation_loop_part_1(currency="USD")
        usd_total_value = get_portfolio_value(usd_portfolio, currency="USD") + usd_cash

        # Now ask if the user wants to balance currencies
        print("\nDo you want to balance the currency split across your portfolios? (yes/no)")
        balanced_currencies  = False
        valid_answer = False
        while not valid_answer:
            answer = input(">>> ")
            if answer.isalpha():
                answer = answer.upper()
                if answer in ["YES", "NO", "Y", "N"]:
                    valid_answer = True
                else:
                    print("Invalid answer.")
            else:
                print("Invalid answer.")
        if answer == "YES" or answer == "Y":
            overweight_currency, adjustment, rate = balance_currencies(cad_total_value, usd_total_value)
            balanced_currencies = True
        else:
            print("We will not balance currencies today.")
        
        # If we rebalanced currencies ask if we would want to use the newly calculated balances for our rebalance
        recalculate_balances = False
        if balanced_currencies and overweight_currency != None:
            print("\nWould you like to use the newly calculated balances in your rebalances? (yes/no)")
            valid_answer = False
            while not valid_answer:
                answer = input(">>> ")
                if answer.isalpha():
                    answer = answer.upper()
                    if answer == "YES" or answer == "Y":
                        recalculate_balances = True
                        valid_answer = True
                    elif answer == "NO" or answer == "N":
                        valid_answer = True
                    else:
                        print("Invalid answer.")
                else:
                    print("Invalid answer.")
        
        if recalculate_balances:
            if overweight_currency == "CAD":
                # Calculate the new cash balances after transferring from $CAD to $USD
                cad_cash = cad_cash - adjustment / rate
                usd_cash = usd_cash + adjustment
            else:
                # Calculate the new cash balances after transferring from $USD to $CAD
                cad_cash = cad_cash + adjustment * rate
                usd_cash = usd_cash - adjustment

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
            main_calculation_loop_part_2(currency="CAD", portfolio=cad_portfolio, cash=cad_cash)
            input("\nPress Enter to continue...")
            print("\nWe will rebalance your $USD portfolio next.")
            main_calculation_loop_part_2(currency="USD", portfolio=usd_portfolio, cash=usd_cash)
            input("\nPress Enter to exit...")

        else:
            print("\nWe will rebalance your $USD portfolio first.")
            main_calculation_loop_part_2(currency="USD", portfolio=usd_portfolio, cash=usd_cash)
            input("\nPress Enter to continue...")
            print("\nWe will rebalance your $CAD portfolio next.")
            main_calculation_loop_part_2(currency="CAD", portfolio=cad_portfolio, cash=cad_cash)
            input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
