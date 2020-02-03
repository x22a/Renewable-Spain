# Imports 
from src.functions import parser, sendReport

day, month, year = parser()
sendReport(day, month, year)