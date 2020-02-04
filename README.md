# Daily report of Renewable source generation hour-by-hour 

Create a report showing the percentage, the energy and the average wind speed in Spain for the selected day.

![Background](./input/background.png)

## Data

The dataset was created using the information available in https://transparency.entsoe.eu/ 

The API used was AEMET OpenData which provides data from all the meteorological stations in Spain, from which I extracted the average wind speed. (https://opendata.aemet.es)

## Usage

The program accepts 3 parameters: DD (Day) - MM (Month) - YYYY(Year)

Then sends a PDF report to the desired email address containing the information mentioned above.

