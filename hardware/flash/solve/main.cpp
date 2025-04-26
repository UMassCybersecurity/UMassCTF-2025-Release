#include <Arduino.h>
#include <Wire.h>

#define START_ADDR 0x0
#define DUMP_SIZE 0x1000
#define BLOCK_SIZE 32
#define EEPROM_ADDR 0b1010100

void read_eeprom(uint16_t addr, size_t size, uint8_t* buff){
  Wire.beginTransmission(EEPROM_ADDR);
  Wire.write((uint8_t *)&addr,2);
  Wire.endTransmission(false);
  Wire.requestFrom(EEPROM_ADDR, size);
  Wire.readBytes(buff, size);
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Wire.begin();

  uint8_t buff[BLOCK_SIZE];
  uint16_t addr = START_ADDR;
  // const char *target = "UMASS";
  // uint8_t target_len = strlen(target);
  // uint8_t matched = 0;

  while(addr < START_ADDR + DUMP_SIZE) {
    read_eeprom(addr, BLOCK_SIZE, buff);
    // for(uint16_t i = 0; i < BLOCK_SIZE; i++){
    //   if(buff[i] == target[matched]){
    //     matched++;
    //     if(matched == target_len){
    //       Serial.write(buff, BLOCK_SIZE);
    //     }
    //   } else {
    //     matched = 0;
    //   }
    // }
    Serial.write(buff, BLOCK_SIZE);
    addr += BLOCK_SIZE;
  }
}

void loop() {
}