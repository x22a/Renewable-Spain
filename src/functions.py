import re
import pandas as pd
import numpy as np
import json
import requests
import os
from dotenv import load_dotenv
from fpdf import FPDF 
import matplotlib.pyplot as plt
import argparse
import email, smtplib, ssl, getpass
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Extract data from dates column ----> Day, Month, Year, Hour and create new columns

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
    dataframe.insert(0, "Month", Month) 
    dataframe.insert(0, "Day", Day) 
    dataframe.insert(0, "Hour", Hour) 

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

# Extact the information from the desired day and create new DataFrame

def getDateInfo(day, month, year, dataframe):
    answer = dataframe.loc[(dataframe['Year'] == year)]
    answer = answer.loc[(answer['Month'] == month)]
    answer = answer.loc[(answer['Day'] == day)]
    return answer

# Returns the Wind MWh/day, the total MWh/day, the % of Wind and the % of no Wind 

def aggregator(dataframe):
    suma = 0
    sumaWind = 0
    for elem in dataframe["Wind MWh"]:
        sumaWind += float(elem)
    energyWind = round((sumaWind / len(dataframe["Wind MWh"])), 2)
    for columna in dataframe.columns[4::]:
        for elem in dataframe[f"{columna}"]:
            suma += float(elem)
    totalEnergy = round((suma / 24), 2)
    windPercent = round((energyWind / totalEnergy * 100), 2)
    nonWindPercent = round((100 - windPercent), 2)
    return energyWind, totalEnergy, windPercent, nonWindPercent    


# Calculate wind speed mean from Aemet data, which is later passed to requestAemet function

def windSpeedMean(data):
    velmedia = []
    velTot = 0
    for elem in data:
        try:
            velmedia.append(elem['velmedia'])
        except:
            pass
    
    for vel in velmedia:
        vel = vel.replace(',', '.')
        velTot += float(vel)
    veloMed = velTot/len(velmedia)
    return veloMed

# Get the information from Aemet of the desired day

def requestAemet(day, month, year, dataframe = pd.read_csv("./output/clean-dataset.csv", dtype = 'str')):
    load_dotenv()
    token = os.getenv("AEMET_API_KEY")
    thDmonth = ['01', '03', '05', '07', '08', '10']
    tuDmonth = ['04', '06', '09', '11']
    if month == '12' and day >= '31':
        nextYear = str(int(year) + 1)
        nextDay = '01'
        nextMonth = '01'
    elif month in thDmonth and day >= '31':
        nextDay = '01'
        nextMonth = str(int(month) + 1)
        nextYear = year
    elif month in tuDmonth and day >= '30':
        nextDay = '01'
        nextMonth = str(int(month) + 1)
        nextYear = year
    elif (month not in thDmonth or month not in tuDmonth) and (day >= '28'):
        nextDay = '01'
        nextMonth = str(int(month) + 1)
        nextYear = year
    else:
        nextDay = str(int(day) + 1)
        nextYear = year
        nextMonth = month
    if not token:
        raise ValueError("You must set a AEMET_API_KEY token")

    headers = {
        'Accept': 'application/json',
        'api_key': f'{token}',
    }
    res = requests.get(f'https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{year}-{month}-{day}T00%3A00%3A01UTC/fechafin/{nextYear}-{nextMonth}-{nextDay}T00%3A00%3A00UTC/todasestaciones', headers=headers)
    if res.status_code != 200:
        print(res.text)
        raise ValueError("Bad Response")
    res = requests.get(res.json()['datos'])
    data = res.json()
    windInfo = round(windSpeedMean(data), 2)
    dataframe = getDateInfo(day, month, year, dataframe)
    energyInfo = aggregator(dataframe)
    return windInfo, energyInfo, dataframe


def piePlotter(requestElem):
    windPercent = requestElem[1][2]
    totalPercent = requestElem[1][3]
    labels = ['Wind Generated', 'Other Technologies']
    sizes = [windPercent, totalPercent]
    colors = ["dodgerblue", "darkorange"]
    explode = (0.15, 0)
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, colors = colors, autopct='%1.1f%%',
        shadow=True, startangle=180)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.savefig('./output/pie.png')
    pass

def barPlotter(requestElem):
    labels = ["MWh/day"]
    windEnergy = [requestElem[1][0]]
    totalEnergy = [requestElem[1][1]]

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width/2, windEnergy, width, label='Wind')
    rects2 = ax.bar(x + width/2, totalEnergy, width, label='Other')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Total MWH/day')
    ax.set_title('MWh/day by technologies')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()


    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')


    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()

    plt.savefig('./output/bar.png')
    pass



def createPDF(day, month, year):
    numToMonth = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December"
    }
    monthName = numToMonth[month]
    element = requestAemet(day, month, year)[0:2]
    dataframe = requestAemet(day, month, year)[2]
    piePlotter(element)
    barPlotter(element)
    pdf = FPDF('P','mm','A4')



    # Add page
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(190, 10, f'Report of {day}-{monthName}-{year}',0,1,'C')
    pdf.cell(190, 20, f"The average wind speed was {element[0]} m/s", 0,1,'C')
    pdf.image("./output/pie.png", 50, 40, h= 80)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(190, 185, "Percentage of wind production from total",0,1,'C')
    pdf.image("./output/bar.png", 50, 140, h= 80)
    pdf.cell(190, 15, "Wind VS Total production in MWh/day",0,1,'C')

    pdf.add_page(orientation = 'L')
    pdf.cell(277, 20, "Production by hour all technologies",0,1,'C')
    dataframe
    # Defining parameters
    num_col = len(dataframe.columns)
    w,h=277,190
    font_type = ('Arial', 'B', 10)
    pdf.set_font(*font_type)
    pdf.set_text_color(0)
    pdf.set_draw_color(0)
    pdf.set_line_width(0.2)
    for col in dataframe.columns:
        pdf.cell(w/num_col,5,col,1,0,'C')
    pdf.ln()
    pdf.set_fill_color(255,255,255)
    font_type = ('Arial', '', 8)
    pdf.set_font(*font_type)
    
    # iteration rows
    for _,row in dataframe.iterrows():
        # iterating columns
        for value in dataframe.columns:
            pdf.cell(w/num_col,10, row[value],1,0,'C',1)
        pdf.ln()
    pdf.output("./output/report.pdf",'F')


def parser(*args):
    parser = argparse.ArgumentParser(description = 'DD-MM-YYYY')
    parser.add_argument('Day', type = str, help = 'Day --> DD')
    parser.add_argument('Month', type = str, help = 'Month --> MM')
    parser.add_argument('Year', type = str, help = 'Year --> YYYY')
    args = parser.parse_args()

    day = args.Day
    month = args.Month
    year = args.Year
    return day, month, year




def sendReport(day, month, year):
    receiver = input('To whom we send the report? ')
    createPDF(day, month, year)
    subject = f"Report of {day}-{month}-{year}"
    body = f"In this report of {day}-{month}-{year}, you can find the information you asked"
    port = 465  # For SSL
    password = getpass.getpass(prompt='Password: ', stream=None) 
    sender_email = "xabironspam@gmail.com"
    receiver_email = f"{receiver}" 

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))
    filename = "./output/report.pdf"

    # Open PDF file in binary mode
    with open("./output/report.pdf", "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= Report of {day}-{month}-{year}.pdf",
    )
    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login("xabironspam@gmail.com", password)
        # TODO: Send email here
        server.sendmail(sender_email, receiver_email, text)