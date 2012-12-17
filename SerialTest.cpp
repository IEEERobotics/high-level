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

int main()
{
    SerialCommands sc;
    sc.init();
    sc.move(45,20);
    sc.arm_rotate(45);



}


