import pandas as pd
import numpy  as np

import pickle

import remap_values as rv
import read_quote   as rq



cat_dict = {    
                'aapl':'comp',    'acm' :'cons',    'amzn':'csmr',    'awk' :'wate',    'awr' :'wate',    'ba'  :'aero',    
                'bac' :'fina',    'c'   :'fina',    'cat' :'cons',    'cop' :'ener',    'cvx' :'ener',    'dal' :'tran',    
                'dd'  :'agri',    'farm':'agri',    'fdp' :'agri',    'gnc' :'agri',    'hes' :'ener',    'ibm' :'comp',    
                'mas' :'cons',    'mcd' :'food',    'mon' :'agri',    'msex':'wate',    'msft':'comp',    'nflx':'ente',    
                'sbux':'food',    'strl':'cons',    'tgt' :'csmr',    'tsla':'ener',    'ups' :'tran',    'xom' :'ener',    
                'xpo' :'tran',    'vmc' :'cons'
            }
# Generate all the data, and scale it
def get_scaled_data( inpList, roll_n, mom_n, rsi_n, band_n, close_percentage=True ):

    quote_df_list = []
    
    scale = {}
    with open( 'data/scaling_dict.pkl', 'rb' ) as handle:
        scale = pickle.load( handle )

    # For each quote, read in and scale
    for i in range( 0, len(inpList)):
            fileName = 'quotes/'+inpList[i]+'.csv'
            quote = rq.readQuote( fileName )

            # Generate features
            diffs = generate_differentials   ( quote          ).drop('diff_v',axis=1)
            moms  = generate_momentum_close  ( quote,  mom_n  )
            rsis  = generate_rsi             ( quote,  rsi_n  )
            bands = generate_bollinger_bands ( quote, band_n  )
            rolls = generate_rolling_close   ( quote, roll_n  , onlyMean=True )
            dates = get_frac_year_vars       ( quote          )
    
            # Seasonality in some stocks
            categ = get_seasonal_stocks      ( cat_dict[inpList[i]], quote.shape[0] )
            categ.index = quote.index
    
            # Log of current price minus 1.5, gives proxy for price percentage movement
            l_cp_m = ( np.log10( quote['close'] )-1.6 ) / 0.5

            
            # The target variables are stored in the data frame
            # Fractional component increased/decreased next day
            for i in roll_n:
                if ( close_percentage ):
                    rolls['close_mean_'+str(i)] = ( rolls['close_mean_'+str(i)].shift(i) / rolls['close_mean_'+str(i)] - 1 )
                else:
                    rolls['close_mean_'+str(i)] = ( rolls['close_mean_'+str(i)].shift(i) - rolls['close_mean_'+str(i)] )
            rolls = rolls.replace( [np.inf, -np.inf], np.nan )

            
            # Perform scaling
            diffs['diff_co'] = (           diffs['diff_co']   - scale[    'diff_co_mean'] ) / scale[    'diff_co_std']
            diffs['diff_hl'] = ( np.log10( diffs['diff_hl'] ) - scale['log_diff_hl_mean'] ) / scale['log_diff_hl_std']
            
            # Scale momentum
            for n in mom_n:
                moms  [ 'momentum_'+str(n)] = ( moms[  'momentum_'+str(n)] - scale['momentum_mean'] ) / scale[ 'momentum_std']
            
            # Scale relative strength index
            for n in rsi_n:
                rsis  [      'rsi_'+str(n)] = ( rsis[       'rsi_'+str(n)] - scale[     'rsi_mean'] ) / scale[     'rsi_std']

            # Scale bollinger bands
            for n in band_n:
                bands ['bollinger_'+str(n)] = ( bands['bollinger_'+str(n)] - scale[    'band_mean'] ) / scale[     'band_std']
                
            # Combine all the data frames
            var_df_list = [ diffs, moms, rsis, bands, dates, categ, l_cp_m, rolls ]
            all_variables = reduce( lambda left,right: left.join(right,how='inner'), var_df_list )
            
            quote_df_list.append( all_variables )
                        
    return pd.concat( quote_df_list )



def gen_data( inpList, roll_n, mom_n, rsi_n, band_n ):

    quote_df_list = []
    
    for i in range( 0, len(inpList)):
            fileName = 'quotes/'+inpList[i]+'.csv'
            quote = rq.readQuote( fileName )

            # Generate features
            diffs = generate_differentials   ( quote            ).drop('diff_v',axis=1)
            moms  = generate_momentum_close  ( quote, mom_nums  )
            rsis  = generate_rsi             ( quote, rsi_nums  )
            bands = generate_bollinger_bands ( quote, band_nums )
            rolls = generate_rolling_close   ( quote, roll_nums, onlyMean=True )
            dates = get_frac_year_vars       ( quote            )
    
            # Seasonality in some stocks
            categ = get_seasonal_stocks      ( inpList[i], quote.shape[0] )
            categ.index = quote.index
    
            # Log of current price minus 1.5, gives proxy for price percentage movement
            l_cp_m = np.log10( quote['close'] )

            
            # The target variables are stored in the data frame
            # Fractional component increased/decreased next day
            for i in roll_nums:
                rolls['close_mean_'+str(i)] = ( rolls['close_mean_'+str(i)].shift(i) / rolls['close_mean_'+str(i)] - 1 )
            rolls = rolls.replace( [np.inf, -np.inf], np.nan )

            # Combine all the data frames
            var_df_list = [ diffs, moms, rsis, bands, dates, categ, l_cp_m, rolls ]
            all_variables = reduce( lambda left,right: left.join(right,how='inner'), var_df_list )
            
            quote_df_list.append( all_variables )
            
    # Combine all the data
    return pd.concat( quote_df_list )


# To manage seasonality trends, return two variables to track time of year.
# Date must be index
def get_frac_year_vars( inp_quote ):

    day_of_year = pd.to_datetime( inp_quote.index ).dayofyear
    dy1 = 2*( (   day_of_year         % 367 ) / 366. ) - 1
    dy2 = 2*( ( ( day_of_year + 183 ) % 367 ) / 366. ) - 1

    return pd.DataFrame( { 'frac_year_1':dy1, 'frac_year_2':dy2 }, index = inp_quote.index )


# We expect some stocks to have strong seasonal trends,
# If so, mark with categorical variables
def get_seasonal_stocks( category, n_rows ):

    category = category[:4].lower()

    ind_list = ['aero','agri','chem','comp','cons',
                'defe','educ','ener','ente','fina',
                'food','heal','medi','tele','tran','wate']

    long_list = ['aerospace','agriculture','chemical','computer',
                 'construction','defense','education','energy',
                 'entertainment','financial','food','healthcare',
                 'media','telecommunications','transportation','water']

    time_list = ['agri', 'cons', 'ener', 'tran', 'wate' ]
    # Ag, construction, energy, transportation, water should have time dependence

    foo = pd.DataFrame()

    for ind in time_list:
        cat_col = ind + '_ind'
        foo[cat_col] = np.zeros( n_rows, dtype=int )

    if category in time_list:
        foo[ category+'_ind' ] = 1

    return foo


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
        
        # 1 if above, -1 if below
        ban_df[ b_labels[-1] ] = 2*( new_df[ 'close' ] - lowerBand ) / ( upperBand - lowerBand ) - 1.
        
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