#!/usr/bin/python3

import smbus
import os
import time
import socket
from datetime import datetime
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

### Configuracoes
# Verifique o endereco com 'sudo i2cdetect -y 1'
address = 0x48
# Entradas e sensores integrados
A0 = 0x40  # Sensor de luz RDL (Resistor Dependente de Luz) (Jumper P5)
A1 = 0x41  # Sensor de temperatura integrada (Jumper P4)
A2 = 0x42  # Entrada analógica normal (sem esteroide)
A3 = 0x43  # Potenciometro  (Jumper P6)
# for RPI version 1, use "bus = smbus.SMBus(0)"
bus = smbus.SMBus(1)
###

''' Lembretes
UMIDADE (Entrada A2 e A3) # Entrada analógica normal (sem esteroide)
	Em 5V
		Completamente seco = [249, 251]
		Completamente molhado ~= [35, 40]

	Em 3.3V
		Completamente seco = 255
		Completamente molhado ~= [12, 16] || [16, 22]

LUZ A0
	Bastante escuro (mas não escuridão total) >= ~225
	Sala com 9 luzes brancas fria = [145, 148]
	Flash muito forte = [24, 30]

Temperatura (medido com sensor DS18B20)
	18~19 C = 255??

#Volts = value * 3.3 / 255
'''

# Informacoes do host
dir_path = os.path.dirname(os.path.realpath(__file__))
hostname = socket.gethostname()

# Credenciais do Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(dir_path, 'secret_key.json'), scope)
client = gspread.authorize(creds)
# Abre um documeto (spreadsheet)
spreadsheet = client.open(hostname)

def log_local(row):
	try:
		with open(os.path.join(dir_path, 'log.csv'), 'a') as f:
			w = csv.writer(f)
			w.writerow(row)
	except Exception as e:
		print(e)
		print('Erro ao salvar dado em arquivo .csv')

def log_nuvem(row):
	# Todas as worksheets
	try:
		worksheet = spreadsheet.worksheet('dados-sensores')
		worksheet.append_row(['Luz', 'Temperatura', 'Umidade1', 'Umidade2'])
	except Exception as e:
		print(e)
		print('Erro ao abrir worksheet')

	try:
		worksheet.append_row(row)
	except Exception as e:
		print(e)
		print('Erro ao enviar dados para a nuvem')

def main():
	sensores = dict(
		zip(
			['Luz', 'Temperatura', 'Umidade1', 'Umidade2'],
			[A0, A1, A2, A3]
		)
	)

	for descricao, entrada in sensores.items():
		try:
			bus.write_byte(address, entrada)
			# Primeira amostra eh descartada (workaraound)
			bus.read_byte(address)
			# Leitura e ajuste empírico
			value = (bus.read_byte(address) - 275) * -1
			# data e hora, luz, temperatura, umidade1, umidade2
			row = [hora, dados['Luz'], dados['Temperatura'], dados['Umidade1'], dados['Umidade2']]
			log_local(row)
			print('{}  -> {}  \n'.format(descricao, value))
		except Exception as e:
			print(e)
			print('Erro ao ler entrada ', entrada)

if __name__ == '__main__':
	# TODO: loop apenas para demonstracao
	while True:
		main()
		time.sleep(2)