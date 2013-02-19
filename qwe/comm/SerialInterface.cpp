/*
***************************************************************************
* Author: Bhanu Pulluri
* btpullur@ncsu.edu
***************************************************************************
* Defines serial port interface class for use by NCSU IEEE ground robotics team
***************************************************************************
*/

#include<iostream>
#include "SerialInterface.h"
extern "C"
{
#include<stdio.h>
#include<fcntl.h>
#include<unistd.h>
#include<termios.h>
}

using namespace std;



bool SerialInterface::openPort(char *devname)
{
	serial_dev_fd=-1;


	serial_dev_fd = open(devname, O_RDWR | O_NOCTTY | O_NDELAY);
	if (serial_dev_fd == -1) /*port open fail*/
	{
		cout<<"open_port: Unable to open given port - ";
		return false;
	}
	else
	{
		fcntl(serial_dev_fd, F_SETFL, 0);
		cout<<"open_port: success\n ";


	}


	return true;
}
bool SerialInterface::init()
{
	//port settings

	struct termios s_config;

tcflush(serial_dev_fd, TCIOFLUSH); // flush both input and output

	if(tcgetattr(serial_dev_fd, &s_config) < 0)
{
cout<<"couldn't get port attributes. Config not done\n";
return false; // shd return -1?
}
else
{

        s_config.c_iflag=0;
        s_config.c_oflag=0;
        s_config.c_cflag=0;
        s_config.c_lflag=0;

	//set baud to 115200
	if(cfsetispeed(&s_config, B115200) < 0 || cfsetospeed(&s_config, B115200) < 0) {
	    cout<<"couldn't set baud rate. Config not done\n";
	return false; // shd return -1?;
	}
// no parity, one stopbit, 8 bits

	s_config.c_cflag &= ~PARENB;    //not req
	s_config.c_cflag |= CSTOPB;
	s_config.c_cflag |= CS8;

//mode of operation

	//SETTING not REQUIRED. Already zero
	s_config.c_lflag &= ~ICANON; //set mode to non canonical .. sends data without waiting for return character and no input processing is done

	s_config.c_cc[VTIME]=0; //use value for timeout and lock prevention
	s_config.c_cc[VMIN]=1; //min number of bytes to be received before read is done?

//flow control?

//mode.. canonical, non..?

		if(tcsetattr(serial_dev_fd, TCSANOW, &s_config))
	{
		cout<<"couldn't apply config. Config not done\n";
		return false; // shd return -1 on fail?
	}

	return true;
}
}
bool SerialInterface::closePort()
{
	if(close(serial_dev_fd))
	return true;
	else
	return false;
}
bool SerialInterface::sendByte(char b)
{
	//check if open?
	if(write(serial_dev_fd,&b,1)==1)
	return(true);
	else
	return false;
}
int SerialInterface::sendBuf(char* sbptr,int nSend)
{
	//check for buffer overflow?
	return(write(serial_dev_fd,sbptr,nSend));
}
char SerialInterface::getByte()
{
	char c;
	if(read(serial_dev_fd, &c, 1)==1)
	return c;
	else
	return 0;
}
int SerialInterface::getBuf(char* rbptr,int nRead)
{

	int n;
	n = read(serial_dev_fd, rbptr, nRead);
	tcflush(serial_dev_fd, TCIOFLUSH);
	return n;
}



