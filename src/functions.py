import re
import pandas as pd

def dateTo(dataframe):

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

    return dataframe