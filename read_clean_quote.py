import os
import sys
import types
import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt


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
            
            
# Generate measures of (close-open)/open, 
#                        (high-low)/open,
#                  (adj_close-open)/open, 
#                 (vol_tod-vol_yes)/vol_yes
def generate_differentials( inp_df ):
    new_df = inp_df.copy()

    # diff is just differences between close and open
    new_df['Diff_co'] = new_df[    'Close']/new_df['Open'] - 1.0
    #new_df['Diff_ao'] = new_df['Adj Close']/new_df['Open'] - 1.0
    
    # diff is breadth of high-low prices, relative to open
    new_df['Diff_hl'] = (new_df['High']-new_df['Low']) / new_df['Open']
    
    new_df['Diff_v']  = new_df.ix[:-1,['Volume']].astype(float)/new_df.ix[1:,['Volume']].values - 1.0
    new_df.ix[ -1,['Diff_v']] = 0
    
    return new_df[ ['Diff_co', 'Diff_hl', 'Diff_v'] ]


# Generate some rolling values of the data
def generate_rolling_close( inp_df, inp_list ):
    
    # Reverse things, list is reversed from direction of rolling
    new_df  = inp_df[::-1].copy()
    my_days = inp_list
    
    # Make sure we are working with a list
    if ( not isinstance( inp_list, list ) ):
        my_days = [ inp_list ]

    labelList = []
        
    # Generate rolline mean and std for each length of days
    for day in my_days:
        
        labelList.append( 'Close_mean_'+str(day) )
        labelList.append( 'Close_std_' +str(day) )
        
        new_df[ labelList[-2] ] = new_df['Adj Close'].rolling(day).mean()
        new_df[ labelList[-1] ] = new_df['Adj Close'].rolling(day).std()
        
    new_df.fillna( 0, inplace=True )
        
    return new_df.ix[ ::-1, labelList ]


# Generate momentum list, momentum is calculated as day/oldDay - 1
def generate_momentum_close( inp_df, inp_list ):
    
    new_df  = inp_df.copy()
    my_days = inp_list
    
    # Make sure we are working with a list
    if ( not isinstance( inp_list, list ) ):
        my_days = [ inp_list ]
    labelList = []
        
    # Generate rolline mean and std for each length of days
    for day in my_days:
        
        labelList.append( 'Momentum_'+str(day) )

        new_df[ labelList[-1] ] = new_df.ix[:-day,'Adj Close'].astype(float)/new_df.ix[day:,'Adj Close'].values - 1.0
        new_df.ix[-day:, labelList[-1] ] = 0
    
    return new_df[ labelList ]


# Relative strength index in measure of # days pos close vs num days neg close
def generate_rsi( inp_df, inp_days ):
    
    new_df = inp_df[['Diff_co','Close']].copy()
    
    my_days = inp_days
    
    # Make sure we are working with a list
    if ( not isinstance( inp_days, list ) ):
        my_days = [ inp_days ]

    labelList = []
    
    # Go through each day range to calc RSI
    for day in my_days:
        
        labelList.append('RSI_'+str(day))
        
        posList = np.zeros( new_df.shape[0] )
        negList = np.zeros( new_df.shape[0] ) + 1.e-6
        
        # Need to handle each window of indexes individually
        for ind in range( 0, new_df.shape[0]-day ):
            
            temp_df = new_df[ ind:ind+day ]
            
            posList[ind] = temp_df[ temp_df['Diff_co']>0 ][ 'Close' ].mean()
            negList[ind] = temp_df[ temp_df['Diff_co']<0 ][ 'Close' ].mean()
        
            if ( posList[ind] != posList[ind] ):
                posList[ind] = 0.0
            if ( negList[ind] != negList[ind] ):
                negList[ind] = 1.e-6

        # First set value to up closes, then divide by downs
        new_df[labelList[-1]] = 100.0 * ( 1.0 - 1.0/ ( 1 + posList/negList ) )
               

    return new_df[ labelList ]