class MCP23S08_Pin:
    IN = 0
    OUT = 1
    PULL_UP = 1
    
    def __init__(self, bus, id):
        self._bus = bus
        self._address = id[0]
        self._bit = 1 << id[1]
        self._mask = 255 ^ self._bit
        
    def init(self, mode=-1, pull=-1, value=None):
        self.mode(mode)
        self.pull(pull)
        self.value(value)

    def _do(self, x, register, blank, on_low, on_high):
        if x == blank:
            return on_high if bool(self._bus._read(self._address, register) & self._bit) else on_low
        elif x in [on_low, on_high]:
            self._bus._write(self._address, register, self._mask, self._bit if x == on_high else 0)
        else:
            raise ValueError
        
    def value(self, x=None):
        return self._do(x if x is None else bool(x), MCP23S08.GPIO, None, False, True)

    def __call__(self, x=None):
        return self.value(x)

    def on(self):
        self.value(True)

    def off(self):
        self.value(False)

    def low(self):
        self.value(False)

    def high(self):
        self.value(True)

    def mode(self, x=-1):
        return self._do(x, MCP23S08.IODIR, -1, self.OUT, self.IN)
        
    def pull(self, x=-1):
        return self._do(x, MCP23S08.GPPU, -1, None, self.PULL_UP)      

    def toggle(self):
        self.value(not self.value())
    

class MCP23S08:
    IODIR = 0x00    # I/O Direction Register (0 - output, 1 - input)
    IPOL = 0x01     # Input Polarity Register (0 - normal, 1 - inverted)
    GPINTEN = 0x02  # Interrupt-On-Change Control Register (0 - disabled, 1 - enabled)
    DEFVAL = 0x03   # Default Compare Register for Interrupt-On-Change
    INTCON = 0x04   # Interrupt Control Register (0 - interrupt on edge, 1 - interrupt on change from DEFVAL)
    IOCON = 0x05    # Configuration Register
    GPPU = 0x06     # Pull-Up Resistor Configuration Register (0 - disabled, 1 - enabled)
    INTF = 0x07     # Interrupt Flag Register (0 - no pending interrupt, 1 - pending interrupt)
    INTCAP = 0x08   # Interrupt Capture Register (captures port value at time of interrupt)
    GPIO = 0x09     # Port Register
    OLAT = 0x0A     # Output Latch Register
    
    def __init__(self, spi, cs, reset):
        self._spi = spi
        self._cs = cs
        self._reset = reset
        self._cs.init(mode=self._cs.OUT)
        self._reset.init(mode=self._reset.OUT)
        self._cs(1)
        self._reset(0)
        self._reset(1)        
        self._write(0, MCP23S08.IOCON, 0b11110111, 0b00001000)

    def _read(self, address, register):
        txdata = bytearray(2)
        txdata[0] = 0b01000001 | (address << 1)
        txdata[1] = register
        try:
            self._cs(0)
            self._spi.write(txdata)
            return self._spi.read(1)[0]
        finally:
            self._cs(1)
            
    def _write(self, address, register, mask, bits):
        old_value = self._read(address, register)
        new_value = (old_value & mask) | bits
        if old_value != new_value:
            txdata = bytearray(3)
            txdata[0] = txdata[0] = 0b01000000 | (address << 1)
            txdata[1] = register
            txdata[2] = new_value
            try:
                self._cs(0)
                self._spi.write(txdata)
            finally:
                self._cs(1)
                
    def Pin(self, id, mode=-1, pull=-1, value=None):
        pin = MCP23S08_Pin(self, id)
        pin.init(mode=mode, pull=pull, value=value)
        return pin
