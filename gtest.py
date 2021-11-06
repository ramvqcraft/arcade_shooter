import RPi.GPIO as GPIO  
from time import sleep     # this lets us have a time delay (see line 12)  
GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering  
GPIO.setup(23, GPIO.IN)    # Joystick Vx RIGHT
GPIO.setup(24, GPIO.IN)    # Joystick Vx LEFT
GPIO.setup(20, GPIO.IN)    # Joystick Vy FOR
GPIO.setup(21, GPIO.IN)    # Joystick Vy BACK

counter = 0
  
try:  
    while True:            # this will carry on until you hit CTRL+C
        print(str(counter))
        if GPIO.input(23):  
            print (", Vx RIGHT " ) 
        elif GPIO.input(24):  
            print (", Vx LEFT " )
        elif GPIO.input(20):  
            print (", Vy FOR " )
        elif GPIO.input(21):  
            print (", Vy BACK " )             
            
        sleep(1)         # wait 0.1 seconds
        counter=counter+1
  
except KeyboardInterrupt:  
    GPIO.cleanup()         # clean up after yourself  
        