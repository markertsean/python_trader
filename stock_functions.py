import pandas as pd
import numpy  as np


# Generate measures of (close-open)/open, 
#                        (high-low)/open,
#                  (adj_close-open)/open, 
#                 (vol_tod-vol_yes)/vol_yes
def generate_differentials( inp_df ):
    new_df = inp_df.copy()

    # diff is just differences between close and open
    new_df['diff_co'] = new_df['close']/new_df['open'] - 1.0
    
    # diff is breadth of high-low prices, relative to open
    new_df['diff_hl'] = (new_df['high']-new_df['low']) / new_df['open']
    
    new_df['diff_v']  = new_df.ix[:-1,['volume']].astype(float)/new_df.ix[1:,['volume']].values - 1.0
    new_df.ix[ -1, ['diff_v'] ] = 0
    
    return new_df[ ['diff_co', 'diff_hl', 'diff_v'] ]


# Generate some rolling values of the data
def generate_rolling_close( inp_df, inp_list, onlyMean=False ):
    
    # Reverse things, list is reversed from direction of rolling
    new_df  = inp_df[::-1].copy()
    my_days = inp_list
    
    # Make sure we are working with a list
    if ( not isinstance( inp_list, list ) ):
        my_days = [ inp_list ]

    labelList = []
    meanList  = []
    
    # Generate rolline mean and std for each length of days
    for day in my_days:
        
        labelList.append( 'close_mean_'+str(day) )
        meanList .append(          labelList[-1] )
        labelList.append( 'close_std_' +str(day) )
        
        new_df[ labelList[-2] ] = new_df['close'].rolling(day).mean()
        new_df[ labelList[-1] ] = new_df['close'].rolling(day).std()
        
    new_df.fillna( 0, inplace=True )
        
    if ( onlyMean ):
        return new_df.ix[::-1, meanList]
        
    return new_df.ix[ ::-1, labelList ]


# Generate momentum list, momentum is calculated as day/oldDay - 1
def generate_momentum_close( inp_df, inp_list ):
    
    new_df  = inp_df.copy()
    my_days = inp_list
    
    # Make sure we are working with a list
    if ( not isinstance( inp_list, list ) ):
        my_days = [ inp_list ]
    labelList = []
        
    # Generate rolling mean and std for each length of days
    for day in my_days:
        
        labelList.append( 'momentum_'+str(day) )

        new_df[ labelList[-1] ] = new_df.ix[:-day,'close'].astype(float)/new_df.ix[day:,'close'].values - 1.0
        new_df.ix[-day:, labelList[-1] ] = 0
    
    return new_df[ labelList ]


# Relative strength index in measure of # days pos close vs num days neg close
def generate_rsi( inp_df, inp_days ):
    
    
    # New_df contains differential of price from prev day
    new_df = inp_df.ix[::-1,['close']].copy()
    new_df = new_df - new_df.shift(1)
    new_df = new_df.fillna( 0.0 )
    
    # Make sure we are working with a list
    my_days = inp_days
    if ( not isinstance( inp_days, list ) ):
        my_days = [ inp_days ]
    labelList = []
    
    new_df['gain'] = 0.
    new_df['loss'] = 0.
    new_df['gain'] = new_df.ix[ new_df['close']>0, ['close'] ]
    new_df['loss'] = new_df.ix[ new_df['close']<0, ['close'] ]
    new_df         = new_df.fillna(0)

    labelList = []

    # Go through each day range to calc RSI
    for day in inp_days:

        day_str = str(day)
        labelList.append('rsi_'+day_str)

        new_df['gain_'+day_str] =         new_df['gain'].rolling( day ).sum()
        new_df['loss_'+day_str] = np.abs( new_df['loss'].rolling( day ).sum() )

        new_df[ labelList[-1] ] = ( 1. - 1. / ( 1. + new_df['gain_'+day_str] / new_df['loss_'+day_str] ) ).fillna(0.5)

    new_df = new_df[::-1]        

    return new_df[ labelList ]

# Bollinger bands, computes bollinger band crossings
#  0   indicates below bottom band
#  1   indicates above top band
#  0.5 indicates nothing happening
def generate_bollinger_bands( inp_df, day_list, band_width=2.0 ):
    
    new_df  = inp_df[['close','open']].copy()

    ban_df = generate_rolling_close( inp_df, day_list )
    
    my_days = day_list
    
    # Make sure we are working with a list
    if ( not isinstance( day_list, list ) ):
        my_days = [ day_list ]
        
    mean_labels = []
    std_labels  = []
    b_labels    = []
    
    for day in my_days:
        
        mean_labels.append( 'close_mean_'+str(day) )
        std_labels .append( 'close_std_' +str(day) )
        b_labels   .append( 'bollinger_' +str(day) )
        
        upperBand = ban_df[ mean_labels[-1] ] + band_width * ban_df[ std_labels[-1] ]
        lowerBand = ban_df[ mean_labels[-1] ] - band_width * ban_df[ std_labels[-1] ]
        
        # 1 if above, 0 if below
        ban_df[ b_labels[-1] ] = ( new_df[ 'close' ] - lowerBand ) / ( upperBand - lowerBand )
        
        ban_df.ix[ -day+1:, b_labels[-1] ] = 0.5
        
    return ban_df[ b_labels ]


# Generates percentage price difference over number of days
def generate_deltas( inp_df, inp_days, cols = 'close' ):
    
    if ( inp_days < 1 ):
        print 'Bad input days in generate_deltas: ', inp_days
        sys.exit()
        
    use_df    = inp_df[::-1].copy()
    labelList = []
    
    for day in range( 1, inp_days+1 ):
        
        labelList.append( 'close_'+str(day) )
        use_df[labelList[-1]] = 0.0
        
        use_df[labelList[-1]] = use_df[cols] / use_df[cols].shift(day) - 1

    use_df = use_df[::-1]
    return use_df[labelList]*100

def generate_volatility( inp_roll, day_list ):

    my_days = day_list
    
    # Make sure we are working with a list
    if ( not isinstance( day_list, list ) ):
        my_days = [ day_list ]

    foo = inp_roll['close_std_'+str(my_days[0])] / inp_roll['close_mean_'+str(my_days[0])]
    foo.fillna( foo.mean() )
    foo.iloc[-my_days[0]:] = foo.mean()
    return foo.to_frame( name='volatility' )