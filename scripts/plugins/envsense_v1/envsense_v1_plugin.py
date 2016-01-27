class register(object):
    def __init__(self, name, man):
    	man[name] = 1
        sensor_read()

def sensor_read():
    import time, serial, sys, datetime, pprint
    sys.path.append('../waggle_protocol/')
    from utilities import packetmaker
    from send import send
    """
    This connects to a sensor board via a serial connection. It reads and parses the sensor data into meaningful information, packs, and sends the data packet to the cloud. 


    """

    print 'Beginning sensor script...'


    # TODO this sensor description is deprecated. See sensor hash below.
    Sensor_Index=["D6T_44L_06_1_T_C","MMA8452_1_A_X_Units","MMA8452_1_A_Y_Units",
               "MMA8452_1_A_Z_Units","MMA8452_1_A_RMS_Units","SHT15_1_T_C","SHT15_1_H_%","SHT75_1_T_C",
               "SHT75_1_H_%","MAX4466_1_Units","AMBI_1_Units","PhoRes_10K4.7K_Units","HIH4030_Units",
               "THERMIS_100K_Units","DS18B20_1_T_C","TMP421_1_T_C","RHT03_1_T_C","RHT03_1_H_%",
               "BMP_180_1_T_C","BMP_180_1_P_PA","TMP102_1_T_F","HIH_6130_1_T_C","HIH_6130_1_H_%",
               "MLX90614_T_F"]

    reading_names = [ ["Temperature",
                    "Temperature","Temperature","Temperature","Temperature",
                    "Temperature","Temperature","Temperature","Temperature",
                    "Temperature","Temperature","Temperature","Temperature",
                    "Temperature","Temperature","Temperature","Temperature"],
                     "Acceleration",
                     "Acceleration",
                     "Acceleration",
                     "Vibration",
                     "Temperature",
                     "Humidity",
                     "Temperature",
                     "Humidity",
                     "Acoustic_Intensity",
                     "Luminous_Intensity",
                     "Luminous_Intensity",
                     "Humidity",
                     "Temperature",
                     "Temperature",
                     "Temperature",
                     "Temperature",
                     "Humidity",
                     "Temperature",
                     "Pressure",
                     "Temperature",
                     "Temperature",
                     "Humidity",
                     "Temperature"]

    reading_type = [['f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f'],
                 'f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f','f']

    reading_unit = [["C","C","C","C","C","C","C","C","C","C","C","C","C","C","C","C","C"],
                 "g","g","g","g","C","%RH","C","%RH","Units10B0V5","Units10B0V5","Units10B0V5","Units10B0V5",
                 "Units10B0V5","C","C","C","%RH","C","PA","F","C","%RH","F"]

    reading_note = [["PTAT",
                    "1x1","1x2","1x3","1x4",
                    "2x1","2x2","2x3","2x4",
                    "3x1","3x2","3x3","3x4",
                    "4x1","4x2","4x3","4x4"],
                     "X",
                     "Y",
                     "Z",
                     "RMS_3Axis",
                     "",
                     "RH",
                     "", 
                     "RH",
                     "non-standard",
                     "non-standard",
                     "Voltage_Divider_5V_PDV_Tap_4K7_GND", 
                     "RH",
                     "Voltage_Divider_5V_NTC_Tap_68K_GND",
                     "",
                     "",
                     "",
                     "RH", 
                     "", 
                     "Barometric",
                     "",
                     "", 
                     "", 
                     ""]    

    sensor_array_index = [2,7,7,7,7,5,5,12,12,15,14,0,13,3,8,9,10,10,6,6,11,4,4,1]

    sensor_names = ["PDV_P8104.API.2006", "MLX90614ESF-DAA.Melexis.008-2013", "D6T-44L-06.Omron.2012", "Thermistor_NTC_PR103J2.US_Sensor.2003", 
         "HIH6130.Honeywell.2011", "SHT15.Sensirion.4_3-2010", "BMP180.Bosch.2_5-2013", "MMA8452Q.Freescale.8_1-2013", 
         "DS18B20.Maxim.2008", "TMP421.Texas_Instruments.2012", "RHT03.Maxdetect.2011", "TMP102.Texas_Instruments.2008", 
         "SHT75.Sensirion.5_2011", "HIH4030.Honeywell.2008", "GA1A1S201WP.Sharp.2007", "MAX4466.Maxim.1_2001"]
    
    

    # convert above tables into hash
    output2sensor={}

    sensors={}
    for i in range(len(Sensor_Index)):
     sensor_name=sensor_names[sensor_array_index[i]]
     if not sensor_name in sensors:
         sensors[sensor_name]={}

     s_output = Sensor_Index[i]
     print "s_output: ", s_output
     output2sensor[s_output]=sensor_name
     sensors[sensor_name][s_output]={}
     sensors[sensor_name][s_output]['measurement']=reading_names[i]
     sensors[sensor_name][s_output]['data_type']=reading_type[i]
     sensors[sensor_name][s_output]['unit']=reading_unit[i]
     sensors[sensor_name][s_output]['reading_note']=reading_note[i]


    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(sensors)




    try:
     while True:
         wxconnection = False
         while wxconnection == False:
             try:
                 #TODO change this if the serial port is different than the one specified
                 wxsensor = serial.Serial('/dev/ttyACM0',57600,timeout=300)
                 wxconnection = True
             except:
                 #Will not work if sensor board is not plugged in. 
                 #If sensor board is plugged in, check to see if it is trying to connect to the right port
                 #TODO may want to add a rule to the configuration to specify which port will be used.
                 print "Still waiting for connection... Is the sensor board plugged in?"
                 time.sleep(1)
         try:
             wxsensor.flushInput()
             wxsensor.flushOutput()
         except:
             wxsensor.close()
             wxconnection = False
         while wxconnection == True:
             time.sleep(1)
             try:
                 readData = ' '
                 readData=wxsensor.readline()
             except:
                 wxsensor.close()
                 wxconnection = False
             if len(readData) > 0 and wxconnection == True:
                 try:
                     sensorsData = readData.split(';')
                     if len(sensorsData) > 2:
                         sensorDataAvail = True
                     else:
                         sensorDataAvail = False
                 except:
                     sensorDataAvail = False

                 if sensorDataAvail == True:
                     if sensorsData[0] == 'WXSensor' and sensorsData[-1]=='WXSensor\r\n':
                    
                         timestamp_utc = datetime.datetime.utcnow()
                         timestamp_date = timestamp_utc.date()
                         timestamp_epoch =  int(float(timestamp_utc.strftime("%s.%f"))* 1000)
                    
                    
                         # extract sensor name    
                         output_array = sensorsData[1].split(':')
                         output_name = output_array[0]
                   
                    
                         try:
                             sensor_name = output2sensor[output_name]
                         except Exception as e:
                             print "Output %s unknown" % (output_name)
                             sensor_name = ''
                    
                         if sensor_name:
                             sendData=[str(timestamp_date), 'env_sense', '1', 'default', str(timestamp_epoch), sensor_name, "meta.txt", sensorsData[1:-1]]
                             print 'Sending data: ', str(sendData)
                             #packs and sends the data
                             packet = packetmaker.make_data_packet(sendData)
                             for pack in packet:
                                 send(pack)
                        
                            
                   
                    
    except KeyboardInterrupt, k:
     try:
         wxsensor.close()
     except: 
         pass


if __name__ == '__main__':
     sensor_read()
     
     
     
     