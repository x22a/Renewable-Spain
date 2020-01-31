import re
import pandas as pd

def dateTo(dataframe):
    dataframe = dataframe.drop(["Area", "Fossil Coal-derived gas  - Actual Aggregated [MW]", "Fossil Oil shale  - Actual Aggregated [MW]", "Fossil Peat  - Actual Aggregated [MW]", "Geothermal  - Actual Aggregated [MW]", "Hydro Pumped Storage  - Actual Aggregated [MW]", "Marine  - Actual Aggregated [MW]", "Wind Offshore  - Actual Aggregated [MW]"], axis=1)
    Hour = pd.Series([])
    Day = pd.Series([])
    Month = pd.Series([])
    Year = pd.Series([])

    index = 0
    for date in dataframe.MTU:
        matchHour = re.findall(r"[0-9]{2}:[0-9]{2}\s", date)
        Hour[index] = matchHour[0]
        matchDay = re.findall(r"^[0-9]{2}", date)
        Day[index] = matchDay[0]
        matchMonth = re.findall(r"(?<=\.)([0-9]{2})(?=\.)", date)
        Month[index] = matchMonth[0]
        yearMatch = re.findall(r"(?<=\.)([0-9]{4})", date)
        Year[index] = yearMatch[0]
        index += 1
    
    dataframe.insert(0, "Year", Year) 
    dataframe.insert(0, "Day", Day) 
    dataframe.insert(0, "Month", Month) 
    dataframe.insert(0, "Hour", Hour) 

    #Pendiente quitar la columna MTU
    dataframe = dataframe.drop(["MTU"], axis=1)

    newNames = {
    'Biomass  - Actual Aggregated [MW]': 'Biomass MWh',
    'Fossil Brown coal/Lignite  - Actual Aggregated [MW]': 'Fossil Lignite MWh',
    'Fossil Gas  - Actual Aggregated [MW]': "Fossil Gas MWh",
    'Fossil Hard coal  - Actual Aggregated [MW]': "Fossil Coal MWh",
    'Fossil Oil  - Actual Aggregated [MW]': "Fossil Oil MWh",
    'Hydro Pumped Storage  - Actual Consumption [MW]': "Hydro Pumped Storage MWh",
    'Hydro Run-of-river and poundage  - Actual Aggregated [MW]': "Hydro Run-of-river MWh",
    'Hydro Water Reservoir  - Actual Aggregated [MW]': "Hydro Water Reservoir MWh",
    'Nuclear  - Actual Aggregated [MW]': "Nuclear MWh",
    'Other  - Actual Aggregated [MW]': "Other MWh",
    'Other renewable  - Actual Aggregated [MW]': "Other Renewable MWh",
    'Solar  - Actual Aggregated [MW]': "Solar MWh",
    'Waste  - Actual Aggregated [MW]': "Waste MWh",
    'Wind Onshore  - Actual Aggregated [MW]': "Wind MWh"
    }

    dataframe = dataframe.rename(columns=newNames, errors="raise")

    return dataframe