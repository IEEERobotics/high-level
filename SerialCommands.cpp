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

bool SerialCommands::init()
{

	char *devname;


    devname = (char *)malloc(10*sizeof(char));
    strcpy(devname,"/dev/ttyUSB0");

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
    if(sp.sendBuf((char *)&ard,(int)sizeof(ard))>0)
    return true;
    else
    return false;
    //wait to rcv ack
}
bool SerialCommands::get_state(int num) //number of samples to get
{
    get_sensor_data gsd;
    gsd.cmd = DATA_CMD_ID;
    gsd.num = num;
    if(sp.sendBuf((char *)&gsd,(int)sizeof(gsd))>0)
    return true;
    else
    return false;
}
