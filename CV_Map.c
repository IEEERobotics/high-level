/*
 ===========================================================================================
 Name        : CV_Map.c
 Author      : Ricker
 Version     :
 Copyright   :
 Description :

 Map of playing field with simple interface to individually check tiles.

 I have increased the width and length of the map to map the actual distances of the ramps
 on to the 2-D map so that no angle calculations are required to calculate the distances of
 the ramps during real time.  To compensate, widths of the walls have been adjusted to ensure
 that the playing field dimensions are preserved (walls along length and width of ground level
 do not have the same thickness). Alternatively, the flat distances could be mapped and the
 actual distance of the ramp could be calculated from the angle during real time.

 There has been a problem of using to much memory for the map array in this program.  By changing
 the data types in variables in TileProp struct from int to short and Bool, the map is now able
 to handle 8 tiles per inch. The goal was to have 16 tiles per inch to not lose any resolution from the
 actual course map (If 16 is used the way it is now seg fault occurs).  Since this is
 the static map, I have commented out the struct elements color and status to try to
 preserve memory but this was not enough to make 16 tiles per inch possible. It may be that 8
 tiles per inch is good enough.  Suggestions for improving the program to increase resolution
 where to use malloc, some system of pointers, or code the map directly in CV.

 Note that there still needs to be some way to visualize the code in this program to ensure that
 it has been coded properly.
 ============================================================================================
 */

#include <stdio.h>
#include <stdlib.h>
//#include <math.h>

int main(){

	struct TileProp
	{
		short type;	//driving surface (0), start (1), storage (2), land (3), sea (4), air(5), marker/white lines (7), wall (8)
		//_Bool status; //empty (0), filled (1)	// if status and color are uncommented the check tile interface will have to be fixed
		//short color; //unknown(0) blue(1), black(2), green(3), yellow (4), red(5), brown (6), white(7)
		short level; //ground (0), ramp (1), lower platform (2), upper platform (3)
		_Bool path; // not path (0) path (1)  //this element was suggested for implementing a path for the bot to stay on
	};

	//double cmPerIn = 2.54;
	int tileSize = 8; // tiles per in
	int width = 97.4375*tileSize;	// width in tiles course width (in. * tiles per in)
									//width is the distance from the edge of upper platform to the edge of lower platform
									// 24 + 24 + 49.4375 = 97.4375
	int length = 73.75*tileSize;  	// length in tiles course length (in. * tiles per in)
									//length is the distance from the edge of upper platform to edge of ground level where start area is


	struct TileProp map[length][width];	//make map of tiles

	//loop variables
	int i;
	int j;
	int k;
	int m;
	//variables for tile check
	char ans1 = 'y';
	int row = 0;
	int col = 0;

	int upPltW = 24*tileSize;			//Upper platform width
	int upPltL = 24*tileSize;			//Upper platform length
	int upRmpW = 49.4375*tileSize;		//upper ramp width
	int upRmpL = 24*tileSize;			//upper ramp length
	int loPltW = 24*tileSize;			//lower platform width
	int loPltL = 24*tileSize;			//lower platform length
	int loRmpW = 24*tileSize;			//lower ramp width
	int loRmpL = 24.75*tileSize;		//lower ramp length
	int fatWall = 1.125 *tileSize;		// the thicker wall, on the east and west sides of course
	int skinnyWall = .98675*tileSize;	// the thinner wall, on north and south sides of course
	int whiteLine = 0.5 * tileSize;		//thickness of white lines
	int startW = 12 * tileSize;			//start square width
	int startL = 12 * tileSize;			//start square length


	for (i = 0; i < length; i++)  //general initialization for entire board
	{
		for (j = 0; j < width; j++)
		{
			//map[i][j].status = 0; //define all areas as empty
			map[i][j].path = 0;	//define entire area as not path
			//map[i][j].color = 2; //define as black
			map[i][j].type = 0; //define all area as driving surface
			map[i][j].level = 0; //define all area as ground
		}
	}

	for (i = 0; i < upPltL; i++) // define upper platform
	{
			for (j = 0; j < upPltW; j++)
			{
				map[i][j].level = 3; //define area as upper platform
			}
	}

	for (i = 0; i < upRmpL; i++) //define upper ramp

		for (j = upPltW - 1; j < (width - loPltW - 1); j++)
		{
			map[i][j].level = 1; //define area as ramp
		}

	for (i = 0; i < loPltL; i++) // define lower platform
	{
			for (j = width - 1 - loPltW; j < width; j++)
			{
				map[i][j].level = 2;  //define as lower platform
			}
	}

	for (i = loPltL - 1; i < (loPltL + loRmpL); i++) //define lower ramp
	{
		for (j = (width - 1 - loRmpW); j < width; j++)
		{
			map[i][j].level = 1;  //define as ramp
		}
	}

	//walls
	for (i = (length - skinnyWall - 1); i < length; i++)	//define long wall along width of course (south side)
	{
		for (j = 0; j < width; j++)
		{
			map[i][j].type = 8;	//define as wall
		}
	}

	for (i = upPltL - 1; i < upPltL + skinnyWall; i++)	//define short wall along width of course (north side)
	{
		for (j = 0; j < upPltW + upRmpW; j++)
		{
			map[i][j].type = 8;	//define as wall
		}
	}

	for (i = upPltL - 1; i < length; i++)	//define long wall along length of course (west side)
	{
		for (j = 0; j < fatWall; j++)
		{
			map[i][j].type = 8;	//define as wall
		}
	}

	for (i = loPltL + loRmpL; i < length; i++)	//define short wall along length of course (east side)
	{
		for (j = width - fatWall - 1; j < width; j++)
		{
			map[i][j].type = 8;	//define as wall
		}
	}

	// start area
	for (i = length - 1 - skinnyWall - startL - whiteLine ; i < length - skinnyWall; i++)  	//define white outline of start area
	{																						// this loop includes the actual start area
		for (j = fatWall; j < fatWall + startW + whiteLine; j++)							// next loop will fix the enclosed start area
		{
			map[i][j].type = 7; //define as marker/white lines
			//map[i][j].color = 7; //define as white
		}
	}

	for (i = length - 1 - skinnyWall - startL; i < length - skinnyWall; i++)	// fix enclosed start area
	{
		for (j = fatWall; j < fatWall + startW; j++)
		{
			map[i][j].type = 1; //define as start
			//map[i][j].color = 2;  //define as black
		}
	}

	//air loading zone
	for (i = 8.75*tileSize - 1; i < (24 - 8.75)*tileSize; i++) 	//define white outline of air storage
										// this loop includes actual air dropoff area, next loop will fix the dropoff area
	{									// loop after that will take care of white line separating each indiv storage area
		for(j = 0; j < 3.5*tileSize; j++)
		{
			map[i][j].type = 7; //define as marker/white lines
			//map[i][j].color = 7; //define as white
		}
	}

	for (i = (8.75+0.5)*tileSize -1; i < (24-8.75-0.5)*tileSize; i++) 	//fix enclosed air storage space
	{
		for(j = 0; j < 3*tileSize; j++)
		{
			map[i][j].type = 5;	//define as air
			//map[i][j].color = 0; //define as unknown color
		}
	}

	for(i = (8.75+0.5+2.5)*tileSize - 1; i < 0.5*tileSize; i ++) //make separating line between adjacent air storage spaces
	{
		for (j = 0; j < 3.5*tileSize; j++)
		{
			map[i][j].type = 7; //define as marker/white lines
			//map[i][j].color = 7; //define as white
		}
	}

// storage area
	for (i = upPltL + skinnyWall - 1; i < upPltL + skinnyWall + 6.5*tileSize; i++)	//define white outline of cargo storage
	{																		// this loop includes actual storage area, next loop will fix the storage area
																			// loop after that will take care of white line separating each indiv storage area
		for (j = fatWall+ 14.875*tileSize -1; j < fatWall + (14.875+ 42.5)*tileSize; j++)
		{
			map[i][j].type = 7; //define as marker/white lines
			//map[i][j].color = 7; //define as white
		}
	}

	k = 0;
	m = fatWall + (14.875+3)*tileSize;
	while(k<=12)					// fix enclosed storage area
	{
		m = m + 3*tileSize*k;
		for(i = upPltL + skinnyWall -1; i < upPltL + skinnyWall + 6*tileSize; i++)
		{
			for (j = m-1 ; j < m + 2.5*tileSize; j++)
			{
				map[i][j].type = 2;		//type is storage
				//map[i][j].color = 0;	//color is unknown
			}
		}
		k = k + 1;
	}
	/*
	for (i = upPltL + skinnyWall - 1; i < upPltW + skinnyWall + 6*tileSize; i++)	//fix enclosed storage area
	{
		for (j = fatWall+(14.875+0.5)*tileSize - 1; j < (14.875+14*0.5+14*2.5)*tileSize; j++)
		{
			map[i][j].type = 2;	//define as storage
			//map[i][j].color = 0; //define as unknown color
		}
	}

	j = fatWall + (14.875+0.5+2.5)*tileSize - 1;			//make separating white lines in storage area
	k = fatWall + (14.875+14*0.5+14*2.5)*tileSize;
	for (i = upPltL + skinnyWall - 1; i < upPltL + skinnyWall + 6.5*tileSize; i++)
	{
		while (j < k)
		{
			map[i][j].type = 7;	//define as marker
			//map[i][j].color = 7;	//define as white color
			j = j + 3*tileSize;
		}
	}
	*/

	//sea loading zone
	for (i = upPltL+skinnyWall+8.25*tileSize-1; i < length-skinnyWall-(12.5+8.25)*tileSize; i++) 	//define white outline of sea storage
										// this loop includes actual sea dropoff area, next loop will fix the dropoff area
	{
		for(j = 0; j < 4.5*tileSize; j++)
		{
			map[i][j].type = 7; //define as marker/white lines
			//map[i][j].color = 7; //define as white
		}
	}

	k = 0;
	m = upPltL + skinnyWall + (8.25+3)*tileSize;
	while(k <= 4)
	{
		for (i = m-1; i < m + 2.5*tileSize; i++);
		{
			for(j = fatWall -1; j < fatWall + 4*tileSize; j++)
				map[i][j].type = 4; //define as sea
				//map[i][j].color = 0; //define as unknown
		}
		k = k + 1;
	}


	/*
	for (i = upPltL+skinnyWall+8.75*tileSize; i < length-skinnyWall-(12.5+8.75)*tileSize; i++) 	//fix enclosed air storage space
	{
		for(j = 0; j < 4*tileSize; j++)
		{
			map[i][j].type = 4;	//define as sea
			//map[i][j].color = 0; //define as unknown color
		}
	}

	i = upPltL+skinnyWall+(8.25+3)*tileSize - 1;			//make separating white lines in storage area
	k = length - skinnyWall - (12.5+8.25+.5)*tileSize;
	while (i < k)
	{
		for (j = fatWall - 1; j < fatWall + 4.5*tileSize; j++)
		{
			//map[i][j].color = 7;
			map[i][j].type = 7;
		}
		i = i + 3*tileSize;
	}
	*/

	//land loading zone
	for (i = length-skinnyWall-5.5*tileSize - 1; i < length - skinnyWall; i++)	//define white outline of land storage
	{																		// this loop includes actual land area, next loop will fix the storage area

		for (j = fatWall+(12.5+32.25)*tileSize-1; j < width - fatWall - 32.25*tileSize; j++)
		{
			map[i][j].type = 7; //define as marker/white lines
			//map[i][j].color = 7; //define as white
		}
	}

	k = 0;
	m = fatWall + (12.5+32.25+3)*tileSize;
	while(k<=4)		// fix enclosed land storage area
	{
		m = m + 3*tileSize*k;
		for(i = length - fatWall - 5*tileSize; i < length - fatWall; i++)
		{
			for (j = m-1 ; j < m + 2.5*tileSize; j++)
			{
				map[i][j].type = 3;		//type is land
				//map[i][j].color = 0;	//color is unknown
			}
		}
		k = k + 1;
	}

	// short checking loop, still need some sort of visualization to confirm map
	printf("Want to check the properties of a tile? (y/n)\n");
	scanf("%c", &ans1);
	while(ans1 != 'n')
	{
		printf("fyi map[0][0] is the corner of the upper most platform");
		printf("enter the row number as a positive int.\n");
		scanf("%d", &row);
		printf("enter the column number as a positive int. \n");
		scanf("%d", &col);
		if ((row < 0) || (col < 0))
		{
			printf("please enter positive values");
			continue;
		}
		if ((row < length) && (col < width))
		{
				printf("map[row][col].type = %d.\n"
				//"map[row][col].status = %d.\n"
				//"map[row][col].color = %d.\n"
				"map[row][col].level = %d.\n"
				"map[row][col].path = %d.\n", map[row][col].type, /*map[row][col].status, map[row][col].color,*/ map[row][col].level, map[row][col].path);
		}
		else
		{
			printf("the coordinate does not exist.\n");
		}
		printf("Would you like to check another tile? (y/n)\n");
		scanf("%c", &ans1);
	}
	printf("goodbye\n");


	return 0;
}
