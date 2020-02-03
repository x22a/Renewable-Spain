# Imports 
from src.functions import parser, sendReport

day, month, year, receiver = parser()
sendReport(day, month, year, receiver)