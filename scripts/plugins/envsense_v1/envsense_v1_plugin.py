import time, serial, sys, datetime, pprint
sys.path.append('../waggle_protocol/')
from utilities import packetmaker
from send import send


class register(object):
    def __init__(self, name, man):
    	man[name] = 1
        sensor_read()


def process_data(output2sensor, data):
    sensorDataAvail = False
    if len(readData) > 0:
        try:
            sensorsData = readData.split(';')
            if len(sensorsData) > 2:
                sensorDataAvail = True
            
        except:
            pass

    if not sensorDataAvail:
        print "Data empty or format wrong"
        return
        
    if not (sensorsData[0] == 'WXSensor' and sensorsData[-1]=='WXSensor\r\n'):
        print "Format wrong, WXSensor keywords missing"
        return

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
        return

    
    sendData=[str(timestamp_date), 'env_sense', '1', 'default', str(timestamp_epoch), sensor_name, "meta.txt", sensorsData[1:-1]]
    print 'Sending data: ', str(sendData)
    #packs and sends the data
    packet = packetmaker.make_data_packet(sendData)
    for pack in packet:
        try:
            send(pack)
        except Exception as e:
            print "Exception sending pack: "+str(e)
            raise
                    

def sensor_read():
    
    """
    This connects to a sensor board via a serial connection. It reads and parses the sensor data into meaningful information, packs, and sends the data packet to the cloud. 


    """

    print 'Beginning sensor script...'

    sensors = {   'BMP180.Bosch.2_5-2013': {   'BMP_180_1_P_PA': {   'data_type': 'f',
                                                           'measurement': 'Pressure',
                                                           'reading_note': 'Barometric',
                                                           'unit': 'PA'},
                                     'BMP_180_1_T_C': {   'data_type': 'f',
                                                          'measurement': 'Temperature',
                                                          'reading_note': '',
                                                          'unit': 'C'}},
        'D6T-44L-06.Omron.2012': {   'D6T_44L_06_1_T_C': {   'data_type': [   'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f',
                                                                              'f'],
                                                             'measurement': [   'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature',
                                                                                'Temperature'],
                                                             'reading_note': [   'PTAT',
                                                                                 '1x1',
                                                                                 '1x2',
                                                                                 '1x3',
                                                                                 '1x4',
                                                                                 '2x1',
                                                                                 '2x2',
                                                                                 '2x3',
                                                                                 '2x4',
                                                                                 '3x1',
                                                                                 '3x2',
                                                                                 '3x3',
                                                                                 '3x4',
                                                                                 '4x1',
                                                                                 '4x2',
                                                                                 '4x3',
                                                                                 '4x4'],
                                                             'unit': [   'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C',
                                                                         'C']}},
        'DS18B20.Maxim.2008': {   'DS18B20_1_T_C': {   'data_type': 'f',
                                                       'measurement': 'Temperature',
                                                       'reading_note': '',
                                                       'unit': 'C'}},
        'GA1A1S201WP.Sharp.2007': {   'AMBI_1_Units': {   'data_type': 'f',
                                                          'measurement': 'Luminous_Intensity',
                                                          'reading_note': 'non-standard',
                                                          'unit': 'Units10B0V5'}},
        'HIH4030.Honeywell.2008': {   'HIH4030_Units': {   'data_type': 'f',
                                                           'measurement': 'Humidity',
                                                           'reading_note': 'RH',
                                                           'unit': 'Units10B0V5'}},
        'HIH6130.Honeywell.2011': {   'HIH_6130_1_H_%': {   'data_type': 'f',
                                                            'measurement': 'Humidity',
                                                            'reading_note': '',
                                                            'unit': '%RH'},
                                      'HIH_6130_1_T_C': {   'data_type': 'f',
                                                            'measurement': 'Temperature',
                                                            'reading_note': '',
                                                            'unit': 'C'}},
        'MAX4466.Maxim.1_2001': {   'MAX4466_1_Units': {   'data_type': 'f',
                                                           'measurement': 'Acoustic_Intensity',
                                                           'reading_note': 'non-standard',
                                                           'unit': 'Units10B0V5'}},
        'MLX90614ESF-DAA.Melexis.008-2013': {   'MLX90614_T_F': {   'data_type': 'f',
                                                                    'measurement': 'Temperature',
                                                                    'reading_note': '',
                                                                    'unit': 'F'}},
        'MMA8452Q.Freescale.8_1-2013': {   'MMA8452_1_A_RMS_Units': {   'data_type': 'f',
                                                                        'measurement': 'Vibration',
                                                                        'reading_note': 'RMS_3Axis',
                                                                        'unit': 'g'},
                                           'MMA8452_1_A_X_Units': {   'data_type': 'f',
                                                                      'measurement': 'Acceleration',
                                                                      'reading_note': 'X',
                                                                      'unit': 'g'},
                                           'MMA8452_1_A_Y_Units': {   'data_type': 'f',
                                                                      'measurement': 'Acceleration',
                                                                      'reading_note': 'Y',
                                                                      'unit': 'g'},
                                           'MMA8452_1_A_Z_Units': {   'data_type': 'f',
                                                                      'measurement': 'Acceleration',
                                                                      'reading_note': 'Z',
                                                                      'unit': 'g'}},
        'PDV_P8104.API.2006': {   'PhoRes_10K4.7K_Units': {   'data_type': 'f',
                                                              'measurement': 'Luminous_Intensity',
                                                              'reading_note': 'Voltage_Divider_5V_PDV_Tap_4K7_GND',
                                                              'unit': 'Units10B0V5'}},
        'RHT03.Maxdetect.2011': {   'RHT03_1_H_%': {   'data_type': 'f',
                                                       'measurement': 'Humidity',
                                                       'reading_note': 'RH',
                                                       'unit': '%RH'},
                                    'RHT03_1_T_C': {   'data_type': 'f',
                                                       'measurement': 'Temperature',
                                                       'reading_note': '',
                                                       'unit': 'C'}},
        'SHT15.Sensirion.4_3-2010': {   'SHT15_1_H_%': {   'data_type': 'f',
                                                           'measurement': 'Humidity',
                                                           'reading_note': 'RH',
                                                           'unit': '%RH'},
                                        'SHT15_1_T_C': {   'data_type': 'f',
                                                           'measurement': 'Temperature',
                                                           'reading_note': '',
                                                           'unit': 'C'}},
        'SHT75.Sensirion.5_2011': {   'SHT75_1_H_%': {   'data_type': 'f',
                                                         'measurement': 'Humidity',
                                                         'reading_note': 'RH',
                                                         'unit': '%RH'},
                                      'SHT75_1_T_C': {   'data_type': 'f',
                                                         'measurement': 'Temperature',
                                                         'reading_note': '',
                                                         'unit': 'C'}},
        'TMP102.Texas_Instruments.2008': {   'TMP102_1_T_F': {   'data_type': 'f',
                                                                 'measurement': 'Temperature',
                                                                 'reading_note': '',
                                                                 'unit': 'F'}},
        'TMP421.Texas_Instruments.2012': {   'TMP421_1_T_C': {   'data_type': 'f',
                                                                 'measurement': 'Temperature',
                                                                 'reading_note': '',
                                                                 'unit': 'C'}},
        'Thermistor_NTC_PR103J2.US_Sensor.2003': {   'THERMIS_100K_Units': {   'data_type': 'f',
                                                                               'measurement': 'Temperature',
                                                                               'reading_note': 'Voltage_Divider_5V_NTC_Tap_68K_GND',
                                                                               'unit': 'Units10B0V5'}}}

    

    # convert above tables into hash
    output2sensor={}
    for sensor in sensors:
    	for output in sensors[sensor]:
    		output2sensor[output]=sensor
            

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
                continue
                
            while wxconnection == True:
                time.sleep(1)
                try:
                    readData = ' '
                    readData=wxsensor.readline()
                except Exception as e:
                    print "wxsensor.readline failed: "+str(e)
                    wxsensor.close()
                    wxconnection = False
                    break
                try:     
                    process_data(output2sensor, readData)
                except Exception as e:
                    print "process_data failed: "+ str(e)
                    break
                        
                            
                   
                        
    except KeyboardInterrupt, k:
        try:
             wxsensor.close()
        except: 
             pass
    except Exception as e:
        print "Exception: "+str(e)
        


if __name__ == '__main__':
     sensor_read()
     
     
     
     