%module pyComm
 %{
 /* Put header files here or function declarations like below */
#include "SerialInterface.h"
#include "SerialCommands.h"
 %}

class SerialCommands
{
    SerialInterface sp; //use new?
public:

bool init(char *);
bool move(int heading,int distance); //heading in degrees, distance in cms
bool arm_rotate(int angle); //angle in degrees
bool get_sensor_data(sensor_data *);


};

class SerialInterface 
{
//constructor and destructor??

//make serial_dev_fd public?
int serial_dev_fd;
public:
bool openPort(char *devname); 						/*opens a device given by devname ex:"/dev/ttyS0"*/
bool init();
bool closePort();
bool sendByte(char b);				/*should return success or fail sending the byte*/
int sendBuf(char * sbptr,int nSend);			/*sends 'nSend' number of bytes starting from 'sbptr' , returns number of bytes sent*/ 
char getByte();					/*should return success or fail reading a byte*/
int getBuf(char* rbptr,int nRead);			/*reads 'nRead' bytes into rbptr, returns number of bytes read*/
   
};
