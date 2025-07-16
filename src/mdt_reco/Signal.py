import numpy as np
import random

class Signal():
    def __init__(self, config):
        self._config = config
        if config['Signal']['DataType'] == "Phase2":
            self._header_length = 5
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
        header_string = self._header_string
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
        tdc_data += chnl_id_bits
        mode = 1
        tdc_data += self.convert_int_to_bits(mode, 2)
        print((event['tdc_time'][index] + trigger_time) * (32 / 25))
        # You have to multiply by 32 / 25 and ceil it
        lEdge = int((np.ceil(event['tdc_time'][index] + trigger_time) * (32 / 25)))
        tdc_data += self.convert_int_to_bits(lEdge, 17)
        # Made width an int, but the distribution returns floats with decimal points
        # It is not the specific amount of bits that you wanted.
        width = int(np.random.normal(loc=200, scale=25))
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
        bit_string = format(byte_value, '40b')
        is_header = bit_string[:len(self._header_id)] == self._header_id
        return is_header

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
        return header_locations
    

                    # if counter > 0:
                    #     if header_locations[counter] - header_locations[counter - 1] > self._config['Reconstruction']['MaxHits'] * 3 or header_locations[counter] - header_locations[counter - 1] < self._config['Reconstruction']['MinHits'] * 3:
                    #         header_locations.pop(counter - 1)

    