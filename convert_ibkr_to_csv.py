import pandas as pd
import os
import glob

def find_latest_files():
    excel_files = glob.glob('Portfolio*.xlsx') + glob.glob('portfolio*.xlsx')
    csv_files = glob.glob('*Inception*.csv') + glob.glob('*inception*.csv')
    excel_file = max(excel_files, key=os.path.getctime) if excel_files else None
    csv_file = max(csv_files, key=os.path.getctime) if csv_files else None
    return excel_file, csv_file

def extract_portfolio_data(xlsx_file):
    df = pd.read_excel(xlsx_file, sheet_name=0, header=5)
    portfolio_df = df[df['AssetClass'] == 'STK'].copy()
    result = portfolio_df[['Symbol', 'Quantity', 'CostBasisMoney', 'PositionValue', 'FifoPnlUnrealized', 'CurrencyPrimary']].copy()
    result.columns = ['Symbol', 'Quantity', 'Cost Basis', 'Market Value', 'Unrealized PL', 'Currency']
    return result

def extract_options_data(xlsx_file):
    df = pd.read_excel(xlsx_file, sheet_name=0, header=5)
    options_df = df[df['AssetClass'] == 'OPT'].copy()

    underlyings, strategies = [], []

    for _, row in options_df.iterrows():
        underlying = str(row['UnderlyingSymbol']) if pd.notna(row['UnderlyingSymbol']) else str(row['Symbol'])
        underlyings.append(underlying)
        opttype = str(row['Put/Call'])
        qty = float(row['Quantity'])
        strategies.append(f"{opttype} Sold" if qty < 0 else f"{opttype} Bought")

    options_df = options_df.copy()
    options_df['Underlying'] = underlyings
    options_df['Strategy'] = strategies

    result = options_df[['Symbol', 'Description', 'Quantity', 'CostBasisMoney',
                          'PositionValue', 'FifoPnlUnrealized', 'CurrencyPrimary',
                          'Expiry', 'Strike', 'Put/Call', 'Strategy', 'Underlying']].copy()
    result.columns = ['Symbol', 'Description', 'Quantity', 'Cost Basis',
                      'Market Value', 'Unrealized PL', 'Currency',
                      'Expiry', 'Strike', 'Type', 'Strategy', 'Underlying']
    return result

def extract_performance_data(csv_file):
    monthly_data = []
    annual_data = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'Historical Performance Benchmark Comparison,Data,' in line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) > 10:
                    date_str = parts[2]
                    try:
                        spx_return = float(parts[4])
                        portfolio_return = float(parts[10])
                        if len(date_str) == 6:
                            formatted_date = f"{date_str[:4]}-{date_str[4:]}-01"
                            monthly_data.append({
                                'Date': formatted_date,
                                'Portfolio_Return': portfolio_return,
                                'SP500_Return': spx_return
                            })
                        elif len(date_str) == 4 and date_str.isdigit():
                            annual_data.append({
                                'Year': int(date_str),
                                'Portfolio_Return': portfolio_return,
                                'SP500_Return': spx_return
                            })
                    except ValueError:
                        continue

    monthly_df = pd.DataFrame(monthly_data)
    annual_df = pd.DataFrame(annual_data)

    if not monthly_df.empty:
        # ✅ FIX: Sort by date BEFORE calculating cumulative returns
        monthly_df['Date'] = pd.to_datetime(monthly_df['Date'])
        monthly_df = monthly_df.sort_values('Date').reset_index(drop=True)

        monthly_df['Portfolio_Cumulative'] = (1 + monthly_df['Portfolio_Return']/100).cumprod() * 100 - 100
        monthly_df['SP500_Cumulative'] = (1 + monthly_df['SP500_Return']/100).cumprod() * 100 - 100

        # Format date back to string for CSV storage
        monthly_df['Date'] = monthly_df['Date'].dt.strftime('%Y-%m-%d')

    return monthly_df, annual_df


def extract_instrument_performance(csv_file):
    instrument_data = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'Performance by Financial Instrument,Data,' in line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 7 and parts[2] != 'Total':
                    date_str = parts[2]
                    if len(date_str) == 6:
                        try:
                            formatted_date = f"{date_str[:4]}-{date_str[4:]}-01"
                            instrument_data.append({
                                'Date':    formatted_date,
                                'ETFs':    float(parts[3]),
                                'Options': float(parts[4]),
                                'Stocks':  float(parts[5]),
                                'Cash':    float(parts[6])
                            })
                        except ValueError:
                            continue

    return pd.DataFrame(instrument_data)

def main():
    print("=" * 50)
    print("IBKR to Dashboard Converter v2.2")
    print("=" * 50)

    excel_file, csv_file = find_latest_files()

    if not excel_file:
        print("ERROR: No Portfolio Excel file found (Portfolio*.xlsx)")
        return
    if not csv_file:
        print("ERROR: No Inception CSV file found (*Inception*.csv)")
        return

    print(f"Portfolio file : {excel_file}")
    print(f"Performance CSV: {csv_file}")
    print("-" * 50)

    try:
        print("1. Extracting stock positions...")
        portfolio_df = extract_portfolio_data(excel_file)
        print(f"   -> {len(portfolio_df)} stocks found")

        print("2. Extracting options...")
        options_df = extract_options_data(excel_file)
        print(f"   -> {len(options_df)} option contracts found")

        print("3. Extracting performance data...")
        monthly_df, annual_df = extract_performance_data(csv_file)
        print(f"   -> {len(monthly_df)} months of performance data")
        print(f"   -> {len(annual_df)} annual periods")

        print("4. Extracting instrument breakdown...")
        instrument_df = extract_instrument_performance(csv_file)
        print(f"   -> {len(instrument_df)} months of instrument data")

        print("-" * 50)
        print("Saving CSV files...")

        portfolio_df.to_csv('portfolio_data.csv', index=False, encoding='utf-8')
        options_df.to_csv('options_data.csv', index=False, encoding='utf-8')
        monthly_df.to_csv('performance_data.csv', index=False, encoding='utf-8')
        annual_df.to_csv('annual_returns.csv', index=False, encoding='utf-8')
        instrument_df.to_csv('instrument_performance.csv', index=False, encoding='utf-8')

        print("   -> portfolio_data.csv       OK")
        print("   -> options_data.csv         OK")
        print("   -> performance_data.csv     OK")
        print("   -> annual_returns.csv       OK")
        print("   -> instrument_performance.csv  OK [NEW]")
        print("=" * 50)
        print("CONVERSION COMPLETE!")
        print("=" * 50)

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()