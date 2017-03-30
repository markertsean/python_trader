import os
import sys
import pandas as pd
import numpy  as np


# Sets path to data
def symbol_to_path(symbol, base_dir="data"):
    """Return CSV file path given ticker symbol."""
    return os.path.join(base_dir, "{}.csv".format(str(symbol)))


# Reads the csv file
def read_quote_data( symbol, new_path="data" ):
    
    """Read stock data (adjusted close) for given symbols from CSV files."""
    df = pd.read_csv(  symbol_to_path(symbol,new_path), 
                                      index_col='Date',
                                      parse_dates=True, 
                                     na_values=['nan'])
    return df


# Forward fill quote gaps
# Then backfill
def fill_quote_gaps( inp_df ):
    inp_df.fillna( method='bfill', axis=0, inplace=True )
    inp_df.fillna( method='ffill', axis=0, inplace=True )

    
# Find locations where stock dropped by const number
# These stock splits need to be normalized out, divide previous dates by const
def fix_splits( inp_df ):
    
    # Possible values for splits
    split_list = [ 1/5., 1/4., 1/3., 1/2., 2., 3., 4., 5. ]
    
    while True:
    
        # Breaks loop if we found a split
        break_it = False
        rat_list = inp_df['Open']/inp_df['Close'].shift(1)
    
        for     split in split_list:
            for     i in range( 0, len(rat_list)) :
                
                # If stock changes by what would expect from a split
                if ( abs(rat_list[i]-split) < 1e-4 ):
                    
                    # Modulate everything by the split
                    inp_df.ix[i:,['Close','Open','High','Low','Adj Close']] = \
                    inp_df.ix[i:,['Close','Open','High','Low','Adj Close']] / split
                    
                    # Volume behaves opposite
                    inp_df.ix[i:,'Volume'] = inp_df.ix[i:,'Volume'] * split
                    
                    # Break out of loops and double check for more splits
                    break_it = True
                    break
            if ( break_it ):
                break
        
        # If we didn't find a split
        if ( break_it == False ):
            break