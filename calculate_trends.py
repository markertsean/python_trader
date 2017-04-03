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
def generate_rsi( inp_df, inp_days ):
    
    
    # New_df contains differential of price from prev day
    new_df = inp_df.ix[::-1,['Close','Adj Close']].copy()
    new_df = new_df - new_df.shift(1)
    new_df = new_df[::-1]
    
    # Make sure we are working with a list
    my_days = inp_days
    if ( not isinstance( inp_days, list ) ):
        my_days = [ inp_days ]
    labelList = []
    
    
    # Go through each day range to calc RSI
    for day in my_days:
        
        labelList.append('RSI_'+str(day))
        
        new_df[labelList[-1]] = 50.0
                 
        # Need to handle each window of indexes individually
        for ind in range( 0, new_df.shape[0]-day ):
            
            new_df.ix[ ind, labelList[-1] ] = 100.0 * ( 1.0 - 1.0 / ( 1 + \
                                              ( new_df.ix[ind:ind+day,'Close'][ new_df['Close']>0 ].mean()      ) / \
                                              (-new_df.ix[ind:ind+day,'Close'][ new_df['Close']<0 ].mean()+1.e-6) ) )
                
        # Remove outliers
        new_df[labelList[-1]].fillna( new_df[labelList[-1]].mean(),inplace=True)
        new_df.ix[ new_df[labelList[-1]]< 1, labelList[-1]] = new_df[labelList[-1]].mean()
        new_df.ix[ new_df[labelList[-1]]>99, labelList[-1]] = new_df[labelList[-1]].mean()
        

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
        
        ban_df.ix[ -day+1:, b_labels[-1] ] = 0.5
        
    return ban_df[ b_labels ]

# Normalize index
def normalize_column( inp_df, column, maxVal=None, minVal=None ):
    
    new_column = inp_df.copy()
    
    max_value = maxVal
    min_value = minVal
    
    if( max_value == None ):
        max_value = inp_df[column].max()
    if( min_value == None ):
        min_value = inp_df[column].min()
        
    print new_column.head()
    new_column[column] = ( inp_df[ column ] - float(min_value) ) / ( max_value - min_value )
    new_column.ix[ new_column[column]<0, column ] = 0.0
    new_column.ix[ new_column[column]>1, column ] = 1.0
    print new_column.head()
    print ' '
    return new_column[column]