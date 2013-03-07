%module pyComm
 %{
  
#include "SerialInterface.h"
#include "SerialCommands.h"
 %}
#define __attribute__(x)

typedef struct ss
{
char resp;
int USS_arr[USS_NUM];
int USS_EDGE_arr[USS_EDGE_NUM];
int heading;
int servo_arr[SERVO_NUM];
char eol;		//use non-canonical?
}__attribute__((packed)) sensor_data;

class SerialCommands
{
    SerialInterface sp; //use new?
public:
sensor_data sd;
bool init(char *);
bool move(int heading,int distance); //heading in degrees, distance in cms
bool arm_rotate(int angle); //angle in degrees
bool get_sensor_data(void);


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


