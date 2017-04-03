import os
import sys
import pandas as pd
import numpy  as np

import calculate_trends as ct

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
            
            
# Calculates all the trends we want
def build_quote( symbol, roll_list, mom_list, rsi_list, max_dist, days_pred ):

    tempDf = read_quote_data( symbol )

    fill_quote_gaps( tempDf )
    fix_splits( tempDf )
    
    diffs = ct.generate_differentials(   tempDf                   ) # Differentials between c,ac, o, h, l, v
    rolls = ct.generate_rolling_close(   tempDf,        roll_list ) # Rolling averages of adj c, listed as C_mean_n and C_std_10
    moms  = ct.generate_momentum_close(  tempDf,         mom_list ) # Momentum between day and days offset in list, Momentum_n
    rsis  = ct.generate_rsi(             tempDf,         rsi_list ) # Relative Strength Indexes over n days, RSI_n
    bolls = ct.generate_bollinger_bands( tempDf, rolls, roll_list ) # percentB of Bollinger bands, 1 is at upper, 0 at lower
    deltas= ct.generate_deltas(          tempDf,        days_pred ) # Generates differentials of price from number of days in past
    volis = ct.generate_volatility(              rolls, roll_list ) # Generates volatility as percentage
    
    # Diff_co goes to +/- .05
    # Diff_v goes to -1 +2
    # Momentum_5 +/- .15
    # Momentum_15 -.25 +.25
    # Momentum_30 -.3 +.25
    # RSI naturally normalized to 0-100
    
    norm_diffs = diffs.copy()
    norm_moms  =  moms.copy()
    norm_rsis  =  rsis.copy()
    norm_volis = volis.copy()

    norm_diffs['Diff_co']    = ct.normalize_column( norm_diffs, 'Diff_co'    , minVal=-0.05, maxVal=0.05 )
    norm_diffs['Diff_v' ]    = ct.normalize_column( norm_diffs, 'Diff_v'     , minVal=-1.00, maxVal=2.00 )
    norm_moms['Momentum_'+str(mom_list)] = ct.normalize_column(  norm_moms, 'Momentum_'+str(mom_list), minVal=-0.15, maxVal=0.15 )
    norm_rsis['RSI_'+str(rsi_list)]      = ct.normalize_column(  norm_rsis, 'RSI_'+str(rsi_list)     , minVal=0    , maxVal=100  )
    norm_volis['Volatility'] = ct.normalize_column( norm_volis, 'Volatility' , minVal=0    , maxVal=0.1  )
    
    # Create table to track all the things we will use to make predictions
    predictors_df =    norm_volis.join(     bolls, how = 'inner' )
    predictors_df = predictors_df.join( norm_rsis, how = 'inner' )
    predictors_df = predictors_df.join( norm_moms, how = 'inner' )
    predictors_df = predictors_df[:-max_dist]
    
    # Join everything, or can leave as seperate 
    tempDf   = tempDf.join( rolls     , how='inner' )
    tempDf   = tempDf.join( norm_diffs, how='inner' )
    tempDf   = tempDf.join( deltas    , how='inner' )
    price_df = tempDf.drop( ['Open','High','Low','Volume','Close'], axis=1 )
    price_df = price_df[:-max_dist]
    
    return predictors_df, price_df