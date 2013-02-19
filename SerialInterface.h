/*
***************************************************************************
* Author: Bhanu Pulluri
* btpullur@ncsu.edu
***************************************************************************
* Declares serial port class for use by NCSU IEEE ground robotics team
***************************************************************************
*/
#ifndef SERIAL_H
#define SERIAL_H
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

#endif



