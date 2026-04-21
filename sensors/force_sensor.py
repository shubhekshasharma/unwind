import spidev
import time

# Setup SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel):
    """Read SPI data from MCP3008, channel 0-7"""
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

print("Reading FSR values... Press Ctrl+C to stop")
print("No pressure should be ~0-100, phone placed should be ~500-1000")
print()

try:
    while True:
        fsr_value = read_adc(0)  # Read channel 0
        print(f"FSR value: {fsr_value}")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nStopped!")
    spi.close()