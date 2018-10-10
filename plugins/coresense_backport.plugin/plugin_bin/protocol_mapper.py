from waggle.protocol.v5.decoder import decode_frame

table = {
    'metsense_tmp112': (0x0001, 0x01),
    'metsense_htu21d_temperature': (0x0002, 0x01),
    'metsense_htu21d_humidity': (0x0002, 0x02),
    'metsense_hih4030_humidity': (0x0003, 0x01),
    'metsense_bmp180_temperature': (0x0004, 0x01),
    'metsense_bmp180_pressure': (0x0004, 0x02),
    'metsense_pr103j2_temperature': (0x0005, 0x01),
    'metsense_tsl250rd_light': (0x0006, 0x01),
    'metsense_mma8452q_acc_x': (0x0007, 0x01),
    'metsense_mma8452q_acc_y': (0x0007, 0x02),
    'metsense_mma8452q_acc_z': (0x0007, 0x03),
    'metsense_spv1840lr5h-b': (0x0008, 0x01),
    'metsense_tsys01_temperature': (0x0009, 0x01),
    'lightsense_hmc5883l_hx': (0x000a, 0x01),
    'lightsense_hmc5883l_hz': (0x000a, 0x02),
    'lightsense_hmc5883l_hy': (0x000a, 0x03),
    'lightsense_hih6130_temperature': (0x000b, 0x01),
    'lightsense_hih6130_humidity': (0x000b, 0x02),
    'lightsense_apds_9006_020_light': (0x000c, 0x01),
    'lightsense_tsl260_light': (0x000d, 0x01),
    'lightsense_tsl250_light': (0x000e, 0x01),
    'lightsense_mlx75305': (0x000f, 0x01),
    'lightsense_ml8511': (0x0010, 0x01),
    'lightsense_tmp421': (0x0011, 0x01),
    'chemsense_config': None,
    'chemsense_raw': (0x0110, 0x01),
    'alpha_status': None,
    'rg3_onset_rain': None,
    '5te_soil_dielectric': None,
    '5te_soil_conductivity': None,
    '5te_soil_temperature': None,
    'alpha_histo': None,
    'alpha_serial': None,
    'alpha_firmware': None,
    'alpha_config': None,
    'pms7003_header': None,
    'pms7003_frame_length': None,
    'pms7003_pm1_cf1': None,
    'pms7003_pm25_cf1': None,
    'pms7003_pm10_cf1': None,
    'pms7003_pm1_atm': None,
    'pms7003_pm25_atm': None,
    'pms7003_pm10_atm': None,
    'pms7003_point_3um_particle': None,
    'pms7003_point_5um_particle': None,
    'pms7003_1um_particle': None,
    'pms7003_2_5um_particle': None,
    'pms7003_5um_particle': None,
    'pms7003_10um_particle': None,
    'pms7003_version': None,
    'pms7003_error_code': None,
    'pms7003_check_sum': None,
}


def map_v1_to_v2(datagram_v1):
    decoded_message = decode_frame(datagram_v1)

    for values in decoded_message.values():
        for key, value in values.items():
            try:
                sensor_id, parameter_id = table[key]
            except Exception:
                print('unmatched measurement', key)
                continue

            yield {
                'sensor_id': sensor_id,
                'parameter_id': parameter_id,
                'value': value,
            }
