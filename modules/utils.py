def format_currency(amount):
    """Formats a number as Turkish currency string: 1.234,56"""
    try:
        return "{:,.2f}".format(amount).replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(amount)
