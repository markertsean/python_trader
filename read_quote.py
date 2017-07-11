import numpy as np
import pandas as pd



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
        rat_list = inp_df['open']/inp_df['close'].shift(1)
    
        for     split in split_list:
            for     i in range( 0, len(rat_list)) :
                
                # If stock changes by what would expect from a split
                if ( abs(rat_list[i]-split) < 1e-4 ):
                    
                    # Modulate everything by the split
                    inp_df.ix[i:,['close','open','high','low']] = \
                    inp_df.ix[i:,['close','open','high','low']] / split
                    
                    # Volume behaves opposite
                    inp_df.ix[i:,'volume'] = inp_df.ix[i:,'volume'] * split
                    
                    # Break out of loops and double check for more splits
                    break_it = True
                    break
            if ( break_it ):
                break
        
        # If we didn't find a split
        if ( break_it == False ):
            break

# Read csv quote file
def readQuote( inpFileName ):
    
    new_df = pd.read_csv( inpFileName, header=0, index_col=0 )

    # Forward fill then back fill data that may be missing
    fill_quote_gaps( new_df )
    
    # If the 
    fix_splits( new_df )
    
    return new_df