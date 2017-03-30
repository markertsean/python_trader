import pandas as pd
import numpy  as np


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
    
    return new_df[ ['Diff_co', 'Diff_v'] ]


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
def generate_rsi( inp_df, inp_diff, inp_days ):
    
    new_df = inp_df[['Close']].copy()
    new_df['Diff_co'] = inp_diff['Diff_co'].copy()
    
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

# Bollinger bands, computes bollinger band crossings
# -1 indicates below bottom band
#  1 indicates above top band
#  0 indicates nothing happening
def generate_bollinger_bands( inp_df, band_df, day_list , band_width=2.0, cl='Adj Close', bl='Close' ):
    
    new_df  = inp_df.copy()
    ban_df  = band_df.copy()
    my_days = day_list
    
    # Make sure we are working with a list
    if ( not isinstance( day_list, list ) ):
        my_days = [ day_list ]
    mean_labels = []
    std_labels  = []
    b_labels    = []
    
    for day in my_days:
        
        mean_labels.append( bl+'_mean_'+str(day) )
        std_labels .append( bl+'_std_' +str(day) )
        b_labels   .append('Bollinger_'+str(day) )
        
        upperBand = ban_df[ mean_labels[-1] ] + band_width * ban_df[ std_labels[-1] ]
        lowerBand = ban_df[ mean_labels[-1] ] - band_width * ban_df[ std_labels[-1] ]
        
        # 1 if above, 0 if below
        ban_df[ b_labels[-1] ] = ( new_df[ cl ] - lowerBand ) / ( upperBand - lowerBand )

    return ban_df[ b_labels ]