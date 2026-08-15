class OtpExpiredException(Exception):
    """Raised when the OTP key does not exist in Redis (expired or never generated)."""

    def __init__(self, message: str = "OTP has expired or was never generated."):
        self.message = message
        super().__init__(self.message)


class OtpMaxAttemptsException(Exception):
    """Raised when the maximum number of OTP verification attempts has been exceeded."""

    def __init__(self, message: str = "Maximum OTP verification attempts exceeded."):
        self.message = message
        super().__init__(self.message)


class OtpInvalidException(Exception):
    """Raised when the provided OTP does not match the stored value."""

    def __init__(self, message: str = "Invalid OTP provided."):
        self.message = message
        super().__init__(self.message)
