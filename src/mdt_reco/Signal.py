import numpy as np
import random
import mdt_reco

class Signal():
    def __init__(self, config):
        self._config = config
        if config['Signal']['DataType'] == "Phase2":
            self._header_length = 5
            self._word_length = 40
            self._header_id = '10100000000'
            self._csm_id = '000'
            self._tdc_header_id = '11111000'
            self._tdc_trailer_id = '11110000000000000000'
            self._trailer_id = '1100'
            self._trailer_four_zeroes = '0000'
    
    # Encoding methods
    def convert_int_to_bits(self, n, width):
        """
        This function formats an int as a binary string in a specified bit size. If the initial
        binary number is not long enough for the specified bit size, the function pads the
        number with zeroes at the beginning of the bit string.

        Parameters:
        n : int
        The integer you are converting to binary

        width : int
        The amount of bits you want to be contained within the bit string.

        Returns:
        formatted_string : string
        A string of bits that represents the input integer in binary. The amount of bits
        contained in the string is equal to the width provided.
        """
        formatted_string = format(n, f'0{width}b')
        return formatted_string

    def write_bytes(self, bit_string, binary_file):
        """
        This function writes a word to a binary file split up into bytes.

        Parameters:
        bit_string : string
        A string of binary digits that represent the word (or words) you are trying to write to
        the file. Currently, the word must be divisible by 8, otherwise the remaining bits will
        not be written to the file.

        binary_file ; _io.BufferedWriter
        The binary file to which you are writing the word.
        """
        byte_to_write = ""
        for i in range(len(bit_string)):
            byte_to_write += bit_string[i]
            if i % 8 == 7:
                bit_number = int(byte_to_write, 2)
                byte_number = bit_number.to_bytes(1, byteorder="big")
                binary_file.write(byte_number)
                byte_to_write = ""

    def write_header(self, file):
        """
        This function writes a Header section for a singular event to a specified binary file.

        Parameters:
        file : _io.BufferedWriter
        The file to which you are writing the Header.

        Returns:
        trigger_lEdge_ns : float
        The trigger time in nanoseconds.

        event_id : int
        The ID of the event.
        """
        header_string = self._header_id
        event_id = random.getrandbits(12)
        print(event_id)
        header_string += self.convert_int_to_bits(event_id, 12)
        trigger_lEdge = random.getrandbits(17)
        print(trigger_lEdge)
        header_string += self.convert_int_to_bits(trigger_lEdge, 17)
        self.write_bytes(header_string, file)
        trigger_lEdge_ns = trigger_lEdge * (25 / 32)
        return trigger_lEdge_ns, event_id

    def write_tdc(self, event, file, index, trigger_time):
        """
        This function writes a TDC Header, TDC Data, and TDC Trailer section for a singular
        hit within an event.

        Parameters:
        event : dictionary
        The event that contains the hit information that you are encoding.

        file : _io.BufferedWriter
        The file to which you are writing the TDC sections.

        index : int
        The index that specifies which hit you are writing in the list of hits in the event.

        trigger_time : float
        The trigger time in nanoseconds.
        """
        tdc_header = self._csm_id
        tdc_id = int(event['tdc'][index])
        tdc_id_bits = self.convert_int_to_bits(tdc_id, 5)
        tdc_header += tdc_id_bits
        tdc_header += self._tdc_header_id
        tdc_event_id = random.getrandbits(12)
        tdc_header += self.convert_int_to_bits(tdc_event_id, 12)
        trigger_bcid = random.getrandbits(12)
        tdc_header += self.convert_int_to_bits(trigger_bcid, 12)
        self.write_bytes(tdc_header, file)
        tdc_data = self._csm_id
        tdc_data += tdc_id_bits
        chnl_id = int(event['channel'][index])
        chnl_id_bits = self.convert_int_to_bits(chnl_id, 5)
        print(f"Channel ID int = {chnl_id}")
        print(f"Channel ID bits = {chnl_id_bits}")
        tdc_data += chnl_id_bits
        mode = 1
        tdc_data += self.convert_int_to_bits(mode, 2)
        # print((event['tdc_time'][index] + trigger_time) * (32 / 25))
        # You have to multiply by 32 / 25 and ceil it
        lEdge = int((np.ceil(event['tdc_time'][index] + trigger_time) * (32 / 25)))
        tdc_data += self.convert_int_to_bits(lEdge, 17)
        # Made width an int, but the distribution returns floats with decimal points
        # It is not the specific amount of bits that you wanted.
        width = random.getrandbits(8)
        tdc_data += self.convert_int_to_bits(width, 8)
        self.write_bytes(tdc_data, file)
        tdc_trailer = self._csm_id
        tdc_trailer += tdc_id_bits
        tdc_trailer += self._tdc_trailer_id
        trigger_lost = random.getrandbits(1)
        tdc_trailer += self.convert_int_to_bits(trigger_lost, 1)
        time_out = random.getrandbits(1)
        tdc_trailer += self.convert_int_to_bits(time_out, 1)
        tdc_hit_count = random.getrandbits(10)
        tdc_trailer += self.convert_int_to_bits(tdc_hit_count, 10)
        self.write_bytes(tdc_trailer, file)

    def write_trailer(self, event, file, event_id):
        """
        This function writes a Trailer section for a singular event to a specified binary file.

        Parameters:
        event : dictionary
        The event that contains the hit information that you are encoding.

        file : _io.BufferedWriter
        The file to which you are writing the Trailer.

        event_id : int
        The ID of the event.
        """
        trailer_string = self._trailer_id
        # I have the tdc header count being the amount of hits in the event. Idk if this is correct.
        tdc_header_count = len(event['tdc'])
        trailer_string += self.convert_int_to_bits(tdc_header_count, 4)
        tdc_trailer_count = tdc_header_count
        trailer_string += self.convert_int_to_bits(tdc_trailer_count, 4)
        trailer_string += self.convert_int_to_bits(event_id, 12)
        header_count_error = random.getrandbits(1)
        trailer_string += self.convert_int_to_bits(header_count_error, 1)
        trailer_count_error = random.getrandbits(1)
        trailer_string += self.convert_int_to_bits(trailer_count_error, 1)
        trailer_string += self._trailer_four_zeroes
        hit_count = tdc_header_count
        trailer_string += self.convert_int_to_bits(hit_count, 10)
        self.write_bytes(trailer_string, file)


    def encode_event(self, event: dict, file):
        """
        This function writes a singular event to a specified binary file.

        event : dictionary
        The event that contains the hit information that you are encoding.

        file : string
        The path to the file to which you are writing the event.
        """
        # Open the file
        with open(file, "ab") as binary_file:
            # Write the Header
            trigger_lEdge, event_id = self.write_header(binary_file)

            # Write the TDC information for each hit
            for i in range(len(event['tdc'])):
                self.write_tdc(event, binary_file, i, trigger_lEdge)
            
            # Write the Trailer
            self.write_trailer(event, binary_file, event_id)

    def encode_events(self, events, file):
        """
        This function writes all of the events contained in events to a specified binary file.

        Parameters:
        events : list
        A list of the event objects being written to the binary file.

        file : string
        The path to the binary file to which you want to write the events.
        """
        for i in range(len(events)):
            self.encode_event(events[i], file)

    # Decoding methods
    def checkHeader(self, bytes):
        byte_value = int.from_bytes(bytes, byteorder='big')
        bit_string = format(byte_value, f'0{self._word_length}b')
        is_header = bit_string[:len(self._header_id)] == self._header_id
        return is_header
    
    def getBits(self, byte, width):
        byte_value = int.from_bytes(byte, byteorder='big')
        bit_string = self.convert_int_to_bits(byte_value, width)
        return bit_string
    
    def findHeaders(self, binary_file):
        with open(binary_file, 'rb') as b_file:
            # Initialize an array to store the Header locations
            header_locations = []
            # Counter for your location in the bytes
            counter = 0
            # Load the first five bytes
            bytes = b_file.read(self._header_length)
            # Add in some sort of check for partial bytes at the end of the file
            while bytes:
                if self.checkHeader(bytes):
                    header_locations.append(counter)
                counter += self._header_length
                bytes = b_file.read(self._header_length)
            print(header_locations)
        return header_locations
    
    def accumulateEvents(self, event):
        # Get overall trigger time
        geometry = mdt_reco.geo(self._config)
        trigger_bytes = event[0]
        trigger_string = self.getBits(trigger_bytes, self._word_length)
        trigger_time = int(trigger_string[23:], 2)
        csm_id_array = []
        tdc_id_array = []
        channel_array = []
        pulse_width_array = []
        tdc_time_array = []
        x_array = []
        y_array = []
        for i in range(len(event)):
            # Get information for a singular hit
            possible_tdc = self.getBits(event[i], self._word_length)
            if possible_tdc[8:16] == self._tdc_header_id:
                if i < len(event) - 2:
                    possible_tdc_trailer = self.getBits(event[i + 2], self._word_length)
                    if possible_tdc_trailer[8:28] == self._tdc_trailer_id:
                        tdc_data = self.getBits(event[i + 1], self._word_length)
                        csm_id = np.uint8(int(tdc_data[:3], 2))
                        tdc_id = np.uint8(int(tdc_data[3:8], 2))
                        channel = np.uint8(int(tdc_data[8:13], 2))
                        pulse_width = np.float32(int(tdc_data[32:], 2))
                        lEdge = int(tdc_data[15:32], 2)
                        print(f"tdc_time = {(lEdge - trigger_time) * (25 / 32)}")
                        tdc_time = np.float32((lEdge - trigger_time) * (25 / 32))
                        x, y = geometry.GetXY(tdc_id, channel)
                        csm_id_array.append(csm_id)
                        tdc_id_array.append(tdc_id)
                        channel_array.append(channel)
                        pulse_width_array.append(pulse_width)
                        tdc_time_array.append(tdc_time)
                        x_array.append(np.float32(x[0]))
                        y_array.append(np.float32(y[0]))
        event_object = mdt_reco.Event()
        event_object['csm_id'] = csm_id_array
        event_object['tdc_id'] = tdc_id_array
        event_object['channel'] = channel_array
        event_object['tdc_time'] = tdc_time_array
        event_object['pulseWidth'] = pulse_width_array
        event_object['x'] = x_array
        event_object['y'] = y_array
        return event_object

    
    def decodeEvents(self, binary_file):
        header_locations = self.findHeaders(binary_file)
        print(header_locations)
        with open(binary_file, 'rb') as b_file:
            packet = b_file.read(self._header_length)
            counter = 0
            event = []
            events = []
            next_header_location = -1
            last_header = False
            still_do = True
            good_packet = False
            while packet:
                if counter == next_header_location and still_do:
                    print("inside if")
                    if good_packet:
                        event_object = self.accumulateEvents(event)
                        events.append(event_object)
                        event = []
                        good_packet = False
                    else:
                        print(f"counter = {counter}")
                        event = []
                    if last_header:
                        still_do = False
                event.append(packet)
                if counter in header_locations:
                    index_of_header = header_locations.index(counter)
                    if counter < header_locations[-1]:
                        next_header_location = header_locations[index_of_header + 1]
                        if header_locations[index_of_header + 1] - header_locations[index_of_header] <= (self._config['Reconstruction']['MaxHits'] * 3 * self._header_length) + 2 * self._header_length and header_locations[index_of_header + 1] - header_locations[index_of_header] >= (self._config['Reconstruction']['MinHits'] * 3 * self._header_length) + 2 * self._header_length:
                            good_packet = True
                    else:
                        last_header = True
                        next_header_location = header_locations[index_of_header]
                counter += self._header_length
                packet = b_file.read(self._header_length)
                if not packet and last_header == True:
                    if counter - next_header_location <= self._config['Reconstruction']['MaxHits'] * 3 * self._header_length and counter - next_header_location >= self._config['Reconstruction']['MinHits'] * 3 * self._header_length:
                        event_object = self.accumulateEvents(event)
                        events.append(event_object)
        return events

                    # if counter > 0:
                    #     if header_locations[counter] - header_locations[counter - 1] > self._config['Reconstruction']['MaxHits'] * 3 or header_locations[counter] - header_locations[counter - 1] < self._config['Reconstruction']['MinHits'] * 3:
                    #         header_locations.pop(counter - 1)




config_path = "/Users/bstarzee/mdt-reco/configs/ci_config.yaml"
config = mdt_reco.configParser(config_path)
chamber=mdt_reco.geo(config)


signal_object = Signal(config)
test_file = "/Users/bstarzee/Downloads/mdt-reco_data/events_10k.npy"
array = np.load(test_file, allow_pickle=True)
print(array[0]['tdc_time'])
print(signal_object._config['Signal']['DataType'])
# signal_object.encode_event(array[0], "/Users/bstarzee/mdt-reco/src/mdt_reco/test_binary_19.txt")
# signal_object.encode_event(array[1], "/Users/bstarzee/mdt-reco/src/mdt_reco/test_binary_19.txt")
# signal_object.encode_event(array[2], "/Users/bstarzee/mdt-reco/src/mdt_reco/test_binary_19.txt")
# signal_object.encode_event(array[3], "/Users/bstarzee/mdt-reco/src/mdt_reco/test_binary_19.txt")
events = []
events = signal_object.decodeEvents("/Users/bstarzee/mdt-reco/src/mdt_reco/test_binary_19.txt")
geometry = mdt_reco.geo(signal_object._config)
events[2].draw(chamber=geometry)
# print(events)
# print(events[0]['csm_id'])
print(f"length = {len(events)}")
# print(array[2])
# print(events[2]['tdc_time'])
# print(events[3]['tdc_time'])
print(array[0]['tdc_time'])
print(array[1]['tdc_time'])
print(array[2]['tdc_time'])
print(array[3]['tdc_time'])
# signal_object.encode_events(array, "/Users/bstarzee/mdt-reco/src/mdt_reco/test_binary_16.txt")
# all_events = signal_object.decodeEvents("/Users/bstarzee/mdt-reco/src/mdt_reco/test_binary_16.txt")