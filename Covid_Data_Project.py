# Sam Carlson
# Ryan Alian

# Cameron Ahn
# Colin Braddy
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
import datetime as dt 
from vega_datasets import data

#Get Recorded US deaths csv from Official Github and return as Pandas dataframe
st.set_page_config(layout="wide")
@st.cache
def load_raw_deaths_csv():
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
    df = pd.read_csv(url)
    df.to_csv("covid_deaths.csv")
    return df

#Get Recorded US cases csv from Official Github and return as Pandas dataframe
@st.cache
def load_raw_cases_csv():
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
    df = pd.read_csv(url)
    df.to_csv("covid_cases.csv")
    return df

# This method returns a dataframe which columns with no recorded deaths in any state are dropped.
def stateDeathsOverTime(raw):
    # Drop arbitrary columns (We can't .copy columns because each indivudal date is a column)
    rawdf = raw.drop(['UID','iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Lat', 'Long_', 'Combined_Key', 'Country_Region', 'Population'], 1)
    # At this point we have a Dataframe of deaths in the United States per County per State.
    # Sum county deaths to confine deaths to indivual States
    rawdf  = rawdf.reset_index().groupby(['Province_State']).sum()
    # Deaths are recorded as a cumulative total. Not each day.
    # So, Some Columns are sum = 0, Remove these to remove eventless days.
    deathsOvertime = rawdf.loc[(rawdf.sum(axis=1) != 0), (rawdf.sum(axis=0) != 0)]
    deathsOvertime = deathsOvertime.drop(['index'], 1)
    return deathsOvertime

#This method starts by getting the dataframe with only columns containing deaths in them (From stateDeathOT()) and summing each row.
def stateDeathTotal(raw):
    # Remove useless columns and condense to only days with recorded deaths
    rawdf = stateDeathsOverTime(raw)
    # We need to access the most recent data entry (Last column) which will provide us total deaths per state
    rawdf["Deaths"] = rawdf.iloc[:,-1:]
    # Now we can create a Dataframe with only the states and their cumulative deaths (dfStateDeaths)
    dfStateDeaths = rawdf[["Deaths"]].copy()
    dfStateDeaths = pd.merge(dfStateDeaths, stateIDs(), on='Province_State')
    return dfStateDeaths

def stateIDs():
    #In order to properly present this visually we need to assign StateIDs to their respective states.
    #! import previously used .csv from another project to get State IDS (We need to replace this if we can)
    df2 = pd.read_csv('https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/population_engineers_hurricanes.csv')
    stateID = df2[["state","id"]].copy()
    stateID.columns = ['Province_State', 'id']
    stateID.set_index('Province_State')
    return stateID


def stateDeathsChart(raw):
    #raw = raw.drop(['American Samoa'], 0)
    raw = pd.melt(raw, ignore_index=False)
    raw['variable'] = pd.to_datetime(raw.variable)
    raw = raw.sort_values(by=['Province_State', 'value'])
    raw = raw.reset_index('Province_State')
    return raw

# returns a dataframe which columns with no recorded cases in any state are dropped
def stateCasesOverTime(raw): 
    # drop arbitrary columns
    rawdf = raw.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2','Country_Region', 'Lat', 'Long_', 'Combined_Key'], 1) 
    # sums county cases to provide cases per territory
    rawdf  = rawdf.reset_index().groupby(['Province_State']).sum()
    #Cases are recorded as a cumulative total. Not per day
    #Some Columns are sum = 0, Remove these
    casesOvertime = rawdf.loc[(rawdf.sum(axis=1) != 0), (rawdf.sum(axis=0) != 0)]
    casesOvertime = casesOvertime.drop(['index'], 1)
    return casesOvertime

# Gets the dataframe with only columns containing deaths in them (From stateCasesOT()) and summing each row
def stateCaseTotal(raw): 
    rawdf = stateCasesOverTime(raw)
    #We need to access the most recent data entry (Last column) which will provide us total cases per state
    rawdf["Cases"] = rawdf.iloc[:,-1:]
    #Now we can create a Dataframe with only the states and their cumulative cases (dfStateCases)
    dfStateCases = rawdf[["Cases"]].copy()
    dfStateCases = pd.merge(dfStateCases, stateIDs(), on='Province_State')
    return dfStateCases

# converts dataframe containing state cases over time into a format compatible for use in line chart
def stateCaseChart(raw):
    #df = df.drop(['American Samoa'], 0)
    raw = pd.melt(raw, ignore_index=False)
    raw['variable'] = pd.to_datetime(raw.variable)
    raw = raw.sort_values(by=['Province_State', 'value'])
    raw = raw.reset_index('Province_State')
    return raw

def userSelectedStateDeaths(selected):
    deathsDf = stateDeathsOverTime(rawDeathsdf)
    selectedDf = deathsDf.loc[selected].copy()
    return selectedDf

def userSelectedStateCases(selected):
    casesDf = stateCasesOverTime(raw_cases)
    selectedDf = casesDf.loc[selected].copy()
    return selectedDf

# State death dataframe setup
rawDeathsdf = load_raw_deaths_csv()
dfStateDeathsOverTime = stateDeathsOverTime(rawDeathsdf)
dfStateTotalDeaths = stateDeathTotal(rawDeathsdf)
deathChartDf = stateDeathsChart(dfStateDeathsOverTime)

# State case dataframe setup
raw_cases = load_raw_cases_csv()
dfStateCasesOverTime = stateCasesOverTime(raw_cases)
dfStateTotalCases = stateCaseTotal(raw_cases)
caseChartDf = stateCaseChart(dfStateCasesOverTime)

#Death to Cases Ratio dataframe setup
dfStateCaseDeathRatio = pd.merge(dfStateTotalDeaths, dfStateTotalCases.drop(['id'], 1), on='Province_State')
dfStateCaseDeathRatio['Ratio'] = dfStateCaseDeathRatio['Deaths']/dfStateCaseDeathRatio['Cases']

###CHARTS###
# Choropleth map for US deaths
usDeathMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=["Province_State:N", 'Deaths:O'],
    color='Deaths:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalDeaths, 'id', ['Deaths'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Choropleth map for US cases
usCaseMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=["Province_State:O", 'Cases:O'],
    color='Cases:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalCases, 'id', ['Cases'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

#Here is a barchart with Average Deaths comparing all States
avgDeaths = dfStateTotalDeaths["Deaths"].mean()
bar = alt.Chart(dfStateTotalDeaths).mark_bar().encode(
    x='Province_State:O',
    y='Deaths:Q',
    color=alt.condition(
        alt.datum.Deaths > avgDeaths, 
        alt.value('orange'),
        alt.value('steelblue')
    )
)
sortedbar = alt.Chart(dfStateTotalDeaths).mark_bar().encode(
    x=alt.X('Province_State:O', sort='-y'),
    y='Deaths:Q',
    color=alt.condition(
        alt.datum.Deaths > avgDeaths, 
        alt.value('orange'),
        alt.value('steelblue')
    )
)
rule = alt.Chart(dfStateTotalDeaths).mark_rule(color='red').encode(
    y='mean(Deaths):Q'
)
barChart = (bar + rule).properties(width=900, height = 500)
sortedbarChart = (sortedbar + rule).properties(width=900, height = 500)

#

highlight = alt.selection(type='single', on='mouseover',
                          fields=['Province_State'], nearest=True)

deathsAllStatesbase = alt.Chart(deathChartDf).mark_line().encode(
    #opacity=alt.value(0),
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value"]
)

deathsAllStatespoints = deathsAllStatesbase.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
).properties(
    width=900,
    height=1000
)

deathsAllStateslines = deathsAllStatesbase.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
)

deathsAllStates = deathsAllStatespoints + deathsAllStateslines

# Line chart
# Line chart base - ask team members about. Why do the base, points, and lines of the chart have to be created separately
casesAllStatesbase = alt.Chart(caseChartDf).mark_line().encode(
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value"]
)

# Line chart points 
casesAllStatespoints = casesAllStatesbase.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
).properties(
    width=900,
    height=1000
)

casesAllStateslines = casesAllStatesbase.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
)

# Line chart - why do the points and lines have to be created separately, then combined?
casesAllStates = casesAllStatespoints + casesAllStateslines


############
## CHARTS ##
############
# Choropleth map for US deaths
usDeathMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Deaths:O'],
    color='Deaths:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalDeaths, 'id', ['Deaths'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Choropleth map for US cases
usCaseMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Cases:O'],
    color='Cases:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalCases, 'id', ['Cases'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Choropleth map for US Deaths to Cases Ratio
usCaseDeathRatioMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Ratio:O'],
    color='Ratio:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateCaseDeathRatio, 'id', ['Ratio'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Here is a barchart with Average Deaths comparing all States
avgDeaths = dfStateTotalDeaths["Deaths"].mean()
bar = alt.Chart(dfStateTotalDeaths).mark_bar().encode(
    x='Province_State:O',
    y='Deaths:Q',
    color=alt.condition(
        alt.datum.Deaths > avgDeaths, 
        alt.value('orange'),
        alt.value('steelblue')
    )
)
# Here is a barchart with Average Deaths comparing all States sorted by most to least
sortedbar = alt.Chart(dfStateTotalDeaths).mark_bar().encode(
    x=alt.X('Province_State:O', sort='-y'),
    y='Deaths:Q',
    color=alt.condition(
        alt.datum.Deaths > avgDeaths, 
        alt.value('orange'),
        alt.value('steelblue')
    )
)
rule = alt.Chart(dfStateTotalDeaths).mark_rule(color='red').encode(
    y='mean(Deaths):Q'
)
barChart = (bar + rule).properties(width=900, height = 500)
sortedbarChart = (sortedbar + rule).properties(width=900, height = 500)

# Here is a barchart with recorded Cases comparing all States average
avgCases = dfStateTotalCases["Cases"].mean()
bar_case = alt.Chart(dfStateTotalCases).mark_bar().encode(
    x='Province_State:O',
    y='Cases:Q',
    color=alt.condition(
        alt.datum.Cases > avgCases,
        alt.value('orange'),
        alt.value('steelblue')
    )
)
# Here is a barchart with recorded Cases comparing all States average sorted by most to least
sortedbar_case = alt.Chart(dfStateTotalCases).mark_bar().encode(
    x=alt.X('Province_State:O', sort='-y'),
    y='Cases:Q',
    color=alt.condition(
        alt.datum.Cases > avgCases,
        alt.value('orange'),
        alt.value('steelblue')
    )
)
rule_case = alt.Chart(dfStateTotalCases).mark_rule(color='red').encode(
    y='mean(Cases):Q'
)
barChart_case = (bar_case + rule_case).properties(width=900, height=500)
sortedbarChart_case = (sortedbar_case + rule_case).properties(width=900, height=500)

# This is the multiline graph which displays deaths over time for every state
highlight = alt.selection(type='single', on='mouseover',
                          fields=['Province_State'], nearest=True)

deathsAllStatesbase = alt.Chart(deathChartDf).mark_line().encode(
    #opacity=alt.value(0),
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value"]
)

deathsAllStatespoints = deathsAllStatesbase.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
).properties(
    width=900,
    height=1000
)

deathsAllStateslines = deathsAllStatesbase.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
)

deathsAllStates = deathsAllStatespoints + deathsAllStateslines

# This is the multiline graph which displays cases over time for every state
casesAllStatesbase = alt.Chart(caseChartDf).mark_line().encode(
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value"]
)

# Line chart points 
casesAllStatespoints = casesAllStatesbase.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
).properties(
    width=900,
    height=1000
)

casesAllStateslines = casesAllStatesbase.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
)

# Line chart - why do the points and lines have to be created separately, then combined?
casesAllStates = casesAllStatespoints + casesAllStateslines



########################
# Streamlit App Layout #
########################

st.title('COVID Data')
st.header("Visual Analytics Project | Team 7");
st.write("Cameron Ahn, Ryan Alian, Colin Braddy, Sam Carlson")

allStates = dfStateTotalDeaths['Province_State'].values.tolist()

deathCol, caseCol = st.beta_columns(2)
#caseCol, deathCol = st.beta_columns(2)

with st.beta_expander('Data to View: '):
    
    #Container for Death stats
    if st.checkbox('All Recorded Deaths Across the United States'):
        allDeaths = st.beta_container()
        allDeaths.header("Recorded Deaths in the United States")

        if allDeaths.checkbox('View Original Dataframe:'):
            allDeaths.header("Dataframe of State Cumulative Deaths from COVID-19: ")
            allDeaths.dataframe(rawDeathsdf)
        if allDeaths.checkbox('View Simplified Dataframe:'):
            allDeaths.header("Dataframe of States/Total Deaths from COVID-19: ")
            allDeaths.dataframe(dfStateTotalDeaths)

        allDeaths.subheader("Deaths from COVID-19 across the United States: ")
        allDeaths.write(usDeathMap)

        allDeaths.subheader("Chart of States/Deaths (Highlighted is above the National Average)")
        if allDeaths.checkbox('Sort by Most to Least Deaths'):
            allDeaths.write(sortedbarChart)
        else:
            allDeaths.write(barChart)

        allDeaths.subheader("Graph of Death trends for every State: ")
        allDeaths.write(deathsAllStates)


    #Container for Case stats
    if st.checkbox('All Recorded Cases Across the United States'):
        allCases = st.beta_container()
        allCases.header("Recorded Cases Across the United States")

        if allCases.checkbox('View Original Cases Dataframe:'):
            allCases.header("Dataframe of State Cumulative Cases from COVID-19: ")
            allCases.dataframe(raw_cases)
        if allCases.checkbox('View Simplified Cases Dataframe:'):
            allCases.header("Dataframe of States/Total Cases from COVID-19: ")
            allCases.dataframe(dfStateTotalCases)

        allCases.subheader("Confirmed Cases of COVID-19 Across the United States: ")
        allCases.write(usCaseMap)

        allCases.subheader("Chart of States/Cases (Highlighted is above the National Average)")
        if allCases.checkbox('Sort by Most to Least Cases'):
            allCases.write(sortedbarChart_case)
        else:
            allCases.write(barChart_case)

        allCases.subheader("Graph of Case trends for every State: ")
        allCases.write(casesAllStates)
    
    #Container for Ratio stats
    if st.checkbox('Ratio of Deaths per Cases Across the United States'):
        ratioDeathCase = st.beta_container()
        ratioDeathCase.subheader('Ratio of Deaths to Cases in the United States')
        ratioDeathCase.write(usCaseDeathRatioMap)
    
    if st.checkbox('Select States to compare: '):
        userSelectedStates = st.beta_container()
        statesSelected = userSelectedStates.multiselect('What States do you want to compare?', allStates, allStates[0])
        
        selectedStateDeaths = userSelectedStateDeaths(statesSelected)
        selectedStateCases = userSelectedStateCases(statesSelected)
        
            
        stateDeathsChart = stateDeathsChart(selectedStateDeaths)
        stateCaseChart = stateCaseChart(selectedStateCases)
        
        if userSelectedStates.checkbox('Compare Overall Deaths: '):
            selectedStateTotalDeaths = selectedStateDeaths.copy()
            selectedStateTotalDeaths = selectedStateTotalDeaths.reset_index()
            selectedStateTotalDeaths['Deaths'] = selectedStateTotalDeaths.iloc[:,-1:]
            
            st.write('Overall Deaths for each selected State:')
            st.write(selectedStateTotalDeaths)
            
            deathSelectBar = alt.Chart(selectedStateTotalDeaths).mark_bar().encode(
                x='Province_State:O',
                y='Deaths:Q',
                color= alt.value('steelblue')
            ).properties(
                width=700,
                height=700
            )
            st.write(deathSelectBar)
            
        if userSelectedStates.checkbox('Compare Deaths Overtime: '):
            st.subheader('Deaths overtime for each State: ')
            selectDeathsLine = alt.Chart(stateDeathsChart).mark_line().encode(
                x='variable',
                y='value',
                color='Province_State',
                tooltip=["Province_State:N", "value", "variable"]
            ).properties(
                width=900,
                height=1000
            )
            st.write(selectDeathsLine)
            
        if userSelectedStates.checkbox('Compare Overall Cases: '):
            selectedStateTotalCases = selectedStateCases.copy()
            selectedStateTotalCases = selectedStateCases.reset_index()
            selectedStateTotalCases['Deaths'] = selectedStateTotalCases.iloc[:,-1:]
            
            st.write('Overall Cases for each selected State:')
            st.write(selectedStateTotalCases)
            
            deathSelectBar = alt.Chart(selectedStateTotalCases).mark_bar().encode(
                x='Province_State:O',
                y='Deaths:Q',
                color= alt.value('steelblue')
            ).properties(
                width=700,
                height=700
            )
            st.write(deathSelectBar)
            
        if userSelectedStates.checkbox('Compare Cases Overtime: '):
            st.write("Cases Overtime")
            selectCasesLine = alt.Chart(stateCaseChart).mark_line().encode(
                x='variable',
                y='value',
                color='Province_State',
                tooltip=["Province_State:N", "value", "variable"]
            ).properties(
                width=900,
                height=1000
            )
            st.write(selectCasesLine)
            
            
            
#
#if st.sidebar.checkbox('Show Raw Death Data'):
#    st.write("Raw COVID Death data from Github: ")
#    st.dataframe(raw)
#    
#if st.sidebar.checkbox('Show Raw Case Data'):
#    st.write("Raw COVID Case data from Github: ")
#    st.dataframe(raw_cases)
# df.index[df['BoolCol'] == True].tolist()
