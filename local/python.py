#include "libschsat.h"


void take_data(uint16_t data11, uint16_t data12, uint16_t data21, uint16_t data22, uint16_t data31, uint16_t data32, uint16_t data41, uint16_t data42){
	
	const int num1=3, num2=4,num3=2,num4=1;
	
	if(LSS_OK==sun_sensor_request_raw(num1, &data11, &data12)){ 
		printf("Sensor 1: %d\n", data11);
	}
	else{
		printf("fail\n");
	}
	
	if(LSS_OK==sun_sensor_request_raw(num2, &data21, &data22)){
		printf("Sensor 2: %d\n", data21);
	}
	else{
		printf("fail\n");
	}

	if(LSS_OK==sun_sensor_request_raw(num3, &data31, &data32)){
		printf("Sensor 3: %d\n", data31);
	}
	else{
		printf("fail\n");

		}
	
	if(LSS_OK==sun_sensor_request_raw(num4, &data41, &data42)){
		printf("Sensor 4: %d\n", data41);
	}
}


void rotate_left(uint16_t rdata11, uint16_t rdata12, uint16_t rdata21, uint16_t rdata22, uint16_t rdata31, uint16_t rdata32, uint16_t rdata41, uint16_t rdata42){
	uint16_t temp_data=rdata11-10;
	int const num=1;
	int16_t temp_rt=0;
	uint16_t max_luminosity=60000;
	
	motor_turn_on(num);
	
	Sleep(1);
 	
	
	if(LSS_OK==motor_set_speed(num, -1500, &temp_rt)){
		printf("Motor speed = 500\n");
		
	}  
	take_data(rdata11, rdata12, rdata21, rdata22, rdata31, rdata32, rdata41, rdata42);
	printf("RData11=%d, max_luminosity =%d temp_data = %d", rdata11, max_luminosity, temp_data);
	while((rdata11<max_luminosity)&&(temp_data<rdata11))
	{
		Sleep(1);	
		take_data(rdata11, rdata12, rdata21, rdata22, rdata31, rdata32, rdata41, rdata42);
		temp_data=rdata11;
		printf("Temp data = %d", temp_data);
	}
	if(LSS_OK==motor_set_speed(num, 0, &temp_rt)){
		printf("Motor speed = 0\n");
		
	}    
	printf("Done\n");
	motor_turn_off(num);
}
void rotate_right(uint16_t rdata11, uint16_t rdata12, uint16_t rdata21, uint16_t rdata22, uint16_t rdata31, uint16_t rdata32, uint16_t rdata41, uint16_t rdata42){
	uint16_t temp_data=rdata11-10;
	int const num=1;
	int16_t temp_rt=0;
	uint16_t max_luminosity=60000;
	
	motor_turn_on(num);
	
	Sleep(1);
 	
	
	if(LSS_OK==motor_set_speed(num, 1500, &temp_rt)){
		printf("Motor speed = 500\n");
		
	}  
	take_data(rdata11, rdata12, rdata21, rdata22, rdata31, rdata32, rdata41, rdata42);
	printf("RData11=%d, max_luminosity =%d temp_data = %d", rdata11, max_luminosity, temp_data);
	while((rdata11<max_luminosity)&&(temp_data<rdata11))
	{
		Sleep(1);	
		take_data(rdata11, rdata12, rdata21, rdata22, rdata31, rdata32, rdata41, rdata42);
		temp_data=rdata11;
		printf("Temp data = %d", temp_data);
	}
	if(LSS_OK==motor_set_speed(num, 0, &temp_rt)){
		printf("Motor speed = 0\n");
		
	}    
	printf("Done\n");
	motor_turn_off(num);
}


void control(){
	uint16_t data11=0, data12=0, data21=0, data22=0, data31=0, data32=0, data41=0, data42=0;
	const int num1=3, num2=4,num3=2,num4=1; 
	uint16_t max_luminosity=60000; // максимальные показатели света лампы на сенсоре

	
	if(LSS_OK==sun_sensor_turn_on(num1)){
		printf("Sensor 1 on\n");
	}
	if(LSS_OK==sun_sensor_turn_on(num2)){
		printf("Sensor 2 on\n");
	}
	if(LSS_OK==sun_sensor_turn_on(num3)){
		printf("Sensor 3 on\n");
	}
	if(LSS_OK==sun_sensor_turn_on(num4)){
		printf("Sensor 4 on\n");
	}
	
	Sleep(1);

	take_data(data11, data12, data21, data22, data31, data32, data41, data42);
	printf("Data11=%d\n", data11);
	if(data11>max_luminosity){
		printf("Done\n");
	}
	else
	{
		if(data21>data41){
			rotate_right(data11, data12, data21, data22, data31, data32, data41, data42);
		}
		else{
			rotate_left(data11, data12, data21, data22, data31, data32, data41, data42);
		}
		
	}
}