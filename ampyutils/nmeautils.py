


def findTimeFields(parseNMEAs, fieldsNMEA):
    """
    findTimeFields finds the indices of time/date fields in the different NMEA mesages

    :param parseNMEAs: list of NMEA messages to parse
    :type parseNMEAs: list
    :param fieldsNMEA: contains (short)names of fields in this NMEA type of message
    :type fieldsNMEA: array

    :return timeFieldsIndices: contains indices where the time/date field is in the fieldsNMEA array
    :rtype timeFieldsIndices: dictionary
    """
    # add to sttinge and find indices of time info in the fields
    timeFieldsIndices = {}
    for nmeaType in parseNMEAs:
        # print('fieldsNMEA[{type:s}] = {fields!s}'.format(type=nmeaType, fields=fieldsNMEA[nmeaType]))

        # for getting timeinfo find location of timestamp end datestamp in the fieldsNMEA for each message, store it in dictionary about timing
        timeFieldsIndices[nmeaType] = {}
        for timeField in ('timestamp', 'day', 'month', 'year'):
            try:
                timeFieldsIndices[nmeaType][timeField] = fieldsNMEA[nmeaType].index(timeField)
            except ValueError:
                timeFieldsIndices[nmeaType][timeField] = None

    # print('timeFieldsIndices {!s}'.format(timeFieldsIndices))

    return timeFieldsIndices
