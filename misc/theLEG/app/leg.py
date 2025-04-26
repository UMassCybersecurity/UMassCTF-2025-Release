###############################################################
##                                                           ##
##                         THE LEG                           ##
##                                                           ##
###############################################################

import random


###############################################################
##                                                           ##
##                          MEMORY                           ##
##                                                           ##
###############################################################

LINE_SIZE = 16  # Number of words in a line
WORD_SIZE = 4  # Number of bytes in a word


class Memory:
    def __init__(self, latency):
        self.latency = latency  # Latency in clock cycles
        self.cycles_remaining = latency  # Remaining cycles for the current access
        self.current_stage = None  # Stage of the pipeline (e.g., fetch, decode, execute)

    def attempt_access(self, stage) -> bool:
        if self.current_stage is None:
            self.current_stage = stage
            
        if self.current_stage != stage:
            return False

        self.cycles_remaining -= 1
        return self.cycles_remaining <= 0
    
    def reset_access_state(self):
        self.cycles_remaining = random.randint((self.latency - (self.latency // 7)), (self.latency + (self.latency // 7)))
        self.current_stage = None
        
    def align(self, address):
        return address & ~0x3
    
    def make_address(self, address):
        aligned_address = self.align(address) // 4
        return (aligned_address // LINE_SIZE), (aligned_address % LINE_SIZE)
    
    def reset_state_deep(self):
        self.reset_access_state()
        if hasattr(self, 'lower_memory'):
            self.lower_memory.reset_state_deep()
        
        
class RAM(Memory):
    def __init__(self, latency, size):
        super().__init__(latency)
        self.data = [[0] * LINE_SIZE for _ in range(size // LINE_SIZE)]  # Initialize RAM with zeros
        self.size = size  # Size of the RAM in bytes

    def read(self, address: int, stage: str, line: bool):
        if not self.attempt_access(stage):
            return None
        self.reset_access_state()
        
        line_index, offset = self.make_address(address)
        try:
            if line:
                return self.data[line_index]
            else:
                return self.data[line_index][offset]
        except Exception as e:
            raise ValueError(f"Attempted access outside of memory space: {hex(address)}")


    def write(self, address, value, stage, line: bool):
        if not self.attempt_access(stage):
            return False
        self.reset_access_state()
        
        line_index, offset = self.make_address(address)
        if line:
            self.data[line_index] = value[:LINE_SIZE]
        else:
            self.data[line_index][offset] = value
        return True
    
    
class Cache(Memory):
    def __init__(self, latency, size, lower_memory):
        super().__init__(latency)
        self.size = size  # Size of the cache in bytes
        self.lower_memory = lower_memory  # Reference to the lower memory (RAM)
        self.flush()  # Initialize cache with zeros
        
    def flush(self):
        self.data = [[0] * LINE_SIZE for _ in range(self.size // LINE_SIZE)]
        self.tags = [None] * (self.size // LINE_SIZE)
        self.valid = [False] * (self.size // LINE_SIZE)
        
    def read(self, address: int, stage: str, line: bool):
        if not self.attempt_access(stage):
            return None
        
        aligned_address = self.align(address)
        line_index, offset = self.make_address(address)
        line_index = line_index % len(self.data)  # Ensure line index is within cache size
        
        # Check if the data is in the cache
        if self.tags[line_index] == (aligned_address // self.size) and self.valid[line_index]:
            self.reset_access_state()
            if line:
                return self.data[line_index]
            else:
                return self.data[line_index][offset]
            
        # If not in cache, read from lower memory (RAM)
        new_data = self.lower_memory.read(address, stage, True)
        if new_data is None:
            return None
        
        self.reset_access_state()
        
        # Update the cache with the new data
        self.data[line_index] = new_data
        self.tags[line_index] = (aligned_address // self.size)
        self.valid[line_index] = True
        if line:
            return self.data[line_index]
        else:
            return self.data[line_index][offset]
        
        
    def write(self, address, value, stage, line: bool) -> bool:
        if not self.attempt_access(stage):
            return False

        # Write through no allocate
        value = self.lower_memory.write(address, value, stage, line)
        if value is False:
            return False
        
        self.valid[self.make_address(address)[0] % len(self.data)] = False  # Invalidate the cache line
        self.reset_access_state()
        return True
    
    
###############################################################
##                                                           ##
##                      TOMASULO STUFF                       ##
##                                                           ##
###############################################################

class ReservationStation:
    def __init__(self, index):
        self.index = index        # Name of the reservation station (e.g., 0, 1, 2, etc.)
        self.reset()              # Reset the reservation station
        
    def reset(self):
        """Reset the reservation station."""
        self.busy = False         # Whether the station is currently in use
        self.unit = None          # Which functional unit this station is associated with (e.g., "ALU", "Memory", etc.)
        self.op = None            # Operation to perform (e.g., "ADD", "SUB", "MUL", "DIV")
        self.vj = None            # Value of first operand
        self.vk = None            # Value of second operand
        self.qj = None            # Reservation station producing first operand (or None if available)
        self.qk = None            # Reservation station producing second operand (or None if available)
        self.imm = None           # Immediate value (if applicable)
        self.dest = None          # Destination ROB entry

    def is_ready(self):
        """Check if both operands are available and the station can execute."""
        return self.busy and self.qj is None and self.qk is None and not self.dest.ready
    
    def reset(self):
        """Reset the reservation station."""
        self.busy = False
        self.unit = None
        self.op = None
        self.vj = None
        self.vk = None
        self.qj = None
        self.qk = None
        self.imm = None
        self.dest = None

        
class ReservationStations:
    def __init__(self, num_stations):
        self.stations = [ReservationStation(i) for i in range(num_stations)]

    def get_free_station(self):
        """Get a free reservation station."""
        for station in self.stations:
            if not station.busy:
                return station
        return None
    
    def reset(self):
        """Reset all reservation stations."""
        for station in self.stations:
            station.reset()
    
    def in_rob_order(self, rob):
        """Return the order of reservation stations in the ROB."""
        lst = []
        for station in self.stations:
            if station.busy:
                lst.append((station.index, station.dest.index))
        lst.sort(key=lambda x: x[1])
        return [x[0] for x in lst]
    
    def common_data_bus(self, value, destination):
        """Update the common data bus with the given value."""
        for station in self.stations:
            if station.qj == destination:
                station.vj = value
                station.qj = None
            if station.qk == destination:
                station.vk = value
                station.qk = None


class ReorderBufferEntry:
    def __init__(self, index):
        self.index = index        # Index of this entry in the reorder buffer
        self.reset()
        
    def reset(self):
        """Reset the entry."""
        self.busy = False         # Whether this entry is currently in use
        self.instr = None         # Operation to perform (tuple (UNIT, OP))
        self.address = None       # Address of the instruction that produced this entry
        self.prediction = None    # Prediction for branch instructions (True/False)
        self.state = None         # "Issued", "Executing", "WriteResult", "Commit"
        self.destination = None   # Destination register
        self.value = None         # Result value (when available)
        self.ld_str_addr = None   # If load/store, address in memory dealt with
        self.ready = False        # Whether the result is ready to commit
        
        
class ReorderBuffer:
    def __init__(self, size):
        self.entries = [ReorderBufferEntry(i) for i in range(size)]
        self.head = 0             # Pointer to the head of the buffer (oldest entry)
        self.tail = 0             # Pointer to the tail of the buffer (newest entry)
        self.size = size          # Size of the reorder buffer
    
    def get_all_before(self, index):
        i = self.head
        entries = []
        while i != index:
            entries.append(self.entries[i])
            i = (i + 1) % self.size
        return entries
    
    def get_all_stores_before(self, index):
        """Get all store instructions in the reorder buffer."""
        return [entry for entry in self.get_all_before(index) if entry.instr == (1, 1)]
    
    def reset(self):
        """Reset the reorder buffer."""
        for entry in self.entries:
            entry.reset()
        self.head = 0
        self.tail = 0
    
    def is_full(self):
        """Check if the reorder buffer is full."""
        return (self.tail + 1) % self.size == self.head
    
    def get_free_entry(self):
        """Get a free entry in the reorder buffer."""
        if self.is_full():
            return None
        entry = self.entries[self.tail]
        entry.busy = True
        self.tail = (self.tail + 1) % self.size
        return entry
    
    
class Registers:
    def __init__(self):
        num_registers = 16
        
        self.SP = 12
        self.BF = 13
        self.LR = 14
        self.PC = 15
        # Maps each register to the ROB entry producing its value (or None if no pending write)
        self.registers = [None] * num_registers
        # Architectural register file values
        self.values = [0] * num_registers
        
    def reset(self):
        """Reset the register file."""
        self.registers = [None] * len(self.registers)
        
        
class InstrQueue:
    def __init__(self):
        self.queue = []  # Queue to hold instructions

    def add_instruction(self, instruction):
        """Add an instruction to the queue."""
        self.queue.append(instruction)

    def get_next_instruction(self):
        """Get the next instruction from the queue."""
        if self.queue:
            return self.queue.pop(0)
        return None

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.queue) == 0
    
    def reset(self):
        """Reset the instruction queue."""
        self.queue = []
    
    
##################################################################
##                                                              ##
##                       BRANCH PREDICTOR                       ##
##                                                              ##
##################################################################
GLOBAL_HISTORY_SIZE = 16
COUNTER_BITS = 2
PHT_LENGTH = 2 ** GLOBAL_HISTORY_SIZE

class Predictor:
    def __init__(self):
        self.ghr = 0
        self.pht = [0] * PHT_LENGTH
    
    def get_table_index(self, program_counter):
        return (program_counter ^ self.ghr) & (PHT_LENGTH - 1)
    
    def predict(self, program_counter):
        index = self.get_table_index(program_counter)
        return self.pht[index] > (2 ** COUNTER_BITS // 2)
    
    def update(self, program_counter, branch_taken):
        index = self.get_table_index(program_counter)
        
        if branch_taken:
            if self.pht[index] < 4:
                self.pht[index] += 1
            
            self.global_history_register = ((self.ghr << 1) | 1) & (PHT_LENGTH - 1)
        else:
            if self.pht[index] > 0:
                self.pht[index] -= 1
            
            self.ghr = (self.ghr << 1) & (PHT_LENGTH - 1)


#################################################################
##                                                             ##
##                       EXCEPTION HANDLER                     ##
##                                                             ##
#################################################################

class ExceptionHandler:
    def __init__(self, latency):
        self.latency = latency
        self.cycles_remaining = random.randint((self.latency - (self.latency // 8)), (self.latency + (self.latency // 8)))
        
    def get_handler_location(self, type: str):
        handler_location = (MEMORY_SIZE // 2) - (MEMORY_SIZE // 10)
        handler_max_size = (MEMORY_SIZE // 100)
        
        match type:
            case "DATA_ABORT":
                return handler_location
            case "UNDEFINED_INSTRUCTION":
                return handler_location + handler_max_size
            case "PREFETCH_ABORT":
                return handler_location + (handler_max_size * 2)
            case _:
                raise ValueError(f"Unsupported exception handler: {type}")
         
    def delay(self):
        self.cycles_remaining -= 1
        if self.cycles_remaining <= 0:
            self.cycles_remaining = random.randint((self.latency - (self.latency // 8)), (self.latency + (self.latency // 8)))
            return True
        return False


#################################################################
##                                                             ##
##                         ISSUE STAGE                         ##
##                                                             ##
#################################################################

class IssueStage:
    def __init__(self, stations: ReservationStations, 
          rob: ReorderBuffer, 
          instr_queue: InstrQueue, 
          regs: Registers,
          memory,
          predictor: Predictor):
        self.stations = stations
        self.rob = rob
        self.instr_queue = instr_queue
        self.regs = regs
        self.memory = memory
        self.predictor = predictor

    def fetch(self):
        """Fetch the next instruction from memory."""
        
        instruction = self.memory.read(self.regs.values[self.regs.PC], 'FETCH', False)
        
        if instruction is not None:
            self.instr_queue.add_instruction(instruction)
            

    def decode(self, station: ReservationStation, instr: int):
        """Decode the next instruction."""
        
        station.unit = instr >> 29
        station.op = (instr >> 25) & 0xF
        
        addr_mode = (instr >> 22) & 0x7
        match addr_mode:
            case 0b000:  # Register-Register addressing mode
                rs1 = (instr >> 18) & 0xF
                rs2 = (instr >> 14) & 0xF
                station.dest.destination = rs1
                
                if self.regs.registers[rs1] is not None:
                    station.qj = self.regs.registers[rs1]
                else:
                    station.vj = self.regs.values[rs1]
                    
                if self.regs.registers[rs2] is not None:
                    station.qk = self.regs.registers[rs2]
                else:
                    station.vk = self.regs.values[rs2]
                
            case 0b001:  # Register-Register with offset addressing mode
                station.imm = instr & 0xFFFF
                
                rs1 = (instr >> 18) & 0xF
                rs2 = (instr >> 14) & 0xF
                station.dest.destination = rs1
                
                if self.regs.registers[rs1] is not None:
                    station.qj = self.regs.registers[rs1]
                else:
                    station.vj = self.regs.values[rs1]
                    
                if self.regs.registers[rs2] is not None:
                    station.qk = self.regs.registers[rs2]
                else:
                    station.vk = self.regs.values[rs2]
                    
            case 0b010:  # Register-Immediate addressing mode
                station.imm = instr & 0xFFFF
                
                rs1 = (instr >> 18) & 0xF
                station.dest.destination = rs1
                
                if self.regs.registers[rs1] is not None:
                    station.qj = self.regs.registers[rs1]
                else:
                    station.vj = self.regs.values[rs1]
                    
            case 0b011:  # Immediate addressing mode
                station.dest.destination = self.regs.PC
                station.imm = instr & 0x3FFFFF
                
            case 0b100:  # Single Register addressing mode
                rs1 = (instr >> 18) & 0xF
                station.dest.destination = rs1
                
                if self.regs.registers[rs1] is not None:
                    station.qj = self.regs.registers[rs1]
                else:
                    station.vj = self.regs.values[rs1]
                
            case _:
                raise ValueError(f"Invalid addressing mode: {addr_mode}")
            
        if station.unit == 0 and station.op == 8: # Compare instruction
            station.dest.destination = self.regs.BF
            
        if station.unit == 3: # Branch instruction
            if self.regs.registers[self.regs.BF] is not None:
                station.qk = self.regs.registers[self.regs.BF]
            else:
                station.vk = self.regs.values[self.regs.BF]
                
            station.dest.destination = self.regs.PC
            

    def tick(self):

        self.fetch()
            
        instr = self.instr_queue.get_next_instruction()
        if instr is None:
            return
        
        station = self.stations.get_free_station()
        if station is None:
            return
        
        rob_entry = self.rob.get_free_entry()
        if rob_entry is None:
            return
        
        station.busy = True
        station.dest = rob_entry
        station.dest.address = self.regs.values[self.regs.PC]
        try:
            self.decode(station, instr)
        except:
            station.dest.reset()
            station.reset()
            return
            
        station.dest.instr = (station.unit, station.op)
        
        if station.unit == 3: # Branch instruction
            if self.predictor.predict(station.dest.address): # Branch taken
                station.dest.prediction = True
                if station.qj is not None: # Branch target is in a reorder buffer entry
                    self.regs.registers[self.regs.PC] = rob_entry.index
                else: # Branch target is available
                    vj = station.vj if station.vj is not None else 0
                    imm = station.imm if station.imm is not None else 0
                    self.regs.values[self.regs.PC] = vj + imm
            else:
                station.dest.prediction = False
                # Update the PC with the next instruction address
                self.regs.values[self.regs.PC] += 4
        else:
            # Update the PC with the next instruction address
            self.regs.values[self.regs.PC] += 4
        
        if not (station.unit == 1 and station.op == 1) and not (station.unit == 4 and station.op == 0): # Store instruction or Flush instruction
            self.regs.registers[station.dest.destination] = rob_entry.index


#################################################################
##                                                             ##
##                        EXECUTE STAGE                        ##
##                                                             ##
#################################################################

class FunctionalUnit:
    def __init__(self, type: str, latency: int, rob: ReorderBuffer, memory: Cache):
        self.latency = latency  # Latency in cycles
        self.busy = False  # Whether the unit is currently busy
        self.type = type # Type of functional unit (e.g., ALU, Control)
        self.station = None  # Reservation station associated with this unit
        self.rob = rob
        self.memory = memory
           
    
    def reset(self):
        """Reset the functional unit."""
        self.busy = False
        self.station = None
        self.cycles_remaining = self.latency
        
        
    def assign(self, station: ReservationStation):
        """Assign a reservation station to this functional unit."""
        self.cycles_remaining = self.latency
        self.station = station
        self.busy = True
   
        
    def execute(self) -> int:
        """Execute the function with the given reservation station."""
        if not self.busy:
            raise RuntimeError("Functional unit is not busy.")
        
        if self.cycles_remaining > 0:
            self.cycles_remaining -= 1
            return None
        
        if self.type == "ALU":
            return self.alu()
        elif self.type == "Memory":
            return self.load_store()
        elif self.type == "Control":
            return self.control_unit()
        else:
            raise ValueError(f"Unsupported functional unit type: {self.type}")
        
        
    def load_store(self):
        
        op = self.station.op
        vj = self.station.vj if self.station.vj is not None else 0
        vk = self.station.vk if self.station.vk is not None else 0
        imm = self.station.imm if self.station.imm is not None else 0
        
        value = vj
        address = vk + imm
        
        self.station.dest.ld_str_addr = address
        
        if op == 0b000:  # Load
            for store in self.rob.get_all_stores_before(self.station.dest.index):
                if store.value == address or store.value is None:
                    return None
            
            return self.memory.read(address, "EXECUTE", False)
        
        elif op == 0b001:  # Store
            return value
            
    
    def alu(self) -> int:
        """Perform the ALU operation."""
        
        op = self.station.op
        vj = self.station.vj if self.station.vj is not None else 0
        vk = self.station.vk if self.station.vk is not None else 0
        imm = self.station.imm if self.station.imm is not None else 0
        
        match op:
            case 0b0000:  # MOV
                return vk + imm
            case 0b0001:  # ADD
                return vj + (vk + imm)
            case 0b0010:  # SUB
                return vj - (vk + imm)
            case 0b0011:  # MUL
                return vj * (vk + imm)
            case 0b0100:  # DIV
                return vj // (vk + imm)
            case 0b0101:  # AND
                return vj & (vk + imm)
            case 0b0110:  # OR
                return vj | (vk + imm)
            case 0b0111:  # XOR
                return vj ^ (vk + imm)
            case 0b1000:  # CMP
                return vj - (vk + imm)  # Assuming CMP is a subtraction for comparison
            case 0b1001:  # MOD
                return vj % (vk + imm)
            case 0b1010:  # NOT
                return ~(vj + imm)
            case 0b1011:  # SHL (Shift Left)
                return vj << (vk + imm)
            case 0b1100:  # SHR (Shift Right)
                return vj >> (vk + imm)
            case _:  # Unsupported operation
                raise ValueError(f"Unsupported ALU operation: {op}")
            
            
    def control_unit(self):
        """Perform the control operation."""
        
        op = self.station.op
        flags = self.station.vk if self.station.vk is not None else 0
        
        vj = self.station.vj if self.station.vj is not None else 0
        imm = self.station.imm if self.station.imm is not None else 0
        
        dest = vj + imm
        
        match op:
            case 0:  # BEQ
                if flags == 0:
                    return dest
            case 1:  # BLT
                if flags < 0:
                    return dest
            case 2:  # BGT
                if flags > 0:
                    return dest
            case 3:  # BNE
                if flags != 0:
                    return dest
            case 4:  # B
                return dest
            case 7:  # BGE
                if flags >= 0:
                    return dest
            case 8:  # BLE
                if flags <= 0:
                    return dest
            case _:
                raise ValueError(f"Unsupported control operation: {op}")
            
        return -1  # Branch not taken

class ExecuteStage:
    def __init__(self, stations: ReservationStations, rob: ReorderBuffer, memory: Cache):
        self.stations = stations
        self.rob = rob
        
        self.alu_units = [FunctionalUnit("ALU", 0, rob, memory) for _ in range(2)]
        self.control_units = [FunctionalUnit("Control", 0, rob, memory) for _ in range(1)]
        self.memory_units = [FunctionalUnit("Memory", 0, rob, memory) for _ in range(1)]
        
    def all_units(self):
        return self.alu_units + self.control_units + self.memory_units
    
    def reset(self):
        for unit in self.all_units():
            unit.reset()
        
    def tick(self):
        """Execute instructions in the reservation stations."""
        
        for station_num in self.stations.in_rob_order(self.rob):
            station = self.stations.stations[station_num]
            if station.is_ready():
                if station.unit == 0: # ALU unit
                    for unit in self.alu_units:
                        if not unit.busy:
                            unit.assign(station)
                            break
                elif station.unit == 1:
                    for unit in self.memory_units:
                        if not unit.busy:
                            unit.assign(station)
                            break
                elif station.unit == 2: # Interrupt unit
                    station.dest.ready = True
                    station.reset()
                    break
                elif station.unit == 3: # Control unit
                    for unit in self.control_units:
                        if not unit.busy:
                            unit.assign(station)
                            break
                elif station.unit == 4: # Meta unit
                    station.dest.ready = True
                    station.reset()
                    break
                else:
                    raise ValueError(f"Unknown functional unit type: {station.unit}")
        
        for unit in self.all_units():
            if unit.busy:
                result = unit.execute()
                if result is not None:
                    unit.station.dest.value = result
                    unit.station.dest.ready = True
                    unit.station.reset()
                    unit.reset()
                        
                
##################################################################
##                                                              ##
##                          WRITE RESULT                        ##
##                                                              ##
##################################################################

class WriteResultStage:
    def __init__(self, stations: ReservationStations, rob: ReorderBuffer):
        self.stations = stations
        self.rob = rob
        
    def tick(self):
        """Write the result back to the registers."""
        
        for entry in self.rob.entries:
            if entry.ready:
                # Write the result back to the register file
                if (entry.destination is not None) and entry.instr != (4, 1):
                    self.stations.common_data_bus(entry.value, entry.index)
                
                # Mark the ROB entry as ready for commit
                entry.state = "Commit"
                    
            
##################################################################
##                                                              ##
##                          COMMIT STAGE                        ##
##                                                              ##
##################################################################

class CommitStage:
    def __init__(self, rob: ReorderBuffer, stations: ReservationStations, regs: Registers, predictor: Predictor, memory: Cache, instr_queue: InstrQueue, exception_handler: ExceptionHandler, execute_stage: ExecuteStage):
        self.rob = rob
        self.stations = stations
        self.regs = regs
        self.predictor = predictor
        self.memory = memory
        self.instr_queue = instr_queue
        self.exception_handler = exception_handler
        self.execute_stage = execute_stage
       
        
    def start_with_clean_state_at(self, addr_to_reset_to):
        self.regs.values[self.regs.PC] = addr_to_reset_to
        self.rob.reset()
        self.regs.reset()
        self.stations.reset()
        self.instr_queue.reset()
        self.memory.reset_state_deep()
        self.execute_stage.reset()
        

    def tick(self, cycle_count):
        """Commit the results from the reorder buffer."""
        
        if self.rob.head == self.rob.tail:
            return
        
        entry = self.rob.entries[self.rob.head]
        
        if entry.state == "Commit":
            if entry.instr[0] == 2: # Interrupt unit
                # Handle interrupt
                return True
            
            if entry.prediction is not None:
                # Update the global history register based on the prediction
                self.predictor.update(entry.address, entry.value != -1)
                
                if entry.prediction is True and entry.value == -1:
                    # Branch incorrectly predicted taken
                    self.start_with_clean_state_at(entry.address + 4)
                    return
                
                if entry.prediction is False and entry.value != -1:
                    # Branch incorrectly predicted not taken
                    self.start_with_clean_state_at(entry.value)
                    return

                entry.reset()
                self.rob.head = (self.rob.head + 1) % self.rob.size
                return 
            
            
            if entry.instr == (4, 0): # Flush cache instruction
                self.memory.flush()
                
            if entry.instr == (4, 1): # Cycle count instruction
                entry.value = cycle_count
                self.stations.common_data_bus(entry.value, entry.index)

            if entry.instr == (1, 1): # Store instruction
                if entry.ld_str_addr >= MEMORY_SIZE // 2:
                    # Handle out-of-bounds memory access
                    if not self.exception_handler.delay():
                        return
                    raise ValueError(f"Attempt to access protected memory: {entry.ld_str_addr}")
                else:
                    if not self.memory.write(entry.ld_str_addr, entry.value, "COMMIT", False):
                        return
                    
            if entry.instr == (1, 0): # Load instruction
                if entry.ld_str_addr >= MEMORY_SIZE // 2:
                    # Handle out-of-bounds memory access
                    if not self.exception_handler.delay():
                        return
                    else:
                        handler_addr = self.exception_handler.get_handler_location("DATA_ABORT")
                        self.start_with_clean_state_at(handler_addr)
                        return
        
            
            # Commit the result to the register file
            if entry.destination is not None and entry.instr != (1, 1) and entry.instr != (4, 0):
                self.regs.values[entry.destination] = entry.value
                
                if self.regs.registers[entry.destination] == entry.index:
                    # If the register is still pointing to this ROB entry, clear it
                    self.regs.registers[entry.destination] = None
            
            # Reset the ROB entry
            entry.reset()
            
            # Move the head pointer forward
            self.rob.head = (self.rob.head + 1) % self.rob.size
 
            
##################################################################
##                                                              ##
##                          ASSEMBLER                           ##
##                                                              ##
##################################################################  
            
def assemble(code: list):
    
    code = list(filter(lambda x: not x.startswith(";"), code))  # commentz
    code = list(map(lambda x: x.split(";")[0].strip(), code))  # commentz
    code = list(filter(lambda x: x != "", code))  # blank linez
    
    tokens = []
    
    for tok in code:
        mnemonic = tok.split(' ')[0]
        filtered = tok.replace(mnemonic,"",1).replace(' ','').lower().split(',')
        if(filtered[0] == ""):
            filtered[0] = "unset"
            
        if(len(filtered) < 2):
            filtered.append("unset")
        tokens.append((mnemonic.lower(),filtered[0],filtered[1]))

    REGISTERS = ['r0','r1','r2','r3','r4','r5','r6','r7','r8','r9','r10','r11','sp','bf','lr','pc']

    ALU = ["mov","add","sub","mul","div","and","or","xor","cmp","mod","not","lsl","lsr"]
    MEM = ["ldr","str"]
    INT = ["syscall","halt"]
    FLOW = ["beq","blt","bgt","bne","b","call","ret","bge","ble"]
    META = ["flush", "cycles"]


    UNITS = [ALU,MEM,INT,FLOW,META]

    instructions = []

    for ind, (ins,op1,op2) in enumerate(tokens):
        TYPE = -1
        OPCODE = -1
        ADDRMODE = -1
        OPERAND1 = -1
        OPERAND2 = -1
        OFFSET = -1
        for i in range(len(UNITS)):
            if ins in UNITS[i]:
                TYPE = i
                break
        if(TYPE == -1):
            raise ValueError(f"Line {hex(ind * 4)}: no valid instruction for {ins}")
        
        OPCODE = UNITS[TYPE].index(ins)


        if op1 in REGISTERS and op2 in REGISTERS:
            ADDRMODE = 0
            OPERAND1 = REGISTERS.index(op1)
            OPERAND2 = REGISTERS.index(op2)
        elif op1 in REGISTERS:
            OPERAND1 = REGISTERS.index(op1)
            for reg in REGISTERS:
                if(reg in op2):
                    ADDRMODE = 1
                    raise ValueError(f"Have not implemented offset based '{ins} {op1},{op2}'")
            try:
                ADDRMODE = 2
                
                OPERAND2 = int(op2,16) & 262143 if op2[0:2] == "0x" else int(op2)
            except Exception as e:
                ADDRMODE = 4
        elif op1 == "unset" and op2 == "unset":
            ADDRMODE = 0
            OPERAND1 = 0
            OPERAND2 = 0
        else:
            try:
                ADDRMODE = 3
                OPERAND1 = int(op1,16) & 0b11111111111111111111111 if op1[0:2] == "0x" else int(op1)
            except Exception as e:
                raise Exception(e)

        INSTRUCTION = 0x0

        if ADDRMODE == 0:
            INSTRUCTION = TYPE << 29 | OPCODE << 25 | ADDRMODE << 22 | OPERAND1 << 18 | OPERAND2 << 14
        elif ADDRMODE == 1:
            INSTRUCTION = TYPE << 29 | OPCODE << 25 | ADDRMODE << 22 | OPERAND1 << 18 | OPERAND2 << 14 | OFFSET
        elif ADDRMODE == 2:
            INSTRUCTION = TYPE << 29 | OPCODE << 25 | ADDRMODE << 22 | OPERAND1 << 18 | OPERAND2 
        elif ADDRMODE == 3:
            INSTRUCTION = TYPE << 29 | OPCODE << 25 | ADDRMODE << 22 | OPERAND1
        elif ADDRMODE == 4:
            INSTRUCTION = TYPE << 29 | OPCODE << 25 | ADDRMODE << 22 | OPERAND1 << 18 
        else:
            raise ValueError(f"Invalid addr mode for '{ins} {op1},{op2}'")
        
        instructions.append(INSTRUCTION & 0xffffffff)
    
    return instructions
            
                       
###################################################################
##                                                               ##
##                            PROCESSOR                          ##
##                                                               ##
###################################################################

MEMORY_SIZE = 0x1000000
CACHE_SIZE = 0x100000

class LEG:
    def __init__(self):
        self.cycle_count = 0
        
        self.ram = RAM(latency=15, size=MEMORY_SIZE)  
        self.instr_cache = Cache(latency=1, size=CACHE_SIZE, lower_memory=self.ram)
        self.data_cache = Cache(latency=1, size=CACHE_SIZE, lower_memory=self.ram)
    
        self.instr_queue = InstrQueue()
        self.regs = Registers()
        self.reorder_buffer = ReorderBuffer(size=16)
        self.reservation_stations = ReservationStations(num_stations=16)
        self.predictor = Predictor()
        self.exception_handler = ExceptionHandler(latency=50)
        
        self.issue = IssueStage(self.reservation_stations, self.reorder_buffer, self.instr_queue, self.regs, self.instr_cache, self.predictor)
        self.execute = ExecuteStage(self.reservation_stations, self.reorder_buffer, self.data_cache)
        self.write_result = WriteResultStage(self.reservation_stations, self.reorder_buffer)
        self.commit = CommitStage(self.reorder_buffer, self.reservation_stations, self.regs, self.predictor, self.data_cache, self.instr_queue, self.exception_handler, self.execute)
        
    def flash(self, addr, code):
        addr = addr // 4 * 4
        for i in range(len(code)):
            while not self.instr_cache.write(addr + (i * 4), code[i], "FETCH", False):
                continue
            
    def register_handlers(self, exception_handlers):
        for handler in exception_handlers:
            loc = self.exception_handler.get_handler_location(handler[0].strip(".handler "))
            self.flash(loc, handler[1])
        
    def tick(self):
        self.cycle_count += 1
        
        self.issue.tick()
        self.execute.tick()
        self.write_result.tick()
        return self.commit.tick(self.cycle_count)
    
    def run(self):
        done = False
        while not done and self.cycle_count <= 1000000:
            done = self.tick()
         
        
###################################################################
##                                                               ##
##                               UI                              ##
##                                                               ##
###################################################################

from flask import Flask, current_app, request
from base64 import b64encode

app = Flask(__name__)

        
def hexdump_ram(data):
    dump = ""
    hexify = lambda line: " ".join(line[x:x+2] for x in range(0, len(line), 2)) + "  " + "".join(chr(x) if 32 <= x <= 126 else "." for x in [int(line[x:x+2], 16) for x in range(0, len(line), 2)])
    
    for i, line in enumerate(data[:0x80]):
        index = i * 64
        dump += f"{index:08x}" + "  " + hexify("".join(f"{x:08x}" for x in line[0:4])) + "\n"
        dump += f"{index + 16:08x}" + "  " + hexify("".join(f"{x:08x}" for x in line[4:8])) + "\n"
        dump += f"{index + 32:08x}" + "  " + hexify("".join(f"{x:08x}" for x in line[8:12])) + "\n"
        dump += f"{index + 48:08x}" + "  " + hexify("".join(f"{x:08x}" for x in line[12:16])) + "\n"
        
    return dump


def parse_handlers(raw_handlers: list):
    raw_handlers = list(filter(lambda x: not x.startswith(";"), raw_handlers))  # commentz
    raw_handlers = list(map(lambda x: x.split(";")[0].strip(), raw_handlers))  # commentz
    raw_handlers = list(filter(lambda x: x != "", raw_handlers))

    handlers = []
    for item in raw_handlers:
        try:
            if item.startswith(".handler"):
                handlers.append([item])
            else:
                handlers[-1].append(item)
        except:
            raise Exception("Invalid exception handler format")
               
    assembled_handlers = []
    for handler in handlers:
        asm = [x.strip() for x in handler[1:]]
        assembled_handlers.append([handler[0]])
        assembled_handlers[-1].append(asm)
        
    for i, handler in enumerate(assembled_handlers):
        assembled_handlers[i][1] = assemble(handler[1])
        
    return assembled_handlers


def flag_to_words(flag: bytes):
    flag = flag + (b"\x00" * (len(flag) % 4))
    return [int.from_bytes(flag[i:i+4], "big") for i in range(0, len(flag), 4)]


@app.route("/")
def index():
    return current_app.send_static_file("index.html")


@app.route("/run", methods=["POST"])
def run():
    try:
        stuff = request.get_json()
        
        assembly = stuff["assembly"]
        exception_handlers = stuff["exception_handlers"]
        
        assert type(assembly) == list and type(exception_handlers) == list

        code = assemble(assembly)
        handlers = parse_handlers(exception_handlers)
        
        with open("./flag.txt", "rb") as fd:
            flag = flag_to_words(fd.read())
                        
        leg = LEG()
        
        leg.flash(0, code)
        leg.register_handlers(handlers)
        
        leg.flash(0x800000, flag)
        
        leg.run()
        
        return { "memory": b64encode(hexdump_ram(leg.ram.data).encode()).decode() }

    except Exception as e:
        return { "error": f"{e}" }
    
    
        
if __name__ == "__main__":
    app.run(host="0.0.0.0")

        
    