### Synchrophasor measurements

The plugin is designed to communicate with synchrophasor units that support IEEE C37.118 protocol. The plugin reads out synchrophasor measurements using the protocol through TCP/IP.

### Setup for Power Standards Lab's Micro PMU

The unit accepts ftp file transfer to update its configuration. To change configuration, set the following environment variables and run the updating script. The password in `FTP_CONFIG_PASSWORD` must be set in both the host device and the unit prior to the update (This can be done via the web service that the unit hosts).

```bash
# the variables by default
SETUP_INI_PATH=./Setup.ini
UPMU_ADDRESS="172.16.1.101"
FTP_CONFIG_PASSWORD=/wagglerw/waggle/upmu_ftp_password

./update_config_upmu.sh
```

### Data frame of the Micro PMU unit

Data frame transferred from the unit contains L1, L2, L3, C1, C2, and C3 angle as well as frequency and ROCOF.

```
## Reading Config Frame...
Type:  Config2
Vers:  1
SOC:  947199857  -  2000/01/06 17:04:17
75504D555F33002D6964636F64650031
STN: uPMU_3-idcode1
IDCODE_data:  1
FreqFmt:  FLOAT
AnlgFmt:  FLOAT
PhsrFmt:  FLOAT
PhsrFmt:  POLAR
PHNMR: 6
ANNMR: 0
DGNMR: 0
L1MagAng
L2MagAng
L3MagAng
C1MagAng
C2MagAng
C3MagAng
PHUNIT: VOLTAGE - 0
PHUNIT: VOLTAGE - 0
PHUNIT: VOLTAGE - 0
PHUNIT: CURRENT - 0
PHUNIT: CURRENT - 0
PHUNIT: CURRENT - 0
FNOM:  HZ60
CFGCNT:  0
```
