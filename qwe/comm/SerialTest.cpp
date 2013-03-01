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

int main(int argc, char *argv[])
{
    SerialCommands sc;
    cout<<sizeof(move_data)<<endl;
    cout<<sizeof(arm_rotate_data)<<endl;
    sc.init(argv[1]);
    sc.move(45,20);
    sc.arm_rotate(45);



}


