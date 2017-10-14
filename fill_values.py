import pandas as pd
import numpy  as np



# Predict closing values by de-collapsing the mean,
# and custom cubic spline interpolation
def pred_from_mean( inp_close_df, roll_nums ):
    
    n_s = 3.
    pred_list = [] # For sorting the labels
    
    # Stores values predicted from mean
    my_df = inp_close_df['close'].to_frame()
    
    
    rolls = sorted( roll_nums )
    diff  = np.array( rolls[1:] )-np.array( rolls[:-1] )

    # First predict the first few days, indexing starts at 1
    roll_str = str( rolls[0] )
    mid      = str((rolls[0]+1)/2)
    
    
    my_df['pred_'+roll_str+'_day_1'         ] = my_df['close']
    
    # Odd
#    if ( (rolls[0] % 2) == 1 ):
    my_df['pred_'+str( rolls[0] )+'_day_'+mid ] = inp_close_df['pred_mean_'+roll_str]

    my_df['pred_'+roll_str+'_day_'+roll_str ] =  2 * inp_close_df['pred_mean_'+roll_str ] - my_df['close']

    pred_list = ['pred_'+roll_str+'_day_1','pred_'+str( rolls[0] )+'_day_'+mid,'pred_'+roll_str+'_day_'+roll_str]
    
    # Find values not covered
    predicted_list = [1,(rolls[0]+1)/2,rolls[0]]
    need_to_predict = [x for x in range(1,rolls[0]+1) if x not in predicted_list]

    # Find values not covered
    if ( len(need_to_predict) > 0 ):

        # Assemble data needing predicting
        x1 = my_df['pred_'+roll_str+'_day_1'        ]
        x5 = my_df['pred_'+roll_str+'_day_'+roll_str]
        str_pred_list = ['pred_'+roll_str+'_day_1','pred_'+roll_str+'_day_'+roll_str]
        
        if ( (rolls[0] % 2) == 1 ):
            x3 = my_df['pred_'+roll_str+'_day_'+mid]

            str_pred_list = ['pred_'+roll_str+'_day_1',
                             'pred_'+roll_str+'_day_'+mid,
                             'pred_'+roll_str+'_day_'+roll_str]
            
# Interpolation method could potentially be changed        

        # Predict using custom cubic spline, for pandas arrays
        preds = cubic_pandas_spline( predicted_list, my_df[str_pred_list].values, need_to_predict )
        
        # Save the interpolated arrays
        for i in range( 0, len(need_to_predict) ):
            my_df['pred_'+roll_str+'_day_'+str(need_to_predict[i])] = preds[:,i]
            pred_list.append('pred_'+roll_str+'_day_'+str(need_to_predict[i]))

    # Should sort the prediction list, so predicted days in order
    pred_list = sorted( pred_list )
    
    # Need to take mean chunks, and calculate amount in later chunk
    # In later chunck, midpoint will be the mean value, interpolate
    #  from previous mean value centerpoint to find chunck x1,
    #  then use ( x5=2m-x1 ) to calcuate chunck x5, interpolate, repeat
        
    for i in range( 1, len(rolls) ):
        
        prev_str   = str(rolls[i-1])
        chunk_str  = str(rolls[i  ])
        
        prev_days  = rolls[i-1]
        tot_days   = rolls[i  ]
        chunk_days = tot_days - prev_days
        
        prev_mean  = inp_close_df['pred_mean_'+ prev_str]
        tot_mean   = inp_close_df['pred_mean_'+chunk_str]

        chunk_mean = ( tot_days*tot_mean - prev_days*prev_mean ) / ( chunk_days )
        
    
        # Odd, use midpoint
        # Will need these values for later iterations anyway
        prev_mid = int(mid)
        mid      = (chunk_days+1)/2
        mid_str  = str(mid)
        
        new_col_list = []
        
        if ( (chunk_days % 2) == 1 ):


            my_df['pred_'+chunk_str+'_day_'+mid_str ] = chunk_mean
            
            
            # Get the first day from interpolation between two midpoints
            my_df['pred_'+chunk_str+'_day_1' ] = ( (      mid - 1 ) * chunk_mean  +
                                                   ( prev_mid     ) * my_df['pred_'+prev_str+'_day_'+str(prev_mid)] 
                                                 ) / (    mid - 1   + prev_mid ) 

            my_df['pred_'+chunk_str+'_day_'+str(chunk_days) ] =  2 * chunk_mean - my_df['pred_'+chunk_str+'_day_1' ]

# These were large errors, lets try to smooth them a little
            my_df['pred_'+chunk_str+'_day_1' ] =  ( my_df['pred_'+chunk_str+'_day_1' ] + (n_s-1)*chunk_mean ) / n_s
            my_df['pred_'+chunk_str+'_day_'+str(chunk_days) ] = ( my_df['pred_'+chunk_str+'_day_'+str(chunk_days) ] + (n_s-1)*chunk_mean ) / n_s
            
            # Find values not covered
            predicted_list = [1,mid,chunk_days]
            need_to_predict = [x for x in range(1,chunk_days) if x not in predicted_list]
            
            new_col_list = ['pred_'+chunk_str+'_day_1','pred_'+chunk_str+'_day_'+str(chunk_days),'pred_'+chunk_str+'_day_'+mid_str]
            
            # Find values not covered
            if ( len(need_to_predict) > 0 ):

                # Assemble data needing predicting
                x1 = my_df['pred_'+chunk_str+'_day_1'        ]
                x5 = my_df['pred_'+chunk_str+'_day_'+str(chunk_days)]
                str_pred_list = ['pred_'+chunk_str+'_day_1',
                                 'pred_'+chunk_str+'_day_'+mid_str,
                                 'pred_'+chunk_str+'_day_'+str(chunk_days)]

# Interpolation method could potentially be changed        

                # Predict using custom cubic spline, for pandas arrays
                preds = cubic_pandas_spline( predicted_list, my_df[str_pred_list].values, need_to_predict )

                # Save the interpolated arrays
                for i in range( 0, len(need_to_predict) ):
                    my_df['pred_'+chunk_str+'_day_'+str(need_to_predict[i])] = preds[:,i]
                    new_col_list.append('pred_'+chunk_str+'_day_'+str(need_to_predict[i]))
        # Even
        else:
            # Use mean difference, and difference from chunk to last day
            delta = inp_close_df['pred_mean_'+chunk_str] - my_df['pred_'+prev_str+'_day_'+str(diff[i-1])]
            my_df['pred_'+chunk_str+'_day_1'] = inp_close_df['pred_mean_'+chunk_str] - delta/2.
            my_df['pred_'+chunk_str+'_day_2'] = inp_close_df['pred_mean_'+chunk_str] + delta/2.
            
            my_df['pred_'+chunk_str+'_day_1'] = (my_df['pred_'+chunk_str+'_day_1']+(n_s-1)*chunk_mean)/n_s
            my_df['pred_'+chunk_str+'_day_2'] = (my_df['pred_'+chunk_str+'_day_2']+(n_s-1)*chunk_mean)/n_s

            new_col_list = ['pred_'+chunk_str+'_day_1','pred_'+chunk_str+'_day_2']

        pred_list = pred_list + sorted( new_col_list )
        
    # This will institute proper order of predictions
    my_df = my_df[ ['close']+pred_list[1:] ]
    
    # Rewrite so just ordered predictions
    for i in range( 1, len(my_df.columns.values) ):
        my_df.columns.values[i] = 'pred_'+str(i)
            
    # Going to fill not smoothed values (null) with extrapolated data
    # We don't need high accuracy-these are going to be very heavily weighted 
    #  with a large error
    for col in my_df.columns.values[1:]:
        null_or_not = my_df[col].isnull()

        # Only do those where we have nulls at recent dates
        if ( null_or_not.sum() > 1 ):

            found_one=False
            
            # Find most recent data index
            for index in range( 1, my_df.shape[0] ):
                if ( (null_or_not[index-1] == True ) and
                     (null_or_not[index  ] == False) ):
                    found_one=True
                    break

            if ( found_one ):
                data_index = range( index, index+5 ) # Data to use for extrapolation
                pred_index = range(     0, index   ) # Data to extrapolate

                data_values = my_df[col].values[ data_index ]

                # Predict using simple quadratic extrapolation
                z            = np.polyfit( data_index, data_values, 2 )
                quad_extrap  = np.poly1d ( z )

                pred_values  = quad_extrap( pred_index )

                my_df[col].values[pred_index] = pred_values
            
    return my_df




# Performs interpolations with the data format we have
def cubic_pandas_spline( inp_x, y, pred_x ):
    
    x      = np.array(inp_x)
    pred_x = np.array( pred_x )

    a = np.zeros( [y.shape[0], y.shape[1]+1] )
    b = np.zeros( [y.shape[0], y.shape[1]  ] )
    d = np.zeros( [y.shape[0], y.shape[1]  ] )
    
    h = np.ones( y.shape[1] )+1
    
    for i in range( 0, y.shape[1] ):
        a[:,i] = y[:,i]

    alpha = np.zeros( [y.shape[0], y.shape[1]] )
    alpha[:,1:] = 3./h[1:]*(a[:,2:]-a[:,1:-1]) - 3./h[:-1]*(a[:,1:-1]-a[:,:-2])

    c = np.zeros( [y.shape[0], y.shape[1]  ] )
    l = np.zeros( [y.shape[0], y.shape[1]  ] )
    m = np.zeros( [y.shape[0], y.shape[1]  ] )
    z = np.zeros( [y.shape[0], y.shape[1]  ] )

    l[:,0] = 1
    l[:,y.shape[1]-1] = 1
    
    for i in range( 1, y.shape[1]-1 ):
        l[:,i] = 2 * ( x[i+1] - x[i-1] ) - h[i-1] * m[:,i-1]
        m[:,i] = h[i] / l[:,i]
        z[:,i] = ( alpha[:,i]-h[i-1]*z[:,i-1] ) / l[:,i]
                
    for j in range( y.shape[1]-2, -1, -1 ):
        c[:,j] =  z[:,j]  -  m[:,j] *c[:,j+1]
        b[:,j] =((a[:,j+1]-  a[:,j])/h[  j  ] - 
                 (c[:,j+1]+2*c[:,j])*h[  j  ]/3. )
        d[:,j] = (c[:,j+1]-  c[:,j])/(h[ j  ]*3. )
                
    mid_index = int((y.shape[1])/2)
    
    ret_y = np.zeros( [y.shape[0],pred_x.shape[0]] )

    for i in range( 0, pred_x.shape[0] ):
        ret_y[:,i]= ( 
                 a[:,mid_index]*(pred_x[i]-inp_x[mid_index])**0 +
                 b[:,mid_index]*(pred_x[i]-inp_x[mid_index])**1 +
                 c[:,mid_index]*(pred_x[i]-inp_x[mid_index])**2 +
                 d[:,mid_index]*(pred_x[i]-inp_x[mid_index])**3 )
    
    return ret_y