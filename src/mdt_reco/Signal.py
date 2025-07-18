import numpy as np
import random
import mdt_reco

class Signal():
    """
    A class used to represent the information contained within a data format.

    Attributes:
    -----------
    config : ConfigParser
    The config file that gives information on the DataType under the header Signal
    and MaxHits and MinHits under the header Reconstruction.
    """
    def __init__(self, config):
        """
        Parameters:
        -----------
        config : ConfigParser
        The config file that gives information on the DataType under the header Signal
        and MaxHits and MinHits under the header Reconstruction.
        """
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
    def convertIntToBits(self, n, width):
        """
        This function formats an int as a binary string in a specified bit size. If the initial
        binary number is not long enough for the specified bit size, the function pads the
        number with zeroes at the beginning of the bit string.

        Parameters:
        -----------
        n : int
        The integer you are converting to binary

        width : int
        The amount of bits you want to be contained within the bit string.

        Returns:
        --------
        formatted_string : string
        A string of bits that represents the input integer in binary. The amount of bits
        contained in the string is equal to the width provided.
        """
        formatted_string = format(n, f'0{width}b')
        return formatted_string

    def writeBytes(self, bit_string, binary_file):
        """
        This function writes a word to a binary file split up into bytes.

        Parameters:
        -----------
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

    def writeHeader(self, file, index):
        """
        This function writes a Header section for a singular event to a specified binary file.

        Parameters:
        -----------
        file : _io.BufferedWriter
        The file to which you are writing the Header.

        Returns:
        --------
        trigger_lEdge_ns : float
        The trigger time in nanoseconds.

        event_id : int
        The ID of the event.
        """
        header_string = self._header_id
        event_id = index
        header_string += self.convertIntToBits(event_id, 12)
        trigger_lEdge = random.getrandbits(17)
        header_string += self.convertIntToBits(trigger_lEdge, 17)
        self.writeBytes(header_string, file)
        trigger_lEdge_ns = trigger_lEdge * (25 / 32)
        return trigger_lEdge_ns, event_id

    def writeTdc(self, event, file, index, trigger_time):
        """
        This function writes a TDC Header, TDC Data, and TDC Trailer section for a singular
        hit within an event.

        Parameters:
        -----------
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
        tdc_id_bits = self.convertIntToBits(tdc_id, 5)
        tdc_header += tdc_id_bits
        tdc_header += self._tdc_header_id
        tdc_event_id = random.getrandbits(12)
        tdc_header += self.convertIntToBits(tdc_event_id, 12)
        trigger_bcid = 0
        tdc_header += self.convertIntToBits(trigger_bcid, 12)
        self.writeBytes(tdc_header, file)
        tdc_data = self._csm_id
        tdc_data += tdc_id_bits
        chnl_id = int(event['channel'][index])
        chnl_id_bits = self.convertIntToBits(chnl_id, 5)
        tdc_data += chnl_id_bits
        mode = 1
        tdc_data += self.convertIntToBits(mode, 2)
        lEdge = int((np.ceil(event['tdc_time'][index] + trigger_time) * (32 / 25)))
        tdc_data += self.convertIntToBits(lEdge, 17)
        width = event['pulseWidth'][index]
        tdc_data += self.convertIntToBits(width, 8)
        self.writeBytes(tdc_data, file)
        tdc_trailer = self._csm_id
        tdc_trailer += tdc_id_bits
        tdc_trailer += self._tdc_trailer_id
        trigger_lost = random.getrandbits(1)
        tdc_trailer += self.convertIntToBits(trigger_lost, 1)
        time_out = random.getrandbits(1)
        tdc_trailer += self.convertIntToBits(time_out, 1)
        tdc_hit_count = random.getrandbits(10)
        tdc_trailer += self.convertIntToBits(tdc_hit_count, 10)
        self.writeBytes(tdc_trailer, file)

    def writeTrailer(self, event, file, event_id):
        """
        This function writes a Trailer section for a singular event to a specified binary file.

        Parameters:
        -----------
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
        trailer_string += self.convertIntToBits(tdc_header_count, 4)
        tdc_trailer_count = tdc_header_count
        trailer_string += self.convertIntToBits(tdc_trailer_count, 4)
        trailer_string += self.convertIntToBits(event_id, 12)
        header_count_error = random.getrandbits(1)
        trailer_string += self.convertIntToBits(header_count_error, 1)
        trailer_count_error = random.getrandbits(1)
        trailer_string += self.convertIntToBits(trailer_count_error, 1)
        trailer_string += self._trailer_four_zeroes
        hit_count = tdc_header_count
        trailer_string += self.convertIntToBits(hit_count, 10)
        self.writeBytes(trailer_string, file)


    def encodeEvent(self, event: dict, file, index):
        """
        This function writes a singular event to a specified binary file.

        Parameters:
        -----------
        event : dictionary
        The event that contains the hit information that you are encoding.

        file : string
        The path to the file to which you are writing the event.
        """
        # Open the file
        with open(file, "ab") as binary_file:
            # Write the Header
            trigger_lEdge, event_id = self.writeHeader(binary_file, index)

            # Write the TDC information for each hit
            for i in range(len(event['tdc'])):
                self.writeTdc(event, binary_file, i, trigger_lEdge)
            
            # Write the Trailer
            self.writeTrailer(event, binary_file, event_id)

    def encodeEvents(self, events, file):
        """
        This function writes all of the events contained in events to a specified binary file.

        Parameters:
        -----------
        events : list
        A list of the event objects being written to the binary file.

        file : string
        The path to the binary file to which you want to write the events.
        """
        for i in range(len(events)):
            self.encodeEvent(events[i], file, i)

    # Decoding methods
    def checkHeader(self, bytes):
        """
        This function checks if the input list of five bytes is Header.

        Parameters:
        -----------
        bytes : list
        A list of five bytes.

        Returns:
        --------
        is_header : bool
        True if the bytes are a Header, False if not.
        """
        byte_value = int.from_bytes(bytes, byteorder='big')
        bit_string = format(byte_value, f'0{self._word_length}b')
        is_header = bit_string[:len(self._header_id)] == self._header_id
        return is_header
    
    def getBits(self, byte, width):
        """
        This function returns a bit string representing the input byte.

        Parameters:
        -----------
        byte : bytes
        The byte you want to convert to a bit string.

        width : int
        The amount of bits you want to be contained within the bit string.

        Returns:
        --------
        bit_string : string
        The string of bits representing the input byte.
        """
        byte_value = int.from_bytes(byte, byteorder='big')
        bit_string = self.convertIntToBits(byte_value, width)
        return bit_string
    
    def findHeaders(self, binary_file):
        """
        This function finds the location of the Headers in a binary file that contains
        one or multiple events.

        Parameters:
        -----------
        binary_file : binaryIO
        A binary file that contains events.

        Returns:
        --------
        header_locations : list
        A list containing the location of each Header in the binary file.

        Raises:
        -------
        NotImplemented:
        This error is raised if the data format that you have specified is not
        currently supported.
        """
        if self._config['Signal']['DataType'] == "Phase2":
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
            return header_locations
        else:
            msg = f"Data format is {self.data_format} is not supported."
            raise NotImplemented(msg)
    
    def findTriggerTime(self, event):
        """
        This function finds the trigger time from the Header of an event.

        Parameters:
        -----------
        event : list
        A list of all the bytes contained in the event.

        Returns:
        --------
        trigger_time : int
        The trigger time in clock cycles.
        """
        trigger_bytes = event[0]
        trigger_string = self.getBits(trigger_bytes, self._word_length)
        trigger_time = int(trigger_string[23:], 2)
        return trigger_time
    
    def checkTdc(self, event, index):
        """
        This function checks to see if a three five byte sequence contains the
        TDC data for a singular event.

        Parameters:
        -----------
        event : list
        A list of all the bytes contained in the event.

        index : int
        The index of the hit within the list of events.

        Returns:
        --------
        is_tdc : bool
        This parameter returns True if the byte sequence is an event, False if not.
        """
        is_tdc = False
        possible_tdc = self.getBits(event[index], self._word_length)
        if possible_tdc[8:16] == self._tdc_header_id:
            if index < len(event) - 2:
                possible_tdc_trailer = self.getBits(event[index + 2], self._word_length)
                if possible_tdc_trailer[8:28] == self._tdc_trailer_id:
                    is_tdc = True
        return is_tdc
    
    def accumulateEvents(self, event):
        """
        This function creates an event object with all of the hit information
        encoded in a singular event. It adds arrays of the CSM ID, TDC ID,
        channel number, TDC time, pulse width, x coordinate of the hit and
        y coordinate of the hit to the event object.

        Parameters:
        -----------
        event : list
        A list of all the bytes contained in the event.

        Returns:
        --------
        event_object : Event
        An Event object that contains the information from the event list.
        """
        # Get overall trigger time
        geometry = mdt_reco.geo(self._config)
        trigger_time = self.findTriggerTime(event)
        csm_id_array = []
        tdc_id_array = []
        channel_array = []
        pulse_width_array = []
        tdc_time_array = []
        x_array = []
        y_array = []
        for i in range(len(event)):
            # Get information for a singular hit
            is_tdc = self.checkTdc(event, i)
            if is_tdc:
                tdc_data = self.getBits(event[i + 1], self._word_length)
                csm_id = np.uint8(int(tdc_data[:3], 2))
                tdc_id = np.uint8(int(tdc_data[3:8], 2))
                channel = np.uint8(int(tdc_data[8:13], 2))
                pulse_width = np.float32(int(tdc_data[32:], 2))
                lEdge = int(tdc_data[15:32], 2)
                tdc_time = np.float32((lEdge - trigger_time) * (25 / 32))
                x, y = geometry.getXY(tdc_id, channel)
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
        """
        This function produces a list of Event objects that represents all of
        the events contained in a binary file. The events in the file are decoded
        so that the CSM ID, TDC ID, channel number, TDC time, pulse width, x
        coordinate, and y coordinate can be easily read.

        Parameters:
        -----------
        binary_file : binaryIO
        A binary file containing one or multiple events.

        Returns:
        --------
        events : list
        A list of Event objects, all taken from the input file.

        Raises:
        -------
        NotImplemented:
        This error is raised if the data format that you have specified is not
        currently supported.
        """
        if self._config['Signal']['DataType'] == "Phase2":
            # Find the headers
            header_locations = self.findHeaders(binary_file)

            with open(binary_file, 'rb') as b_file:
                bytes = b_file.read(self._header_length)
                counter = 0
                event = []
                events = []
                next_header_location = -1
                last_header = False
                still_do = True
                good_packet = False
                while bytes:
                    if counter == next_header_location and still_do:
                        if good_packet:
                            event_object = self.accumulateEvents(event)
                            events.append(event_object)
                            event = []
                            good_packet = False
                        else:
                            event = []
                        if last_header:
                            still_do = False
                    event.append(bytes)
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
                    bytes = b_file.read(self._header_length)
                    if not bytes and last_header == True:
                        if counter - next_header_location <= self._config['Reconstruction']['MaxHits'] * 3 * self._header_length and counter - next_header_location >= self._config['Reconstruction']['MinHits'] * 3 * self._header_length:
                            event_object = self.accumulateEvents(event)
                            events.append(event_object)
            return events
        else:
            msg = f"Data format is {self.data_format} is not supported."
            raise NotImplemented(msg)