import os
import socket
import time
import struct
import pycom
import utime
from network import LoRa

# A basic package header, B: 1 byte for the deviceId, B: 1 byte for the pkg size
_LORA_PKG_FORMAT = "BB%ds"
_LORA_PKG_ACK_FORMAT = "BBB"
DEVICE_ID = 0x00
MODE = 0

MAX_PAYLOAD_LENGTH = 100


# Open a Lora Socket, use tx_iq to avoid listening to our own messages
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
def send_message():
    not_sent = True
    while(not_sent):
        # Package send containing a simple string
        msg = choose_message_to_send()
        pkg = struct.pack(_LORA_PKG_FORMAT % len(msg), SENDER_ID, len(msg), msg)
        print("Sending message: " + msg)
        pycom.rgbled(0x050505) 


        #Try 100000 times to receive the ack, if it doesn't it gives up
        i = 0
        while(i < 10):
            lora_sock.send(pkg)
            for j in range(500):
                time.sleep(0.01)
                recv_ack = lora_sock.recv(512)
                
                if (len(recv_ack) > 0):
                    print("received ack")
                    device_id, pkg_len, ack = struct.unpack(_LORA_PKG_ACK_FORMAT, recv_ack)
                    if (device_id == 1):
                        if (ack == 200):
                            pycom.rgbled(0x007f00) # green
                            not_sent = False
                            print("ACK")
                            i = 10
                            j=501
                            time.sleep(1)
                            
                        else:
                            pycom.rgbled(0x7f0000) # red
                            print("Message Failed")
                            i = 10
                            break
                else:
                    None
                    #time.sleep(0.01)
                i = i + 1

# Function to receive messages
def receive_msg(is_first):
    i = 0
    if(is_first):
        send_message()
    while True:
        pycom.rgbled(0x00ff00) 
        start_time = utime.ticks_ms()
        recv_pkg = lora_sock.recv(512)
        end_time = utime.ticks_ms()
        time_taken = utime.ticks_diff(end_time, start_time)
        
        #lacks checking if message is for this device
        if (len(recv_pkg) > 2):
            try:
                recv_pkg_len = recv_pkg[1]
                device_id, pkg_len, msg = struct.unpack(_LORA_PKG_FORMAT % recv_pkg_len, recv_pkg)
                if device_id==DEVICE_ID:
                    pycom.rgbled(0x007f00)
                    print("Received:", msg)
                    print("Dest: " , device_id)
                    print("Time to send: " + str(time_taken) + "ms")
                    pycom.rgbled(0x34bdeb)
                    ack_pkg = struct.pack(_LORA_PKG_ACK_FORMAT, 0x01, SENDER_ID, 200)
                    lora_sock.send(ack_pkg)
                    time.sleep(0.5)
                    if(choose_answer()):
                        send_message()
            except Exception as e:
                pycom.rgbled(0x7f0000)
                print("Error unpacking the received package: ", e)
                break
        else:
            print("Sniffing for some packets")
            time.sleep(1)

def choose_device_id():
    while True:
        DEVICE_ID = int(input("Choose a device id (1- 0x01, 2- 0x02):"))
        if(DEVICE_ID != 1 and DEVICE_ID != 2):
            pycom.rgbled(0x7f7f00) # yellow
            print("Invalid device id!")
        else:
            if(DEVICE_ID == 1):
                SENDER_ID = 2
            else:
                SENDER_ID = 1
            pycom.rgbled(0x007f00) # green
            return DEVICE_ID, SENDER_ID
        
def choose_mode():
    while True:
        MODE = int(input("Choose a mode (1- sending, 2- receiving):"))
        if(MODE != 1 and MODE != 2):
            pycom.rgbled(0x7f7f00) # yellow
            print("Invalid mode!")
        else:
            pycom.rgbled(0x007f00) # green
            return MODE

def choose_message_to_send():
    while True:
        msg = input("Choose a message (less than 100 chars)")
        if(len(msg) > MAX_PAYLOAD_LENGTH):
            pycom.rgbled(0x7f7f00) # yellow
            print("Invalid message size!")
        else:
            pycom.rgbled(0x007f00) # green
            return msg
        
def choose_answer():
    while True:
        answer_back = input("Do you want to answer? Y/N: ")
        if(answer_back != 'N' and answer_back != 'n' and answer_back != 'Y' and answer_back != 'y'):
            print("Invalid answer!")
            continue
        if(answer_back =='N' or answer_back == 'n'):
            return 0
        else:
            return 1

pycom.rgbled(0x007f00) # green
DEVICE_ID, SENDER_ID = choose_device_id()
if DEVICE_ID==1:
    lora = LoRa(mode=LoRa.LORA, tx_iq=True, region=LoRa.EU868)
if DEVICE_ID==2:
    lora = LoRa(mode=LoRa.LORA, rx_iq=True, region=LoRa.EU868)

lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

# Set common LoRa parameters
frequency = 868000000  # adjust based on your region
spreading_factor = 7
bandwidth = LoRa.BW_500KHZ

lora.frequency(frequency)
lora.bandwidth(bandwidth)
lora.sf(spreading_factor)

lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

# Set common LoRa parameters
frequency = 868000000  # adjust based on your region
spreading_factor = 7
bandwidth = LoRa.BW_500KHZ

lora.frequency(frequency)
lora.bandwidth(bandwidth)
lora.sf(spreading_factor)

while True:
    MODE = choose_mode()

    if(MODE == 1):
        while True:
            receive_msg(1)
    else:
        print("Entered else")
        receive_msg(0)