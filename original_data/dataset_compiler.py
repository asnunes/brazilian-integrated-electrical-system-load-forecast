#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 31 14:51:19 2019

@author: alexandrenunes
"""
import functools, os, math
import datetime as dt
import pandas as pd
import numpy as np
import holidays

class WeekDay():
    def __init__(self, datetime):
        self.is_holiday = self.is_holiday(datetime)
        self.day_of_week = datetime.weekday()

    def is_holiday(self, datetime):
        br_holidays = holidays.CountryHoliday('BR')
        return int(datetime in br_holidays)

class DateHour:
    def __init__(self, datetime):
        self.date = datetime
        self.delta_date = self.get_delta_date()
        self.hour = self.date.hour
        self.load = None
        self.temps = {}
        
    def get_delta_date(self):
        delta_in_seconds = (self.date - DateHour.str_to_datetime("01/01/1999 00:00:00")).total_seconds()
        delta_in_hours = divmod(delta_in_seconds, 3600)[0] 
        return delta_in_hours
        
    def add_temp(self, temp, temp_header):
        self.temps[temp_header] = temp
    
    def add_load(self, load):
        self.load = load
        
    def get_data_line(self, temp_headers):
        keys = ["Data", "Dia da Semana", "Feriado", *temp_headers, "Carga"]
        data_line = {key: "" for key in keys}
        
        data_line["Data"] = self.delta_date
        if self.load: data_line["Carga"] = self.load.replace(".", "").replace(",",".")
        
        for temp_header in temp_headers:
            if temp_header in self.temps:
                data_line[temp_header] = self.temps[temp_header]
                
        return data_line
        
    def is_load_none(self):
        return self.load is None
    
    def datetime_to_str(self):
        return self.date.strftime('%d/%m/%Y %H:%M:%S')
    
    @staticmethod
    def str_to_datetime(str_date):
        return dt.datetime.strptime(str_date,'%d/%m/%Y %H:%M:%S')

class DateDay:
    def __init__(self, day):
        self.day = day
        self.weekDay = None
        self.dateHours = {}
        
    def add_new_date(self, datetime):
        self.dateHours[datetime.hour] = DateHour(datetime)
        self.set_week_day(datetime)
    
    def add_load(self, load, datetime):
        hour = datetime.hour
        self.dateHours[hour].add_load(load)
        
    def add_temp(self, temp, temp_header, datetime):
        hour = datetime.hour
        if hour in self.dateHours:
            self.dateHours[hour].add_temp(temp, temp_header)
            
    def set_mean_temp(self, temp_header):
        if not self.dateHours:
            return
        
        for temp_name in temp_header:
            list_of_temps = [date_hour.temps[temp_name] for date_hour in self.dateHours.values() if temp_name in date_hour.temps]
            if list_of_temps:
                mean = round(sum(list_of_temps)/len(list_of_temps), 2)
                for date_hour in self.dateHours.values():
                    date_hour.temps[temp_name] = mean
        
    def set_week_day(self, datetime):
        self.weekDay = WeekDay(datetime)        
    
    def get_data_table(self, temp_headers):
        return [self.add_week_days_to_line(dateHour.get_data_line(temp_headers)) for dateHour in self.dateHours.values()]
            
    def add_week_days_to_line(self, line):
        if not self.weekDay or "Dia da Semana" not in line or "Feriado" not in line:
            return list(line.values())
        
        line["Dia da Semana"] = self.weekDay.day_of_week
        line["Feriado"] = self.weekDay.is_holiday
        
        return list(line.values())
    
    def number_of_dates(self):
        return len(self.dateHours)
    
    def number_of_dates_without_load(self):
        return sum([dateHour.is_load_none() for dateHour in self.dateHours.values()])

class DateMonth:
    def __init__(self, month):
        self.month = month
        self.dateDays = {}
        
    def add_new_date(self, datetime):
        day = datetime.day
        
        if day not in self.dateDays:
            self.dateDays[day] = DateDay(day)
            
        self.dateDays[day].add_new_date(datetime)
        
    def add_load(self, load, datetime):
        day = datetime.day
        self.dateDays[day].add_load(load, datetime)
        
    def add_temp(self, temp, temp_header, datetime):
        day = datetime.day
        if day in self.dateDays:
            self.dateDays[day].add_temp(temp, temp_header, datetime)
            
    def get_data_table(self, temp_headers):
        list_days_tables = [dateDay.get_data_table(temp_headers) for dateDay in self.dateDays.values()]
        return sum(list_days_tables, [])

    def number_of_dates(self):
        return sum([dateDay.number_of_dates() for dateDay in self.dateDays.values()])
        
    def number_of_dates_without_load(self):
        return sum([dateDay.number_of_dates_without_load() for dateDay in self.dateDays.values()])

    def set_mean_temp(self, temp_header):
        for date_day in self.dateDays.values():
            date_day.set_mean_temp(temp_header)

class DateYear:
    def __init__(self, year):
        self.year = year
        self.dateMonths = {}
        
    def add_new_date(self, datetime):
        month = datetime.month
        
        if month not in self.dateMonths:
            self.dateMonths[month] = DateMonth(month)
            
        self.dateMonths[month].add_new_date(datetime)
          
    def add_load(self, load, datetime):
        month = datetime.month
        self.dateMonths[month].add_load(load, datetime)
        
    def add_temp(self, temp, temp_header, datetime):
        month = datetime.month
        if month in self.dateMonths:
            try:
                temp = float(temp)
                if not math.isnan(temp):
                    self.dateMonths[month].add_temp(temp, temp_header, datetime)
            except ValueError:
                pass
                    
    def get_data_table(self, temp_headers):
        list_of_months_tables = [dateMonth.get_data_table(temp_headers) for dateMonth in self.dateMonths.values()]
        return sum(list_of_months_tables, [])
    
    def number_of_dates(self):
        return sum([dateMonth.number_of_dates() for dateMonth in self.dateMonths.values()])
   
    def number_of_dates_without_load(self):
        return sum([dateMonth.number_of_dates_without_load() for dateMonth in self.dateMonths.values()])
    
    def set_mean_temp(self, temp_header):
        for date_month in self.dateMonths.values():
            date_month.set_mean_temp(temp_header)
    
class DateHandler:
    @staticmethod
    def get_years(str_dates):
        return functools.reduce(DateHandler.years_reducer, str_dates, {})
    
    @staticmethod
    def add_loads(str_dates, loads, years):
        for index, load in enumerate(loads):
            str_date = str_dates[index]
            datetime = DateHandler.str_to_datetime(str_date)
            year = datetime.year
            years[year].add_load(load, datetime)
            
    @staticmethod
    def add_temps(temp_days, temp_hours, temps, temp_header, years):
        for index, day in enumerate(temp_days):
            hour = int(temp_hours[index])/100 #1800 to 18
            datetime0 = DateHandler.str_day_to_datetime(day)
            temp = temps[index]
            
            datetime = datetime0 + dt.timedelta(hours=hour)
            year = datetime.year
            
            if year in years:
                years[year].add_temp(temp, temp_header, datetime)
                
    @staticmethod
    def set_mean_temp(temp_header, years):
        for year in years.values():
            year.set_mean_temp(temp_header)
                
    @staticmethod
    def get_data_table(date_years, temp_headers):
        list_of_years_tables = [date_year.get_data_table(temp_headers) for date_year in date_years.values()]
        return sum(list_of_years_tables, [])
    
    @staticmethod
    def number_of_dates(date_years):
        return sum([date_year.number_of_dates() for date_year in date_years.values()])
            
    @staticmethod
    def number_of_dates_without_load(date_years):
        return sum([date_year.number_of_dates_without_load() for date_year in date_years.values()])
            
    @staticmethod
    def years_reducer(years, str_date):
        datetime = DateHandler.str_to_datetime(str_date)
        year = datetime.year
        
        if year not in years:
            years[year] = DateYear(year)
            
        years[year].add_new_date(datetime)
        return years
        
    @staticmethod
    def str_to_datetime(str_date):
        return dt.datetime.strptime(str_date,'%d/%m/%Y %H:%M:%S')
    
    @staticmethod
    def str_day_to_datetime(str_date):
        return dt.datetime.strptime(str_date,'%d/%m/%Y')
    
#Load loads dateset
load_dataset = pd.read_csv('loads_by_hours.csv')
str_dates = load_dataset.iloc[1:, 0].values
loads = load_dataset.iloc[1:, 3].values

# Set Objects tree
print("Iniciado...")
date_years = DateHandler.get_years(str_dates)
print("Datas setadas...")
print("Número de Datas: "+ str(DateHandler.number_of_dates(date_years)))
print("Número de Datas sem carga: "+ str(DateHandler.number_of_dates_without_load(date_years)))
DateHandler.add_loads(str_dates, loads, date_years)
print("Cargas setadas...")
print("Número de Datas sem carga: "+ str(DateHandler.number_of_dates_without_load(date_years)))

# Load temps dateset
print("Carregando Temperaturas...")
files_names = os.listdir()
csv_names = list(filter(
        lambda file_name : '.csv' in file_name and 'loads_by_hours' not in file_name,
        files_names))
temp_datasets = [pd.read_csv(csv_name, sep=',') for csv_name in csv_names]

# Get each temp dataset
print("Setando temperaturas...")
for index, temp_dataset in enumerate(temp_datasets):
    temp_days = temp_dataset.iloc[1:, 0].values
    temp_hours = temp_dataset.iloc[1:, 1].values # 18:00 as 1800
    temps = temp_dataset.iloc[1:, 2].values
    temp_header = csv_names[index]
    
    DateHandler.add_temps(temp_days, temp_hours, temps, temp_header, date_years)
    print("Setado para: " + str(temp_header) + "(" + str(index + 1) + " de " + str(len(csv_names)) + ")...")

# Settings temperatures
print("Configurando temperaturas...")
DateHandler.set_mean_temp(csv_names, date_years)

# Get table
print("Obtendo tabela de dados...")
dataset = [["Data", "Dia da Semana", "Feriado", *csv_names, "Carga"], *DateHandler.get_data_table(date_years, csv_names)]

# Remove lines without content
print("Limpando dados...")
dataset = [line for line in dataset if "" not in line]

print("Salvando...")
mtx = np.array(dataset)
np.savetxt("dataset.csv", mtx, delimiter=";", fmt='%s')
print("Tudo Pronto!")
    
    
    
        