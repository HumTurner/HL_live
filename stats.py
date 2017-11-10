import pandas
import numpy
import datetime
idx = pandas.IndexSlice
import general
import discretionary_aua
import vantage_aua
import combined
import revenue
import costs
import data_accessing
import discf
'''
FY annual statistics
'''

def total_revenue(data_dic, input_dic):
    result = revenue.annual_revenue(data_dic,input_dic).sum(axis='columns')
    result.name = 'Total Revenue'
    return result

def costs_no_capex(input_dic):
    result = costs.annual_costs(input_dic).sum(axis='columns')-costs.annual_costs(input_dic)['capital_expenditure']
    result.name = 'Total Costs'
    return result

def net_earning_before_tax(data_dic, input_dic):
    revenue = total_revenue(data_dic, input_dic)
    costs = costs_no_capex(input_dic)
    result = revenue + costs
    result.name = 'Net Earning Before Tax'
    return result

def net_earning_after_tax(data_dic, input_dic):
    net_earning_bef_tax = net_earning_before_tax(data_dic, input_dic)
    tax_rate = general.fillna_monthly(input_dic['tax rate']).reindex(net_earning_bef_tax.index).fillna(method='ffill')['Tax']
    result = net_earning_bef_tax*(1-tax_rate)
    result.name = 'Net Earning After Tax'
    return result

def earning_per_share(data_dic, input_dic):
    '''
    Capital expenditure is not included in the calculation
    '''
    net_earning_af_tax = net_earning_after_tax(data_dic, input_dic)
    result = net_earning_af_tax / discf.no_of_shares
    result.name = 'EPS'
    return result

def total_aua(data_dic, input_dic):
    test = combined.total_aua(data_dic,input_dic)
    test.index  = test.index.get_level_values(level='month_end')
    if general.last_result_month == 6:
        temp = general.recent_end_year + 1
    else:
        temp = general.recent_end_year
    result = test[test.index.month==general.financial_year_month]['total_assets_aua']
    result =  general.convert_fy_quarter_half_index(result, result.index).groupby('financial_year').sum()['total_assets_aua'].loc[temp:]
    result.name='Total AUA'
    return result

def summary_total(data_dic, input_dic):
    df1 = total_revenue(data_dic, input_dic)
    df2 = costs_no_capex(input_dic)
    df = net_earning_before_tax(data_dic, input_dic)
    df3 = net_earning_after_tax(data_dic, input_dic)
    df4 = earning_per_share(data_dic, input_dic)
    df5 = total_aua(data_dic, input_dic)
    return pandas.concat([df1, df2, df, df3, df4, df5],axis='columns')

def summary_revenue_dist(data_dic, input_dic):
    revenue_shares = revenue.annual_revenue(data_dic, input_dic)['management_fee']+revenue.annual_revenue(data_dic, input_dic)['stockbroking_commission']
    revenue_shares.name = 'Shares'
    revenue_funds = revenue.annual_revenue(data_dic, input_dic)['platform_fee']
    revenue_funds.name = 'Funds'
    revenue_hlf_amc = revenue.annual_revenue(data_dic, input_dic)['hlf_amc']
    revenue_hlf_amc.name = 'HLF AMC'
    revenue_cash = revenue.annual_revenue(data_dic, input_dic)['interest_on_cash']
    revenue_cash.name = 'Cash'
    revenue_cash_service = revenue.annual_revenue(data_dic, input_dic)['cash_service']
    revenue_cash_service.name = 'Cash Service'
    revenue_other = revenue.annual_revenue(data_dic, input_dic).drop(['management_fee','stockbroking_commission','platform_fee','hlf_amc','interest_on_cash','cash_service'], axis='columns').sum(axis='columns')
    revenue_other.name = 'Other'
    return pandas.concat([revenue_shares,revenue_funds,revenue_hlf_amc,revenue_cash,revenue_cash_service,revenue_other],axis='columns')

def summary_revenue_dist_percent(data_dic, input_dic):
    df = summary_revenue_dist(data_dic, input_dic)
    return df.divide(df.sum(axis='columns'),axis='index')

def summary_avg_aua_dist(data_dic, input_dic):
    df = combined.total_aua(data_dic, input_dic).groupby('financial_year').mean()
    avg_aua_funds = df['total_funds_aua']
    avg_aua_funds.name = 'Funds'
    avg_aua_shares = df['vantage_shares_aua']
    avg_aua_shares.name = 'Shares'
    avg_aua_hlf_amc = df['discretionary_aua']
    avg_aua_hlf_amc.name = 'HLF AMC'
    avg_aua_cash = df['vantage_cash_aua']
    avg_aua_cash.name = 'Cash'
    avg_aua_cash_service = df['cash_service_aua']
    avg_aua_cash_service.name = 'Cash Service'
    
    if general.last_result_month == 6:
        temp = general.recent_end_year + 1
    else:
        temp = general.recent_end_year
    result = pandas.concat([avg_aua_funds,avg_aua_shares,avg_aua_hlf_amc,avg_aua_cash,avg_aua_cash_service],axis='columns')
    return result.loc[temp:,:]

def cash_margin(data_dic):
    result = revenue.cash_interest_margin(data_dic)
    result.name='Cash Margin'
    if general.last_result_month == 6:
        temp = general.recent_end_year + 1
    else:
        temp = general.recent_end_year
    result = general.convert_fy_quarter_half_index(result, result.index)
    return result.groupby('financial_year').mean().loc[temp:,:]

def hlf_implied_actual_nnb(data_dic, input_dic):
    result = combined.historic_nnb_distribution(data_dic, input_dic)
    hlf_nnb = result['pms_others_aua'] +result['pms_hlf_aua'] +result['thirdparty_hlf_aua']+result['vantage_hlf_aua']
    result = general.convert_fy_quarter_half_index(hlf_nnb,hlf_nnb.index)
    return result

def hlf_to_date_implied_nnb(data_dic,typ=None):
    '''
    typ: 'day','month','quarter','annual'
    '''
    df = combined.get_historic_implied_nnb(data_dic,idx=data_dic['acc price'].index)
    df.name = 'HLF nnb'
    df2 = general.convert_fy_quarter_half_index(df,df.index)
    df2 = df2.reset_index()
    df2.loc[:,'month_no'] = pandas.DatetimeIndex(df2['month_end']).month
    result = df2.set_index(['month_end','financial_year','quarter_no','half_no','calendar_year','month_no'])
    if typ=='day':
        return df[df.index<=pandas.to_datetime(datetime.datetime.today())]
    elif typ=='month':
        return result.groupby(['calendar_year','month_no']).sum()
    elif typ=='quarter':
        return result.groupby(['financial_year','quarter_no']).sum()
    elif typ=='annual':
        return result.groupby('financial_year').sum()
    else:
        return result