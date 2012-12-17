/*
***************************************************************************
* Author: Bhanu Pulluri
* btpullur@ncsu.edu
***************************************************************************
* Defines structures and enums for mc communication protocol
***************************************************************************
*/

#define USS_NUM 4
#define SERVO_NUM 5
#define USS_EDGE_NUM 4;

/**command and response ids**/

#define MOVE_CMD_ID 0x01
#define ROTATE_CMD_ID 0x02
#define DATA_CMD_ID 0x03
#define SENSOR_RESP_ID 0x04
#define ASYNC_RESP_ID   0x05

/*ACK for each command*/
#define MOVE_ACK_ID 0x06
#define ROTATE_ACK_ID 0x07



/**command structures**/
/*commands and data put into as tructure*/
typedef struct move_data
{
    char cmd;
    int heading; //heading in degrees with respect to the arena reference frame?
    int distance;  //distance to move in cms
} move_data;

typedef struct arm_rotate_data
{
    char cmd;
    int angle; //angle to rotate in degrees

} arm_rotate_data;

typedef struct get_sensor_data
{
    char cmd;
    int num;        //number of samples to receive
}get_sensor_data;

/*define structures to receive*/
struct ss
{
char resp;
int USS_arr[USS_NUM];
int heading;
int servo_arr[SERVO_NUM];
};/*__attribute_packed__;*/
typedef struct ss sensor_values;


/*async response struct for fall detection**/
struct async
{

char resp;
int USS_arr[4];
};

typedef struct async async;


class SerialCommands
{
    SerialInterface sp; //use new?
public:
bool init();
bool move(int heading,int distance); //heading in degrees, distance in cms
bool arm_rotate(int angle); //angle in degrees
bool get_state(int num); //number of samples to get

};



