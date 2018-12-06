from datetime import timezone, datetime, timedelta


class TimeStamp(object):

    @staticmethod
    def get_time_stamp(delta=None):
        """
        @param delta    datetime.timedelta object specifying the difference
                            between today and the desired date
        """

        if delta is None:
            return datetime.now().timestamp()
        else:
            if not isinstance(delta, timedelta):
                raise Exception("delta must be an object of datetime.timedelta.")
            return (datetime.now() + delta).timestamp()

    @staticmethod
    def to_str(time_stamp):
        """
        Returns a string containing the time stamp in ISO format
        """
        return datetime.fromtimestamp(time_stamp, timezone.utc).isoformat()
