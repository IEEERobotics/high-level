/*
***************************************************************************
* Author: Bhanu Pulluri
* btpullur@ncsu.edu
***************************************************************************
* Serial port commands class for use by NCSU IEEE ground robotics team
***************************************************************************
*/

#include<iostream>
#include<stdio.h>
#include<stdlib.h>
#include<fcntl.h>
#include<unistd.h>
#include<string.h>
#include "SerialInterface.h"
#include "SerialCommands.h"

using namespace std;



//channels?

bool SerialCommands::init(char *portname)
{

	char *devname;


    devname = (char *)malloc(10*sizeof(char));
    //strcpy(devname,"/dev/ttyUSB0");
    strcpy(devname,portname);

    //open
	if(!sp.openPort(devname))
	return 0;

    //init
	return(sp.init());

}

bool SerialCommands::move(int heading,int distance) //heading in degrees, distance in cms
{
    move_data md;
    md.cmd = MOVE_CMD_ID;
    md.heading = heading;
    md.distance = distance;
    md.eol = '\n';
    if(sp.sendBuf((char *)&md,(int)sizeof(md))>0)
    return true;
    else
    return false;

    //wait to rcv ack

}
bool SerialCommands::arm_rotate(int angle) //angle in degrees
{
    arm_rotate_data ard;
    ard.cmd = ROTATE_CMD_ID;
    ard.angle = angle;
    ard.eol = '\n';
    if(sp.sendBuf((char *)&ard,(int)sizeof(ard))>0)
    return true;
    else
    return false;
    //wait to rcv ack
}
bool SerialCommands::get_sensor_data(sensor_data *sd) //number of samples to get
{
    sensor_data_cmd gsd;
    gsd.cmd = DATA_CMD_ID;
    gsd.eol='\n';
   // gsd.num = num;
    if(sp.sendBuf((char *)&gsd,(int)sizeof(gsd))>0)
    {
      sp.getBuf((char *)&sd,(int)sizeof(sd));
      return true;
    }
    else
    return false;
}


