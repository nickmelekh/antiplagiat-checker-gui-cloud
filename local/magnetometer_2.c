#include "libschsat.h"

void control(void) {
	uint16_t num = 1;
	printf("Number of magnetometer: %i", num);
	
	magnetometer_turn_on(num);
	Sleep(1);
	printf("Magnetometer number %i was enabled\n",magnetometer_get_state(num));
	
	int16_t x, y, z;
	int i;
	
	if (magnetometer_get_state(num) != 1) {
		magnetometer_request_reset(num); 
	} 
	for (i=0; i<10; i++) {
		if ( magnetometer_request_raw(num, &x, &y, &z) == LSS_OK) {
			printf("x: %i, y: %i, z: %i", &x, &y, &z);
		} else printf("Error");
	}
	
	Sleep(1);
	magnetometer_turn_off(1);
	printf("Magnetometer number %i was disabled\n",magnetometer_get_state(num));
	
	
}